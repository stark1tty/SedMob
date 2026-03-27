"""Seed the database with default reference data."""
from sedmob.models import (
    db, LithologyType, Lithology, StructureType, Structure,
    GrainClastic, GrainCarbonate, Bioturbation, Boundary,
)


def seed_database():
    """Populate reference tables if they are empty."""
    if LithologyType.query.count() == 0:
        _seed_lithology_types()
    if Lithology.query.count() == 0:
        _seed_lithologies()
    if StructureType.query.count() == 0:
        _seed_structure_types()
    if Structure.query.count() == 0:
        _seed_structures()
    if GrainClastic.query.count() == 0:
        _seed_grain_clastic()
    if GrainCarbonate.query.count() == 0:
        _seed_grain_carbonate()
    if Bioturbation.query.count() == 0:
        _seed_bioturbation()
    if Boundary.query.count() == 0:
        _seed_boundaries()
    db.session.commit()


def _seed_lithology_types():
    for id_, name in [(1, "Basic"), (2, "Carbonates"), (3, "Other")]:
        db.session.add(LithologyType(id=id_, name=name))
    db.session.flush()


def _seed_lithologies():
    data = [
        (1, "Mudstone"), (1, "Claystone"), (1, "Shale"), (1, "Siltstone"),
        (1, "Sandstone"), (1, "Conglomerate"), (1, "Coal"), (1, "Limestone"),
        (1, "Chert"), (1, "Volcaniclastic"),
        (2, "Lime mudstone"), (2, "Wackestone"), (2, "Packstone"),
        (2, "Grainstone"), (2, "Halite"), (2, "Gypsum/Anhydrite"), (2, "Dolomite"),
        (3, "Breccia"), (3, "Matrix-supported conglomerate"),
        (3, "Clast-supported conglomerate"), (3, "Lava"), (3, "Fine ash"), (3, "Coarse ash"),
    ]
    for type_id, name in data:
        db.session.add(Lithology(type_id=type_id, name=name))
    db.session.flush()


def _seed_structure_types():
    for id_, name in [
        (1, "Sedimentary structures"), (2, "Fossils"),
        (3, "Trace fossils"), (4, "Other"),
    ]:
        db.session.add(StructureType(id=id_, name=name))
    db.session.flush()


def _seed_structures():
    data = [
        (1, "Current ripple cross-lamination"), (1, "Wave ripple cross-lamination"),
        (1, "Planar cross bedding"), (1, "Trough cross bedding"),
        (1, "Horizontal planar lamination"), (1, "Hummocky cross stratification"),
        (1, "Swaley cross stratification"), (1, "Mudcracks"),
        (1, "Synaeresis cracks"), (1, "Convolute lamination"),
        (1, "Load casts"), (1, "Water structures"), (1, "Herring-bone cross bedding"),
        (2, "Shells"), (2, "Bivalves"), (2, "Gastropods"), (2, "Cephalopods"),
        (2, "Brachiopods"), (2, "Echinoids"), (2, "Crinoids"),
        (2, "Solitary corals"), (2, "Colonial corals"), (2, "Foraminifera"),
        (2, "Algae"), (2, "Bryozoa"), (2, "Stromatolites"), (2, "Vertebrates"),
        (2, "Plant material"), (2, "Roots"), (2, "Logs"), (2, "Tree stumps"),
        (2, "Ostracods"), (2, "Radiolaria"), (2, "Sponges"),
        (3, "Minor bioturbation"), (3, "Moderate bioturbation"),
        (3, "Intense bioturbation"), (3, "Tracks"), (3, "Trails"),
        (3, "Vertical burrows"), (3, "Horizontal burrows"),
        (4, "Nodules and concretions"), (4, "Intraclasts"), (4, "Mudclasts"),
        (4, "Flute marks"), (4, "Groove marks"), (4, "Scours"),
    ]
    for type_id, name in data:
        db.session.add(Structure(type_id=type_id, name=name))
    db.session.flush()


def _seed_grain_clastic():
    data = [
        ("clay", "10.0"), ("clay/silt", "8.0"), ("silt", "6.0"),
        ("silt/vf", "4.0"), ("vf", "3.5"), ("vf/f", "3.0"),
        ("f", "2.5"), ("f/m", "2.0"), ("m", "1.5"), ("m/c", "1.0"),
        ("c", "0.5"), ("c/vc", "0.0"), ("vc", "-0.5"), ("vc/granule", "-1.0"),
        ("granule", "-1.5"), ("granule/pebble", "-2.3"), ("pebble", "-3.0"),
        ("pebble/cobble", "-4.5"), ("cobble", "-6.0"), ("cobble/boulder", "-8.0"),
        ("boulder", "-10.0"),
    ]
    for name, phi in data:
        db.session.add(GrainClastic(name=name, phi=phi))
    db.session.flush()


def _seed_grain_carbonate():
    data = [
        ("mudstone", "6.0"), ("wackestone", "3.5"), ("packstone", "1.5"),
        ("grainstone", "-0.5"), ("rudstone fine", "-1.5"),
        ("rudstone medium", "-3.0"), ("rudstone", "-6.0"),
    ]
    for name, phi in data:
        db.session.add(GrainCarbonate(name=name, phi=phi))
    db.session.flush()


def _seed_bioturbation():
    for name in [
        "Minor bioturbation", "Moderate bioturbation", "Intense bioturbation",
        "Tracks", "Trails", "Vertical burrows", "Horizontal burrows",
    ]:
        db.session.add(Bioturbation(name=name))
    db.session.flush()


def _seed_boundaries():
    for name in ["Sharp", "Erosion", "Gradational"]:
        db.session.add(Boundary(name=name))
    db.session.flush()
