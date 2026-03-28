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
