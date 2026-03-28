"""Property-based tests for profile photo functionality."""
import io
import os
import uuid as uuid_mod

import pytest
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st
from sedmob.app import create_app
from sedmob.models import db as _db

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    """Replicate the allowed_file helper defined inside create_app() for direct testing."""
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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


# Feature: profile-photos, Property 1: Extension validation
# **Validates: Requirements 1.4, 3.1**
@given(
    base=st.text(min_size=0, max_size=50),
    ext=st.sampled_from(
        list(ALLOWED_EXTENSIONS) + ["bmp", "tiff", "pdf", "exe", "txt", "svg"]
    ),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_allowed_file_iff_extension_in_set(base, ext):
    """For any filename with a dot and extension, allowed_file returns True iff
    the lowercased extension is in the allowed set {"png", "jpg", "jpeg", "gif", "webp"}."""
    filename = f"{base}.{ext}"
    expected = ext.lower() in ALLOWED_EXTENSIONS
    assert allowed_file(filename) == expected


@given(name=st.text(min_size=1, max_size=50).filter(lambda s: "." not in s))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_allowed_file_rejects_no_extension(name):
    """Filenames without a dot are always rejected by allowed_file."""
    assert allowed_file(name) is False


# Feature: profile-photos, Property 2: Upload round trip
# **Validates: Requirements 2.1, 2.3**
@given(
    content=st.binary(min_size=1, max_size=1024),
    ext=st.sampled_from(list(ALLOWED_EXTENSIONS)),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_upload_round_trip(app, client, db, content, ext):
    """POSTing a valid file saves it to disk, updates Profile.photo, and content matches."""
    name = f"upload-test-{uuid_mod.uuid4().hex[:8]}"
    client.post("/profile/new", data={"name": name})

    with app.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name=name).first()
        profile_id = profile.id

    # Upload file
    data = {"photo": (io.BytesIO(content), f"test.{ext}")}
    client.post(
        f"/profile/{profile_id}/photo",
        data=data,
        content_type="multipart/form-data",
    )

    with app.app_context():
        profile = _db.session.get(Profile, profile_id)
        # Profile.photo is set and has the correct extension
        assert profile.photo != ""
        assert profile.photo.endswith(f".{ext}")
        # File exists on disk at UPLOAD_FOLDER/<profile_id>/<filename>
        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"], str(profile_id), profile.photo
        )
        assert os.path.exists(file_path)
        # Saved content matches what was uploaded
        with open(file_path, "rb") as f:
            assert f.read() == content


# Feature: profile-photos, Property 3: Filename uniqueness
# **Validates: Requirements 2.2**
@given(
    content1=st.binary(min_size=1, max_size=512),
    content2=st.binary(min_size=1, max_size=512),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_upload_filenames_are_unique(app, client, db, content1, content2):
    """Two successive uploads to the same profile produce different filenames."""
    name = f"unique-test-{uuid_mod.uuid4().hex[:8]}"
    client.post("/profile/new", data={"name": name})
    with app.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name=name).first()
        profile_id = profile.id

    # First upload
    data1 = {"photo": (io.BytesIO(content1), "photo.png")}
    client.post(f"/profile/{profile_id}/photo", data=data1, content_type="multipart/form-data")
    with app.app_context():
        profile = _db.session.get(Profile, profile_id)
        filename1 = profile.photo

    # Second upload
    data2 = {"photo": (io.BytesIO(content2), "photo.png")}
    client.post(f"/profile/{profile_id}/photo", data=data2, content_type="multipart/form-data")
    with app.app_context():
        profile = _db.session.get(Profile, profile_id)
        filename2 = profile.photo

    assert filename1 != filename2


# Feature: profile-photos, Property 4: Photo replacement cleanup
# **Validates: Requirements 5.1, 5.2**
@given(
    content_old=st.binary(min_size=1, max_size=512),
    content_new=st.binary(min_size=1, max_size=512),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_replacement_removes_old_file(app, client, db, content_old, content_new):
    """Uploading a new photo removes the old file, saves the new file, and updates the column."""
    name = f"replace-test-{uuid_mod.uuid4().hex[:8]}"
    client.post("/profile/new", data={"name": name})
    with app.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name=name).first()
        profile_id = profile.id

    # Upload old photo
    data_old = {"photo": (io.BytesIO(content_old), "old.jpg")}
    client.post(f"/profile/{profile_id}/photo", data=data_old, content_type="multipart/form-data")
    with app.app_context():
        profile = _db.session.get(Profile, profile_id)
        old_filename = profile.photo
        old_path = os.path.join(app.config["UPLOAD_FOLDER"], str(profile_id), old_filename)
        assert os.path.exists(old_path)

    # Upload new photo
    data_new = {"photo": (io.BytesIO(content_new), "new.png")}
    client.post(f"/profile/{profile_id}/photo", data=data_new, content_type="multipart/form-data")
    with app.app_context():
        profile = _db.session.get(Profile, profile_id)
        new_filename = profile.photo
        new_path = os.path.join(app.config["UPLOAD_FOLDER"], str(profile_id), new_filename)
        # Old file removed
        assert not os.path.exists(old_path)
        # New file exists
        assert os.path.exists(new_path)
        # Column updated
        assert profile.photo == new_filename
        assert new_filename != old_filename


# Feature: profile-photos, Property 5: Photo deletion round trip
# **Validates: Requirements 6.1**
@given(content=st.binary(min_size=1, max_size=512))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_delete_removes_file_and_clears_column(app, client, db, content):
    """Deleting a photo removes the file from disk and sets Profile.photo to empty string."""
    name = f"delete-test-{uuid_mod.uuid4().hex[:8]}"
    client.post("/profile/new", data={"name": name})
    with app.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name=name).first()
        profile_id = profile.id

    # Upload a photo
    data = {"photo": (io.BytesIO(content), "photo.jpg")}
    client.post(f"/profile/{profile_id}/photo", data=data, content_type="multipart/form-data")
    with app.app_context():
        profile = _db.session.get(Profile, profile_id)
        photo_filename = profile.photo
        photo_path = os.path.join(app.config["UPLOAD_FOLDER"], str(profile_id), photo_filename)
        assert os.path.exists(photo_path)

    # Delete the photo
    client.post(f"/profile/{profile_id}/photo/delete")
    with app.app_context():
        profile = _db.session.get(Profile, profile_id)
        assert profile.photo == ""
        assert not os.path.exists(photo_path)


# Feature: profile-photos, Property 6: Cascade file cleanup on profile deletion
# **Validates: Requirements 7.1**
@given(content=st.binary(min_size=1, max_size=512))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_profile_delete_removes_upload_dir(app, client, db, content):
    """Deleting a profile removes the entire upload directory from disk."""
    name = f"cascade-test-{uuid_mod.uuid4().hex[:8]}"
    client.post("/profile/new", data={"name": name})
    with app.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name=name).first()
        profile_id = profile.id

    # Upload a photo
    data = {"photo": (io.BytesIO(content), "photo.png")}
    client.post(f"/profile/{profile_id}/photo", data=data, content_type="multipart/form-data")

    upload_dir = os.path.join(app.config["UPLOAD_FOLDER"], str(profile_id))
    assert os.path.isdir(upload_dir)

    # Delete the profile
    client.post(f"/profile/{profile_id}/delete")

    # Upload directory should be gone
    assert not os.path.exists(upload_dir)


# ── Unit Tests: Edge Cases and Template Rendering ─────────────


def _create_profile(client, name="Test Profile"):
    """Helper to create a profile via POST and return the response."""
    client.post("/profile/new", data={"name": name})


# Validates: Requirement 3.2
def test_upload_no_file_flashes_error(client, db):
    """POST to upload with no file part flashes 'No file selected.'"""
    _create_profile(client, name="no-file-test")
    with client.application.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name="no-file-test").first()
    resp = client.post(
        f"/profile/{profile.id}/photo",
        data={},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"No file selected." in resp.data


# Validates: Requirement 3.3
def test_upload_empty_filename_flashes_error(client, db):
    """POST with empty filename flashes 'No file selected.'"""
    _create_profile(client, name="empty-name-test")
    with client.application.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name="empty-name-test").first()
    data = {"photo": (io.BytesIO(b"fake image data"), "")}
    resp = client.post(
        f"/profile/{profile.id}/photo",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"No file selected." in resp.data


# Validates: Requirement 3.1
def test_upload_disallowed_extension_flashes_error(client, db):
    """POST with .bmp file flashes 'File type not allowed'."""
    _create_profile(client, name="bmp-ext-test")
    with client.application.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name="bmp-ext-test").first()
    data = {"photo": (io.BytesIO(b"fake image data"), "photo.bmp")}
    resp = client.post(
        f"/profile/{profile.id}/photo",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"File type not allowed" in resp.data


# Validates: Requirement 2.5
def test_upload_nonexistent_profile_returns_404(client, db):
    """POST to /profile/9999/photo returns 404."""
    data = {"photo": (io.BytesIO(b"fake image data"), "photo.png")}
    resp = client.post(
        "/profile/9999/photo",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 404


# Validates: Requirement 6.3
def test_delete_no_photo_flashes_error(client, db):
    """POST delete on profile with no photo flashes 'No photo to delete.'"""
    _create_profile(client, name="no-photo-del-test")
    with client.application.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name="no-photo-del-test").first()
    resp = client.post(
        f"/profile/{profile.id}/photo/delete",
        follow_redirects=True,
    )
    assert b"No photo to delete." in resp.data


# Validates: Requirement 6.4
def test_delete_nonexistent_profile_returns_404(client, db):
    """POST to /profile/9999/photo/delete returns 404."""
    resp = client.post("/profile/9999/photo/delete")
    assert resp.status_code == 404


# Validates: Requirement 7.2
def test_profile_delete_no_photo_succeeds(client, db):
    """Delete profile with no photo succeeds without error."""
    _create_profile(client, name="del-no-photo-test")
    with client.application.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name="del-no-photo-test").first()
        profile_id = profile.id
    resp = client.post(f"/profile/{profile_id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    with client.application.app_context():
        from sedmob.models import Profile as P
        assert P.query.get(profile_id) is None


# Validates: Requirement 4.1
def test_edit_form_shows_photo_when_present(app, client, db):
    """Upload photo, GET edit form, check img tag present."""
    _create_profile(client, name="photo-present-test")
    with app.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name="photo-present-test").first()
        profile_id = profile.id
    data = {"photo": (io.BytesIO(b"fake image data"), "test.png")}
    client.post(
        f"/profile/{profile_id}/photo",
        data=data,
        content_type="multipart/form-data",
    )
    resp = client.get(f"/profile/{profile_id}")
    assert resp.status_code == 200
    assert b"<img" in resp.data
    assert b"Profile photo" in resp.data


# Validates: Requirement 4.2
def test_edit_form_shows_placeholder_when_no_photo(client, db):
    """GET edit form with no photo shows 'No photo uploaded.'"""
    _create_profile(client, name="no-photo-placeholder-test")
    with client.application.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name="no-photo-placeholder-test").first()
    resp = client.get(f"/profile/{profile.id}")
    assert resp.status_code == 200
    assert b"No photo uploaded." in resp.data


# Validates: Requirement 4.3
def test_edit_form_has_upload_form(client, db):
    """GET edit form has enctype='multipart/form-data' and file input."""
    _create_profile(client, name="upload-form-test")
    with client.application.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name="upload-form-test").first()
    resp = client.get(f"/profile/{profile.id}")
    assert resp.status_code == 200
    assert b'enctype="multipart/form-data"' in resp.data
    assert b'type="file"' in resp.data


# Validates: Requirement 4.4
def test_new_profile_form_has_no_photo_section(client, db):
    """GET /profile/new has no Photo card."""
    resp = client.get("/profile/new")
    assert resp.status_code == 200
    assert b"No photo uploaded." not in resp.data
    assert b'enctype="multipart/form-data"' not in resp.data


# Validates: Requirement 1.2
def test_upload_folder_created_on_startup(app):
    """Check UPLOAD_FOLDER directory exists after app creation."""
    assert os.path.isdir(app.config["UPLOAD_FOLDER"])


# Validates: Requirement 1.3
def test_serve_uploaded_file(app, client, db):
    """Upload file, GET /uploads/<id>/<filename>, check 200 and content."""
    _create_profile(client, name="serve-file-test")
    with app.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name="serve-file-test").first()
        profile_id = profile.id
    content = b"fake image data for serving"
    data = {"photo": (io.BytesIO(content), "serve.png")}
    client.post(
        f"/profile/{profile_id}/photo",
        data=data,
        content_type="multipart/form-data",
    )
    with app.app_context():
        from sedmob.models import Profile as P
        profile = P.query.get(profile_id)
        filename = profile.photo
    resp = client.get(f"/uploads/{profile_id}/{filename}")
    assert resp.status_code == 200
    assert resp.data == content


# Validates: Requirement 2.4
def test_upload_redirects_to_profile_edit(app, client, db):
    """Upload file, check redirect to profile edit."""
    _create_profile(client, name="upload-redirect-test")
    with app.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name="upload-redirect-test").first()
        profile_id = profile.id
    data = {"photo": (io.BytesIO(b"fake image data"), "redir.png")}
    resp = client.post(
        f"/profile/{profile_id}/photo",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert f"/profile/{profile_id}" in resp.headers["Location"]


# Validates: Requirement 6.2
def test_delete_redirects_to_profile_edit(app, client, db):
    """Delete photo, check redirect to profile edit."""
    _create_profile(client, name="delete-redirect-test")
    with app.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name="delete-redirect-test").first()
        profile_id = profile.id
    # Upload first
    data = {"photo": (io.BytesIO(b"fake image data"), "del.png")}
    client.post(
        f"/profile/{profile_id}/photo",
        data=data,
        content_type="multipart/form-data",
    )
    # Delete
    resp = client.post(
        f"/profile/{profile_id}/photo/delete",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert f"/profile/{profile_id}" in resp.headers["Location"]
