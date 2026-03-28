"""Gneisswork – Sedimentary logging web application."""
import collections
import csv
import io
import json
import logging
import os
import re
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, Response, send_from_directory, abort, jsonify


# ── In-memory log buffer ──────────────────────────────────
_LOG_BUFFER_SIZE = 200

class _BufferedHandler(logging.Handler):
    """Ring-buffer handler that keeps the last N formatted log lines."""
    def __init__(self, capacity=_LOG_BUFFER_SIZE):
        super().__init__()
        self.buffer = collections.deque(maxlen=capacity)

    def emit(self, record):
        self.buffer.append(self.format(record))
from sedmob.models import (
    db, Profile, Bed, BedPhoto, LithologyType, Lithology, StructureType, Structure,
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

    # ── Logging setup ─────────────────────────────────────
    _log_handler = _BufferedHandler()
    _log_handler.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    _log_handler.setLevel(logging.DEBUG)
    # Attach to Flask's logger and the root werkzeug logger
    app.logger.addHandler(_log_handler)
    app.logger.setLevel(logging.DEBUG)
    logging.getLogger("werkzeug").addHandler(_log_handler)

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
        # Clean up uploaded files
        profile_upload_dir = os.path.join(
            app.config["UPLOAD_FOLDER"], str(profile_id)
        )
        if os.path.isdir(profile_upload_dir):
            shutil.rmtree(profile_upload_dir)
        db.session.delete(profile)
        db.session.commit()
        flash(f"Log '{profile.name}' deleted.")
        return redirect(url_for("home"))

    # ── Photo Upload ──────────────────────────────────────
    @app.route("/uploads/<int:profile_id>/<filename>")
    def uploaded_file(profile_id, filename):
        folder = os.path.join(app.config["UPLOAD_FOLDER"], str(profile_id))
        return send_from_directory(folder, filename)

    @app.route("/uploads/<int:profile_id>/<int:bed_id>/<filename>")
    def uploaded_bed_file(profile_id, bed_id, filename):
        folder = os.path.join(app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id))
        return send_from_directory(folder, filename)

    @app.route("/profile/<int:profile_id>/photo", methods=["POST"])
    def profile_photo_upload(profile_id):
        profile = db.get_or_404(Profile, profile_id)
        file = request.files.get("photo")
        if not file or file.filename == "":
            flash("No file selected.")
            return redirect(url_for("profile_edit", profile_id=profile.id))
        if not allowed_file(file.filename):
            flash("File type not allowed. Use: png, jpg, jpeg, gif, webp.")
            return redirect(url_for("profile_edit", profile_id=profile.id))
        # Remove old photo if replacing
        if profile.photo:
            old_path = os.path.join(
                app.config["UPLOAD_FOLDER"], str(profile.id), profile.photo
            )
            if os.path.exists(old_path):
                os.remove(old_path)
        # Save new photo
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        folder = os.path.join(app.config["UPLOAD_FOLDER"], str(profile.id))
        os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, filename))
        profile.photo = filename
        db.session.commit()
        flash("Photo uploaded.")
        return redirect(url_for("profile_edit", profile_id=profile.id))

    @app.route("/profile/<int:profile_id>/photo/delete", methods=["POST"])
    def profile_photo_delete(profile_id):
        profile = db.get_or_404(Profile, profile_id)
        if not profile.photo:
            flash("No photo to delete.")
            return redirect(url_for("profile_edit", profile_id=profile.id))
        photo_path = os.path.join(
            app.config["UPLOAD_FOLDER"], str(profile.id), profile.photo
        )
        if os.path.exists(photo_path):
            os.remove(photo_path)
        profile.photo = ""
        db.session.commit()
        flash("Photo deleted.")
        return redirect(url_for("profile_edit", profile_id=profile.id))

    # ── Bed Photo Upload ──────────────────────────────────
    @app.route("/profile/<int:profile_id>/bed/<int:bed_id>/photo/new", methods=["POST"])
    def bed_photo_upload(profile_id, bed_id):
        profile = db.get_or_404(Profile, profile_id)
        bed = db.get_or_404(Bed, bed_id)
        if bed.profile_id != profile_id:
            abort(404)
        file = request.files.get("photo")
        if not file or file.filename == "":
            flash("No file selected.")
            return redirect(url_for("bed_edit", profile_id=profile_id, bed_id=bed_id))
        if not allowed_file(file.filename):
            flash("File type not allowed. Use: png, jpg, jpeg, gif, webp.")
            return redirect(url_for("bed_edit", profile_id=profile_id, bed_id=bed_id))
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        folder = os.path.join(app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id))
        os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, filename))
        description = request.form.get("description", "").strip()
        photo = BedPhoto(bed_id=bed_id, profile_id=profile_id,
                         filename=filename, description=description)
        db.session.add(photo)
        db.session.commit()
        flash("Photo uploaded.")
        return redirect(url_for("bed_edit", profile_id=profile_id, bed_id=bed_id))

    @app.route("/profile/<int:profile_id>/bed/<int:bed_id>/photo/<int:photo_id>/delete",
               methods=["POST"])
    def bed_photo_delete(profile_id, bed_id, photo_id):
        photo = db.get_or_404(BedPhoto, photo_id)
        if photo.bed_id != bed_id or photo.profile_id != profile_id:
            abort(404)
        photo_path = os.path.join(
            app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id), photo.filename
        )
        if os.path.exists(photo_path):
            os.remove(photo_path)
        db.session.delete(photo)
        db.session.commit()
        flash("Photo deleted.")
        return redirect(url_for("bed_edit", profile_id=profile_id, bed_id=bed_id))

    # ── Bed Audio Upload ──────────────────────────────────
    @app.route("/profile/<int:profile_id>/bed/<int:bed_id>/audio", methods=["POST"])
    def bed_audio_upload(profile_id, bed_id):
        profile = db.get_or_404(Profile, profile_id)
        bed = db.get_or_404(Bed, bed_id)
        if bed.profile_id != profile_id:
            abort(404)
        file = request.files.get("audio")
        if not file or file.filename == "":
            flash("No file selected.")
            return redirect(url_for("bed_edit", profile_id=profile_id, bed_id=bed_id))
        if not allowed_audio_file(file.filename):
            flash("File type not allowed. Use: mp3, wav, ogg, m4a, webm.")
            return redirect(url_for("bed_edit", profile_id=profile_id, bed_id=bed_id))
        # Remove previous audio file if exists
        if bed.audio:
            old_path = os.path.join(
                app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id), bed.audio
            )
            if os.path.exists(old_path):
                os.remove(old_path)
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        folder = os.path.join(app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id))
        os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, filename))
        bed.audio = filename
        db.session.commit()
        flash("Audio uploaded successfully.")
        return redirect(url_for("bed_edit", profile_id=profile_id, bed_id=bed_id))

    @app.route("/profile/<int:profile_id>/bed/<int:bed_id>/audio/delete",
               methods=["POST"])
    def bed_audio_delete(profile_id, bed_id):
        profile = db.get_or_404(Profile, profile_id)
        bed = db.get_or_404(Bed, bed_id)
        if bed.profile_id != profile_id:
            abort(404)
        if not bed.audio:
            flash("No audio to delete.")
            return redirect(url_for("bed_edit", profile_id=profile_id, bed_id=bed_id))
        audio_path = os.path.join(
            app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id), bed.audio
        )
        if os.path.exists(audio_path):
            os.remove(audio_path)
        bed.audio = ""
        db.session.commit()
        flash("Audio deleted.")
        return redirect(url_for("bed_edit", profile_id=profile_id, bed_id=bed_id))

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
        # Clean up bed photo files
        bed_upload_dir = os.path.join(
            app.config["UPLOAD_FOLDER"], str(profile_id), str(bed_id)
        )
        if os.path.isdir(bed_upload_dir):
            shutil.rmtree(bed_upload_dir)
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

    # ── Backup/Restore ────────────────────────────────────
    @app.route("/backup")
    def backup():
        data = _build_backup_dict()
        payload = json.dumps(data, indent=2)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return Response(
            payload,
            mimetype="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=gneisswork_backup_{ts}.json"
            },
        )

    @app.route("/restore", methods=["POST"])
    def restore():
        file = request.files.get("file")
        if not file:
            flash("No file provided")
            return redirect(url_for("settings"))
        try:
            data = json.loads(file.read())
        except (json.JSONDecodeError, UnicodeDecodeError):
            flash("Invalid JSON file")
            return redirect(url_for("settings"))
        if "version" not in data:
            flash("Unrecognized backup format")
            return redirect(url_for("settings"))
        try:
            _restore_from_dict(data)
        except Exception as e:
            db.session.rollback()
            flash(str(e))
            return redirect(url_for("settings"))
        flash("Database restored successfully.")
        return redirect(url_for("settings"))

    @app.route("/export/full")
    def export_full():
        """Export database JSON + all uploaded files as a single ZIP."""
        data = _build_backup_dict()
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        buf = io.BytesIO()
        upload_root = app.config["UPLOAD_FOLDER"]
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("database.json", json.dumps(data, indent=2))
            if os.path.isdir(upload_root):
                for dirpath, _dirs, filenames in os.walk(upload_root):
                    for fname in filenames:
                        full = os.path.join(dirpath, fname)
                        arc = os.path.join("uploads", os.path.relpath(full, upload_root))
                        zf.write(full, arc)
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=gneisswork_full_backup_{ts}.zip"
            },
        )

    @app.route("/restore/full", methods=["POST"])
    def restore_full():
        """Restore database + uploaded files from a full backup ZIP."""
        file = request.files.get("file")
        if not file:
            flash("No file provided.")
            return redirect(url_for("settings"))
        try:
            zf = zipfile.ZipFile(io.BytesIO(file.read()))
        except zipfile.BadZipFile:
            flash("Invalid ZIP file.")
            return redirect(url_for("settings"))
        if "database.json" not in zf.namelist():
            flash("ZIP does not contain database.json.")
            return redirect(url_for("settings"))
        try:
            data = json.loads(zf.read("database.json"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            flash("Invalid database.json inside ZIP.")
            return redirect(url_for("settings"))
        if "version" not in data:
            flash("Unrecognized backup format.")
            return redirect(url_for("settings"))
        # Restore database
        try:
            _restore_from_dict(data)
        except Exception as e:
            db.session.rollback()
            flash(str(e))
            return redirect(url_for("settings"))
        # Restore uploaded files
        upload_root = app.config["UPLOAD_FOLDER"]
        # Clear existing uploads
        if os.path.isdir(upload_root):
            shutil.rmtree(upload_root)
        os.makedirs(upload_root, exist_ok=True)
        for entry in zf.namelist():
            if entry.startswith("uploads/") and not entry.endswith("/"):
                rel = entry[len("uploads/"):]
                dest = os.path.join(upload_root, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as f:
                    f.write(zf.read(entry))
        flash("Full backup restored successfully (database + files).")
        return redirect(url_for("settings"))

    @app.route("/settings")
    def settings():
        return render_template("settings.html")

    @app.route("/logs")
    def logs():
        """Return recent log lines as JSON (used by the live-logs panel)."""
        after = request.args.get("after", -1, type=int)
        all_lines = list(_log_handler.buffer)
        # Each response includes a cursor so the client only fetches new lines
        start = max(0, after + 1)
        return jsonify({"cursor": len(all_lines) - 1, "lines": all_lines[start:]})

    # ── Helpers ────────────────────────────────────────────
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav", "ogg", "m4a", "webm"}

    def allowed_file(filename):
        return "." in filename and \
               filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    def allowed_audio_file(filename):
        return "." in filename and \
               filename.rsplit(".", 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

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

    # ── Backup / Restore helpers ──────────────────────────
    def _build_backup_dict():
        """Serialize all database tables into a backup dict."""
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
        data = {
            "version": "1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        for key, model in table_models:
            rows = [row.to_dict() for row in model.query.all()]
            if key == "bed_photos":
                for row in rows:
                    if isinstance(row.get("created_at"), datetime):
                        row["created_at"] = row["created_at"].isoformat()
            data[key] = rows
        return data

    def _restore_from_dict(data):
        """Clear database and import from backup dict. Raises on error."""
        # Table-to-model mapping for insert order (FK-safe)
        insert_order = [
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

        # Delete order (FK-safe): children before parents
        delete_order = [
            BedPhoto, Bed, Profile,
            Lithology, LithologyType,
            Structure, StructureType,
            GrainClastic, GrainCarbonate,
            Bioturbation, Boundary,
        ]

        # Delete all existing rows in FK-safe order
        for model in delete_order:
            db.session.execute(model.__table__.delete())

        # Insert rows in FK-safe order
        for key, model in insert_order:
            rows = data.get(key, [])
            for row_dict in rows:
                if key == "bed_photos" and "created_at" in row_dict:
                    val = row_dict["created_at"]
                    if isinstance(val, str):
                        row_dict["created_at"] = datetime.fromisoformat(val)
                db.session.add(model(**row_dict))

        db.session.commit()

    return app
