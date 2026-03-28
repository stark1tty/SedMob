---
layout: default
title: Architecture
---

# Architecture

## Tech Stack

| Layer     | Technology                    |
| --------- | ----------------------------- |
| Backend   | Python 3.10+, Flask 3.0+      |
| ORM       | Flask-SQLAlchemy 3.1+         |
| Database  | SQLite                        |
| Templates | Jinja2 (Flask built-in)       |
| Frontend  | HTML5, inline CSS, vanilla JS |

## Project Structure

```
Gneisswork/
├── run.py                  # Application entry point
├── sedmob/
│   ├── __init__.py         # Package marker
│   ├── app.py              # Flask app factory, routes, and helpers
│   ├── api.py              # REST API blueprint
│   ├── models.py           # SQLAlchemy ORM models
│   ├── seed.py             # Reference data seeding
│   ├── requirements.txt    # Python dependencies
│   ├── static/
│   │   └── favicon.png     # Site icon
│   ├── templates/
│   │   ├── base.html       # Master layout template
│   │   ├── home.html       # Profile list (home page)
│   │   ├── profile_form.html  # Profile create/edit + bed list
│   │   ├── bed_form.html      # Bed create/edit form
│   │   └── reference.html     # Reference data management
│   └── tests/
│       ├── conftest.py     # Fixtures: app, client, db (in-memory SQLite)
│       └── test_*.py       # Feature test modules
├── .pwlw-sedmob/           # Legacy Cordova mobile app (archived)
├── media/                  # Banner, icon, and screenshots
└── docs/                   # This documentation
```

## Application Factory Pattern

Gneisswork uses Flask's application factory pattern via `create_app()` in `sedmob/app.py`. This function:

1. Creates the Flask app instance with configuration
2. Initializes the SQLAlchemy database extension
3. Registers the API blueprint (`/api` prefix)
4. Creates all database tables
5. Seeds reference data if tables are empty
6. Registers all web routes

```python
def create_app(config=None):
    app = Flask(__name__)
    # ... config setup ...
    db.init_app(app)
    from sedmob.api import api
    app.register_blueprint(api)
    with app.app_context():
        db.create_all()
        seed_database()
    # ... route registration ...
    return app
```

## Route Organization

Routes are organized into logical groups within `app.py`:

| Group           | Prefix                  | Purpose                            |
| --------------- | ----------------------- | ---------------------------------- |
| Home            | `/`                     | Profile listing                    |
| Profile CRUD    | `/profile/...`          | Create, edit, delete profiles      |
| Bed CRUD        | `/profile/<id>/bed/...` | Create, edit, delete, reorder beds |
| CSV Export      | `/profile/<id>/export`  | Download profile as CSV            |
| Bulk Export     | `/export/all`           | Download all profiles as ZIP of CSVs |
| Reference Data  | `/reference/...`        | Manage lithologies and structures  |
| API (Blueprint) | `/api/...`              | Read-only JSON API                 |

## Design Patterns

### Nested Resource URLs

Beds are nested under their parent profile in the URL structure, reflecting the domain relationship:

```
/profile/1/bed/new
/profile/1/bed/3
/profile/1/bed/3/delete
```

### Position-Based Ordering

Beds use an integer `position` field for ordering within a profile rather than relying on primary key order. This supports:

- Drag-and-drop reordering via `POST /profile/<id>/bed/reorder`
- Automatic position shifting when a bed is deleted
- Explicit ordering in queries: `Bed.query.order_by(Bed.position)`

### Reference Data by Name

Beds store lithology, structure, and grain size values as string names rather than foreign keys. This allows:

- Simpler CSV export (no joins needed)
- Custom values that don't exist in reference tables
- Reference data can be deleted without breaking existing bed records

### Shared Reference Data Helper

The `_ref_data()` helper function queries all reference tables at once and passes them to templates as a single `ref` dict, keeping template rendering consistent across forms.

## Database

SQLite is used as the database engine. The database file is created automatically at Flask's `instance/gneisswork.db` on first run. No migrations framework is used — `db.create_all()` handles schema creation.
