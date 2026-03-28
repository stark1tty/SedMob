"""Tests for popup description coverage and script loading."""
import os
import re


# --- Helpers ---

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATES = os.path.join(_ROOT, "templates")
_STATIC = os.path.join(_ROOT, "static")


def _parse_label_fors(template_filename):
    """Extract all `for` attribute values from <label> tags in a template."""
    path = os.path.join(_TEMPLATES, template_filename)
    with open(path) as f:
        html = f.read()
    return set(re.findall(r'<label\s+for="([^"]+)"', html))


def _parse_field_descriptions_keys():
    """Extract all keys from the FIELD_DESCRIPTIONS object in popups.js."""
    path = os.path.join(_STATIC, "popups.js")
    with open(path) as f:
        js = f.read()
    return set(re.findall(r'"([^"]+)"\s*:', js))


# --- 4.1: Bed form description coverage ---

def test_bed_form_labels_have_descriptions():
    """Every label on bed_form.html (excluding photo-description) has a
    matching key in FIELD_DESCRIPTIONS."""
    label_ids = _parse_label_fors("bed_form.html")
    excluded = {"photo-description"}
    label_ids -= excluded

    desc_keys = _parse_field_descriptions_keys()
    missing = label_ids - desc_keys
    assert not missing, f"Bed form labels missing from FIELD_DESCRIPTIONS: {missing}"


# --- 4.2: Profile form description coverage ---

def test_profile_form_labels_have_descriptions():
    """Every label on profile_form.html has a matching key in
    FIELD_DESCRIPTIONS."""
    label_ids = _parse_label_fors("profile_form.html")
    # No photo-related labels exist on profile_form.html, but guard anyway
    excluded = set()
    label_ids -= excluded

    desc_keys = _parse_field_descriptions_keys()
    missing = label_ids - desc_keys
    assert not missing, f"Profile form labels missing from FIELD_DESCRIPTIONS: {missing}"


# --- 4.3: popups.js loaded on bed form page ---

def test_bed_form_loads_popups_js(client, db):
    """The bed form page includes the popups.js script tag."""
    # Create a profile first (bed form requires one)
    client.post("/profile/new", data={"name": "Test Profile"})
    from sedmob.models import Profile
    p = Profile.query.first()

    resp = client.get(f"/profile/{p.id}/bed/new")
    assert resp.status_code == 200
    assert b"popups.js" in resp.data


# --- 4.4: popups.js loaded on profile form page ---

def test_profile_form_loads_popups_js(client):
    """The profile form page includes the popups.js script tag."""
    resp = client.get("/profile/new")
    assert resp.status_code == 200
    assert b"popups.js" in resp.data
