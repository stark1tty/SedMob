# Data Models

All models are defined in `sedmob/models.py` using Flask-SQLAlchemy. Every model includes a `to_dict()` method for JSON serialization.

## Entity Relationship Overview

```
Profile (1) ──── (Many) Bed
LithologyType (1) ──── (Many) Lithology
StructureType (1) ──── (Many) Structure
```

Beds reference lithology/structure/grain data by name (not by foreign key), so they are loosely coupled to the reference tables.

---

## Core Domain Models

### Profile

Represents a single sedimentary log (a field section or borehole).

| Column              | Type    | Constraints      | Default     | Description                               |
| ------------------- | ------- | ---------------- | ----------- | ----------------------------------------- |
| `id`                | Integer | Primary Key      | Auto        | Unique identifier                         |
| `name`              | String  | NOT NULL, UNIQUE | —           | Log name                                  |
| `description`       | String  |                  | `""`        | Free-text description                     |
| `direction`         | String  |                  | `"off"`     | Borehole reversal flag (`"on"` / `"off"`) |
| `latitude`          | String  |                  | `"No data"` | GPS latitude                              |
| `longitude`         | String  |                  | `"No data"` | GPS longitude                             |
| `altitude`          | String  |                  | `"No data"` | GPS altitude                              |
| `accuracy`          | String  |                  | `"No data"` | GPS accuracy                              |
| `altitude_accuracy` | String  |                  | `"No data"` | GPS altitude accuracy                     |
| `photo`             | String  |                  | `""`        | Photo path/reference                      |

Relationships:
- `beds` — One-to-many relationship to `Bed`, ordered by `Bed.position`, with cascade delete

### Bed

Represents a single stratigraphic unit (bed/layer) within a profile.

| Column                   | Type    | Constraints  | Default | Description                        |
| ------------------------ | ------- | ------------ | ------- | ---------------------------------- |
| `id`                     | Integer | Primary Key  | Auto    | Unique identifier                  |
| `profile_id`             | Integer | FK, NOT NULL | —       | Parent profile                     |
| `position`               | Integer | NOT NULL     | —       | Order within profile (1-based)     |
| `name`                   | String  |              | `""`    | Bed name/label                     |
| `thickness`              | String  | NOT NULL     | —       | Thickness in cm                    |
| `facies`                 | String  |              | `""`    | Facies classification              |
| `notes`                  | String  |              | `""`    | Free-text notes                    |
| `boundary`               | String  |              | `""`    | Base boundary type                 |
| `paleocurrent`           | String  |              | `""`    | Paleocurrent direction             |
| `lit1_group`             | String  |              | `""`    | Lithology 1 group name             |
| `lit1_type`              | String  |              | `""`    | Lithology 1 type name              |
| `lit1_percentage`        | String  |              | `"100"` | Lithology 1 percentage             |
| `lit2_group`             | String  |              | `""`    | Lithology 2 group name             |
| `lit2_type`              | String  |              | `""`    | Lithology 2 type name              |
| `lit2_percentage`        | String  |              | `"0"`   | Lithology 2 percentage             |
| `lit3_group`             | String  |              | `""`    | Lithology 3 group name             |
| `lit3_type`              | String  |              | `""`    | Lithology 3 type name              |
| `lit3_percentage`        | String  |              | `"0"`   | Lithology 3 percentage             |
| `size_clastic_base`      | String  |              | `""`    | Clastic grain size at base         |
| `phi_clastic_base`       | String  |              | `""`    | Clastic phi value at base          |
| `size_clastic_top`       | String  |              | `""`    | Clastic grain size at top          |
| `phi_clastic_top`        | String  |              | `""`    | Clastic phi value at top           |
| `size_carbo_base`        | String  |              | `""`    | Carbonate grain size at base       |
| `phi_carbo_base`         | String  |              | `""`    | Carbonate phi value at base        |
| `size_carbo_top`         | String  |              | `""`    | Carbonate grain size at top        |
| `phi_carbo_top`          | String  |              | `""`    | Carbonate phi value at top         |
| `bioturbation_type`      | String  |              | `""`    | Bioturbation type                  |
| `bioturbation_intensity` | String  |              | `""`    | Bioturbation intensity             |
| `structures`             | String  |              | `""`    | Sedimentary structures (comma-sep) |
| `bed_symbols`            | String  |              | `""`    | Bed symbols (comma-sep)            |
| `top`                    | String  |              | `""`    | Top boundary description           |
| `bottom`                 | String  |              | `""`    | Bottom boundary description        |
| `audio`                  | String  |              | `""`    | Audio recording path               |

---

## Reference Data Models

These tables store the classification schemes used in dropdown menus throughout the app. They are pre-seeded on first run (see [Reference Data](reference-data.md)).

### LithologyType

Groups lithologies into categories (e.g., "Basic", "Carbonates", "Other").

| Column | Type    | Constraints      | Description       |
| ------ | ------- | ---------------- | ----------------- |
| `id`   | Integer | Primary Key      | Unique identifier |
| `name` | String  | NOT NULL, UNIQUE | Group name        |

Relationships: `lithologies` — One-to-many to `Lithology`, cascade delete

### Lithology

Individual lithology types within a group.

| Column    | Type    | Constraints         | Description       |
| --------- | ------- | ------------------- | ----------------- |
| `id`      | Integer | Primary Key         | Unique identifier |
| `type_id` | Integer | FK to LithologyType | Parent group      |
| `name`    | String  | NOT NULL, UNIQUE    | Lithology name    |

### StructureType

Groups structures into categories (e.g., "Sedimentary structures", "Fossils").

| Column | Type    | Constraints      | Description       |
| ------ | ------- | ---------------- | ----------------- |
| `id`   | Integer | Primary Key      | Unique identifier |
| `name` | String  | NOT NULL, UNIQUE | Group name        |

Relationships: `structures` — One-to-many to `Structure`, cascade delete

### Structure

Individual structure types within a group.

| Column    | Type    | Constraints         | Description       |
| --------- | ------- | ------------------- | ----------------- |
| `id`      | Integer | Primary Key         | Unique identifier |
| `type_id` | Integer | FK to StructureType | Parent group      |
| `name`    | String  | NOT NULL, UNIQUE    | Structure name    |

### GrainClastic

Clastic grain size scale with phi values.

| Column | Type    | Constraints | Description                   |
| ------ | ------- | ----------- | ----------------------------- |
| `id`   | Integer | Primary Key | Unique identifier             |
| `name` | String  | NOT NULL    | Size name (e.g., "silt", "f") |
| `phi`  | String  | NOT NULL    | Phi value (e.g., "6.0")       |

### GrainCarbonate

Carbonate grain size scale with phi values.

| Column | Type    | Constraints | Description                               |
| ------ | ------- | ----------- | ----------------------------------------- |
| `id`   | Integer | Primary Key | Unique identifier                         |
| `name` | String  | NOT NULL    | Size name (e.g., "mudstone", "packstone") |
| `phi`  | String  | NOT NULL    | Phi value                                 |

### Bioturbation

Bioturbation classification types.

| Column | Type    | Constraints | Description       |
| ------ | ------- | ----------- | ----------------- |
| `id`   | Integer | Primary Key | Unique identifier |
| `name` | String  | NOT NULL    | Bioturbation type |

### Boundary

Base boundary types for beds.

| Column | Type    | Constraints | Description       |
| ------ | ------- | ----------- | ----------------- |
| `id`   | Integer | Primary Key | Unique identifier |
| `name` | String  | NOT NULL    | Boundary type     |
