"""Tests for CSV export."""
import csv
import io
from sedmob.models import Profile


def test_csv_export(client, db):
    client.post("/profile/new", data={"name": "ExportLog"})
    p = Profile.query.first()
    client.post(f"/profile/{p.id}/bed/new", data={
        "thickness": "50", "name": "Bed1", "facies": "F1",
        "lit1_type": "Sandstone", "lit1_percentage": "80",
        "lit2_percentage": "20", "lit3_percentage": "0",
        "boundary": "Sharp",
    })
    client.post(f"/profile/{p.id}/bed/new", data={
        "thickness": "30", "name": "Bed2", "facies": "F2",
        "lit1_percentage": "100", "lit2_percentage": "0", "lit3_percentage": "0",
    })
    resp = client.get(f"/profile/{p.id}/export")
    assert resp.status_code == 200
    assert resp.content_type == "text/csv; charset=utf-8"
    assert "ExportLog_export.csv" in resp.headers["Content-Disposition"]

    reader = csv.reader(io.StringIO(resp.data.decode()))
    rows = list(reader)
    assert rows[0][0] == "THICKNESS (CM)"  # SedLog-compatible header
    assert len(rows) == 3  # header + 2 beds
    # SedLog columns
    assert rows[1][0] == "50"       # THICKNESS (CM)
    assert rows[1][2] == "Sandstone"  # LITHOLOGY
    assert rows[1][1] == "Sharp"    # BASE BOUNDARY
    # Gneisswork extras (after column 25)
    assert rows[1][26] == "Bed1"    # Name
    assert rows[2][26] == "Bed2"    # Name


def test_csv_export_empty_profile(client, db):
    client.post("/profile/new", data={"name": "EmptyLog"})
    p = Profile.query.first()
    resp = client.get(f"/profile/{p.id}/export")
    assert resp.status_code == 200
    reader = csv.reader(io.StringIO(resp.data.decode()))
    rows = list(reader)
    assert len(rows) == 1  # header only
