"""Tests for profile (log) CRUD."""
from sedmob.models import Profile


def test_home_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Log List" in resp.data


def test_create_profile(client, db):
    resp = client.post("/profile/new", data={
        "name": "Test Log",
        "description": "A test log",
        "direction": "off",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Test Log" in resp.data
    assert Profile.query.count() == 1


def test_create_duplicate_profile(client, db):
    client.post("/profile/new", data={"name": "Dup"})
    resp = client.post("/profile/new", data={"name": "Dup"}, follow_redirects=True)
    assert b"already exists" in resp.data
    assert Profile.query.count() == 1


def test_create_profile_empty_name(client, db):
    resp = client.post("/profile/new", data={"name": ""}, follow_redirects=True)
    assert b"required" in resp.data
    assert Profile.query.count() == 0


def test_edit_profile(client, db):
    client.post("/profile/new", data={"name": "Original"})
    p = Profile.query.first()
    resp = client.post(f"/profile/{p.id}", data={
        "name": "Updated",
        "description": "new desc",
    }, follow_redirects=True)
    assert resp.status_code == 200
    p = db.session.get(Profile, p.id)
    assert p.name == "Updated"
    assert p.description == "new desc"


def test_delete_profile(client, db):
    client.post("/profile/new", data={"name": "ToDelete"})
    p = Profile.query.first()
    resp = client.post(f"/profile/{p.id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert Profile.query.count() == 0


def test_profile_page_shows_beds(client, db):
    client.post("/profile/new", data={"name": "WithBeds"})
    p = Profile.query.first()
    client.post(f"/profile/{p.id}/bed/new", data={
        "name": "Bed A", "thickness": "50",
        "lit1_percentage": "100", "lit2_percentage": "0", "lit3_percentage": "0",
    })
    resp = client.get(f"/profile/{p.id}")
    assert b"Bed A" in resp.data


def test_profile_get_form(client):
    resp = client.get("/profile/new")
    assert resp.status_code == 200
    assert b"New" in resp.data
