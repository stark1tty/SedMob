"""Property-based tests for lithology percentage balancing.

Uses hypothesis to verify invariants across many random inputs.
"""
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from sedmob.models import Profile, Bed


# ---------------------------------------------------------------------------
# Pure Python mirror of the JS balancing logic from bed_form.html
# ---------------------------------------------------------------------------

def balance(lit1: int, lit2: int, lit3: int, changed: str) -> tuple[int, int, int]:
    """Mirror the client-side JS balancing algorithm.

    Implements the same priority cascade as the inline script in bed_form.html:
    - Lit1 is clamped to [0, 100], unconstrained otherwise.
    - Lit2 is clamped to the remaining budget after Lit1.
    - Lit3 is always the remainder (100 - Lit1 - Lit2).

    Parameters
    ----------
    lit1, lit2, lit3 : int
        Current percentage values (may be out of range).
    changed : str
        Which field was changed: "lit1", "lit2", or "lit3".

    Returns
    -------
    tuple of (int, int, int)
        Balanced percentage values, each in [0, 100], summing to 100.
    """

    def clamp(v: int, lo: int, hi: int) -> int:
        return max(lo, min(hi, v))

    if changed == "lit1":
        lit1 = clamp(lit1, 0, 100)
        budget = 100 - lit1
        if budget < lit2:
            lit2 = budget
        lit2 = max(0, lit2)
        lit3 = 100 - lit1 - lit2
    elif changed == "lit2":
        lit1 = clamp(lit1, 0, 100)
        lit2 = clamp(lit2, 0, 100 - lit1)
        lit3 = 100 - lit1 - lit2
    elif changed == "lit3":
        lit1 = clamp(lit1, 0, 100)
        lit2 = clamp(lit2, 0, 100 - lit1)
        lit3 = 100 - lit1 - lit2

    return lit1, lit2, lit3


# ---------------------------------------------------------------------------
# Property 1: Client-side balancing preserves sum-to-100 invariant
# ---------------------------------------------------------------------------

class TestBalancingInvariant:
    """Feature: 02-lithology-percentage-balancing, Property 1: Client-side balancing preserves sum-to-100 invariant"""

    @given(
        lit1=st.integers(min_value=-200, max_value=300),
        lit2=st.integers(min_value=-200, max_value=300),
        lit3=st.integers(min_value=-200, max_value=300),
        changed=st.sampled_from(["lit1", "lit2", "lit3"]),
    )
    @settings(max_examples=100)
    def test_balance_sum_to_100_and_in_range(self, lit1, lit2, lit3, changed):
        """After balancing, all outputs are in [0, 100] and sum to exactly 100.

        **Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 5.1, 5.2, 5.3**
        """
        o1, o2, o3 = balance(lit1, lit2, lit3, changed)

        # All outputs must be integers
        assert isinstance(o1, int)
        assert isinstance(o2, int)
        assert isinstance(o3, int)

        # All outputs in [0, 100]
        assert 0 <= o1 <= 100, f"lit1 out of range: {o1}"
        assert 0 <= o2 <= 100, f"lit2 out of range: {o2}"
        assert 0 <= o3 <= 100, f"lit3 out of range: {o3}"

        # Sum to exactly 100
        assert o1 + o2 + o3 == 100, f"sum is {o1 + o2 + o3}, expected 100"


# ---------------------------------------------------------------------------
# Property 2: Server-side validation accepts iff percentages are valid
# ---------------------------------------------------------------------------

def _create_profile(client):
    """Create a test profile and return it."""
    client.post("/profile/new", data={"name": "PropTestLog"})
    return Profile.query.first()


# Strategy: mix of valid integer strings, out-of-range integers, and non-numeric junk
_pct_strategy = st.one_of(
    st.integers(min_value=-50, max_value=200).map(str),
    st.sampled_from(["", "abc", "3.5", " ", "None"]),
)


class TestServerValidation:
    """Feature: 02-lithology-percentage-balancing, Property 2: Server-side validation accepts if and only if percentages are valid"""

    @given(
        s1=_pct_strategy,
        s2=_pct_strategy,
        s3=_pct_strategy,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_bed_created_iff_valid(self, client, db, s1, s2, s3):
        """A bed is created if and only if all three values parse as integers
        in [0, 100] and sum to 100.

        **Validates: Requirements 6.2, 6.3, 6.4, 6.5**
        """
        # Determine expected validity
        try:
            v1, v2, v3 = int(s1), int(s2), int(s3)
            expected_valid = (
                0 <= v1 <= 100
                and 0 <= v2 <= 100
                and 0 <= v3 <= 100
                and v1 + v2 + v3 == 100
            )
        except (ValueError, TypeError):
            expected_valid = False

        # Ensure a profile exists
        profile = Profile.query.first()
        if profile is None:
            profile = _create_profile(client)

        beds_before = Bed.query.count()

        client.post(
            f"/profile/{profile.id}/bed/new",
            data={
                "thickness": "10",
                "lit1_percentage": s1,
                "lit2_percentage": s2,
                "lit3_percentage": s3,
            },
            follow_redirects=True,
        )

        beds_after = Bed.query.count()
        bed_was_created = beds_after > beds_before

        assert bed_was_created == expected_valid, (
            f"s1={s1!r}, s2={s2!r}, s3={s3!r}: "
            f"expected_valid={expected_valid}, bed_was_created={bed_was_created}"
        )
