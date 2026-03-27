"""SedMob – Sedimentary logging web application."""
import csv
import io
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from sedmob.models import (
    db, Profile, Bed, LithologyType, Lithology, StructureType, Structure,
    GrainClastic, GrainCarbonate, Bioturbation, Boundary,
)
from sedmob.seed import seed_database


def create_app(config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sedmob.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "dev-secret-key"
    if config:
        app.config.update(config)

    db.init_app(app)

    from sedmob.api import api
    app.register_blueprint(api)

    with app.app_context():
        db.create_all()
        seed_database()

    # ── Home ──────────────────────────────────────────────
    @app.route("/")
    def home():
        profiles = Profile.query.all()
        return render_template("home.html", profiles=profiles)

    # ── Profile CRUD ──────────────────────────────────────
    @app.route("/profile/new", methods=["GET", "POST"])
    def profile_new():
        if request.method == "POST":
            return _save_profile(None)
        return render_template("profile_form.html", profile=None, beds=[],
                               ref=_ref_data())

    @app.route("/profile/<int:profile_id>", methods=["GET", "POST"])
    def profile_edit(profile_id):
        profile = db.get_or_404(Profile, profile_id)
        if request.method == "POST":
            return _save_profile(profile)
        beds = Bed.query.filter_by(profile_id=profile_id).order_by(Bed.position).all()
        return render_template("profile_form.html", profile=profile, beds=beds,
                               ref=_ref_data())

    @app.route("/profile/<int:profile_id>/delete", methods=["POST"])
    def profile_delete(profile_id):
        profile = db.get_or_404(Profile, profile_id)
        db.session.delete(profile)
        db.session.commit()
        flash(f"Log '{profile.name}' deleted.")
        return redirect(url_for("home"))

    # ── Bed CRUD ──────────────────────────────────────────
    @app.route("/profile/<int:profile_id>/bed/new", methods=["GET", "POST"])
    def bed_new(profile_id):
        profile = db.get_or_404(Profile, profile_id)
        if request.method == "POST":
            return _save_bed(profile, None)
        return render_template("bed_form.html", profile=profile, bed=None,
                               ref=_ref_data())

    @app.route("/profile/<int:profile_id>/bed/<int:bed_id>", methods=["GET", "POST"])
    def bed_edit(profile_id, bed_id):
        profile = db.get_or_404(Profile, profile_id)
        bed = db.get_or_404(Bed, bed_id)
        if request.method == "POST":
            return _save_bed(profile, bed)
        return render_template("bed_form.html", profile=profile, bed=bed,
                               ref=_ref_data())

    @app.route("/profile/<int:profile_id>/bed/<int:bed_id>/delete", methods=["POST"])
    def bed_delete(profile_id, bed_id):
        bed = db.get_or_404(Bed, bed_id)
        pos = bed.position
        db.session.delete(bed)
        # Shift positions down for beds after the deleted one
        Bed.query.filter(
            Bed.profile_id == profile_id, Bed.position > pos
        ).update({Bed.position: Bed.position - 1})
        db.session.commit()
        flash("Bed deleted.")
        return redirect(url_for("profile_edit", profile_id=profile_id))

    @app.route("/profile/<int:profile_id>/bed/reorder", methods=["POST"])
    def bed_reorder(profile_id):
        """Accept a JSON list of bed IDs in new order."""
        order = request.get_json(force=True)
        for idx, bed_id in enumerate(order, start=1):
            Bed.query.filter_by(id=bed_id, profile_id=profile_id).update(
                {Bed.position: idx}
            )
        db.session.commit()
        return {"ok": True}

    # ── CSV Export ─────────────────────────────────────────
    @app.route("/profile/<int:profile_id>/export")
    def profile_export(profile_id):
        profile = db.get_or_404(Profile, profile_id)
        beds = Bed.query.filter_by(profile_id=profile_id).order_by(Bed.position).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Position", "Name", "Thickness", "Facies", "Notes", "Boundary",
            "Paleocurrent", "Lit1 Group", "Lit1 Type", "Lit1 %",
            "Lit2 Group", "Lit2 Type", "Lit2 %",
            "Lit3 Group", "Lit3 Type", "Lit3 %",
            "Clastic Base Size", "Clastic Base Phi", "Clastic Top Size", "Clastic Top Phi",
            "Carbonate Base Size", "Carbonate Base Phi", "Carbonate Top Size", "Carbonate Top Phi",
            "Bioturbation Type", "Bioturbation Intensity", "Structures", "Symbols",
        ])
        for bed in beds:
            writer.writerow([
                bed.position, bed.name, bed.thickness, bed.facies, bed.notes,
                bed.boundary, bed.paleocurrent,
                bed.lit1_group, bed.lit1_type, bed.lit1_percentage,
                bed.lit2_group, bed.lit2_type, bed.lit2_percentage,
                bed.lit3_group, bed.lit3_type, bed.lit3_percentage,
                bed.size_clastic_base, bed.phi_clastic_base,
                bed.size_clastic_top, bed.phi_clastic_top,
                bed.size_carbo_base, bed.phi_carbo_base,
                bed.size_carbo_top, bed.phi_carbo_top,
                bed.bioturbation_type, bed.bioturbation_intensity,
                bed.structures, bed.bed_symbols,
            ])
        filename = f"{profile.name.replace(' ', '_')}_export.csv"
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # ── Reference data management ─────────────────────────
    @app.route("/reference")
    def reference():
        return render_template("reference.html",
                               lithology_types=LithologyType.query.all(),
                               structure_types=StructureType.query.all())

    @app.route("/reference/lithology/add", methods=["POST"])
    def lithology_add():
        name = request.form["name"].strip()
        type_id = request.form.get("type_id")
        if not name or not name.replace(" ", "").isalnum():
            flash("Name must contain only letters, digits and spaces.")
            return redirect(url_for("reference"))
        if type_id:
            if Lithology.query.filter_by(name=name).first():
                flash(f"Lithology '{name}' already exists.")
            else:
                db.session.add(Lithology(type_id=int(type_id), name=name))
                db.session.commit()
                flash(f"Lithology '{name}' added.")
        else:
            if LithologyType.query.filter_by(name=name).first():
                flash(f"Lithology group '{name}' already exists.")
            else:
                db.session.add(LithologyType(name=name))
                db.session.commit()
                flash(f"Lithology group '{name}' added.")
        return redirect(url_for("reference"))

    @app.route("/reference/structure/add", methods=["POST"])
    def structure_add():
        name = request.form["name"].strip()
        type_id = request.form.get("type_id")
        if not name or not name.replace(" ", "").isalnum():
            flash("Name must contain only letters, digits and spaces.")
            return redirect(url_for("reference"))
        if type_id:
            if Structure.query.filter_by(name=name).first():
                flash(f"Structure '{name}' already exists.")
            else:
                db.session.add(Structure(type_id=int(type_id), name=name))
                db.session.commit()
                flash(f"Structure '{name}' added.")
        else:
            if StructureType.query.filter_by(name=name).first():
                flash(f"Structure group '{name}' already exists.")
            else:
                db.session.add(StructureType(name=name))
                db.session.commit()
                flash(f"Structure group '{name}' added.")
        return redirect(url_for("reference"))

    @app.route("/reference/lithology/<int:item_id>/delete", methods=["POST"])
    def lithology_delete(item_id):
        item = db.get_or_404(Lithology, item_id)
        db.session.delete(item)
        db.session.commit()
        flash(f"Lithology '{item.name}' deleted.")
        return redirect(url_for("reference"))

    @app.route("/reference/structure/<int:item_id>/delete", methods=["POST"])
    def structure_delete(item_id):
        item = db.get_or_404(Structure, item_id)
        db.session.delete(item)
        db.session.commit()
        flash(f"Structure '{item.name}' deleted.")
        return redirect(url_for("reference"))

    # ── Helpers ────────────────────────────────────────────
    def _ref_data():
        return {
            "lithology_types": LithologyType.query.all(),
            "lithologies": Lithology.query.all(),
            "structure_types": StructureType.query.all(),
            "structures": Structure.query.all(),
            "grain_clastic": GrainClastic.query.all(),
            "grain_carbonate": GrainCarbonate.query.all(),
            "bioturbation": Bioturbation.query.all(),
            "boundaries": Boundary.query.all(),
        }

    def _save_profile(profile):
        name = request.form.get("name", "").strip()
        if not name:
            flash("Log name is required.")
            return redirect(request.url)
        if profile is None:
            if Profile.query.filter_by(name=name).first():
                flash(f"Log '{name}' already exists.")
                return redirect(request.url)
            profile = Profile(name=name)
            db.session.add(profile)
        else:
            profile.name = name
        profile.description = request.form.get("description", "")
        profile.direction = request.form.get("direction", "off")
        profile.latitude = request.form.get("latitude", "No data")
        profile.longitude = request.form.get("longitude", "No data")
        profile.altitude = request.form.get("altitude", "No data")
        db.session.commit()
        flash(f"Log '{profile.name}' saved.")
        return redirect(url_for("profile_edit", profile_id=profile.id))

    def _save_bed(profile, bed):
        thickness = request.form.get("thickness", "").strip()
        if not thickness:
            flash("Thickness is required.")
            return redirect(request.url)
        if bed is None:
            max_pos = db.session.query(db.func.max(Bed.position)).filter_by(
                profile_id=profile.id).scalar() or 0
            bed = Bed(profile_id=profile.id, position=max_pos + 1, thickness=thickness)
            db.session.add(bed)
        else:
            bed.thickness = thickness
        for field in [
            "name", "facies", "notes", "boundary", "paleocurrent",
            "lit1_group", "lit1_type", "lit1_percentage",
            "lit2_group", "lit2_type", "lit2_percentage",
            "lit3_group", "lit3_type", "lit3_percentage",
            "size_clastic_base", "phi_clastic_base",
            "size_clastic_top", "phi_clastic_top",
            "size_carbo_base", "phi_carbo_base",
            "size_carbo_top", "phi_carbo_top",
            "bioturbation_type", "bioturbation_intensity",
            "structures", "bed_symbols",
        ]:
            setattr(bed, field, request.form.get(field, ""))
        db.session.commit()
        flash("Bed saved.")
        return redirect(url_for("profile_edit", profile_id=profile.id))

    return app
