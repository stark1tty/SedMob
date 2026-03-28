from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Profile(db.Model):
    __tablename__ = "profiles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    description = db.Column(db.String, default="")
    direction = db.Column(db.String, default="off")
    latitude = db.Column(db.String, default="No data")
    longitude = db.Column(db.String, default="No data")
    altitude = db.Column(db.String, default="No data")
    accuracy = db.Column(db.String, default="No data")
    altitude_accuracy = db.Column(db.String, default="No data")
    photo = db.Column(db.String, default="")

    beds = db.relationship("Bed", backref="profile", cascade="all, delete-orphan",
                           order_by="Bed.position")
    bed_photos = db.relationship("BedPhoto", backref="profile", cascade="all, delete-orphan")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Bed(db.Model):
    __tablename__ = "beds"
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String, default="")
    thickness = db.Column(db.String, nullable=False)
    facies = db.Column(db.String, default="")
    notes = db.Column(db.String, default="")
    boundary = db.Column(db.String, default="")
    paleocurrent = db.Column(db.String, default="")
    lit1_group = db.Column(db.String, default="")
    lit1_type = db.Column(db.String, default="")
    lit1_percentage = db.Column(db.String, default="100")
    lit2_group = db.Column(db.String, default="")
    lit2_type = db.Column(db.String, default="")
    lit2_percentage = db.Column(db.String, default="0")
    lit3_group = db.Column(db.String, default="")
    lit3_type = db.Column(db.String, default="")
    lit3_percentage = db.Column(db.String, default="0")
    size_clastic_base = db.Column(db.String, default="")
    phi_clastic_base = db.Column(db.String, default="")
    size_clastic_top = db.Column(db.String, default="")
    phi_clastic_top = db.Column(db.String, default="")
    size_carbo_base = db.Column(db.String, default="")
    phi_carbo_base = db.Column(db.String, default="")
    size_carbo_top = db.Column(db.String, default="")
    phi_carbo_top = db.Column(db.String, default="")
    bioturbation_type = db.Column(db.String, default="")
    bioturbation_intensity = db.Column(db.String, default="")
    structures = db.Column(db.String, default="")
    bed_symbols = db.Column(db.String, default="")
    top = db.Column(db.String, default="")
    bottom = db.Column(db.String, default="")
    audio = db.Column(db.String, default="")

    photos = db.relationship("BedPhoto", backref="bed", cascade="all, delete-orphan")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class BedPhoto(db.Model):
    __tablename__ = "bed_photos"
    id = db.Column(db.Integer, primary_key=True)
    bed_id = db.Column(db.Integer, db.ForeignKey("beds.id"), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"), nullable=False)
    filename = db.Column(db.String, nullable=False)
    description = db.Column(db.String, default="")
    created_at = db.Column(db.DateTime, default=db.func.now())

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class LithologyType(db.Model):
    __tablename__ = "lithology_types"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    lithologies = db.relationship("Lithology", backref="type", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Lithology(db.Model):
    __tablename__ = "lithologies"
    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey("lithology_types.id"), nullable=False)
    name = db.Column(db.String, nullable=False, unique=True)

    def to_dict(self):
        return {"id": self.id, "type_id": self.type_id, "name": self.name}


class StructureType(db.Model):
    __tablename__ = "structure_types"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    structures = db.relationship("Structure", backref="type", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Structure(db.Model):
    __tablename__ = "structures"
    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey("structure_types.id"), nullable=False)
    name = db.Column(db.String, nullable=False, unique=True)

    def to_dict(self):
        return {"id": self.id, "type_id": self.type_id, "name": self.name}


class GrainClastic(db.Model):
    __tablename__ = "grain_clastic"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    phi = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "phi": self.phi}


class GrainCarbonate(db.Model):
    __tablename__ = "grain_carbonate"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    phi = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "phi": self.phi}


class Bioturbation(db.Model):
    __tablename__ = "bioturbation"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Boundary(db.Model):
    __tablename__ = "boundaries"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name}
