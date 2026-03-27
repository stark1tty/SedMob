"""Tests for reference data management."""
from sedmob.models import Lithology, LithologyType, Structure, StructureType


def test_reference_page(client):
    resp = client.get("/reference")
    assert resp.status_code == 200
    assert b"Reference Data" in resp.data
    assert b"Sandstone" in resp.data


def test_add_lithology(client, db):
    lt = LithologyType.query.filter_by(name="Basic").first()
    initial = Lithology.query.count()
    resp = client.post("/reference/lithology/add", data={
        "name": "Greywacke",
        "type_id": str(lt.id),
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert Lithology.query.count() == initial + 1
    assert Lithology.query.filter_by(name="Greywacke").first() is not None


def test_add_lithology_group(client, db):
    initial = LithologyType.query.count()
    resp = client.post("/reference/lithology/add", data={
        "name": "Metamorphic",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert LithologyType.query.count() == initial + 1


def test_add_duplicate_lithology(client, db):
    lt = LithologyType.query.filter_by(name="Basic").first()
    resp = client.post("/reference/lithology/add", data={
        "name": "Sandstone",
        "type_id": str(lt.id),
    }, follow_redirects=True)
    assert b"already exists" in resp.data


def test_add_lithology_invalid_name(client, db):
    resp = client.post("/reference/lithology/add", data={
        "name": "Bad@Name!",
    }, follow_redirects=True)
    assert b"letters, digits and spaces" in resp.data


def test_delete_lithology(client, db):
    lith = Lithology.query.filter_by(name="Chert").first()
    initial = Lithology.query.count()
    resp = client.post(f"/reference/lithology/{lith.id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert Lithology.query.count() == initial - 1


def test_add_structure(client, db):
    st = StructureType.query.filter_by(name="Other").first()
    initial = Structure.query.count()
    client.post("/reference/structure/add", data={
        "name": "Tool marks",
        "type_id": str(st.id),
    })
    assert Structure.query.count() == initial + 1


def test_delete_structure(client, db):
    s = Structure.query.filter_by(name="Scours").first()
    initial = Structure.query.count()
    client.post(f"/reference/structure/{s.id}/delete")
    assert Structure.query.count() == initial - 1
