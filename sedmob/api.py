"""REST-ish JSON API blueprint for Gneisswork data."""
from flask import Blueprint, jsonify, abort
from sedmob.models import db, Profile, Bed

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
    return jsonify(bed.to_dict())
