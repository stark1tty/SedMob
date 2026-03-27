"""Tests for bed CRUD."""
from sedmob.models import Profile, Bed


def _create_profile(client):
    client.post("/profile/new", data={"name": "TestLog"})
    return Profile.query.first()


def test_create_bed(client, db):
    p = _create_profile(client)
    resp = client.post(f"/profile/{p.id}/bed/new", data={
        "name": "Bed 1",
        "thickness": "25",
        "facies": "F1",
        "lit1_type": "Sandstone",
        "lit1_percentage": "100",
        "boundary": "Sharp",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert Bed.query.count() == 1
    bed = Bed.query.first()
    assert bed.thickness == "25"
    assert bed.lit1_type == "Sandstone"
    assert bed.position == 1


def test_create_bed_requires_thickness(client, db):
    p = _create_profile(client)
    resp = client.post(f"/profile/{p.id}/bed/new", data={
        "name": "No thickness",
        "thickness": "",
    }, follow_redirects=True)
    assert b"required" in resp.data
    assert Bed.query.count() == 0


def test_bed_auto_position(client, db):
    p = _create_profile(client)
    client.post(f"/profile/{p.id}/bed/new", data={"thickness": "10"})
    client.post(f"/profile/{p.id}/bed/new", data={"thickness": "20"})
    client.post(f"/profile/{p.id}/bed/new", data={"thickness": "30"})
    beds = Bed.query.order_by(Bed.position).all()
    assert [b.position for b in beds] == [1, 2, 3]
    assert [b.thickness for b in beds] == ["10", "20", "30"]


def test_edit_bed(client, db):
    p = _create_profile(client)
    client.post(f"/profile/{p.id}/bed/new", data={"thickness": "10", "name": "Old"})
    bed = Bed.query.first()
    resp = client.post(f"/profile/{p.id}/bed/{bed.id}", data={
        "thickness": "99",
        "name": "New",
    }, follow_redirects=True)
    assert resp.status_code == 200
    bed = db.session.get(Bed, bed.id)
    assert bed.thickness == "99"
    assert bed.name == "New"


def test_delete_bed_shifts_positions(client, db):
    p = _create_profile(client)
    client.post(f"/profile/{p.id}/bed/new", data={"thickness": "10", "name": "A"})
    client.post(f"/profile/{p.id}/bed/new", data={"thickness": "20", "name": "B"})
    client.post(f"/profile/{p.id}/bed/new", data={"thickness": "30", "name": "C"})
    bed_b = Bed.query.filter_by(name="B").first()
    resp = client.post(f"/profile/{p.id}/bed/{bed_b.id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert Bed.query.count() == 2
    beds = Bed.query.order_by(Bed.position).all()
    assert [b.name for b in beds] == ["A", "C"]
    assert [b.position for b in beds] == [1, 2]


def test_reorder_beds(client, db):
    p = _create_profile(client)
    client.post(f"/profile/{p.id}/bed/new", data={"thickness": "10", "name": "A"})
    client.post(f"/profile/{p.id}/bed/new", data={"thickness": "20", "name": "B"})
    client.post(f"/profile/{p.id}/bed/new", data={"thickness": "30", "name": "C"})
    beds = Bed.query.order_by(Bed.position).all()
    # Reverse order: C, B, A
    new_order = [beds[2].id, beds[1].id, beds[0].id]
    resp = client.post(f"/profile/{p.id}/bed/reorder",
                       json=new_order, content_type="application/json")
    assert resp.status_code == 200
    beds = Bed.query.order_by(Bed.position).all()
    assert [b.name for b in beds] == ["C", "B", "A"]


def test_delete_profile_cascades_beds(client, db):
    p = _create_profile(client)
    client.post(f"/profile/{p.id}/bed/new", data={"thickness": "10"})
    client.post(f"/profile/{p.id}/bed/new", data={"thickness": "20"})
    assert Bed.query.count() == 2
    client.post(f"/profile/{p.id}/delete")
    assert Bed.query.count() == 0


def test_bed_form_get(client, db):
    p = _create_profile(client)
    resp = client.get(f"/profile/{p.id}/bed/new")
    assert resp.status_code == 200
    assert b"New" in resp.data
