"""Tests for database seeding."""
from sedmob.models import (
    LithologyType, Lithology, StructureType, Structure,
    GrainClastic, GrainCarbonate, Bioturbation, Boundary,
)


def test_seed_lithology_types(db):
    types = LithologyType.query.all()
    assert len(types) == 3
    names = {t.name for t in types}
    assert names == {"Basic", "Carbonates", "Other"}


def test_seed_lithologies(db):
    assert Lithology.query.count() == 23
    sandstone = Lithology.query.filter_by(name="Sandstone").first()
    assert sandstone is not None
    assert sandstone.type.name == "Basic"


def test_seed_structure_types(db):
    types = StructureType.query.all()
    assert len(types) == 4


def test_seed_structures(db):
    assert Structure.query.count() == 47


def test_seed_grain_clastic(db):
    assert GrainClastic.query.count() == 21
    clay = GrainClastic.query.filter_by(name="clay").first()
    assert clay.phi == "10.0"


def test_seed_grain_carbonate(db):
    assert GrainCarbonate.query.count() == 7


def test_seed_bioturbation(db):
    assert Bioturbation.query.count() == 7


def test_seed_boundaries(db):
    boundaries = Boundary.query.all()
    assert len(boundaries) == 3
    names = {b.name for b in boundaries}
    assert names == {"Sharp", "Erosion", "Gradational"}
