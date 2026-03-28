"""REST-ish JSON API blueprint for Gneisswork data."""
from flask import Blueprint, jsonify, abort
from sedmob.models import (db, Profile, Bed, BedPhoto, LithologyType,
                            Lithology, StructureType, Structure,
                            GrainClastic, GrainCarbonate, Bioturbation,
                            Boundary)

api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/profiles")
def profiles_list():
    return jsonify([p.to_dict() for p in Profile.query.all()])


@api.route("/profiles/<int:profile_id>")
def profile_detail(profile_id):
    profile = db.get_or_404(Profile, profile_id)
    data = profile.to_dict()
    data["beds"] = [b.to_dict() for b in
                    Bed.query.filter_by(profile_id=profile_id).order_by(Bed.position).all()]
    return jsonify(data)


@api.route("/profiles/<int:profile_id>/beds")
def beds_list(profile_id):
    db.get_or_404(Profile, profile_id)  # 404 if profile doesn't exist
    beds = Bed.query.filter_by(profile_id=profile_id).order_by(Bed.position).all()
    return jsonify([b.to_dict() for b in beds])


@api.route("/profiles/<int:profile_id>/beds/<int:bed_id>")
def bed_detail(profile_id, bed_id):
    bed = db.get_or_404(Bed, bed_id)
    if bed.profile_id != profile_id:
        abort(404)
    data = bed.to_dict()
    data["photos"] = [p.to_dict() for p in
                      BedPhoto.query.filter_by(bed_id=bed_id).all()]
    return jsonify(data)


@api.route("/profiles/<int:profile_id>/beds/<int:bed_id>/photos")
def bed_photos_list(profile_id, bed_id):
    db.get_or_404(Profile, profile_id)
    bed = db.get_or_404(Bed, bed_id)
    if bed.profile_id != profile_id:
        abort(404)
    photos = BedPhoto.query.filter_by(bed_id=bed_id).all()
    return jsonify([p.to_dict() for p in photos])


@api.route("/profiles/<int:profile_id>/beds/<int:bed_id>/photos/<int:photo_id>")
def bed_photo_detail(profile_id, bed_id, photo_id):
    db.get_or_404(Profile, profile_id)
    bed = db.get_or_404(Bed, bed_id)
    if bed.profile_id != profile_id:
        abort(404)
    photo = db.get_or_404(BedPhoto, photo_id)
    if photo.bed_id != bed_id:
        abort(404)
    return jsonify(photo.to_dict())


# ── Reference Data ──────────────────────────────────────────────

@api.route("/lithology-types")
def lithology_types_list():
    types = LithologyType.query.all()
    result = []
    for t in types:
        d = t.to_dict()
        d["lithologies"] = [l.to_dict() for l in t.lithologies]
        result.append(d)
    return jsonify(result)


@api.route("/structures-types")
def structure_types_list():
    types = StructureType.query.all()
    result = []
    for t in types:
        d = t.to_dict()
        d["structures"] = [s.to_dict() for s in t.structures]
        result.append(d)
    return jsonify(result)


@api.route("/grain-clastic")
def grain_clastic_list():
    return jsonify([g.to_dict() for g in GrainClastic.query.all()])


@api.route("/grain-carbonate")
def grain_carbonate_list():
    return jsonify([g.to_dict() for g in GrainCarbonate.query.all()])


@api.route("/bioturbation")
def bioturbation_list():
    return jsonify([b.to_dict() for b in Bioturbation.query.all()])


@api.route("/boundaries")
def boundaries_list():
    return jsonify([b.to_dict() for b in Boundary.query.all()])
