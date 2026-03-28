"""Tests for bulk CSV export (ZIP of all profiles)."""
import csv
import io
import zipfile

from sedmob.models import Profile


def _create_profile_with_bed(client, name, bed_data=None):
    """Create a profile and optionally add a bed via POST requests."""
    client.post("/profile/new", data={"name": name})
    p = Profile.query.filter_by(name=name).first()
    if bed_data:
        for bd in bed_data:
            client.post(f"/profile/{p.id}/bed/new", data=bd)
    return p


def test_empty_database_redirect(client, db):
    """GET /export/all with no profiles returns 302 + flash message."""
    resp = client.get("/export/all")
    assert resp.status_code == 302

    follow = client.get("/export/all", follow_redirects=True)
    assert b"No profiles to export." in follow.data


def test_valid_zip_response(client, db):
    """GET /export/all returns a valid ZIP with correct headers."""
    _create_profile_with_bed(client, "Log A", [
        {"thickness": "10", "name": "B1",
         "lit1_percentage": "100", "lit2_percentage": "0", "lit3_percentage": "0"},
    ])
    _create_profile_with_bed(client, "Log B", [
        {"thickness": "20", "name": "B2",
         "lit1_percentage": "100", "lit2_percentage": "0", "lit3_percentage": "0"},
    ])

    resp = client.get("/export/all")
    assert resp.status_code == 200
    assert resp.content_type == "application/zip"
    assert "gneisswork_export.zip" in resp.headers["Content-Disposition"]


def test_zip_contains_correct_csv_files(client, db):
    """ZIP has one CSV per profile with correct filenames and headers."""
    _create_profile_with_bed(client, "Log A", [
        {"thickness": "10", "name": "B1",
         "lit1_percentage": "100", "lit2_percentage": "0", "lit3_percentage": "0"},
    ])
    _create_profile_with_bed(client, "Log B", [
        {"thickness": "20", "name": "B2",
         "lit1_percentage": "100", "lit2_percentage": "0", "lit3_percentage": "0"},
    ])

    resp = client.get("/export/all")
    zf = zipfile.ZipFile(io.BytesIO(resp.data))
    names = zf.namelist()

    assert len(names) == 2
    assert "Log_A_export.csv" in names
    assert "Log_B_export.csv" in names

    # Verify CSV headers match in both files
    for name in names:
        reader = csv.reader(io.StringIO(zf.read(name).decode()))
        header = next(reader)
        assert header[0] == "THICKNESS (CM)"
        assert "Position" in header


def test_special_character_filenames(client, db):
    """Profile name with special chars produces a safe ZIP entry name."""
    _create_profile_with_bed(client, "My Log!@#$", [
        {"thickness": "5", "name": "Bed",
         "lit1_percentage": "100", "lit2_percentage": "0", "lit3_percentage": "0"},
    ])

    resp = client.get("/export/all")
    zf = zipfile.ZipFile(io.BytesIO(resp.data))
    names = zf.namelist()

    assert len(names) == 1
    assert names[0] == "My_Log_export.csv"


def test_export_all_button_visible_with_profiles(client, db):
    """Home page shows Export All button with btn-success when profiles exist."""
    _create_profile_with_bed(client, "SomeLog")
    resp = client.get("/")
    assert b'btn-success' in resp.data
    assert b'Export All' in resp.data
    assert b'/export/all' in resp.data


def test_export_all_button_hidden_when_empty(client, db):
    """Home page hides Export All button when no profiles exist."""
    resp = client.get("/")
    assert b'Export All' not in resp.data


def test_csv_helper_matches_route_output(client, db):
    """CSV from /export/all matches CSV from /profile/<id>/export for same profile."""
    _create_profile_with_bed(client, "MatchLog", [
        {"thickness": "15", "name": "Bed1", "facies": "F1",
         "lit1_type": "Sandstone", "lit1_percentage": "80",
         "lit2_percentage": "20", "lit3_percentage": "0",
         "boundary": "Sharp"},
        {"thickness": "25", "name": "Bed2",
         "lit1_percentage": "100", "lit2_percentage": "0", "lit3_percentage": "0"},
    ])
    p = Profile.query.filter_by(name="MatchLog").first()

    # Get single-profile CSV
    single_resp = client.get(f"/profile/{p.id}/export")
    single_csv = single_resp.data.decode()

    # Get bulk ZIP and extract the same profile's CSV
    bulk_resp = client.get("/export/all")
    zf = zipfile.ZipFile(io.BytesIO(bulk_resp.data))
    bulk_csv = zf.read("MatchLog_export.csv").decode()

    assert single_csv == bulk_csv


# ── Property-Based Tests ──────────────────────────────────

import re

from hypothesis import given, settings
from hypothesis import strategies as st


class TestFilenameSanitizationProperty:
    """Property 3: Filename sanitization produces safe names.

    **Validates: Requirements 2.5**
    """

    @staticmethod
    def _sanitize_filename(name):
        """Replicate the sanitize logic from app.py for direct testing."""
        name = name.replace(" ", "_")
        return re.sub(r"[^a-zA-Z0-9_-]", "", name)

    @given(name=st.text())
    @settings(max_examples=100)
    def test_sanitized_name_contains_only_safe_characters(self, name):
        """For any Unicode string, sanitized output contains only [a-zA-Z0-9_-]."""
        result = self._sanitize_filename(name)
        assert re.fullmatch(r"[a-zA-Z0-9_-]*", result) is not None, (
            f"Sanitized name {result!r} contains unsafe characters"
        )

    @given(name=st.text())
    @settings(max_examples=100)
    def test_sanitized_name_has_no_spaces(self, name):
        """For any Unicode string, sanitized output contains no spaces."""
        result = self._sanitize_filename(name)
        assert " " not in result, (
            f"Sanitized name {result!r} still contains spaces"
        )


from hypothesis import HealthCheck
from sedmob.models import Bed


class TestBedRowOrderingProperty:
    """Property 4: Bed rows ordered by position.

    **Validates: Requirements 2.6**
    """

    @given(
        positions=st.lists(
            st.integers(min_value=1, max_value=50),
            min_size=1,
            max_size=10,
            unique=True,
        )
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_csv_rows_ordered_by_position(self, client, db, positions):
        """For any shuffled list of unique positions, exported CSV rows are in ascending position order."""
        # Create a profile
        client.post("/profile/new", data={"name": "OrderTest"})
        profile = Profile.query.filter_by(name="OrderTest").first()

        # Create beds via POST (auto-assigns sequential positions)
        for _ in positions:
            client.post(
                f"/profile/{profile.id}/bed/new",
                data={
                    "thickness": "10",
                    "lit1_percentage": "100",
                    "lit2_percentage": "0",
                    "lit3_percentage": "0",
                },
            )

        # Reassign positions to the shuffled values
        beds = Bed.query.filter_by(profile_id=profile.id).order_by(Bed.position).all()
        for bed, pos in zip(beds, positions):
            bed.position = pos
        db.session.commit()

        # Export and parse CSV
        resp = client.get(f"/profile/{profile.id}/export")
        assert resp.status_code == 200

        reader = csv.reader(io.StringIO(resp.data.decode()))
        header = next(reader)
        pos_index = header.index("Position")

        csv_positions = [int(row[pos_index]) for row in reader]

        assert csv_positions == sorted(positions), (
            f"CSV positions {csv_positions} are not in ascending order "
            f"(expected {sorted(positions)})"
        )

        # Clean up for next hypothesis example
        Bed.query.filter_by(profile_id=profile.id).delete()
        db.session.delete(profile)
        db.session.commit()
