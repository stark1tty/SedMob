"""Tests for grain size phi value dual storage."""
from sedmob.models import Profile, Bed, GrainClastic, GrainCarbonate


def _create_profile(client):
    client.post("/profile/new", data={"name": "PhiTestLog"})
    return Profile.query.first()


# ── Unit Tests ────────────────────────────────────────────


def test_clastic_option_values_are_phi(client, db):
    """Rendered form has <option> elements with value=g.phi and text=g.name for clastic selects."""
    p = _create_profile(client)
    resp = client.get(f"/profile/{p.id}/bed/new")
    html = resp.data.decode()
    for g in GrainClastic.query.all():
        assert f'value="{g.phi}"' in html
        assert f">{g.name}</option>" in html


def test_carbonate_option_values_are_phi(client, db):
    """Rendered form has <option> elements with value=g.phi and text=g.name for carbonate selects."""
    p = _create_profile(client)
    resp = client.get(f"/profile/{p.id}/bed/new")
    html = resp.data.decode()
    for g in GrainCarbonate.query.all():
        assert f'value="{g.phi}"' in html
        assert f">{g.name}</option>" in html


def test_hidden_inputs_exist(client, db):
    """Rendered form contains hidden inputs named size_clastic_base, size_clastic_top, size_carbo_base, size_carbo_top."""
    p = _create_profile(client)
    resp = client.get(f"/profile/{p.id}/bed/new")
    html = resp.data.decode()
    for name in ["size_clastic_base", "size_clastic_top", "size_carbo_base", "size_carbo_top"]:
        assert f'name="{name}"' in html
        assert f'id="{name}"' in html


def test_selects_named_phi(client, db):
    """Selects are named phi_clastic_base, phi_clastic_top, phi_carbo_base, phi_carbo_top."""
    p = _create_profile(client)
    resp = client.get(f"/profile/{p.id}/bed/new")
    html = resp.data.decode()
    for name in ["phi_clastic_base", "phi_clastic_top", "phi_carbo_base", "phi_carbo_top"]:
        assert f'name="{name}"' in html


def test_submit_clastic_stores_both_columns(client, db):
    """Submitting a bed with phi_* and size_* fields stores both columns correctly (clastic)."""
    p = _create_profile(client)
    g = GrainClastic.query.first()
    client.post(f"/profile/{p.id}/bed/new", data={
        "thickness": "10",
        "phi_clastic_base": g.phi,
        "size_clastic_base": g.name,
    })
    bed = Bed.query.first()
    assert bed.phi_clastic_base == g.phi
    assert bed.size_clastic_base == g.name


def test_submit_carbonate_stores_both_columns(client, db):
    """Submitting a bed with phi_* and size_* fields stores both columns correctly (carbonate)."""
    p = _create_profile(client)
    g = GrainCarbonate.query.first()
    client.post(f"/profile/{p.id}/bed/new", data={
        "thickness": "10",
        "phi_carbo_base": g.phi,
        "size_carbo_base": g.name,
    })
    bed = Bed.query.first()
    assert bed.phi_carbo_base == g.phi
    assert bed.size_carbo_base == g.name


def test_empty_selection_stores_empty_strings(client, db):
    """Submitting with no grain size selection stores empty strings in both columns."""
    p = _create_profile(client)
    client.post(f"/profile/{p.id}/bed/new", data={
        "thickness": "10",
    })
    bed = Bed.query.first()
    assert bed.phi_clastic_base == ""
    assert bed.size_clastic_base == ""
    assert bed.phi_carbo_base == ""
    assert bed.size_carbo_base == ""


def test_edit_bed_updates_both_columns(client, db):
    """Editing a bed and changing grain size updates both columns."""
    p = _create_profile(client)
    g1 = GrainClastic.query.first()
    g2 = GrainClastic.query.all()[1]
    client.post(f"/profile/{p.id}/bed/new", data={
        "thickness": "10",
        "phi_clastic_base": g1.phi,
        "size_clastic_base": g1.name,
    })
    bed = Bed.query.first()
    client.post(f"/profile/{p.id}/bed/{bed.id}", data={
        "thickness": "10",
        "phi_clastic_base": g2.phi,
        "size_clastic_base": g2.name,
    })
    bed = db.session.get(Bed, bed.id)
    assert bed.phi_clastic_base == g2.phi
    assert bed.size_clastic_base == g2.name


def test_preselection_on_edit(client, db):
    """Create a bed with known phi values, fetch edit form, verify correct options are selected."""
    p = _create_profile(client)
    g = GrainClastic.query.first()
    client.post(f"/profile/{p.id}/bed/new", data={
        "thickness": "10",
        "phi_clastic_base": g.phi,
        "size_clastic_base": g.name,
    })
    bed = Bed.query.first()
    resp = client.get(f"/profile/{p.id}/bed/{bed.id}")
    html = resp.data.decode()
    assert f'value="{g.phi}" selected' in html


def test_hidden_input_initialization_on_edit(client, db):
    """Create a bed with known size names, fetch edit form, verify hidden input value attributes."""
    p = _create_profile(client)
    g = GrainClastic.query.first()
    client.post(f"/profile/{p.id}/bed/new", data={
        "thickness": "10",
        "phi_clastic_base": g.phi,
        "size_clastic_base": g.name,
    })
    bed = Bed.query.first()
    resp = client.get(f"/profile/{p.id}/bed/{bed.id}")
    html = resp.data.decode()
    assert f'id="size_clastic_base" name="size_clastic_base"' in html
    # The hidden input should have the bed's size name as its value
    assert f'value="{g.name}"' in html



# ── Property-Based Tests (Hypothesis) ────────────────────

import hypothesis
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st


# Feature: 01-grain-size-phi-values, Property 1: Grain size dual storage round trip
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=st.data())
def test_property_dual_storage_round_trip(client, db, data):
    """For any grain size entry, submitting a bed with its phi and name stores both correctly."""
    p = Profile.query.filter_by(name="PhiPropLog").first()
    if p is None:
        client.post("/profile/new", data={"name": "PhiPropLog"})
        p = Profile.query.filter_by(name="PhiPropLog").first()

    clastic_entries = GrainClastic.query.all()
    carbonate_entries = GrainCarbonate.query.all()
    all_entries = [(g, "clastic") for g in clastic_entries] + [(g, "carbonate") for g in carbonate_entries]

    entry, kind = data.draw(st.sampled_from(all_entries))

    if kind == "clastic":
        form_data = {
            "thickness": "10",
            "phi_clastic_base": entry.phi,
            "size_clastic_base": entry.name,
        }
    else:
        form_data = {
            "thickness": "10",
            "phi_carbo_base": entry.phi,
            "size_carbo_base": entry.name,
        }

    client.post(f"/profile/{p.id}/bed/new", data=form_data)
    bed = Bed.query.filter_by(profile_id=p.id).order_by(Bed.id.desc()).first()

    if kind == "clastic":
        assert bed.phi_clastic_base == entry.phi
        assert bed.size_clastic_base == entry.name
    else:
        assert bed.phi_carbo_base == entry.phi
        assert bed.size_carbo_base == entry.name

    # Clean up to avoid accumulating beds
    db.session.delete(bed)
    db.session.commit()



# Feature: 01-grain-size-phi-values, Property 2: Select option values match reference phi values
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=st.data())
def test_property_select_option_values_match_phi(client, db, data):
    """For any grain size entry, the rendered form contains an option with value=phi and text=name."""
    p = Profile.query.filter_by(name="PhiPropLog2").first()
    if p is None:
        client.post("/profile/new", data={"name": "PhiPropLog2"})
        p = Profile.query.filter_by(name="PhiPropLog2").first()

    clastic_entries = GrainClastic.query.all()
    carbonate_entries = GrainCarbonate.query.all()
    all_entries = clastic_entries + carbonate_entries

    entry = data.draw(st.sampled_from(all_entries))

    resp = client.get(f"/profile/{p.id}/bed/new")
    html = resp.data.decode()

    assert f'value="{entry.phi}"' in html
    assert f">{entry.name}</option>" in html
