"""Property-based tests for bed direction reversal."""
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from sedmob.models import Profile, Bed

# Default valid percentages matching bed form defaults.
_PCT = {"lit1_percentage": "100", "lit2_percentage": "0", "lit3_percentage": "0"}


def _create_profile(client, direction="off"):
    """Create a profile via POST and return it."""
    client.post("/profile/new", data={"name": "TestLog", "direction": direction})
    return Profile.query.first()


def _add_beds(client, profile_id, n):
    """Add n beds to a profile via POST requests."""
    for i in range(n):
        client.post(
            f"/profile/{profile_id}/bed/new",
            data={"thickness": str(i + 1), "lit1_percentage": "100",
                  "lit2_percentage": "0", "lit3_percentage": "0"},
        )


# Feature: bed-direction-reversal, Property 1: Reversal applies correct formula
@given(bed_count=st.integers(min_value=0, max_value=20))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_reversal_applies_correct_formula(client, db, bed_count):
    """Property 1: After toggling direction, each bed position == N - original + 1.

    Validates: Requirements 1.1
    """
    # Create a profile with direction "off"
    profile = _create_profile(client, direction="off")
    _add_beds(client, profile.id, bed_count)

    # Record original positions keyed by bed id
    original_positions = {
        bed.id: bed.position
        for bed in Bed.query.filter_by(profile_id=profile.id).all()
    }
    n = len(original_positions)

    # Toggle direction from "off" to "on"
    client.post(
        f"/profile/{profile.id}",
        data={"name": "TestLog", "direction": "on"},
    )

    # Assert each bed's new position matches the reversal formula
    for bed in Bed.query.filter_by(profile_id=profile.id).all():
        expected = n - original_positions[bed.id] + 1
        assert bed.position == expected, (
            f"Bed {bed.id}: expected position {expected}, got {bed.position} "
            f"(N={n}, original={original_positions[bed.id]})"
        )

    # Clean up for next hypothesis example
    db.session.query(Bed).delete()
    db.session.query(Profile).delete()
    db.session.commit()


# Feature: bed-direction-reversal, Property 2: Same direction means no position change
@given(
    bed_count=st.integers(min_value=0, max_value=20),
    direction=st.sampled_from(["off", "on"]),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_same_direction_no_position_change(client, db, bed_count, direction):
    """Property 2: Submitting the same direction leaves all bed positions unchanged.

    Validates: Requirements 1.2
    """
    # Create a profile with the given direction
    profile = _create_profile(client, direction=direction)
    _add_beds(client, profile.id, bed_count)

    # Record positions before re-submitting
    positions_before = {
        bed.id: bed.position
        for bed in Bed.query.filter_by(profile_id=profile.id).all()
    }

    # Submit profile form with the SAME direction value
    client.post(
        f"/profile/{profile.id}",
        data={"name": "TestLog", "direction": direction},
    )

    # Assert all positions are unchanged
    for bed in Bed.query.filter_by(profile_id=profile.id).all():
        assert bed.position == positions_before[bed.id], (
            f"Bed {bed.id}: position changed from {positions_before[bed.id]} "
            f"to {bed.position} when direction was unchanged ('{direction}')"
        )

    # Clean up for next hypothesis example
    db.session.query(Bed).delete()
    db.session.query(Profile).delete()
    db.session.commit()


# Feature: bed-direction-reversal, Property 3: Double reversal is identity (round-trip)
@given(bed_count=st.integers(min_value=0, max_value=20))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_double_reversal_is_identity(client, db, bed_count):
    """Property 3: Toggling direction twice restores all bed positions.

    Validates: Requirements 2.1, 2.2
    """
    # Create a profile with direction "off"
    profile = _create_profile(client, direction="off")
    _add_beds(client, profile.id, bed_count)

    # Record original positions keyed by bed id
    original_positions = {
        bed.id: bed.position
        for bed in Bed.query.filter_by(profile_id=profile.id).all()
    }

    # First toggle: "off" -> "on"
    client.post(
        f"/profile/{profile.id}",
        data={"name": "TestLog", "direction": "on"},
    )

    # Second toggle: "on" -> "off"
    client.post(
        f"/profile/{profile.id}",
        data={"name": "TestLog", "direction": "off"},
    )

    # Assert all positions match the originals
    for bed in Bed.query.filter_by(profile_id=profile.id).all():
        assert bed.position == original_positions[bed.id], (
            f"Bed {bed.id}: expected position {original_positions[bed.id]}, "
            f"got {bed.position} after double reversal (N={bed_count})"
        )

    # Clean up for next hypothesis example
    db.session.query(Bed).delete()
    db.session.query(Profile).delete()
    db.session.commit()


# Feature: bed-direction-reversal, Property 4: Only position changes during reversal
@given(bed_count=st.integers(min_value=1, max_value=10))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_only_position_changes_during_reversal(client, db, bed_count):
    """Property 4: Toggling direction changes only position; all other columns are preserved.

    Validates: Requirements 4.1, 4.2
    """
    _NON_POSITION_COLUMNS = [
        "name", "thickness", "facies", "notes", "boundary", "paleocurrent",
        "top", "bottom",
        "lit1_group", "lit1_type", "lit1_percentage",
        "lit2_group", "lit2_type", "lit2_percentage",
        "lit3_group", "lit3_type", "lit3_percentage",
        "size_clastic_base", "phi_clastic_base",
        "size_clastic_top", "phi_clastic_top",
        "size_carbo_base", "phi_carbo_base",
        "size_carbo_top", "phi_carbo_top",
        "bioturbation_type", "bioturbation_intensity",
        "structures", "bed_symbols", "audio",
    ]

    # Create a profile with direction "off"
    profile = _create_profile(client, direction="off")
    _add_beds(client, profile.id, bed_count)

    # Snapshot non-position columns for each bed (keyed by bed id)
    beds_before = {
        bed.id: {col: getattr(bed, col) for col in _NON_POSITION_COLUMNS}
        for bed in Bed.query.filter_by(profile_id=profile.id).all()
    }
    count_before = len(beds_before)

    # Toggle direction from "off" to "on"
    client.post(
        f"/profile/{profile.id}",
        data={"name": "TestLog", "direction": "on"},
    )

    # Assert bed count is preserved (Req 4.2)
    beds_after = Bed.query.filter_by(profile_id=profile.id).all()
    assert len(beds_after) == count_before, (
        f"Bed count changed from {count_before} to {len(beds_after)} after reversal"
    )

    # Assert all non-position columns are unchanged (Req 4.1)
    for bed in beds_after:
        for col in _NON_POSITION_COLUMNS:
            assert getattr(bed, col) == beds_before[bed.id][col], (
                f"Bed {bed.id}: column '{col}' changed from "
                f"{beds_before[bed.id][col]!r} to {getattr(bed, col)!r} after reversal"
            )

    # Clean up for next hypothesis example
    db.session.query(Bed).delete()
    db.session.query(Profile).delete()
    db.session.commit()
