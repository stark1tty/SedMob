"""Unit tests for database backup and restore."""
import io
import json

from sedmob.models import (
    Profile, Bed, BedPhoto,
    LithologyType, Lithology, StructureType, Structure,
    GrainClastic, GrainCarbonate, Bioturbation, Boundary,
)


def test_backup_returns_200_with_correct_headers(client):
    """GET /backup returns 200 with correct Content-Type and Content-Disposition. (Req 1.4)"""
    resp = client.get("/backup")
    assert resp.status_code == 200
    assert resp.content_type == "application/json"
    cd = resp.headers["Content-Disposition"]
    assert cd.startswith("attachment; filename=gneisswork_backup_")
    assert cd.endswith(".json")


def test_restore_no_file_returns_error(client):
    """POST /restore with no file returns error flash and redirect. (Req 2.10)"""
    resp = client.post("/restore", follow_redirects=True)
    assert b"No file provided" in resp.data


def test_restore_invalid_json_returns_error(client):
    """POST /restore with invalid JSON returns error flash and redirect. (Req 2.2)"""
    data = {"file": (io.BytesIO(b"not json at all{{{"), "bad.json")}
    resp = client.post("/restore", data=data, content_type="multipart/form-data",
                       follow_redirects=True)
    assert b"Invalid JSON file" in resp.data


def test_restore_missing_version_returns_error(client):
    """POST /restore with JSON missing version key returns error flash and redirect. (Req 2.3)"""
    payload = json.dumps({"profiles": []}).encode()
    data = {"file": (io.BytesIO(payload), "no_version.json")}
    resp = client.post("/restore", data=data, content_type="multipart/form-data",
                       follow_redirects=True)
    assert b"Unrecognized backup format" in resp.data


def test_restore_valid_backup_success(client):
    """POST /restore with valid backup redirects with success flash. (Req 2.9)"""
    # Get a valid backup first
    backup_resp = client.get("/backup")
    backup_data = backup_resp.data
    # Restore from it
    data = {"file": (io.BytesIO(backup_data), "backup.json")}
    resp = client.post("/restore", data=data, content_type="multipart/form-data",
                       follow_redirects=True)
    assert b"Database restored successfully" in resp.data


def test_restore_rollback_on_database_error(client, db):
    """Restore rolls back on database error. (Req 2.8)"""
    from unittest.mock import patch

    # Get a valid backup first
    backup_resp = client.get("/backup")
    backup_json = json.loads(backup_resp.data)

    # Patch db.session.commit inside the restore path to raise an error
    with patch.object(db.session, "commit", side_effect=Exception("simulated DB error")):
        payload = json.dumps(backup_json).encode()
        data = {"file": (io.BytesIO(payload), "backup.json")}
        resp = client.post("/restore", data=data, content_type="multipart/form-data",
                           follow_redirects=True)
    # Should flash the error, not success
    assert b"simulated DB error" in resp.data
    assert b"Database restored successfully" not in resp.data


def test_settings_page_returns_200_with_backup_and_restore(client):
    """GET /settings returns 200 with backup link and restore form. (Req 3.1, 3.2)"""
    resp = client.get("/settings")
    assert resp.status_code == 200
    assert b"/backup" in resp.data
    assert b'action="/restore"' in resp.data


def test_settings_page_contains_data_replacement_warning(client):
    """Settings page contains warning about data replacement. (Req 3.3)"""
    resp = client.get("/settings")
    assert b"replace all existing data" in resp.data


def test_settings_page_contains_scope_note(client):
    """Settings page contains note about backup scope. (Req 3.4)"""
    resp = client.get("/settings")
    assert b"database records only" in resp.data


def test_nav_bar_settings_link_position(client):
    """Nav bar contains Settings link between Reference Data and Docs. (Req 4.1, 4.2)"""
    resp = client.get("/")
    html = resp.data.decode()
    ref_pos = html.find("Reference Data")
    settings_pos = html.find(">Settings<")
    docs_pos = html.find("Docs")
    assert ref_pos < settings_pos < docs_pos


def test_round_trip_empty_user_tables_preserves_reference_data(client, db):
    """Round-trip with empty user tables preserves seeded reference data. (Req 5.3)"""
    # Capture reference data counts before backup
    counts_before = {
        "lithology_types": LithologyType.query.count(),
        "lithologies": Lithology.query.count(),
        "structure_types": StructureType.query.count(),
        "structures": Structure.query.count(),
        "grain_clastic": GrainClastic.query.count(),
        "grain_carbonate": GrainCarbonate.query.count(),
        "bioturbation": Bioturbation.query.count(),
        "boundaries": Boundary.query.count(),
    }
    # Ensure there is seeded reference data
    assert counts_before["lithology_types"] > 0

    # Backup
    backup_resp = client.get("/backup")
    backup_data = backup_resp.data

    # Restore
    data = {"file": (io.BytesIO(backup_data), "backup.json")}
    resp = client.post("/restore", data=data, content_type="multipart/form-data",
                       follow_redirects=True)
    assert b"Database restored successfully" in resp.data

    # Verify reference data counts are identical
    counts_after = {
        "lithology_types": LithologyType.query.count(),
        "lithologies": Lithology.query.count(),
        "structure_types": StructureType.query.count(),
        "structures": Structure.query.count(),
        "grain_clastic": GrainClastic.query.count(),
        "grain_carbonate": GrainCarbonate.query.count(),
        "bioturbation": Bioturbation.query.count(),
        "boundaries": Boundary.query.count(),
    }
    assert counts_before == counts_after


# ---------------------------------------------------------------------------
# Property-based tests (hypothesis)
# ---------------------------------------------------------------------------
import json
from datetime import datetime

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from sedmob.models import (
    db as _db,
    Profile, Bed, BedPhoto,
    LithologyType, Lithology, StructureType, Structure,
    GrainClastic, GrainCarbonate, Bioturbation, Boundary,
)

# ── Strategies ────────────────────────────────────────────

_name_st = st.text(
    min_size=1, max_size=50,
    alphabet=st.characters(whitelist_categories=("L", "N", "Zs")),
).filter(lambda s: s.strip() != "")

_str_st = st.text(min_size=0, max_size=50,
                  alphabet=st.characters(whitelist_categories=("L", "N", "Zs")))

_phi_st = st.text(min_size=1, max_size=10,
                  alphabet=st.characters(whitelist_categories=("N",)))

_dt_st = st.datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2099, 12, 31),
).map(lambda dt: dt.replace(microsecond=0))

_profile_st = st.fixed_dictionaries({
    "name": _name_st,
    "description": _str_st,
    "direction": st.sampled_from(["off", "on"]),
    "latitude": _str_st,
    "longitude": _str_st,
    "altitude": _str_st,
    "accuracy": _str_st,
    "altitude_accuracy": _str_st,
    "photo": _str_st,
})

_bed_photo_st = st.fixed_dictionaries({
    "filename": _name_st,
    "description": _str_st,
    "created_at": _dt_st,
})

_ref_name_st = _name_st  # reuse for reference table names


def _profiles_st():
    """Generate 0-3 profiles with unique names, each with 0-3 beds, each bed with 0-2 photos."""
    return st.lists(
        _profile_st,
        min_size=0, max_size=3,
        unique_by=lambda p: p["name"],
    )


def _beds_per_profile_st():
    """Generate 0-3 beds for a profile."""
    return st.lists(
        st.fixed_dictionaries({
            "name": _str_st,
            "thickness": st.just("10"),
            "facies": _str_st,
            "notes": _str_st,
            "boundary": _str_st,
            "paleocurrent": _str_st,
            "top": _str_st,
            "bottom": _str_st,
            "lit1_group": _str_st,
            "lit1_type": _str_st,
            "lit1_percentage": st.just("100"),
            "lit2_group": _str_st,
            "lit2_type": _str_st,
            "lit2_percentage": st.just("0"),
            "lit3_group": _str_st,
            "lit3_type": _str_st,
            "lit3_percentage": st.just("0"),
            "size_clastic_base": _str_st,
            "phi_clastic_base": _str_st,
            "size_clastic_top": _str_st,
            "phi_clastic_top": _str_st,
            "size_carbo_base": _str_st,
            "phi_carbo_base": _str_st,
            "size_carbo_top": _str_st,
            "phi_carbo_top": _str_st,
            "bioturbation_type": _str_st,
            "bioturbation_intensity": _str_st,
            "structures": _str_st,
            "bed_symbols": _str_st,
            "audio": _str_st,
        }),
        min_size=0, max_size=3,
    )


def _photos_per_bed_st():
    return st.lists(_bed_photo_st, min_size=0, max_size=2)


# Reference table strategies
_lith_types_st = st.lists(_name_st, min_size=1, max_size=3, unique=True)
_struct_types_st = st.lists(_name_st, min_size=1, max_size=3, unique=True)
_grain_clastic_st = st.lists(
    st.fixed_dictionaries({"name": _name_st, "phi": _phi_st}),
    min_size=1, max_size=3, unique_by=lambda g: g["name"],
)
_grain_carbonate_st = st.lists(
    st.fixed_dictionaries({"name": _name_st, "phi": _phi_st}),
    min_size=1, max_size=3, unique_by=lambda g: g["name"],
)
_bioturb_st = st.lists(_name_st, min_size=1, max_size=3, unique=True)
_boundary_st = st.lists(_name_st, min_size=1, max_size=3, unique=True)
_lith_names_st = st.lists(_name_st, min_size=1, max_size=3, unique=True)
_struct_names_st = st.lists(_name_st, min_size=1, max_size=3, unique=True)


def _snapshot(db_session):
    """Return a dict of all 11 tables as sorted lists of dicts (id stripped)."""
    table_models = [
        ("profiles", Profile),
        ("beds", Bed),
        ("bed_photos", BedPhoto),
        ("lithology_types", LithologyType),
        ("lithologies", Lithology),
        ("structure_types", StructureType),
        ("structures", Structure),
        ("grain_clastic", GrainClastic),
        ("grain_carbonate", GrainCarbonate),
        ("bioturbation", Bioturbation),
        ("boundaries", Boundary),
    ]
    snap = {}
    for key, model in table_models:
        rows = []
        for row in model.query.all():
            d = row.to_dict()
            # Normalise datetime to string for comparison
            if "created_at" in d and isinstance(d["created_at"], datetime):
                d["created_at"] = d["created_at"].isoformat()
            # Remove auto-generated ids — we compare content only
            d.pop("id", None)
            rows.append(d)
        # Sort by a stable key so order doesn't matter
        rows.sort(key=lambda r: json.dumps(r, sort_keys=True, default=str))
        snap[key] = rows
    return snap


# Tag: "Feature: 10-database-backup-restore, Property 1: Backup/restore round-trip preserves all data"
@given(
    profiles=_profiles_st(),
    beds_per_profile=st.lists(_beds_per_profile_st(), min_size=0, max_size=3),
    photos_per_bed=st.lists(
        st.lists(_photos_per_bed_st(), min_size=0, max_size=3),
        min_size=0, max_size=3,
    ),
    lith_type_names=_lith_types_st,
    lith_names=_lith_names_st,
    struct_type_names=_struct_types_st,
    struct_names=_struct_names_st,
    grain_c=_grain_clastic_st,
    grain_cb=_grain_carbonate_st,
    bioturb_names=_bioturb_st,
    boundary_names=_boundary_st,
)
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
def test_roundtrip_preserves_all_data(
    client, db,
    profiles, beds_per_profile, photos_per_bed,
    lith_type_names, lith_names,
    struct_type_names, struct_names,
    grain_c, grain_cb,
    bioturb_names, boundary_names,
):
    """Backup/restore round-trip preserves all data across all 11 tables.

    **Validates: Requirements 1.1, 1.3, 1.5, 2.1, 2.4, 5.1, 5.2**
    """
    # ── Clear seeded data so we start from a known empty state ──
    for model in [BedPhoto, Bed, Profile, Lithology, LithologyType,
                  Structure, StructureType, GrainClastic, GrainCarbonate,
                  Bioturbation, Boundary]:
        _db.session.execute(model.__table__.delete())
    _db.session.commit()

    # ── Insert reference data ──
    for name in lith_type_names:
        _db.session.add(LithologyType(name=name))
    _db.session.flush()
    lt_ids = [lt.id for lt in LithologyType.query.all()]
    for name in lith_names:
        _db.session.add(Lithology(type_id=lt_ids[0], name=name))

    for name in struct_type_names:
        _db.session.add(StructureType(name=name))
    _db.session.flush()
    st_ids = [st_row.id for st_row in StructureType.query.all()]
    for name in struct_names:
        _db.session.add(Structure(type_id=st_ids[0], name=name))

    for g in grain_c:
        _db.session.add(GrainClastic(name=g["name"], phi=g["phi"]))
    for g in grain_cb:
        _db.session.add(GrainCarbonate(name=g["name"], phi=g["phi"]))
    for name in bioturb_names:
        _db.session.add(Bioturbation(name=name))
    for name in boundary_names:
        _db.session.add(Boundary(name=name))
    _db.session.commit()

    # ── Insert user data (profiles → beds → photos) ──
    for i, prof_data in enumerate(profiles):
        p = Profile(**prof_data)
        _db.session.add(p)
        _db.session.flush()

        bed_list = beds_per_profile[i] if i < len(beds_per_profile) else []
        for j, bed_data in enumerate(bed_list):
            b = Bed(profile_id=p.id, position=j + 1, **bed_data)
            _db.session.add(b)
            _db.session.flush()

            photo_lists = photos_per_bed[i] if i < len(photos_per_bed) else []
            photo_list = photo_lists[j] if j < len(photo_lists) else []
            for ph_data in photo_list:
                _db.session.add(BedPhoto(
                    bed_id=b.id, profile_id=p.id, **ph_data,
                ))
    _db.session.commit()

    # ── Snapshot before backup ──
    snap_before = _snapshot(_db.session)

    # ── Backup via HTTP ──
    backup_resp = client.get("/backup")
    assert backup_resp.status_code == 200
    backup_data = backup_resp.data

    # ── Restore via HTTP ──
    data = {"file": (io.BytesIO(backup_data), "backup.json")}
    restore_resp = client.post(
        "/restore", data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"Database restored successfully" in restore_resp.data

    # ── Snapshot after restore ──
    snap_after = _snapshot(_db.session)

    # ── Compare ──
    for table_key in snap_before:
        assert snap_before[table_key] == snap_after[table_key], (
            f"Table '{table_key}' differs after round-trip.\n"
            f"Before: {snap_before[table_key]}\n"
            f"After:  {snap_after[table_key]}"
        )


# Tag: "Feature: 10-database-backup-restore, Property 2: Backup metadata is always present and well-formed"
@given(profiles=_profiles_st())
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
def test_backup_metadata_always_present_and_well_formed(client, db, profiles):
    """Backup JSON always contains version == "1.0" and a valid ISO 8601 timestamp.

    **Validates: Requirements 1.2**
    """
    # ── Clear user data so we start from a known state ──
    for model in [BedPhoto, Bed, Profile]:
        _db.session.execute(model.__table__.delete())
    _db.session.commit()

    # ── Insert generated profiles ──
    for prof_data in profiles:
        _db.session.add(Profile(**prof_data))
    _db.session.commit()

    # ── Backup via HTTP ──
    resp = client.get("/backup")
    assert resp.status_code == 200
    data = json.loads(resp.data)

    # ── Check version ──
    assert "version" in data, "Backup JSON missing 'version' key"
    assert data["version"] == "1.0", f"Expected version '1.0', got {data['version']!r}"

    # ── Check timestamp is valid ISO 8601 ──
    assert "timestamp" in data, "Backup JSON missing 'timestamp' key"
    ts = data["timestamp"]
    assert isinstance(ts, str), f"Expected timestamp to be a string, got {type(ts)}"
    parsed = datetime.fromisoformat(ts)
    assert isinstance(parsed, datetime), "timestamp is not a valid ISO 8601 datetime"


# ── FK dependency graph for safe key removal ──────────────
# When a parent table key is removed, its dependent children must also be removed.
_FK_DEPENDENTS = {
    "profiles": {"beds", "bed_photos"},
    "beds": {"bed_photos"},
    "lithology_types": {"lithologies"},
    "structure_types": {"structures"},
}

ALL_TABLE_NAMES = [
    "profiles", "beds", "bed_photos",
    "lithology_types", "lithologies",
    "structure_types", "structures",
    "grain_clastic", "grain_carbonate",
    "bioturbation", "boundaries",
]

TABLE_MODEL_MAP = {
    "profiles": Profile,
    "beds": Bed,
    "bed_photos": BedPhoto,
    "lithology_types": LithologyType,
    "lithologies": Lithology,
    "structure_types": StructureType,
    "structures": Structure,
    "grain_clastic": GrainClastic,
    "grain_carbonate": GrainCarbonate,
    "bioturbation": Bioturbation,
    "boundaries": Boundary,
}


def _close_dependents(keys_to_remove):
    """Given a set of table keys to remove, also remove their FK dependents."""
    closed = set(keys_to_remove)
    changed = True
    while changed:
        changed = False
        for parent, children in _FK_DEPENDENTS.items():
            if parent in closed:
                for child in children:
                    if child not in closed:
                        closed.add(child)
                        changed = True
    return closed


# Tag: "Feature: 10-database-backup-restore, Property 3: Missing table keys are treated as empty"
@given(
    keys_to_remove=st.sets(st.sampled_from(ALL_TABLE_NAMES)),
)
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
def test_missing_table_keys_treated_as_empty(client, db, keys_to_remove):
    """Removing table keys from a backup dict causes those tables to be empty after restore.

    **Validates: Requirements 6.1**
    """
    # ── Get a valid backup from the seeded database ──
    backup_resp = client.get("/backup")
    assert backup_resp.status_code == 200
    backup_dict = json.loads(backup_resp.data)

    # ── Close over FK dependents so restore won't hit constraint errors ──
    effective_removals = _close_dependents(keys_to_remove)

    # ── Remove the selected keys from the backup dict ──
    for key in effective_removals:
        backup_dict.pop(key, None)

    # ── Restore from the modified backup ──
    payload = json.dumps(backup_dict).encode()
    data = {"file": (io.BytesIO(payload), "backup.json")}
    restore_resp = client.post(
        "/restore", data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"Database restored successfully" in restore_resp.data

    # ── Verify: removed tables should be empty ──
    for key in effective_removals:
        model = TABLE_MODEL_MAP[key]
        count = model.query.count()
        assert count == 0, (
            f"Table '{key}' should be empty after its key was removed, "
            f"but has {count} rows"
        )

    # ── Verify: kept tables should still have their data ──
    kept_keys = set(ALL_TABLE_NAMES) - effective_removals
    for key in kept_keys:
        model = TABLE_MODEL_MAP[key]
        expected_rows = backup_dict.get(key, [])
        actual_count = model.query.count()
        assert actual_count == len(expected_rows), (
            f"Table '{key}' should have {len(expected_rows)} rows "
            f"but has {actual_count}"
        )


# Tag: "Feature: 10-database-backup-restore, Property 4: Unrecognized table keys are ignored"
# Strategy for generating random keys that are NOT known table names or metadata keys
_KNOWN_KEYS = frozenset(ALL_TABLE_NAMES + ["version", "timestamp"])

_extra_key_st = st.text(
    min_size=1, max_size=30,
    alphabet=st.characters(whitelist_categories=("L", "N", "Zs")),
).filter(lambda s: s.strip() != "" and s not in _KNOWN_KEYS)

_extra_value_st = st.lists(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=20,
                     alphabet=st.characters(whitelist_categories=("L", "N"))),
        values=st.text(min_size=0, max_size=20,
                       alphabet=st.characters(whitelist_categories=("L", "N", "Zs"))),
        min_size=0, max_size=3,
    ),
    min_size=0, max_size=3,
)

_extra_keys_st = st.dictionaries(
    keys=_extra_key_st,
    values=_extra_value_st,
    min_size=1, max_size=5,
)


@given(extra_keys=_extra_keys_st)
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
def test_unrecognized_table_keys_are_ignored(client, db, extra_keys):
    """Restoring a backup with extra unrecognized keys produces the same DB state as a clean restore.

    **Validates: Requirements 6.2**
    """
    # ── Get a valid backup from the seeded database ──
    backup_resp = client.get("/backup")
    assert backup_resp.status_code == 200
    clean_backup = json.loads(backup_resp.data)

    # ── Create a modified backup with extra keys added ──
    dirty_backup = dict(clean_backup)
    dirty_backup.update(extra_keys)

    # ── Restore from the dirty backup (with extra keys) ──
    payload = json.dumps(dirty_backup).encode()
    data = {"file": (io.BytesIO(payload), "dirty_backup.json")}
    resp = client.post(
        "/restore", data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"Database restored successfully" in resp.data

    # ── Snapshot after dirty restore ──
    snap_dirty = _snapshot(_db.session)

    # ── Restore from the clean backup (without extra keys) ──
    clean_payload = json.dumps(clean_backup).encode()
    data = {"file": (io.BytesIO(clean_payload), "clean_backup.json")}
    resp = client.post(
        "/restore", data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"Database restored successfully" in resp.data

    # ── Snapshot after clean restore ──
    snap_clean = _snapshot(_db.session)

    # ── Compare: both snapshots should be identical ──
    for table_key in ALL_TABLE_NAMES:
        assert snap_dirty[table_key] == snap_clean[table_key], (
            f"Table '{table_key}' differs between dirty and clean restore.\n"
            f"Dirty: {snap_dirty[table_key]}\n"
            f"Clean: {snap_clean[table_key]}"
        )
