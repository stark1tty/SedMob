"""Tests for server-side lithology percentage validation (Requirement 7)."""
from sedmob.models import Profile, Bed


def _create_profile(client):
    client.post("/profile/new", data={"name": "TestLog"})
    return Profile.query.first()


def _bed_data(**overrides):
    """Return minimal valid bed POST data, with optional overrides."""
    data = {
        "thickness": "10",
        "lit1_percentage": "100",
        "lit2_percentage": "0",
        "lit3_percentage": "0",
    }
    data.update(overrides)
    return data


def test_valid_60_30_10(client, db):
    """7.1 Valid 60/30/10 → bed saved."""
    p = _create_profile(client)
    resp = client.post(
        f"/profile/{p.id}/bed/new",
        data=_bed_data(
            lit1_percentage="60",
            lit2_percentage="30",
            lit3_percentage="10",
        ),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Bed saved." in resp.data
    assert Bed.query.count() == 1


def test_invalid_sum_110(client, db):
    """7.2 Invalid 50/30/30 (sum=110) → rejected."""
    p = _create_profile(client)
    resp = client.post(
        f"/profile/{p.id}/bed/new",
        data=_bed_data(
            lit1_percentage="50",
            lit2_percentage="30",
            lit3_percentage="30",
        ),
        follow_redirects=True,
    )
    assert b"Lithology percentages must sum to 100." in resp.data
    assert Bed.query.count() == 0


def test_boundary_100_0_0(client, db):
    """7.3 Boundary 100/0/0 → bed saved."""
    p = _create_profile(client)
    resp = client.post(
        f"/profile/{p.id}/bed/new",
        data=_bed_data(
            lit1_percentage="100",
            lit2_percentage="0",
            lit3_percentage="0",
        ),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Bed saved." in resp.data
    assert Bed.query.count() == 1


def test_empty_strings(client, db):
    """7.4 Empty strings → rejected with integer error."""
    p = _create_profile(client)
    resp = client.post(
        f"/profile/{p.id}/bed/new",
        data=_bed_data(
            lit1_percentage="",
            lit2_percentage="",
            lit3_percentage="",
        ),
        follow_redirects=True,
    )
    assert b"Lithology percentages must be valid integers." in resp.data
    assert Bed.query.count() == 0


def test_negative_values(client, db):
    """7.5 Negative value -10/60/50 → rejected with range error."""
    p = _create_profile(client)
    resp = client.post(
        f"/profile/{p.id}/bed/new",
        data=_bed_data(
            lit1_percentage="-10",
            lit2_percentage="60",
            lit3_percentage="50",
        ),
        follow_redirects=True,
    )
    assert b"Each lithology percentage must be between 0 and 100." in resp.data
    assert Bed.query.count() == 0


def test_out_of_range(client, db):
    """7.6 Out-of-range 150/-50/0 → rejected with range error."""
    p = _create_profile(client)
    resp = client.post(
        f"/profile/{p.id}/bed/new",
        data=_bed_data(
            lit1_percentage="150",
            lit2_percentage="-50",
            lit3_percentage="0",
        ),
        follow_redirects=True,
    )
    assert b"Each lithology percentage must be between 0 and 100." in resp.data
    assert Bed.query.count() == 0


def test_non_numeric_strings(client, db):
    """7.7 Non-numeric "abc"/30/70 → rejected with integer error."""
    p = _create_profile(client)
    resp = client.post(
        f"/profile/{p.id}/bed/new",
        data=_bed_data(
            lit1_percentage="abc",
            lit2_percentage="30",
            lit3_percentage="70",
        ),
        follow_redirects=True,
    )
    assert b"Lithology percentages must be valid integers." in resp.data
    assert Bed.query.count() == 0
