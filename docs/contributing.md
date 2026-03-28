---
layout: default
title: Contributing
---

# Contributing

## Development Setup

Requires [uv](https://docs.astral.sh/uv/) (recommended) or pip.

```bash
git clone https://github.com/stark1tty/Gneisswork.git
cd Gneisswork

# Create and activate a virtual environment
uv venv .venv
source .venv/bin/activate
```

Dependencies are installed automatically when you run `python run.py`. To install them manually:

```bash
uv pip install -r sedmob/requirements.txt
```

## Running the App

```bash
python run.py
```

The app runs at `http://localhost:5000` with Flask debug mode enabled (auto-reload on file changes).

## Running Tests

```bash
pytest
```

For a single run without watch mode:

```bash
pytest --tb=short
```

## Code Structure

| File                  | Responsibility                                      |
| --------------------- | --------------------------------------------------- |
| `sedmob/models.py`    | SQLAlchemy ORM models only — no business logic      |
| `sedmob/seed.py`      | Reference data seeding — runs once on first launch  |
| `sedmob/api.py`       | Read-only JSON API blueprint                        |
| `sedmob/app.py`       | App factory, all web routes, and helper functions   |
| `sedmob/templates/`   | Jinja2 HTML templates                               |
| `run.py`              | Entry point — auto-installs dependencies, starts Flask |

## Adding a New Route

Routes are defined inside `create_app()` in `sedmob/app.py`. Add new routes in the appropriate section (Profile CRUD, Bed CRUD, Reference Data, etc.):

```python
@app.route("/profile/<int:profile_id>/something")
def something(profile_id):
    profile = db.get_or_404(Profile, profile_id)
    return render_template("something.html", profile=profile)
```

## Adding a New Model

1. Define the model class in `sedmob/models.py`
2. Add a `to_dict()` method for JSON serialization
3. If it's reference data, add a seeding function in `sedmob/seed.py` and call it from `seed_database()`
4. The table will be created automatically on next app start via `db.create_all()`

## Adding a New Template

1. Create the file in `sedmob/templates/`
2. Extend `base.html`:

```html
{% raw %}{% extends "base.html" %}
{% block title_extra %} – Page Title{% endblock %}
{% block content %}
<!-- your content here -->
{% endblock %}{% endraw %}
```

## Adding API Endpoints

The API blueprint is in `sedmob/api.py`. Add new read endpoints there. If you need write endpoints, consider whether they belong in the API blueprint or as web routes in `app.py`.

```python
@api.route("/profiles/<int:profile_id>/something")
def something(profile_id):
    db.get_or_404(Profile, profile_id)
    # ...
    return jsonify(data)
```

## Conventions

- Use `db.get_or_404()` for all single-record lookups — it returns a proper 404 if not found
- Flash messages for all user-facing create/update/delete operations
- Redirect after POST (PRG pattern) — never render a template directly from a POST handler
- Reference data is passed to templates via `_ref_data()` — add new reference tables there
- All numeric values (thickness, percentages, phi) are stored as strings in the database to match the legacy app behavior

## Roadmap

See the [Roadmap](roadmap.html) page for planned features and completed work.
