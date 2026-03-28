"""Tests for full export/restore (database + uploaded files as ZIP)."""
import io
import json
import os
import zipfile

from sedmob.models import Profile, Bed, BedPhoto


def _create_profile_with_bed(client, name):
    """Create a profile with one bed via POST requests."""
    client.post("/profile/new", data={"name": name})
    p = Profile.query.filter_by(name=name).first()
    client.post(f"/profile/{p.id}/bed/new", data={
        "thickness": "10", "name": "B1",
        "lit1_percentage": "100", "lit2_percentage": "0", "lit3_percentage": "0",
    })
    return p


def _put_upload(app, *parts, content=b"fake-file-data"):
    """Write a fake file into the uploads directory."""
    folder = os.path.join(app.config["UPLOAD_FOLDER"], *parts[:-1])
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, parts[-1])
    with open(path, "wb") as f:
        f.write(content)
    return path


# ── /export/full ──────────────────────────────────────────

def test_full_export_returns_valid_zip(client, db):
    """GET /export/full returns a valid ZIP with correct headers."""
    _create_profile_with_bed(client, "TestLog")
    resp = client.get("/export/full")
    assert resp.status_code == 200
    assert resp.content_type == "application/zip"
    assert "gneisswork_full_backup_" in resp.headers["Content-Disposition"]
    assert resp.headers["Content-Disposition"].endswith('.zip')


def test_full_export_contains_database_json(client, db):
    """ZIP contains database.json with valid backup data."""
    _create_profile_with_bed(client, "TestLog")
    resp = client.get("/export/full")
    zf = zipfile.ZipFile(io.BytesIO(resp.data))
    assert "database.json" in zf.namelist()
    data = json.loads(zf.read("database.json"))
    assert data["version"] == "1.0"
    assert len(data["profiles"]) == 1
    assert data["profiles"][0]["name"] == "TestLog"


def test_full_export_includes_uploaded_files(app, client, db):
    """ZIP includes uploaded photos and audio files."""
    p = _create_profile_with_bed(client, "WithFiles")
    bed = Bed.query.filter_by(profile_id=p.id).first()
    _put_upload(app, str(p.id), "profile_photo.jpg")
    _put_upload(app, str(p.id), str(bed.id), "bed_photo.png")
    _put_upload(app, str(p.id), str(bed.id), "audio.mp3")

    resp = client.get("/export/full")
    zf = zipfile.ZipFile(io.BytesIO(resp.data))
    names = zf.namelist()
    assert f"uploads/{p.id}/profile_photo.jpg" in names
    assert f"uploads/{p.id}/{bed.id}/bed_photo.png" in names
    assert f"uploads/{p.id}/{bed.id}/audio.mp3" in names


def test_full_export_empty_database(client, db):
    """Full export with no data still returns a valid ZIP with database.json."""
    resp = client.get("/export/full")
    assert resp.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(resp.data))
    assert "database.json" in zf.namelist()
    data = json.loads(zf.read("database.json"))
    assert data["profiles"] == []


# ── /restore/full ─────────────────────────────────────────

def _make_full_backup_zip(db_dict, files=None):
    """Build a ZIP bytes object with database.json and optional files."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("database.json", json.dumps(db_dict, indent=2))
        for arc_path, content in (files or {}).items():
            zf.writestr(arc_path, content)
    buf.seek(0)
    return buf


def test_restore_full_no_file(client, db):
    """POST /restore/full with no file returns error flash."""
    resp = client.post("/restore/full", follow_redirects=True)
    assert b"No file provided" in resp.data


def test_restore_full_bad_zip(client, db):
    """POST /restore/full with non-ZIP returns error flash."""
    data = {"file": (io.BytesIO(b"not a zip"), "bad.zip")}
    resp = client.post("/restore/full", data=data,
                       content_type="multipart/form-data", follow_redirects=True)
    assert b"Invalid ZIP file" in resp.data


def test_restore_full_missing_database_json(client, db):
    """POST /restore/full with ZIP missing database.json returns error."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("other.txt", "hello")
    buf.seek(0)
    data = {"file": (buf, "no_db.zip")}
    resp = client.post("/restore/full", data=data,
                       content_type="multipart/form-data", follow_redirects=True)
    assert b"ZIP does not contain database.json" in resp.data


def test_restore_full_invalid_json_inside(client, db):
    """POST /restore/full with bad JSON inside ZIP returns error."""
    buf = _make_full_backup_zip.__wrapped__ if hasattr(_make_full_backup_zip, '__wrapped__') else None
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("database.json", "not json{{{")
    buf.seek(0)
    data = {"file": (buf, "bad_json.zip")}
    resp = client.post("/restore/full", data=data,
                       content_type="multipart/form-data", follow_redirects=True)
    assert b"Invalid database.json" in resp.data


def test_restore_full_missing_version(client, db):
    """POST /restore/full with JSON missing version returns error."""
    buf = _make_full_backup_zip({"profiles": []})
    data = {"file": (buf, "no_ver.zip")}
    resp = client.post("/restore/full", data=data,
                       content_type="multipart/form-data", follow_redirects=True)
    assert b"Unrecognized backup format" in resp.data


def test_restore_full_roundtrip(app, client, db):
    """Full export then full restore preserves database and files."""
    # Create data with files
    p = _create_profile_with_bed(client, "RoundTrip")
    bed = Bed.query.filter_by(profile_id=p.id).first()
    photo_content = b"JPEG-FAKE-DATA"
    audio_content = b"MP3-FAKE-DATA"
    _put_upload(app, str(p.id), "photo.jpg", content=photo_content)
    _put_upload(app, str(p.id), str(bed.id), "note.mp3", content=audio_content)

    # Export
    resp = client.get("/export/full")
    assert resp.status_code == 200

    # Clear everything
    from sedmob.models import db as _db
    BedPhoto.query.delete()
    Bed.query.delete()
    Profile.query.delete()
    _db.session.commit()
    import shutil
    upload_root = app.config["UPLOAD_FOLDER"]
    if os.path.isdir(upload_root):
        shutil.rmtree(upload_root)

    assert Profile.query.count() == 0

    # Restore
    restore_data = {"file": (io.BytesIO(resp.data), "backup.zip")}
    restore_resp = client.post("/restore/full", data=restore_data,
                               content_type="multipart/form-data",
                               follow_redirects=True)
    assert b"Full backup restored successfully" in restore_resp.data

    # Verify database
    assert Profile.query.count() == 1
    assert Profile.query.first().name == "RoundTrip"
    assert Bed.query.count() == 1

    # Verify files
    photo_path = os.path.join(upload_root, str(p.id), "photo.jpg")
    audio_path = os.path.join(upload_root, str(p.id), str(bed.id), "note.mp3")
    assert os.path.exists(photo_path)
    assert os.path.exists(audio_path)
    with open(photo_path, "rb") as f:
        assert f.read() == photo_content
    with open(audio_path, "rb") as f:
        assert f.read() == audio_content


def test_restore_full_clears_old_uploads(app, client, db):
    """Full restore removes pre-existing upload files."""
    # Create an old file
    _put_upload(app, "999", "old_file.jpg", content=b"old")
    old_path = os.path.join(app.config["UPLOAD_FOLDER"], "999", "old_file.jpg")
    assert os.path.exists(old_path)

    # Restore an empty backup
    buf = _make_full_backup_zip({
        "version": "1.0", "timestamp": "2025-01-01T00:00:00",
        "profiles": [], "beds": [], "bed_photos": [],
        "lithology_types": [], "lithologies": [],
        "structure_types": [], "structures": [],
        "grain_clastic": [], "grain_carbonate": [],
        "bioturbation": [], "boundaries": [],
    })
    data = {"file": (buf, "empty.zip")}
    client.post("/restore/full", data=data, content_type="multipart/form-data")

    # Old file should be gone
    assert not os.path.exists(old_path)
