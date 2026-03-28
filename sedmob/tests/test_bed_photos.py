"""Property-based and unit tests for bed photo functionality."""
import io
import os
import uuid as uuid_mod

import pytest
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st
from sedmob.app import create_app
from sedmob.models import db as _db, BedPhoto

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


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


# Feature: bed-photos, Property 1: Upload round trip
# **Validates: Requirements 2.1, 2.3, 2.4**
@given(
    content=st.binary(min_size=1, max_size=1024),
    ext=st.sampled_from(list(ALLOWED_EXTENSIONS)),
    description=st.text(min_size=0, max_size=100),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_upload_round_trip(app, client, db, content, ext, description):
    """POSTing a valid file with description creates a BedPhoto record and saves
    the file to disk with matching content."""
    profile_id, bed_id = _create_profile_and_bed(client)

    data = {
        "photo": (io.BytesIO(content), f"test.{ext}"),
        "description": description,
    }
    client.post(
        f"/profile/{profile_id}/bed/{bed_id}/photo/new",
        data=data,
        content_type="multipart/form-data",
    )

    with app.app_context():
        photo = BedPhoto.query.filter_by(bed_id=bed_id).first()
        assert photo is not None
        assert photo.bed_id == bed_id
        assert photo.profile_id == profile_id
        assert photo.description == description.strip()
        assert photo.filename.endswith(f".{ext}")
        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id), photo.filename
        )
        assert os.path.exists(file_path)
        with open(file_path, "rb") as f:
            assert f.read() == content


# Feature: bed-photos, Property 2: Filename uniqueness
# **Validates: Requirements 9.3**
@given(
    content1=st.binary(min_size=1, max_size=512),
    content2=st.binary(min_size=1, max_size=512),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_upload_filenames_are_unique(app, client, db, content1, content2):
    """Two successive uploads to the same bed produce different filenames."""
    profile_id, bed_id = _create_profile_and_bed(client)

    # First upload
    data1 = {"photo": (io.BytesIO(content1), "photo.png")}
    client.post(f"/profile/{profile_id}/bed/{bed_id}/photo/new",
                data=data1, content_type="multipart/form-data")

    # Second upload
    data2 = {"photo": (io.BytesIO(content2), "photo.png")}
    client.post(f"/profile/{profile_id}/bed/{bed_id}/photo/new",
                data=data2, content_type="multipart/form-data")

    with app.app_context():
        photos = BedPhoto.query.filter_by(bed_id=bed_id).all()
        assert len(photos) == 2
        assert photos[0].filename != photos[1].filename


# Feature: bed-photos, Property 3: Deletion round trip
# **Validates: Requirements 5.1, 5.2**
@given(content=st.binary(min_size=1, max_size=512))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_delete_removes_file_and_record(app, client, db, content):
    """Deleting a photo removes the file from disk and the BedPhoto record from the database."""
    profile_id, bed_id = _create_profile_and_bed(client)

    # Upload a photo
    data = {"photo": (io.BytesIO(content), "photo.jpg")}
    client.post(f"/profile/{profile_id}/bed/{bed_id}/photo/new",
                data=data, content_type="multipart/form-data")

    with app.app_context():
        photo = BedPhoto.query.filter_by(bed_id=bed_id).first()
        photo_id = photo.id
        photo_filename = photo.filename
        photo_path = os.path.join(
            app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id), photo_filename
        )
        assert os.path.exists(photo_path)

    # Delete the photo
    client.post(f"/profile/{profile_id}/bed/{bed_id}/photo/{photo_id}/delete")

    with app.app_context():
        assert _db.session.get(BedPhoto, photo_id) is None
        assert not os.path.exists(photo_path)


# Feature: bed-photos, Property 4: Cascade file cleanup on bed deletion
# **Validates: Requirements 1.3, 6.1**
@given(content=st.binary(min_size=1, max_size=512))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_bed_delete_removes_upload_dir(app, client, db, content):
    """Deleting a bed removes the bed's upload directory and all BedPhoto records."""
    profile_id, bed_id = _create_profile_and_bed(client)

    # Upload a photo
    data = {"photo": (io.BytesIO(content), "photo.png")}
    client.post(f"/profile/{profile_id}/bed/{bed_id}/photo/new",
                data=data, content_type="multipart/form-data")

    bed_upload_dir = os.path.join(
        app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id)
    )
    assert os.path.isdir(bed_upload_dir)

    with app.app_context():
        assert BedPhoto.query.filter_by(bed_id=bed_id).count() == 1

    # Delete the bed
    client.post(f"/profile/{profile_id}/bed/{bed_id}/delete")

    assert not os.path.exists(bed_upload_dir)
    with app.app_context():
        assert BedPhoto.query.filter_by(bed_id=bed_id).count() == 0


# Feature: bed-photos, Property 5: Cascade file cleanup on profile deletion
# **Validates: Requirements 1.4, 6.2**
@given(content=st.binary(min_size=1, max_size=512))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_profile_delete_removes_bed_photos(app, client, db, content):
    """Deleting a profile removes the entire profile upload directory including bed photo subdirectories."""
    profile_id, bed_id = _create_profile_and_bed(client)

    # Upload a bed photo
    data = {"photo": (io.BytesIO(content), "photo.png")}
    client.post(f"/profile/{profile_id}/bed/{bed_id}/photo/new",
                data=data, content_type="multipart/form-data")

    profile_upload_dir = os.path.join(app.config["UPLOAD_FOLDER"], str(profile_id))
    assert os.path.isdir(profile_upload_dir)

    # Delete the profile
    client.post(f"/profile/{profile_id}/delete")

    assert not os.path.exists(profile_upload_dir)


# Feature: bed-photos, Property 6: API bed photos round trip
# **Validates: Requirements 8.1, 8.2, 8.5**
@given(
    content=st.binary(min_size=1, max_size=512),
    description=st.text(min_size=0, max_size=100),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_api_bed_photos_round_trip(app, client, db, content, description):
    """The photos list API and bed detail API return correct serialized BedPhoto data after upload."""
    profile_id, bed_id = _create_profile_and_bed(client)

    # Upload a photo
    data = {
        "photo": (io.BytesIO(content), "test.jpg"),
        "description": description,
    }
    client.post(f"/profile/{profile_id}/bed/{bed_id}/photo/new",
                data=data, content_type="multipart/form-data")

    # Check photos list API
    resp = client.get(f"/api/profiles/{profile_id}/beds/{bed_id}/photos")
    assert resp.status_code == 200
    photos = resp.get_json()
    assert len(photos) == 1
    assert photos[0]["bed_id"] == bed_id
    assert photos[0]["profile_id"] == profile_id
    assert photos[0]["description"] == description.strip()

    # Check bed detail API includes photos key
    resp = client.get(f"/api/profiles/{profile_id}/beds/{bed_id}")
    assert resp.status_code == 200
    bed_data = resp.get_json()
    assert "photos" in bed_data
    assert len(bed_data["photos"]) == 1
    assert bed_data["photos"][0]["bed_id"] == bed_id
