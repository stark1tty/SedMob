"""Property-based and unit tests for bed audio functionality."""
import io
import os
import uuid as uuid_mod

import pytest
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st
from sedmob.app import create_app
from sedmob.models import db as _db

ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav", "ogg", "m4a", "webm"}


def allowed_audio_file(filename):
    """Replicate the allowed_audio_file helper defined inside create_app() for direct testing."""
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS


@pytest.fixture()
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test",
        "WTF_CSRF_ENABLED": False,
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
    })
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    with app.app_context():
        yield _db


def _create_profile_and_bed(client):
    """Create a profile and bed via POST, return (profile_id, bed_id)."""
    name = f"test-{uuid_mod.uuid4().hex[:8]}"
    client.post("/profile/new", data={"name": name})
    with client.application.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name=name).first()
        profile_id = profile.id
    client.post(f"/profile/{profile_id}/bed/new", data={
        "thickness": "10",
        "lit1_percentage": "100",
        "lit2_percentage": "0",
        "lit3_percentage": "0",
    })
    with client.application.app_context():
        from sedmob.models import Bed
        bed = Bed.query.filter_by(profile_id=profile_id).first()
        bed_id = bed.id
    return profile_id, bed_id


# Feature: 09-bed-audio-upload, Property 1: Upload round trip
# **Validates: Requirements 1.1**
@given(
    content=st.binary(min_size=1, max_size=1024),
    ext=st.sampled_from(["mp3", "wav", "ogg", "m4a", "webm"]),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_upload_round_trip(app, client, db, content, ext):
    """POSTing a valid audio file saves it to disk with identical content
    and stores the generated filename with correct extension in Bed.audio."""
    profile_id, bed_id = _create_profile_and_bed(client)

    data = {
        "audio": (io.BytesIO(content), f"test.{ext}"),
    }
    client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data,
        content_type="multipart/form-data",
    )

    with app.app_context():
        from sedmob.models import Bed
        bed = _db.session.get(Bed, bed_id)
        assert bed is not None
        assert bed.audio != ""
        assert bed.audio.endswith(f".{ext}")
        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id), bed.audio
        )
        assert os.path.exists(file_path)
        with open(file_path, "rb") as f:
            assert f.read() == content


# Feature: 09-bed-audio-upload, Property 2: Replacement removes previous file
# **Validates: Requirements 1.3**
@given(
    content1=st.binary(min_size=1, max_size=512),
    content2=st.binary(min_size=1, max_size=512),
    ext1=st.sampled_from(list(ALLOWED_AUDIO_EXTENSIONS)),
    ext2=st.sampled_from(list(ALLOWED_AUDIO_EXTENSIONS)),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_replacement_removes_previous(app, client, db, content1, content2, ext1, ext2):
    """Uploading a new audio file to a bed that already has one removes the old
    file from disk, leaves only the new audio file (aside from photo files),
    and updates Bed.audio to the new filename."""
    profile_id, bed_id = _create_profile_and_bed(client)

    # First upload
    data1 = {"audio": (io.BytesIO(content1), f"first.{ext1}")}
    client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data1,
        content_type="multipart/form-data",
    )

    with app.app_context():
        from sedmob.models import Bed
        bed = _db.session.get(Bed, bed_id)
        old_filename = bed.audio

    old_file_path = os.path.join(
        app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id), old_filename
    )
    assert os.path.exists(old_file_path)

    # Second upload (replacement)
    data2 = {"audio": (io.BytesIO(content2), f"second.{ext2}")}
    client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data2,
        content_type="multipart/form-data",
    )

    with app.app_context():
        from sedmob.models import Bed
        bed = _db.session.get(Bed, bed_id)
        new_filename = bed.audio

    # (a) Old file no longer exists on disk
    assert not os.path.exists(old_file_path)

    # (b) Only the new audio file exists in the bed's upload directory
    #     (aside from any photo files — filter to audio extensions only)
    bed_dir = os.path.join(
        app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id)
    )
    audio_files = [
        f for f in os.listdir(bed_dir)
        if "." in f and f.rsplit(".", 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS
    ]
    assert audio_files == [new_filename]

    # (c) Bed.audio column updated to the new filename
    assert new_filename.endswith(f".{ext2}")
    new_file_path = os.path.join(bed_dir, new_filename)
    assert os.path.exists(new_file_path)
    with open(new_file_path, "rb") as f:
        assert f.read() == content2


# Feature: 09-bed-audio-upload, Property 3: Extension validation
# **Validates: Requirements 2.1, 2.2**
@given(
    base=st.text(min_size=1, max_size=50),
    ext=st.sampled_from(
        list(ALLOWED_AUDIO_EXTENSIONS) + ["mp4", "flac", "aac", "exe", "txt", "pdf"]
    ),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_allowed_audio_file_validation(base, ext):
    """For any filename with a dot and extension, allowed_audio_file returns True iff
    the lowercased extension is in {mp3, wav, ogg, m4a, webm}."""
    filename = f"{base}.{ext}"
    expected = ext.lower() in ALLOWED_AUDIO_EXTENSIONS
    assert allowed_audio_file(filename) == expected


# Feature: 09-bed-audio-upload, Property 6: Filename uniqueness across uploads
# **Validates: Requirements 1.2**
@given(
    content1=st.binary(min_size=1, max_size=512),
    content2=st.binary(min_size=1, max_size=512),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_filename_uniqueness(app, client, db, content1, content2):
    """For any two successive audio uploads to the same bed with the same
    original filename, the generated filenames stored in Bed.audio should
    be different, ensuring no collision."""
    profile_id, bed_id = _create_profile_and_bed(client)

    # First upload — same original filename "note.mp3"
    data1 = {"audio": (io.BytesIO(content1), "note.mp3")}
    client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data1,
        content_type="multipart/form-data",
    )

    with app.app_context():
        from sedmob.models import Bed
        bed = _db.session.get(Bed, bed_id)
        filename1 = bed.audio

    # Second upload — same original filename "note.mp3"
    data2 = {"audio": (io.BytesIO(content2), "note.mp3")}
    client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data2,
        content_type="multipart/form-data",
    )

    with app.app_context():
        from sedmob.models import Bed
        bed = _db.session.get(Bed, bed_id)
        filename2 = bed.audio

    # Both uploads should have succeeded
    assert filename1 != ""
    assert filename2 != ""
    # Generated filenames must be different
    assert filename1 != filename2


# Feature: 09-bed-audio-upload, Property 4: Delete round trip
# **Validates: Requirements 4.1**
@given(content=st.binary(min_size=1, max_size=512))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_delete_round_trip(app, client, db, content):
    """For any bed with an uploaded audio file, POSTing to the audio delete
    route removes the audio file from disk and clears Bed.audio to empty string."""
    profile_id, bed_id = _create_profile_and_bed(client)

    # Upload an audio file first
    data = {"audio": (io.BytesIO(content), "note.mp3")}
    client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data,
        content_type="multipart/form-data",
    )

    with app.app_context():
        from sedmob.models import Bed
        bed = _db.session.get(Bed, bed_id)
        audio_filename = bed.audio
        assert audio_filename != ""

    audio_path = os.path.join(
        app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id), audio_filename
    )
    assert os.path.exists(audio_path)

    # Delete the audio
    client.post(f"/profile/{profile_id}/bed/{bed_id}/audio/delete")

    # (a) Audio file no longer exists on disk
    assert not os.path.exists(audio_path)

    # (b) Bed.audio column is an empty string
    with app.app_context():
        from sedmob.models import Bed
        bed = _db.session.get(Bed, bed_id)
        assert bed.audio == ""


# ── Unit Tests: Template Rendering ────────────────────────


# Validates: Requirement 3.1, 3.2
def test_bed_form_shows_audio_player(app, client, db):
    """Upload audio, GET bed edit form, check <audio> tag with controls and correct src."""
    profile_id, bed_id = _create_profile_and_bed(client)
    data = {"audio": (io.BytesIO(b"fake audio data"), "note.mp3")}
    client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data,
        content_type="multipart/form-data",
    )
    resp = client.get(f"/profile/{profile_id}/bed/{bed_id}")
    assert resp.status_code == 200
    assert b"<audio" in resp.data
    assert b"controls" in resp.data
    assert f"/uploads/{profile_id}/{bed_id}/".encode() in resp.data


# Validates: Requirement 3.3
def test_bed_form_no_audio_no_player(client, db):
    """GET bed edit form with no audio shows no <audio> tag."""
    profile_id, bed_id = _create_profile_and_bed(client)
    resp = client.get(f"/profile/{profile_id}/bed/{bed_id}")
    assert resp.status_code == 200
    assert b"<audio" not in resp.data


# Validates: Requirement 3.4
def test_new_bed_form_no_audio_section(client, db):
    """GET new bed form has no Audio card section."""
    name = f"test-{uuid_mod.uuid4().hex[:8]}"
    client.post("/profile/new", data={"name": name})
    with client.application.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name=name).first()
        profile_id = profile.id
    resp = client.get(f"/profile/{profile_id}/bed/new")
    assert resp.status_code == 200
    assert b"<audio" not in resp.data
    assert b"Upload Audio" not in resp.data


# Validates: Requirement 3.5
def test_bed_form_has_delete_button_when_audio_exists(app, client, db):
    """Upload audio, GET bed edit form, check delete button form is present."""
    profile_id, bed_id = _create_profile_and_bed(client)
    data = {"audio": (io.BytesIO(b"fake audio data"), "note.mp3")}
    client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data,
        content_type="multipart/form-data",
    )
    resp = client.get(f"/profile/{profile_id}/bed/{bed_id}")
    assert resp.status_code == 200
    assert f"/profile/{profile_id}/bed/{bed_id}/audio/delete".encode() in resp.data
    assert b"Delete Audio" in resp.data


# Validates: Requirement 6.1
def test_serve_audio_file(app, client, db):
    """Upload audio file, GET /uploads/<pid>/<bid>/<filename>, check 200 and content."""
    profile_id, bed_id = _create_profile_and_bed(client)
    content = b"fake audio data for serving"
    data = {"audio": (io.BytesIO(content), "serve.mp3")}
    client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data,
        content_type="multipart/form-data",
    )
    with app.app_context():
        from sedmob.models import Bed
        bed = _db.session.get(Bed, bed_id)
        filename = bed.audio
    resp = client.get(f"/uploads/{profile_id}/{bed_id}/{filename}")
    assert resp.status_code == 200
    assert resp.data == content


# ── Unit Tests: Upload Edge Cases ─────────────────────────


# Validates: Requirement 2.3
def test_upload_no_file_flashes_error(client, db):
    """POST to audio upload with no file part flashes 'No file selected.'"""
    profile_id, bed_id = _create_profile_and_bed(client)
    resp = client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data={},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"No file selected." in resp.data


# Validates: Requirement 2.3
def test_upload_empty_filename_flashes_error(client, db):
    """POST with empty filename flashes 'No file selected.'"""
    profile_id, bed_id = _create_profile_and_bed(client)
    data = {"audio": (io.BytesIO(b"fake audio data"), "")}
    resp = client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"No file selected." in resp.data


# Validates: Requirement 2.2
def test_upload_disallowed_extension_flashes_error(client, db):
    """POST with .exe file flashes 'File type not allowed. Use: mp3, wav, ogg, m4a, webm.'"""
    profile_id, bed_id = _create_profile_and_bed(client)
    data = {"audio": (io.BytesIO(b"fake audio data"), "audio.exe")}
    resp = client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"File type not allowed. Use: mp3, wav, ogg, m4a, webm." in resp.data


# Validates: Requirement 1.4
def test_upload_redirects_to_bed_edit(app, client, db):
    """Upload audio file, check redirect to bed edit."""
    profile_id, bed_id = _create_profile_and_bed(client)
    data = {"audio": (io.BytesIO(b"fake audio data"), "redir.mp3")}
    resp = client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert f"/profile/{profile_id}/bed/{bed_id}" in resp.headers["Location"]


# Validates: Requirement 1.5
def test_upload_bed_wrong_profile_returns_404(client, db):
    """POST to audio upload for bed not belonging to profile returns 404."""
    profile_id, bed_id = _create_profile_and_bed(client)
    # Create a second profile
    name2 = f"test2-{uuid_mod.uuid4().hex[:8]}"
    client.post("/profile/new", data={"name": name2})
    with client.application.app_context():
        from sedmob.models import Profile
        profile2 = Profile.query.filter_by(name=name2).first()
        profile2_id = profile2.id
    data = {"audio": (io.BytesIO(b"fake audio data"), "audio.mp3")}
    resp = client.post(
        f"/profile/{profile2_id}/bed/{bed_id}/audio",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 404


# Validates: Requirement 1.3
def test_upload_replaces_previous_audio_file(app, client, db):
    """Upload two audio files, verify the first is gone from disk."""
    profile_id, bed_id = _create_profile_and_bed(client)

    # First upload
    data1 = {"audio": (io.BytesIO(b"first audio content"), "first.mp3")}
    client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data1,
        content_type="multipart/form-data",
    )

    with app.app_context():
        from sedmob.models import Bed
        bed = _db.session.get(Bed, bed_id)
        old_filename = bed.audio

    old_path = os.path.join(
        app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id), old_filename
    )
    assert os.path.exists(old_path)

    # Second upload (replacement)
    data2 = {"audio": (io.BytesIO(b"second audio content"), "second.wav")}
    client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data2,
        content_type="multipart/form-data",
    )

    # Old file should be gone
    assert not os.path.exists(old_path)

    # New file should exist and column updated
    with app.app_context():
        from sedmob.models import Bed
        bed = _db.session.get(Bed, bed_id)
        new_filename = bed.audio
        assert new_filename != old_filename
        assert new_filename.endswith(".wav")
        new_path = os.path.join(
            app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id), new_filename
        )
        assert os.path.exists(new_path)


# ── Unit Tests: Delete Edge Cases ─────────────────────────


# Validates: Requirement 4.2
def test_delete_redirects_to_bed_edit(app, client, db):
    """Delete audio, check 302 redirect to bed edit."""
    profile_id, bed_id = _create_profile_and_bed(client)
    # Upload audio first
    data = {"audio": (io.BytesIO(b"fake audio data"), "del.mp3")}
    client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data,
        content_type="multipart/form-data",
    )
    resp = client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio/delete",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert f"/profile/{profile_id}/bed/{bed_id}" in resp.headers["Location"]


# Validates: Requirement 4.3
def test_delete_no_audio_flashes_message(client, db):
    """POST delete when bed has no audio flashes 'No audio to delete.'"""
    profile_id, bed_id = _create_profile_and_bed(client)
    resp = client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio/delete",
        follow_redirects=True,
    )
    assert b"No audio to delete." in resp.data


# Validates: Requirement 4.4
def test_delete_bed_wrong_profile_returns_404(client, db):
    """POST delete for bed not belonging to profile returns 404."""
    profile_id, bed_id = _create_profile_and_bed(client)
    # Create a second profile
    name2 = f"test2-{uuid_mod.uuid4().hex[:8]}"
    client.post("/profile/new", data={"name": name2})
    with client.application.app_context():
        from sedmob.models import Profile
        profile2 = Profile.query.filter_by(name=name2).first()
        profile2_id = profile2.id
    resp = client.post(f"/profile/{profile2_id}/bed/{bed_id}/audio/delete")
    assert resp.status_code == 404


# Validates: Requirement 4.1
def test_delete_removes_file_from_disk_and_clears_column(app, client, db):
    """Upload audio, delete it, verify file is gone from disk and Bed.audio is empty."""
    profile_id, bed_id = _create_profile_and_bed(client)

    # Upload audio first
    content = b"audio content to delete"
    data = {"audio": (io.BytesIO(content), "remove.mp3")}
    client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data,
        content_type="multipart/form-data",
    )

    with app.app_context():
        from sedmob.models import Bed
        bed = _db.session.get(Bed, bed_id)
        audio_filename = bed.audio
        assert audio_filename != ""

    audio_path = os.path.join(
        app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id), audio_filename
    )
    assert os.path.exists(audio_path)

    # Delete audio
    resp = client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio/delete",
        follow_redirects=True,
    )
    assert b"Audio deleted." in resp.data

    # File should be gone from disk
    assert not os.path.exists(audio_path)

    # Bed.audio column should be empty
    with app.app_context():
        from sedmob.models import Bed
        bed = _db.session.get(Bed, bed_id)
        assert bed.audio == ""


# Feature: 09-bed-audio-upload, Property 5: Cascade cleanup includes audio
# **Validates: Requirements 5.1**
@given(content=st.binary(min_size=1, max_size=512))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_cascade_bed_delete_removes_audio(app, client, db, content):
    """For any bed with an uploaded audio file, deleting the bed should remove
    the entire bed upload directory from disk, including the audio file."""
    profile_id, bed_id = _create_profile_and_bed(client)

    # Upload an audio file
    data = {"audio": (io.BytesIO(content), "note.mp3")}
    client.post(
        f"/profile/{profile_id}/bed/{bed_id}/audio",
        data=data,
        content_type="multipart/form-data",
    )

    # Verify the file exists on disk
    with app.app_context():
        from sedmob.models import Bed
        bed = _db.session.get(Bed, bed_id)
        audio_filename = bed.audio
        assert audio_filename != ""

    bed_upload_dir = os.path.join(
        app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id)
    )
    audio_path = os.path.join(bed_upload_dir, audio_filename)
    assert os.path.isdir(bed_upload_dir)
    assert os.path.exists(audio_path)

    # Delete the bed via POST to the bed delete route
    client.post(f"/profile/{profile_id}/bed/{bed_id}/delete")

    # Verify the entire bed upload directory is gone (including the audio file)
    assert not os.path.exists(bed_upload_dir)
    assert not os.path.exists(audio_path)
