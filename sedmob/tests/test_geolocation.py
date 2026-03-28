"""Tests for browser geolocation form integration and backend persistence."""
from sedmob.models import Profile


# --- Template rendering tests ---


def test_new_profile_form_has_coordinate_inputs(client):
    """GET /profile/new contains text inputs for all five coordinate fields."""
    resp = client.get("/profile/new")
    html = resp.data.decode()
    for name in ("latitude", "longitude", "altitude", "accuracy", "altitude_accuracy"):
        assert f'name="{name}"' in html


def test_new_profile_form_has_gps_button(client):
    """GET /profile/new contains the GPS button with correct id and label."""
    resp = client.get("/profile/new")
    html = resp.data.decode()
    assert 'id="btn-gps"' in html
    assert "Get GPS Location" in html


def test_edit_profile_form_has_gps_button(client, db):
    """GET /profile/<id> (edit) also contains the GPS button."""
    client.post("/profile/new", data={"name": "GPS Edit Test"})
    p = Profile.query.first()
    resp = client.get(f"/profile/{p.id}")
    html = resp.data.decode()
    assert 'id="btn-gps"' in html
    assert "Get GPS Location" in html


def test_new_profile_form_includes_geolocation_script(client):
    """GET /profile/new includes geolocation.js in a <script> tag."""
    resp = client.get("/profile/new")
    html = resp.data.decode()
    assert "geolocation.js" in html
    assert "<script" in html


# --- Backend persistence tests ---


def test_accuracy_fields_persist(client, db):
    """POSTing accuracy and altitude_accuracy persists those values."""
    client.post("/profile/new", data={
        "name": "Accuracy Test",
        "accuracy": "5.2",
        "altitude_accuracy": "10.1",
    })
    p = Profile.query.filter_by(name="Accuracy Test").first()
    assert p.accuracy == "5.2"
    assert p.altitude_accuracy == "10.1"


def test_missing_accuracy_fields_default_to_no_data(client, db):
    """POSTing without accuracy/altitude_accuracy defaults them to 'No data'."""
    client.post("/profile/new", data={"name": "No Accuracy"})
    p = Profile.query.filter_by(name="No Accuracy").first()
    assert p.accuracy == "No data"
    assert p.altitude_accuracy == "No data"


# --- Property-based tests ---

from uuid import uuid4

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st


@given(
    latitude=st.text(max_size=50),
    longitude=st.text(max_size=50),
    altitude=st.text(max_size=50),
    accuracy=st.text(max_size=50),
    altitude_accuracy=st.text(max_size=50),
)
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
def test_geolocation_field_round_trip_persistence(
    client, db, latitude, longitude, altitude, accuracy, altitude_accuracy
):
    """**Validates: Requirements 5.1, 5.2, 5.3**

    For any set of five string values, submitting them via the profile form
    POST and reading the resulting Profile record should yield the same values.
    """
    unique_name = f"pbt-geo-{uuid4()}"
    resp = client.post("/profile/new", data={
        "name": unique_name,
        "latitude": latitude,
        "longitude": longitude,
        "altitude": altitude,
        "accuracy": accuracy,
        "altitude_accuracy": altitude_accuracy,
    })
    assert resp.status_code == 302

    p = Profile.query.filter_by(name=unique_name).first()
    assert p is not None
    assert p.latitude == latitude
    assert p.longitude == longitude
    assert p.altitude == altitude
    assert p.accuracy == accuracy
    assert p.altitude_accuracy == altitude_accuracy
