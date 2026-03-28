"""Gneisswork – Sedimentary logging web application."""
import csv
import io
import os
import re
import shutil
import uuid
import zipfile
from flask import Flask, render_template, request, redirect, url_for, flash, Response, send_from_directory
from sedmob.models import (
    db, Profile, Bed, LithologyType, Lithology, StructureType, Structure,
    GrainClastic, GrainCarbonate, Bioturbation, Boundary,
)
from sedmob.seed import seed_database


def create_app(config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///gneisswork.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "dev-secret-key"
    if config:
        app.config.update(config)

    app.config["UPLOAD_FOLDER"] = app.config.get(
        "UPLOAD_FOLDER",
        os.path.join(app.root_path, "..", "uploads")
    )
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

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
    # SedLog-compatible CSV format (see Wolniewicz 2014, Zervas et al. 2009)
    # Headers and column order match the original SedMob Cordova app so that
    # exported files can be opened directly in SedLog for graphic log generation.

    def _sedlog_val(value):
        """Return value for CSV cell, replacing empty/None with '<none>'."""
        if value is None or str(value).strip() == "":
            return "<none>"
        return str(value)

    def _sedlog_grain_size(bed):
        """Merge clastic/carbonate grain size into single base/top pair.

        SedLog expects one grain size base and one grain size top column.
        The original app used clastic values when present, falling back to
        carbonate values otherwise.
        """
        size_base = bed.size_clastic_base if bed.size_clastic_base else bed.size_carbo_base
        phi_base = bed.phi_clastic_base
        if not phi_base or phi_base == "<none>":
            phi_base = bed.phi_carbo_base
        size_top = bed.size_clastic_top if bed.size_clastic_top else bed.size_carbo_top
        phi_top = bed.phi_clastic_top
        if not phi_top or phi_top == "<none>":
            phi_top = bed.phi_carbo_top
        return size_base, phi_base, size_top, phi_top

    def _generate_csv(profile, beds):
        """Generate SedLog-compatible CSV content for a profile.

        Args:
            profile: Profile model instance
            beds: list of Bed model instances, ordered by position

        Returns:
            str: Complete CSV content including header row
        """
        output = io.StringIO()
        writer = csv.writer(output)
        # Columns 1–25: SedLog-compatible (same order as original SedMob app)
        # Columns 26+: Gneisswork extras (position, name, groups, etc.)
        writer.writerow([
            "THICKNESS (CM)", "BASE BOUNDARY",
            "LITHOLOGY", "LITHOLOGY %",
            "LITHOLOGY2", "LITHOLOGY2 %",
            "LITHOLOGY3", "LITHOLOGY3 %",
            "GRAIN SIZE BASE", "PHI VALUES BASE",
            "GRAIN SIZE TOP", "PHI VALUES TOP",
            "SYMBOLS IN BED", "SYMBOLS/STRUCTURES",
            "NOTES COLUMN", "BIOTURBATION TYPE", "INTENSITY",
            "PALAEOCURRENT VALUES", "FACIES",
            "OTHER1 TEXT", "OTHER1 SYMBOL",
            "OTHER2 TEXT", "OTHER2 SYMBOL",
            "OTHER3 TEXT", "OTHER3 SYMBOL",
            # Gneisswork extras
            "Position", "Name", "Top", "Bottom",
            "Lit1 Group", "Lit2 Group", "Lit3 Group",
            "Clastic Base Size", "Clastic Base Phi",
            "Clastic Top Size", "Clastic Top Phi",
            "Carbonate Base Size", "Carbonate Base Phi",
            "Carbonate Top Size", "Carbonate Top Phi",
        ])
        v = _sedlog_val
        for bed in beds:
            size_base, phi_base, size_top, phi_top = _sedlog_grain_size(bed)
            writer.writerow([
                v(bed.thickness), v(bed.boundary),
                v(bed.lit1_type), v(bed.lit1_percentage),
                v(bed.lit2_type), v(bed.lit2_percentage),
                v(bed.lit3_type), v(bed.lit3_percentage),
                v(size_base), v(phi_base),
                v(size_top), v(phi_top),
                v(bed.bed_symbols), v(bed.structures),
                v(bed.notes), v(bed.bioturbation_type),
                v(bed.bioturbation_intensity),
                v(bed.paleocurrent), v(bed.facies),
                "", "", "", "", "", "",
                # Gneisswork extras
                bed.position, bed.name, bed.top, bed.bottom,
                bed.lit1_group, bed.lit2_group, bed.lit3_group,
                bed.size_clastic_base, bed.phi_clastic_base,
                bed.size_clastic_top, bed.phi_clastic_top,
                bed.size_carbo_base, bed.phi_carbo_base,
                bed.size_carbo_top, bed.phi_carbo_top,
            ])
        return output.getvalue()

    def _sanitize_filename(name):
        """Replace spaces with underscores, remove chars not in [a-zA-Z0-9_-]."""
        name = name.replace(" ", "_")
        return re.sub(r"[^a-zA-Z0-9_-]", "", name)

    @app.route("/profile/<int:profile_id>/export")
    def profile_export(profile_id):
        profile = db.get_or_404(Profile, profile_id)
        beds = Bed.query.filter_by(profile_id=profile_id).order_by(Bed.position).all()
        csv_content = _generate_csv(profile, beds)
        filename = f"{profile.name.replace(' ', '_')}_export.csv"
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    @app.route("/export/all")
    def export_all():
        profiles = Profile.query.all()
        if not profiles:
            flash("No profiles to export.")
            return redirect(url_for("home"))

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for profile in profiles:
                beds = Bed.query.filter_by(profile_id=profile.id).order_by(Bed.position).all()
                csv_content = _generate_csv(profile, beds)
                safe_name = _sanitize_filename(profile.name)
                zf.writestr(f"{safe_name}_export.csv", csv_content)
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="application/zip",
            headers={"Content-Disposition": "attachment; filename=gneisswork_export.zip"},
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

    @app.route("/reference/lithology/<int:item_id>/rename", methods=["POST"])
    def lithology_rename(item_id):
        item = db.get_or_404(Lithology, item_id)
        name = request.form["name"].strip()
        if not name or not name.replace(" ", "").isalnum():
            flash("Name must contain only letters, digits and spaces.")
            return redirect(url_for("reference"))
        existing = Lithology.query.filter_by(name=name).first()
        if existing and existing.id != item.id:
            flash(f"Lithology '{name}' already exists.")
            return redirect(url_for("reference"))
        item.name = name
        db.session.commit()
        flash(f"Lithology renamed to '{name}'.")
        return redirect(url_for("reference"))

    @app.route("/reference/structure/<int:item_id>/rename", methods=["POST"])
    def structure_rename(item_id):
        item = db.get_or_404(Structure, item_id)
        name = request.form["name"].strip()
        if not name or not name.replace(" ", "").isalnum():
            flash("Name must contain only letters, digits and spaces.")
            return redirect(url_for("reference"))
        existing = Structure.query.filter_by(name=name).first()
        if existing and existing.id != item.id:
            flash(f"Structure '{name}' already exists.")
            return redirect(url_for("reference"))
        item.name = name
        db.session.commit()
        flash(f"Structure renamed to '{name}'.")
        return redirect(url_for("reference"))

    @app.route("/reference/lithology-type/<int:item_id>/rename", methods=["POST"])
    def lithology_type_rename(item_id):
        item = db.get_or_404(LithologyType, item_id)
        name = request.form["name"].strip()
        if not name or not name.replace(" ", "").isalnum():
            flash("Name must contain only letters, digits and spaces.")
            return redirect(url_for("reference"))
        existing = LithologyType.query.filter_by(name=name).first()
        if existing and existing.id != item.id:
            flash(f"Lithology group '{name}' already exists.")
            return redirect(url_for("reference"))
        item.name = name
        db.session.commit()
        flash(f"Lithology group renamed to '{name}'.")
        return redirect(url_for("reference"))

    @app.route("/reference/structure-type/<int:item_id>/rename", methods=["POST"])
    def structure_type_rename(item_id):
        item = db.get_or_404(StructureType, item_id)
        name = request.form["name"].strip()
        if not name or not name.replace(" ", "").isalnum():
            flash("Name must contain only letters, digits and spaces.")
            return redirect(url_for("reference"))
        existing = StructureType.query.filter_by(name=name).first()
        if existing and existing.id != item.id:
            flash(f"Structure group '{name}' already exists.")
            return redirect(url_for("reference"))
        item.name = name
        db.session.commit()
        flash(f"Structure group renamed to '{name}'.")
        return redirect(url_for("reference"))

    @app.route("/reference/lithology-type/<int:item_id>/delete", methods=["POST"])
    def lithology_type_delete(item_id):
        item = db.get_or_404(LithologyType, item_id)
        db.session.delete(item)
        db.session.commit()
        flash(f"Lithology group '{item.name}' and all its items deleted.")
        return redirect(url_for("reference"))

    @app.route("/reference/structure-type/<int:item_id>/delete", methods=["POST"])
    def structure_type_delete(item_id):
        item = db.get_or_404(StructureType, item_id)
        db.session.delete(item)
        db.session.commit()
        flash(f"Structure group '{item.name}' and all its items deleted.")
        return redirect(url_for("reference"))

    # ── Helpers ────────────────────────────────────────────
    def _validate_percentages(form):
        """Return an error message string if percentages are invalid, else None."""
        raw = [form.get("lit1_percentage", ""),
               form.get("lit2_percentage", ""),
               form.get("lit3_percentage", "")]
        try:
            values = [int(v) for v in raw]
        except (ValueError, TypeError):
            return "Lithology percentages must be valid integers."
        if any(v < 0 or v > 100 for v in values):
            return "Each lithology percentage must be between 0 and 100."
        if sum(values) != 100:
            return "Lithology percentages must sum to 100."
        return None

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
            # Reverse bed positions if direction changed
            old_direction = profile.direction
            new_direction = request.form.get("direction", "off")
            if old_direction != new_direction:
                bed_count = Bed.query.filter_by(profile_id=profile.id).count()
                if bed_count > 0:
                    Bed.query.filter_by(profile_id=profile.id).update(
                        {Bed.position: bed_count - Bed.position + 1}
                    )
            profile.name = name
        profile.description = request.form.get("description", "")
        profile.direction = request.form.get("direction", "off")
        profile.latitude = request.form.get("latitude", "No data")
        profile.longitude = request.form.get("longitude", "No data")
        profile.altitude = request.form.get("altitude", "No data")
        profile.accuracy = request.form.get("accuracy", "No data")
        profile.altitude_accuracy = request.form.get("altitude_accuracy", "No data")
        db.session.commit()
        flash(f"Log '{profile.name}' saved.")
        return redirect(url_for("profile_edit", profile_id=profile.id))

    def _save_bed(profile, bed):
        thickness = request.form.get("thickness", "").strip()
        if not thickness:
            flash("Thickness is required.")
            return redirect(request.url)
        pct_error = _validate_percentages(request.form)
        if pct_error:
            flash(pct_error)
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
            "top", "bottom",
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
