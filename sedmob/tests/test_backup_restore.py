"""Unit tests for database backup and restore."""
import io
import json

from sedmob.models import (
    Profile, Bed, BedPhoto,
    LithologyType, Lithology, StructureType, Structure,
    GrainClastic, GrainCarbonate, Bioturbation, Boundary,
)


def test_backup_returns_200_with_correct_headers(client):
    """GET /backup returns 200 with correct Content-Type and Content-Disposition. (Req 1.4)"""
    resp = client.get("/backup")
    assert resp.status_code == 200
    assert resp.content_type == "application/json"
    cd = resp.headers["Content-Disposition"]
    assert cd.startswith("attachment; filename=gneisswork_backup_")
    assert cd.endswith(".json")


def test_restore_no_file_returns_error(client):
    """POST /restore with no file returns error flash and redirect. (Req 2.10)"""
    resp = client.post("/restore", follow_redirects=True)
    assert b"No file provided" in resp.data


def test_restore_invalid_json_returns_error(client):
    """POST /restore with invalid JSON returns error flash and redirect. (Req 2.2)"""
    data = {"file": (io.BytesIO(b"not json at all{{{"), "bad.json")}
    resp = client.post("/restore", data=data, content_type="multipart/form-data",
                       follow_redirects=True)
    assert b"Invalid JSON file" in resp.data


def test_restore_missing_version_returns_error(client):
    """POST /restore with JSON missing version key returns error flash and redirect. (Req 2.3)"""
    payload = json.dumps({"profiles": []}).encode()
    data = {"file": (io.BytesIO(payload), "no_version.json")}
    resp = client.post("/restore", data=data, content_type="multipart/form-data",
                       follow_redirects=True)
    assert b"Unrecognized backup format" in resp.data


def test_restore_valid_backup_success(client):
    """POST /restore with valid backup redirects with success flash. (Req 2.9)"""
    # Get a valid backup first
    backup_resp = client.get("/backup")
    backup_data = backup_resp.data
    # Restore from it
    data = {"file": (io.BytesIO(backup_data), "backup.json")}
    resp = client.post("/restore", data=data, content_type="multipart/form-data",
                       follow_redirects=True)
    assert b"Database restored successfully" in resp.data


def test_restore_rollback_on_database_error(client, db):
    """Restore rolls back on database error. (Req 2.8)"""
    from unittest.mock import patch

    # Get a valid backup first
    backup_resp = client.get("/backup")
    backup_json = json.loads(backup_resp.data)

    # Patch db.session.commit inside the restore path to raise an error
    with patch.object(db.session, "commit", side_effect=Exception("simulated DB error")):
        payload = json.dumps(backup_json).encode()
        data = {"file": (io.BytesIO(payload), "backup.json")}
        resp = client.post("/restore", data=data, content_type="multipart/form-data",
                           follow_redirects=True)
    # Should flash the error, not success
    assert b"simulated DB error" in resp.data
    assert b"Database restored successfully" not in resp.data


def test_settings_page_returns_200_with_backup_and_restore(client):
    """GET /settings returns 200 with backup link and restore form. (Req 3.1, 3.2)"""
    resp = client.get("/settings")
    assert resp.status_code == 200
    assert b"/backup" in resp.data
    assert b'action="/restore"' in resp.data


def test_settings_page_contains_data_replacement_warning(client):
    """Settings page contains warning about data replacement. (Req 3.3)"""
    resp = client.get("/settings")
    assert b"replace all existing data" in resp.data


def test_settings_page_contains_scope_note(client):
    """Settings page contains note about backup scope. (Req 3.4)"""
    resp = client.get("/settings")
    assert b"database records only" in resp.data


def test_nav_bar_settings_link_position(client):
    """Nav bar contains Settings link between Reference Data and Docs. (Req 4.1, 4.2)"""
    resp = client.get("/")
    html = resp.data.decode()
    ref_pos = html.find("Reference Data")
    settings_pos = html.find(">Settings<")
    docs_pos = html.find("Docs")
    assert ref_pos < settings_pos < docs_pos


def test_round_trip_empty_user_tables_preserves_reference_data(client, db):
    """Round-trip with empty user tables preserves seeded reference data. (Req 5.3)"""
    # Capture reference data counts before backup
    counts_before = {
        "lithology_types": LithologyType.query.count(),
        "lithologies": Lithology.query.count(),
        "structure_types": StructureType.query.count(),
        "structures": Structure.query.count(),
        "grain_clastic": GrainClastic.query.count(),
        "grain_carbonate": GrainCarbonate.query.count(),
        "bioturbation": Bioturbation.query.count(),
        "boundaries": Boundary.query.count(),
    }
    # Ensure there is seeded reference data
    assert counts_before["lithology_types"] > 0

    # Backup
    backup_resp = client.get("/backup")
    backup_data = backup_resp.data

    # Restore
    data = {"file": (io.BytesIO(backup_data), "backup.json")}
    resp = client.post("/restore", data=data, content_type="multipart/form-data",
                       follow_redirects=True)
    assert b"Database restored successfully" in resp.data

    # Verify reference data counts are identical
    counts_after = {
        "lithology_types": LithologyType.query.count(),
        "lithologies": Lithology.query.count(),
        "structure_types": StructureType.query.count(),
        "structures": Structure.query.count(),
        "grain_clastic": GrainClastic.query.count(),
        "grain_carbonate": GrainCarbonate.query.count(),
        "bioturbation": Bioturbation.query.count(),
        "boundaries": Boundary.query.count(),
    }
    assert counts_before == counts_after
