"""Tests for reference data management."""
import uuid

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from sedmob.models import db as _db, Lithology, LithologyType, Structure, StructureType


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


# ── Lithology group delete tests ──────────────────────────


def test_delete_lithology_group_with_children(client, db):
    group = LithologyType(name="DelTestGroup")
    _db.session.add(group)
    _db.session.flush()
    child1 = Lithology(type_id=group.id, name="DelChild1")
    child2 = Lithology(type_id=group.id, name="DelChild2")
    _db.session.add_all([child1, child2])
    _db.session.commit()
    group_id = group.id

    resp = client.post(f"/reference/lithology-type/{group_id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert _db.session.get(LithologyType, group_id) is None
    assert Lithology.query.filter_by(name="DelChild1").first() is None
    assert Lithology.query.filter_by(name="DelChild2").first() is None


def test_delete_empty_lithology_group(client, db):
    group = LithologyType(name="EmptyLithGroup")
    _db.session.add(group)
    _db.session.commit()
    group_id = group.id
    initial_lith_count = Lithology.query.count()

    resp = client.post(f"/reference/lithology-type/{group_id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert _db.session.get(LithologyType, group_id) is None
    assert Lithology.query.count() == initial_lith_count


def test_delete_lithology_group_404(client, db):
    resp = client.post("/reference/lithology-type/99999/delete")
    assert resp.status_code == 404


def test_delete_lithology_group_others_unaffected(client, db):
    grp_a = LithologyType(name="LithGrpA")
    grp_b = LithologyType(name="LithGrpB")
    _db.session.add_all([grp_a, grp_b])
    _db.session.flush()
    child_a = Lithology(type_id=grp_a.id, name="LithChildA")
    child_b = Lithology(type_id=grp_b.id, name="LithChildB")
    _db.session.add_all([child_a, child_b])
    _db.session.commit()
    grp_a_id = grp_a.id
    grp_b_id = grp_b.id

    client.post(f"/reference/lithology-type/{grp_a_id}/delete")

    assert _db.session.get(LithologyType, grp_a_id) is None
    assert _db.session.get(LithologyType, grp_b_id) is not None
    assert Lithology.query.filter_by(name="LithChildB").first() is not None
    assert Lithology.query.filter_by(name="LithChildA").first() is None


# ── Structure group delete tests ──────────────────────────


def test_delete_structure_group_with_children(client, db):
    group = StructureType(name="DelStrGroup")
    _db.session.add(group)
    _db.session.flush()
    child1 = Structure(type_id=group.id, name="DelStrChild1")
    child2 = Structure(type_id=group.id, name="DelStrChild2")
    _db.session.add_all([child1, child2])
    _db.session.commit()
    group_id = group.id

    resp = client.post(f"/reference/structure-type/{group_id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert _db.session.get(StructureType, group_id) is None
    assert Structure.query.filter_by(name="DelStrChild1").first() is None
    assert Structure.query.filter_by(name="DelStrChild2").first() is None


def test_delete_empty_structure_group(client, db):
    group = StructureType(name="EmptyStrGroup")
    _db.session.add(group)
    _db.session.commit()
    group_id = group.id
    initial_str_count = Structure.query.count()

    resp = client.post(f"/reference/structure-type/{group_id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert _db.session.get(StructureType, group_id) is None
    assert Structure.query.count() == initial_str_count


def test_delete_structure_group_404(client, db):
    resp = client.post("/reference/structure-type/99999/delete")
    assert resp.status_code == 404


def test_delete_structure_group_others_unaffected(client, db):
    grp_a = StructureType(name="StrGrpA")
    grp_b = StructureType(name="StrGrpB")
    _db.session.add_all([grp_a, grp_b])
    _db.session.flush()
    child_a = Structure(type_id=grp_a.id, name="StrChildA")
    child_b = Structure(type_id=grp_b.id, name="StrChildB")
    _db.session.add_all([child_a, child_b])
    _db.session.commit()
    grp_a_id = grp_a.id
    grp_b_id = grp_b.id

    client.post(f"/reference/structure-type/{grp_a_id}/delete")

    assert _db.session.get(StructureType, grp_a_id) is None
    assert _db.session.get(StructureType, grp_b_id) is not None
    assert Structure.query.filter_by(name="StrChildB").first() is not None
    assert Structure.query.filter_by(name="StrChildA").first() is None


# ── Reference page HTML structure tests ────────────────────


def test_reference_page_contains_lithology_rename_forms(client, db):
    """Validates: Requirements 7.1 — lithology items have inline rename forms."""
    resp = client.get("/reference")
    html = resp.data.decode()
    lith = Lithology.query.first()
    assert f'/reference/lithology/{lith.id}/rename' in html
    assert f'value="{lith.name}"' in html


def test_reference_page_contains_structure_rename_forms(client, db):
    """Validates: Requirements 7.2 — structure items have inline rename forms."""
    resp = client.get("/reference")
    html = resp.data.decode()
    struct = Structure.query.first()
    assert f'/reference/structure/{struct.id}/rename' in html
    assert f'value="{struct.name}"' in html


def test_reference_page_contains_lithology_group_rename_forms(client, db):
    """Validates: Requirements 7.3 — lithology groups have inline rename forms."""
    resp = client.get("/reference")
    html = resp.data.decode()
    lt = LithologyType.query.first()
    assert f'/reference/lithology-type/{lt.id}/rename' in html
    assert f'value="{lt.name}"' in html


def test_reference_page_contains_structure_group_rename_forms(client, db):
    """Validates: Requirements 7.4 — structure groups have inline rename forms."""
    resp = client.get("/reference")
    html = resp.data.decode()
    st = StructureType.query.first()
    assert f'/reference/structure-type/{st.id}/rename' in html
    assert f'value="{st.name}"' in html


def test_reference_page_contains_lithology_group_delete_buttons(client, db):
    """Validates: Requirements 7.5 — lithology groups have Delete Group buttons."""
    resp = client.get("/reference")
    html = resp.data.decode()
    lt = LithologyType.query.first()
    assert f'/reference/lithology-type/{lt.id}/delete' in html
    assert 'Delete Group' in html


def test_reference_page_contains_structure_group_delete_buttons(client, db):
    """Validates: Requirements 7.6 — structure groups have Delete Group buttons."""
    resp = client.get("/reference")
    html = resp.data.decode()
    st = StructureType.query.first()
    assert f'/reference/structure-type/{st.id}/delete' in html
    assert 'Delete Group' in html


def test_reference_page_rename_forms_for_all_entities(client, db):
    """Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6 — all entity types present."""
    resp = client.get("/reference")
    html = resp.data.decode()

    # Every lithology item should have a rename form
    for lith in Lithology.query.all():
        assert f'/reference/lithology/{lith.id}/rename' in html
        assert f'value="{lith.name}"' in html

    # Every structure item should have a rename form
    for struct in Structure.query.all():
        assert f'/reference/structure/{struct.id}/rename' in html
        assert f'value="{struct.name}"' in html

    # Every lithology group should have rename + delete forms
    for lt in LithologyType.query.all():
        assert f'/reference/lithology-type/{lt.id}/rename' in html
        assert f'/reference/lithology-type/{lt.id}/delete' in html
        assert f'value="{lt.name}"' in html

    # Every structure group should have rename + delete forms
    for st_type in StructureType.query.all():
        assert f'/reference/structure-type/{st_type.id}/rename' in html
        assert f'/reference/structure-type/{st_type.id}/delete' in html
        assert f'value="{st_type.name}"' in html

    # Name inputs exist
    assert 'name="name"' in html


# ── Property-based tests ──────────────────────────────────

# Feature: reference-data-editing, Property 1: Valid rename updates the name
# Validates: Requirements 1.1, 2.1, 3.1, 4.1, 8.1, 8.2

valid_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Zs")),
    min_size=1,
).filter(lambda s: s.strip().replace(" ", "").isalnum() and len(s.strip()) > 0)


@given(name=valid_name_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_valid_rename_updates_name_lithology(client, db, name):
    """Property 1 – Lithology: any valid name is accepted and stored (stripped)."""
    uid = uuid.uuid4().hex[:8]
    unique_initial = f"PropLith {uid}"
    # Ensure the target name is unique by appending a suffix
    unique_name = f"{name.strip()} {uid}"
    lt = LithologyType.query.first()
    item = Lithology(type_id=lt.id, name=unique_initial)
    _db.session.add(item)
    _db.session.commit()
    item_id = item.id

    resp = client.post(f"/reference/lithology/{item_id}/rename", data={"name": unique_name})
    assert resp.status_code == 302

    updated = _db.session.get(Lithology, item_id)
    assert updated.name == unique_name.strip()

    # cleanup
    _db.session.delete(updated)
    _db.session.commit()


@given(name=valid_name_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_valid_rename_updates_name_structure(client, db, name):
    """Property 1 – Structure: any valid name is accepted and stored (stripped)."""
    uid = uuid.uuid4().hex[:8]
    unique_initial = f"PropStruct {uid}"
    unique_name = f"{name.strip()} {uid}"
    st_type = StructureType.query.first()
    item = Structure(type_id=st_type.id, name=unique_initial)
    _db.session.add(item)
    _db.session.commit()
    item_id = item.id

    resp = client.post(f"/reference/structure/{item_id}/rename", data={"name": unique_name})
    assert resp.status_code == 302

    updated = _db.session.get(Structure, item_id)
    assert updated.name == unique_name.strip()

    _db.session.delete(updated)
    _db.session.commit()


@given(name=valid_name_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_valid_rename_updates_name_lithology_type(client, db, name):
    """Property 1 – LithologyType: any valid name is accepted and stored (stripped)."""
    uid = uuid.uuid4().hex[:8]
    unique_initial = f"PropLithType {uid}"
    unique_name = f"{name.strip()} {uid}"
    item = LithologyType(name=unique_initial)
    _db.session.add(item)
    _db.session.commit()
    item_id = item.id

    resp = client.post(f"/reference/lithology-type/{item_id}/rename", data={"name": unique_name})
    assert resp.status_code == 302

    updated = _db.session.get(LithologyType, item_id)
    assert updated.name == unique_name.strip()

    _db.session.delete(updated)
    _db.session.commit()


@given(name=valid_name_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_valid_rename_updates_name_structure_type(client, db, name):
    """Property 1 – StructureType: any valid name is accepted and stored (stripped)."""
    uid = uuid.uuid4().hex[:8]
    unique_initial = f"PropStructType {uid}"
    unique_name = f"{name.strip()} {uid}"
    item = StructureType(name=unique_initial)
    _db.session.add(item)
    _db.session.commit()
    item_id = item.id

    resp = client.post(f"/reference/structure-type/{item_id}/rename", data={"name": unique_name})
    assert resp.status_code == 302

    updated = _db.session.get(StructureType, item_id)
    assert updated.name == unique_name.strip()

    _db.session.delete(updated)
    _db.session.commit()


# Feature: reference-data-editing, Property 2: Invalid name is rejected
# Validates: Requirements 1.3, 2.3, 3.3, 4.3, 8.3, 8.4

invalid_name_strategy = st.text(min_size=0).filter(
    lambda s: not s.strip() or not s.strip().replace(" ", "").isalnum()
)


@given(name=invalid_name_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_invalid_name_rejected_lithology(client, db, name):
    """Property 2 – Lithology: any invalid name is rejected, record unchanged."""
    uid = uuid.uuid4().hex[:8]
    original_name = f"PropLith {uid}"
    lt = LithologyType.query.first()
    item = Lithology(type_id=lt.id, name=original_name)
    _db.session.add(item)
    _db.session.commit()
    item_id = item.id

    client.post(f"/reference/lithology/{item_id}/rename", data={"name": name})

    unchanged = _db.session.get(Lithology, item_id)
    assert unchanged.name == original_name

    # cleanup
    _db.session.delete(unchanged)
    _db.session.commit()


@given(name=invalid_name_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_invalid_name_rejected_structure(client, db, name):
    """Property 2 – Structure: any invalid name is rejected, record unchanged."""
    uid = uuid.uuid4().hex[:8]
    original_name = f"PropStruct {uid}"
    st_type = StructureType.query.first()
    item = Structure(type_id=st_type.id, name=original_name)
    _db.session.add(item)
    _db.session.commit()
    item_id = item.id

    client.post(f"/reference/structure/{item_id}/rename", data={"name": name})

    unchanged = _db.session.get(Structure, item_id)
    assert unchanged.name == original_name

    _db.session.delete(unchanged)
    _db.session.commit()


@given(name=invalid_name_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_invalid_name_rejected_lithology_type(client, db, name):
    """Property 2 – LithologyType: any invalid name is rejected, record unchanged."""
    uid = uuid.uuid4().hex[:8]
    original_name = f"PropLithType {uid}"
    item = LithologyType(name=original_name)
    _db.session.add(item)
    _db.session.commit()
    item_id = item.id

    client.post(f"/reference/lithology-type/{item_id}/rename", data={"name": name})

    unchanged = _db.session.get(LithologyType, item_id)
    assert unchanged.name == original_name

    _db.session.delete(unchanged)
    _db.session.commit()


@given(name=invalid_name_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_invalid_name_rejected_structure_type(client, db, name):
    """Property 2 – StructureType: any invalid name is rejected, record unchanged."""
    uid = uuid.uuid4().hex[:8]
    original_name = f"PropStructType {uid}"
    item = StructureType(name=original_name)
    _db.session.add(item)
    _db.session.commit()
    item_id = item.id

    client.post(f"/reference/structure-type/{item_id}/rename", data={"name": name})

    unchanged = _db.session.get(StructureType, item_id)
    assert unchanged.name == original_name

    _db.session.delete(unchanged)
    _db.session.commit()


# Feature: reference-data-editing, Property 3: Duplicate name is rejected
# Validates: Requirements 1.4, 2.4, 3.4, 4.4


@given(name_a=valid_name_strategy, name_b=valid_name_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_duplicate_name_rejected_lithology(client, db, name_a, name_b):
    """Property 3 – Lithology: renaming to another record's name is rejected."""
    uid = uuid.uuid4().hex[:8]
    unique_a = f"{name_a.strip()} {uid}a"
    unique_b = f"{name_b.strip()} {uid}b"
    lt = LithologyType.query.first()
    item_a = Lithology(type_id=lt.id, name=unique_a)
    item_b = Lithology(type_id=lt.id, name=unique_b)
    _db.session.add_all([item_a, item_b])
    _db.session.commit()
    id_a = item_a.id
    id_b = item_b.id

    resp = client.post(f"/reference/lithology/{id_a}/rename", data={"name": unique_b})
    assert resp.status_code == 302

    unchanged = _db.session.get(Lithology, id_a)
    assert unchanged.name == unique_a

    # cleanup
    _db.session.delete(_db.session.get(Lithology, id_a))
    _db.session.delete(_db.session.get(Lithology, id_b))
    _db.session.commit()


@given(name_a=valid_name_strategy, name_b=valid_name_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_duplicate_name_rejected_structure(client, db, name_a, name_b):
    """Property 3 – Structure: renaming to another record's name is rejected."""
    uid = uuid.uuid4().hex[:8]
    unique_a = f"{name_a.strip()} {uid}a"
    unique_b = f"{name_b.strip()} {uid}b"
    st_type = StructureType.query.first()
    item_a = Structure(type_id=st_type.id, name=unique_a)
    item_b = Structure(type_id=st_type.id, name=unique_b)
    _db.session.add_all([item_a, item_b])
    _db.session.commit()
    id_a = item_a.id
    id_b = item_b.id

    resp = client.post(f"/reference/structure/{id_a}/rename", data={"name": unique_b})
    assert resp.status_code == 302

    unchanged = _db.session.get(Structure, id_a)
    assert unchanged.name == unique_a

    # cleanup
    _db.session.delete(_db.session.get(Structure, id_a))
    _db.session.delete(_db.session.get(Structure, id_b))
    _db.session.commit()


@given(name_a=valid_name_strategy, name_b=valid_name_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_duplicate_name_rejected_lithology_type(client, db, name_a, name_b):
    """Property 3 – LithologyType: renaming to another record's name is rejected."""
    uid = uuid.uuid4().hex[:8]
    unique_a = f"{name_a.strip()} {uid}a"
    unique_b = f"{name_b.strip()} {uid}b"
    item_a = LithologyType(name=unique_a)
    item_b = LithologyType(name=unique_b)
    _db.session.add_all([item_a, item_b])
    _db.session.commit()
    id_a = item_a.id
    id_b = item_b.id

    resp = client.post(f"/reference/lithology-type/{id_a}/rename", data={"name": unique_b})
    assert resp.status_code == 302

    unchanged = _db.session.get(LithologyType, id_a)
    assert unchanged.name == unique_a

    # cleanup
    _db.session.delete(_db.session.get(LithologyType, id_a))
    _db.session.delete(_db.session.get(LithologyType, id_b))
    _db.session.commit()


@given(name_a=valid_name_strategy, name_b=valid_name_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_duplicate_name_rejected_structure_type(client, db, name_a, name_b):
    """Property 3 – StructureType: renaming to another record's name is rejected."""
    uid = uuid.uuid4().hex[:8]
    unique_a = f"{name_a.strip()} {uid}a"
    unique_b = f"{name_b.strip()} {uid}b"
    item_a = StructureType(name=unique_a)
    item_b = StructureType(name=unique_b)
    _db.session.add_all([item_a, item_b])
    _db.session.commit()
    id_a = item_a.id
    id_b = item_b.id

    resp = client.post(f"/reference/structure-type/{id_a}/rename", data={"name": unique_b})
    assert resp.status_code == 302

    unchanged = _db.session.get(StructureType, id_a)
    assert unchanged.name == unique_a

    # cleanup
    _db.session.delete(_db.session.get(StructureType, id_a))
    _db.session.delete(_db.session.get(StructureType, id_b))
    _db.session.commit()


# Feature: reference-data-editing, Property 4: Group rename preserves children
# Validates: Requirements 3.5, 4.5


@given(
    n_children=st.integers(min_value=0, max_value=10),
    new_name=valid_name_strategy,
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_group_rename_preserves_children_lithology_type(client, db, n_children, new_name):
    """Property 4 – LithologyType: renaming a group preserves all children."""
    uid = uuid.uuid4().hex[:8]
    group_name = f"PropLitGrp {uid}"
    unique_new_name = f"{new_name.strip()} {uid}"

    group = LithologyType(name=group_name)
    _db.session.add(group)
    _db.session.flush()
    group_id = group.id

    child_names = [f"PropChild {uid} {i}" for i in range(n_children)]
    for cname in child_names:
        _db.session.add(Lithology(type_id=group_id, name=cname))
    _db.session.commit()

    resp = client.post(
        f"/reference/lithology-type/{group_id}/rename",
        data={"name": unique_new_name},
    )
    assert resp.status_code == 302

    children_after = Lithology.query.filter_by(type_id=group_id).all()
    assert len(children_after) == n_children
    assert sorted(c.name for c in children_after) == sorted(child_names)
    assert all(c.type_id == group_id for c in children_after)

    # cleanup
    for c in children_after:
        _db.session.delete(c)
    grp = _db.session.get(LithologyType, group_id)
    if grp:
        _db.session.delete(grp)
    _db.session.commit()


@given(
    n_children=st.integers(min_value=0, max_value=10),
    new_name=valid_name_strategy,
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_group_rename_preserves_children_structure_type(client, db, n_children, new_name):
    """Property 4 – StructureType: renaming a group preserves all children."""
    uid = uuid.uuid4().hex[:8]
    group_name = f"PropStrGrp {uid}"
    unique_new_name = f"{new_name.strip()} {uid}"

    group = StructureType(name=group_name)
    _db.session.add(group)
    _db.session.flush()
    group_id = group.id

    child_names = [f"PropSChild {uid} {i}" for i in range(n_children)]
    for cname in child_names:
        _db.session.add(Structure(type_id=group_id, name=cname))
    _db.session.commit()

    resp = client.post(
        f"/reference/structure-type/{group_id}/rename",
        data={"name": unique_new_name},
    )
    assert resp.status_code == 302

    children_after = Structure.query.filter_by(type_id=group_id).all()
    assert len(children_after) == n_children
    assert sorted(c.name for c in children_after) == sorted(child_names)
    assert all(c.type_id == group_id for c in children_after)

    # cleanup
    for c in children_after:
        _db.session.delete(c)
    grp = _db.session.get(StructureType, group_id)
    if grp:
        _db.session.delete(grp)
    _db.session.commit()


# Feature: reference-data-editing, Property 5: Group delete cascades to all children
# Validates: Requirements 5.1, 5.3, 5.4, 6.1, 6.3, 6.4


@given(n_children=st.integers(min_value=0, max_value=10))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_group_delete_cascades_lithology_type(client, db, n_children):
    """Property 5 – LithologyType: deleting a group removes it and all children."""
    uid = uuid.uuid4().hex[:8]
    group_name = f"PropDelLitGrp {uid}"

    # Create the target group with N children
    group = LithologyType(name=group_name)
    _db.session.add(group)
    _db.session.flush()
    group_id = group.id

    child_names = [f"PropDelLitChild {uid} {i}" for i in range(n_children)]
    for cname in child_names:
        _db.session.add(Lithology(type_id=group_id, name=cname))

    # Create a control group with 1 child (should be unaffected)
    ctrl_uid = uuid.uuid4().hex[:8]
    ctrl_group = LithologyType(name=f"CtrlLitGrp {ctrl_uid}")
    _db.session.add(ctrl_group)
    _db.session.flush()
    ctrl_group_id = ctrl_group.id
    ctrl_child_name = f"CtrlLitChild {ctrl_uid}"
    _db.session.add(Lithology(type_id=ctrl_group_id, name=ctrl_child_name))
    _db.session.commit()

    # Delete the target group
    resp = client.post(f"/reference/lithology-type/{group_id}/delete")
    assert resp.status_code == 302

    # Verify target group and all its children are gone
    assert _db.session.get(LithologyType, group_id) is None
    for cname in child_names:
        assert Lithology.query.filter_by(name=cname).first() is None

    # Verify control group and its child still exist
    assert _db.session.get(LithologyType, ctrl_group_id) is not None
    assert Lithology.query.filter_by(name=ctrl_child_name).first() is not None

    # Cleanup control group
    ctrl_child = Lithology.query.filter_by(name=ctrl_child_name).first()
    if ctrl_child:
        _db.session.delete(ctrl_child)
    ctrl_grp = _db.session.get(LithologyType, ctrl_group_id)
    if ctrl_grp:
        _db.session.delete(ctrl_grp)
    _db.session.commit()


@given(n_children=st.integers(min_value=0, max_value=10))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_prop_group_delete_cascades_structure_type(client, db, n_children):
    """Property 5 – StructureType: deleting a group removes it and all children."""
    uid = uuid.uuid4().hex[:8]
    group_name = f"PropDelStrGrp {uid}"

    # Create the target group with N children
    group = StructureType(name=group_name)
    _db.session.add(group)
    _db.session.flush()
    group_id = group.id

    child_names = [f"PropDelStrChild {uid} {i}" for i in range(n_children)]
    for cname in child_names:
        _db.session.add(Structure(type_id=group_id, name=cname))

    # Create a control group with 1 child (should be unaffected)
    ctrl_uid = uuid.uuid4().hex[:8]
    ctrl_group = StructureType(name=f"CtrlStrGrp {ctrl_uid}")
    _db.session.add(ctrl_group)
    _db.session.flush()
    ctrl_group_id = ctrl_group.id
    ctrl_child_name = f"CtrlStrChild {ctrl_uid}"
    _db.session.add(Structure(type_id=ctrl_group_id, name=ctrl_child_name))
    _db.session.commit()

    # Delete the target group
    resp = client.post(f"/reference/structure-type/{group_id}/delete")
    assert resp.status_code == 302

    # Verify target group and all its children are gone
    assert _db.session.get(StructureType, group_id) is None
    for cname in child_names:
        assert Structure.query.filter_by(name=cname).first() is None

    # Verify control group and its child still exist
    assert _db.session.get(StructureType, ctrl_group_id) is not None
    assert Structure.query.filter_by(name=ctrl_child_name).first() is not None

    # Cleanup control group
    ctrl_child = Structure.query.filter_by(name=ctrl_child_name).first()
    if ctrl_child:
        _db.session.delete(ctrl_child)
    ctrl_grp = _db.session.get(StructureType, ctrl_group_id)
    if ctrl_grp:
        _db.session.delete(ctrl_grp)
    _db.session.commit()
