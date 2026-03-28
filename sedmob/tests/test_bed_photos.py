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


# ── Unit Tests: Upload Edge Cases ─────────────────────────


# Validates: Requirement 3.2
def test_upload_no_file_flashes_error(client, db):
    """POST to upload with no file part flashes 'No file selected.'"""
    profile_id, bed_id = _create_profile_and_bed(client)
    resp = client.post(
        f"/profile/{profile_id}/bed/{bed_id}/photo/new",
        data={},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"No file selected." in resp.data


# Validates: Requirement 3.3
def test_upload_empty_filename_flashes_error(client, db):
    """POST with empty filename flashes 'No file selected.'"""
    profile_id, bed_id = _create_profile_and_bed(client)
    data = {"photo": (io.BytesIO(b"fake image data"), "")}
    resp = client.post(
        f"/profile/{profile_id}/bed/{bed_id}/photo/new",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"No file selected." in resp.data


# Validates: Requirement 3.1
def test_upload_disallowed_extension_flashes_error(client, db):
    """POST with .bmp file flashes 'File type not allowed'."""
    profile_id, bed_id = _create_profile_and_bed(client)
    data = {"photo": (io.BytesIO(b"fake image data"), "photo.bmp")}
    resp = client.post(
        f"/profile/{profile_id}/bed/{bed_id}/photo/new",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"File type not allowed" in resp.data


# Validates: Requirement 2.7
def test_upload_nonexistent_bed_returns_404(client, db):
    """POST to upload for nonexistent bed returns 404."""
    name = f"test-{uuid_mod.uuid4().hex[:8]}"
    client.post("/profile/new", data={"name": name})
    with client.application.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name=name).first()
        profile_id = profile.id
    data = {"photo": (io.BytesIO(b"fake image data"), "photo.png")}
    resp = client.post(
        f"/profile/{profile_id}/bed/9999/photo/new",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 404


# Validates: Requirement 2.6
def test_upload_bed_wrong_profile_returns_404(client, db):
    """POST to upload for bed not belonging to profile returns 404."""
    profile_id, bed_id = _create_profile_and_bed(client)
    # Create a second profile
    name2 = f"test2-{uuid_mod.uuid4().hex[:8]}"
    client.post("/profile/new", data={"name": name2})
    with client.application.app_context():
        from sedmob.models import Profile
        profile2 = Profile.query.filter_by(name=name2).first()
        profile2_id = profile2.id
    data = {"photo": (io.BytesIO(b"fake image data"), "photo.png")}
    resp = client.post(
        f"/profile/{profile2_id}/bed/{bed_id}/photo/new",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 404


# Validates: Requirement 2.5
def test_upload_redirects_to_bed_edit(app, client, db):
    """Upload file, check redirect to bed edit."""
    profile_id, bed_id = _create_profile_and_bed(client)
    data = {"photo": (io.BytesIO(b"fake image data"), "redir.png")}
    resp = client.post(
        f"/profile/{profile_id}/bed/{bed_id}/photo/new",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert f"/profile/{profile_id}/bed/{bed_id}" in resp.headers["Location"]



# ── Unit Tests: Delete Edge Cases ─────────────────────────


# Validates: Requirement 5.4
def test_delete_nonexistent_photo_returns_404(client, db):
    """POST to delete nonexistent photo returns 404."""
    profile_id, bed_id = _create_profile_and_bed(client)
    resp = client.post(f"/profile/{profile_id}/bed/{bed_id}/photo/9999/delete")
    assert resp.status_code == 404


# Validates: Requirement 5.5
def test_delete_photo_wrong_bed_returns_404(app, client, db):
    """POST to delete photo not belonging to bed returns 404."""
    profile_id, bed_id = _create_profile_and_bed(client)

    # Upload a photo to the first bed
    data = {"photo": (io.BytesIO(b"fake image data"), "photo.png")}
    client.post(f"/profile/{profile_id}/bed/{bed_id}/photo/new",
                data=data, content_type="multipart/form-data")

    with app.app_context():
        photo = BedPhoto.query.filter_by(bed_id=bed_id).first()
        photo_id = photo.id

    # Create a second bed
    client.post(f"/profile/{profile_id}/bed/new", data={
        "thickness": "20",
        "lit1_percentage": "100",
        "lit2_percentage": "0",
        "lit3_percentage": "0",
    })
    with client.application.app_context():
        from sedmob.models import Bed
        beds = Bed.query.filter_by(profile_id=profile_id).all()
        bed2_id = [b.id for b in beds if b.id != bed_id][0]

    # Try to delete photo via wrong bed
    resp = client.post(f"/profile/{profile_id}/bed/{bed2_id}/photo/{photo_id}/delete")
    assert resp.status_code == 404


# Validates: Requirement 5.3
def test_delete_redirects_to_bed_edit(app, client, db):
    """Delete photo, check redirect to bed edit."""
    profile_id, bed_id = _create_profile_and_bed(client)
    data = {"photo": (io.BytesIO(b"fake image data"), "del.png")}
    client.post(f"/profile/{profile_id}/bed/{bed_id}/photo/new",
                data=data, content_type="multipart/form-data")

    with app.app_context():
        photo = BedPhoto.query.filter_by(bed_id=bed_id).first()
        photo_id = photo.id

    resp = client.post(
        f"/profile/{profile_id}/bed/{bed_id}/photo/{photo_id}/delete",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert f"/profile/{profile_id}/bed/{bed_id}" in resp.headers["Location"]


# Validates: Requirement 6.3
def test_bed_delete_no_photos_succeeds(client, db):
    """Delete bed with no photos succeeds without error."""
    profile_id, bed_id = _create_profile_and_bed(client)
    resp = client.post(f"/profile/{profile_id}/bed/{bed_id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    with client.application.app_context():
        from sedmob.models import Bed
        assert _db.session.get(Bed, bed_id) is None


# ── Unit Tests: Template Rendering ────────────────────────


# Validates: Requirement 4.1, 4.2
def test_bed_form_shows_gallery_with_photos(app, client, db):
    """Upload photo, GET bed edit form, check img tag and description present."""
    profile_id, bed_id = _create_profile_and_bed(client)
    data = {
        "photo": (io.BytesIO(b"fake image data"), "test.png"),
        "description": "Test description",
    }
    client.post(f"/profile/{profile_id}/bed/{bed_id}/photo/new",
                data=data, content_type="multipart/form-data")
    resp = client.get(f"/profile/{profile_id}/bed/{bed_id}")
    assert resp.status_code == 200
    assert b"<img" in resp.data
    assert b"Bed photo" in resp.data
    assert b"Test description" in resp.data


# Validates: Requirement 4.1
def test_bed_form_shows_no_photos_placeholder(client, db):
    """GET bed edit form with no photos shows 'No photos uploaded.'"""
    profile_id, bed_id = _create_profile_and_bed(client)
    resp = client.get(f"/profile/{profile_id}/bed/{bed_id}")
    assert resp.status_code == 200
    assert b"No photos uploaded." in resp.data


# Validates: Requirement 4.5
def test_bed_form_has_upload_form(client, db):
    """GET bed edit form has enctype='multipart/form-data' and file input."""
    profile_id, bed_id = _create_profile_and_bed(client)
    resp = client.get(f"/profile/{profile_id}/bed/{bed_id}")
    assert resp.status_code == 200
    assert b'enctype="multipart/form-data"' in resp.data
    assert b'type="file"' in resp.data
    assert b'name="description"' in resp.data


# Validates: Requirement 4.4
def test_new_bed_form_has_no_gallery(client, db):
    """GET new bed form has no Photo gallery section."""
    name = f"test-{uuid_mod.uuid4().hex[:8]}"
    client.post("/profile/new", data={"name": name})
    with client.application.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name=name).first()
        profile_id = profile.id
    resp = client.get(f"/profile/{profile_id}/bed/new")
    assert resp.status_code == 200
    assert b"No photos uploaded." not in resp.data
    assert b'enctype="multipart/form-data"' not in resp.data


# Validates: Requirement 7.1
def test_serve_bed_photo_file(app, client, db):
    """Upload file, GET /uploads/<pid>/<bid>/<filename>, check 200 and content."""
    profile_id, bed_id = _create_profile_and_bed(client)
    content = b"fake image data for serving"
    data = {"photo": (io.BytesIO(content), "serve.png")}
    client.post(f"/profile/{profile_id}/bed/{bed_id}/photo/new",
                data=data, content_type="multipart/form-data")
    with app.app_context():
        photo = BedPhoto.query.filter_by(bed_id=bed_id).first()
        filename = photo.filename
    resp = client.get(f"/uploads/{profile_id}/{bed_id}/{filename}")
    assert resp.status_code == 200
    assert resp.data == content


# Validates: Requirement 7.3
def test_existing_profile_photo_route_unchanged(app, client, db):
    """Profile photo route still works after adding bed photo route."""
    name = f"test-{uuid_mod.uuid4().hex[:8]}"
    client.post("/profile/new", data={"name": name})
    with app.app_context():
        from sedmob.models import Profile
        profile = Profile.query.filter_by(name=name).first()
        profile_id = profile.id
    content = b"profile photo data"
    data = {"photo": (io.BytesIO(content), "profile.jpg")}
    client.post(f"/profile/{profile_id}/photo",
                data=data, content_type="multipart/form-data")
    with app.app_context():
        from sedmob.models import Profile as P
        profile = _db.session.get(P, profile_id)
        filename = profile.photo
    resp = client.get(f"/uploads/{profile_id}/{filename}")
    assert resp.status_code == 200
    assert resp.data == content


# ── Unit Tests: API Edge Cases ────────────────────────────


# Validates: Requirement 8.1
def test_api_photos_list(app, client, db):
    """GET /api/profiles/<pid>/beds/<bid>/photos returns JSON array."""
    profile_id, bed_id = _create_profile_and_bed(client)
    data = {"photo": (io.BytesIO(b"fake image data"), "api.png")}
    client.post(f"/profile/{profile_id}/bed/{bed_id}/photo/new",
                data=data, content_type="multipart/form-data")
    resp = client.get(f"/api/profiles/{profile_id}/beds/{bed_id}/photos")
    assert resp.status_code == 200
    photos = resp.get_json()
    assert isinstance(photos, list)
    assert len(photos) == 1
    assert "filename" in photos[0]
    assert "bed_id" in photos[0]


# Validates: Requirement 8.2
def test_api_photo_detail(app, client, db):
    """GET /api/profiles/<pid>/beds/<bid>/photos/<photo_id> returns single photo."""
    profile_id, bed_id = _create_profile_and_bed(client)
    data = {"photo": (io.BytesIO(b"fake image data"), "detail.png")}
    client.post(f"/profile/{profile_id}/bed/{bed_id}/photo/new",
                data=data, content_type="multipart/form-data")
    with app.app_context():
        photo = BedPhoto.query.filter_by(bed_id=bed_id).first()
        photo_id = photo.id
    resp = client.get(f"/api/profiles/{profile_id}/beds/{bed_id}/photos/{photo_id}")
    assert resp.status_code == 200
    photo_data = resp.get_json()
    assert photo_data["id"] == photo_id
    assert photo_data["bed_id"] == bed_id


# Validates: Requirement 8.3
def test_api_nonexistent_returns_404(client, db):
    """GET /api/profiles/9999/beds/9999/photos returns 404."""
    resp = client.get("/api/profiles/9999/beds/9999/photos")
    assert resp.status_code == 404


# Validates: Requirement 8.5
def test_api_bed_detail_includes_photos(app, client, db):
    """GET /api/profiles/<pid>/beds/<bid> includes 'photos' key."""
    profile_id, bed_id = _create_profile_and_bed(client)
    resp = client.get(f"/api/profiles/{profile_id}/beds/{bed_id}")
    assert resp.status_code == 200
    bed_data = resp.get_json()
    assert "photos" in bed_data
    assert isinstance(bed_data["photos"], list)
    assert len(bed_data["photos"]) == 0
