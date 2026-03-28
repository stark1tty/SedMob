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


# ── Lithology rename tests ────────────────────────────────


def test_rename_lithology_valid(client, db):
    lith = Lithology.query.filter_by(name="Sandstone").first()
    resp = client.post(
        f"/reference/lithology/{lith.id}/rename",
        data={"name": "Quartzite"},
    )
    assert resp.status_code == 302
    updated = db.session.get(Lithology, lith.id)
    assert updated.name == "Quartzite"


def test_rename_lithology_invalid_name(client, db):
    lith = Lithology.query.filter_by(name="Sandstone").first()
    resp = client.post(
        f"/reference/lithology/{lith.id}/rename",
        data={"name": "Bad@Name!"},
        follow_redirects=True,
    )
    assert b"letters, digits and spaces" in resp.data
    unchanged = db.session.get(Lithology, lith.id)
    assert unchanged.name == "Sandstone"


def test_rename_lithology_duplicate(client, db):
    lith = Lithology.query.filter_by(name="Sandstone").first()
    resp = client.post(
        f"/reference/lithology/{lith.id}/rename",
        data={"name": "Chert"},
        follow_redirects=True,
    )
    assert b"already exists" in resp.data
    unchanged = db.session.get(Lithology, lith.id)
    assert unchanged.name == "Sandstone"


def test_rename_lithology_self_duplicate(client, db):
    lith = Lithology.query.filter_by(name="Sandstone").first()
    resp = client.post(
        f"/reference/lithology/{lith.id}/rename",
        data={"name": "Sandstone"},
    )
    assert resp.status_code == 302
    updated = db.session.get(Lithology, lith.id)
    assert updated.name == "Sandstone"


def test_rename_lithology_404(client, db):
    resp = client.post(
        "/reference/lithology/99999/rename",
        data={"name": "Whatever"},
    )
    assert resp.status_code == 404


# ── Structure rename tests ────────────────────────────────


def test_rename_structure_valid(client, db):
    struct = Structure.query.filter_by(name="Scours").first()
    resp = client.post(
        f"/reference/structure/{struct.id}/rename",
        data={"name": "Gutter casts"},
    )
    assert resp.status_code == 302
    updated = db.session.get(Structure, struct.id)
    assert updated.name == "Gutter casts"


def test_rename_structure_invalid_name(client, db):
    struct = Structure.query.filter_by(name="Scours").first()
    resp = client.post(
        f"/reference/structure/{struct.id}/rename",
        data={"name": "Bad@Name!"},
        follow_redirects=True,
    )
    assert b"letters, digits and spaces" in resp.data
    unchanged = db.session.get(Structure, struct.id)
    assert unchanged.name == "Scours"


def test_rename_structure_duplicate(client, db):
    struct = Structure.query.filter_by(name="Scours").first()
    resp = client.post(
        f"/reference/structure/{struct.id}/rename",
        data={"name": "Flute marks"},
        follow_redirects=True,
    )
    assert b"already exists" in resp.data
    unchanged = db.session.get(Structure, struct.id)
    assert unchanged.name == "Scours"


def test_rename_structure_self_duplicate(client, db):
    struct = Structure.query.filter_by(name="Scours").first()
    resp = client.post(
        f"/reference/structure/{struct.id}/rename",
        data={"name": "Scours"},
    )
    assert resp.status_code == 302
    updated = db.session.get(Structure, struct.id)
    assert updated.name == "Scours"


def test_rename_structure_404(client, db):
    resp = client.post(
        "/reference/structure/99999/rename",
        data={"name": "Whatever"},
    )
    assert resp.status_code == 404


# ── Lithology group (LithologyType) rename tests ─────────


def test_rename_lithology_group_valid(client, db):
    lt = LithologyType.query.filter_by(name="Basic").first()
    resp = client.post(
        f"/reference/lithology-type/{lt.id}/rename",
        data={"name": "Clastic"},
    )
    assert resp.status_code == 302
    updated = db.session.get(LithologyType, lt.id)
    assert updated.name == "Clastic"


def test_rename_lithology_group_preserves_children(client, db):
    lt = LithologyType.query.filter_by(name="Basic").first()
    children_before = Lithology.query.filter_by(type_id=lt.id).all()
    names_before = sorted(c.name for c in children_before)
    count_before = len(children_before)

    client.post(
        f"/reference/lithology-type/{lt.id}/rename",
        data={"name": "Clastic"},
    )

    children_after = Lithology.query.filter_by(type_id=lt.id).all()
    assert len(children_after) == count_before
    assert sorted(c.name for c in children_after) == names_before
    assert all(c.type_id == lt.id for c in children_after)


def test_rename_lithology_group_invalid_name(client, db):
    lt = LithologyType.query.filter_by(name="Basic").first()
    resp = client.post(
        f"/reference/lithology-type/{lt.id}/rename",
        data={"name": "Bad@Name!"},
        follow_redirects=True,
    )
    assert b"letters, digits and spaces" in resp.data
    unchanged = db.session.get(LithologyType, lt.id)
    assert unchanged.name == "Basic"


def test_rename_lithology_group_duplicate(client, db):
    lt = LithologyType.query.filter_by(name="Basic").first()
    resp = client.post(
        f"/reference/lithology-type/{lt.id}/rename",
        data={"name": "Carbonates"},
        follow_redirects=True,
    )
    assert b"already exists" in resp.data
    unchanged = db.session.get(LithologyType, lt.id)
    assert unchanged.name == "Basic"


def test_rename_lithology_group_404(client, db):
    resp = client.post(
        "/reference/lithology-type/99999/rename",
        data={"name": "Whatever"},
    )
    assert resp.status_code == 404


# ── Structure group (StructureType) rename tests ─────────


def test_rename_structure_group_valid(client, db):
    st = StructureType.query.filter_by(name="Other").first()
    resp = client.post(
        f"/reference/structure-type/{st.id}/rename",
        data={"name": "Miscellaneous"},
    )
    assert resp.status_code == 302
    updated = db.session.get(StructureType, st.id)
    assert updated.name == "Miscellaneous"


def test_rename_structure_group_preserves_children(client, db):
    st = StructureType.query.filter_by(name="Other").first()
    children_before = Structure.query.filter_by(type_id=st.id).all()
    names_before = sorted(c.name for c in children_before)
    count_before = len(children_before)

    client.post(
        f"/reference/structure-type/{st.id}/rename",
        data={"name": "Miscellaneous"},
    )

    children_after = Structure.query.filter_by(type_id=st.id).all()
    assert len(children_after) == count_before
    assert sorted(c.name for c in children_after) == names_before
    assert all(c.type_id == st.id for c in children_after)


def test_rename_structure_group_invalid_name(client, db):
    st = StructureType.query.filter_by(name="Other").first()
    resp = client.post(
        f"/reference/structure-type/{st.id}/rename",
        data={"name": "Bad@Name!"},
        follow_redirects=True,
    )
    assert b"letters, digits and spaces" in resp.data
    unchanged = db.session.get(StructureType, st.id)
    assert unchanged.name == "Other"


def test_rename_structure_group_duplicate(client, db):
    st = StructureType.query.filter_by(name="Other").first()
    resp = client.post(
        f"/reference/structure-type/{st.id}/rename",
        data={"name": "Fossils"},
        follow_redirects=True,
    )
    assert b"already exists" in resp.data
    unchanged = db.session.get(StructureType, st.id)
    assert unchanged.name == "Other"


def test_rename_structure_group_404(client, db):
    resp = client.post(
        "/reference/structure-type/99999/rename",
        data={"name": "Whatever"},
    )
    assert resp.status_code == 404
