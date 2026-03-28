---
layout: default
title: Getting Started
---

# Getting Started

## Requirements

- Python 3.10 or higher
- pip (Python package manager)

## Installation

```bash
# Clone the repository
git clone https://github.com/stark1tty/Gneisswork.git
cd Gneisswork

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r sedmob/requirements.txt
```

## Dependencies

Defined in `sedmob/requirements.txt`:

| Package          | Version | Purpose                          |
| ---------------- | ------- | -------------------------------- |
| flask            | >= 3.0  | Web framework                    |
| flask-sqlalchemy | >= 3.1  | SQLAlchemy ORM integration       |
| pytest           | >= 8.0  | Test runner                      |
| pytest-flask     | >= 1.3  | Flask-specific test fixtures     |
| hypothesis       | >= 6.0  | Property-based testing           |
| pytest           | >= 8.0  | Test runner                      |
| pytest-flask     | >= 1.3  | Flask-specific test fixtures     |
| hypothesis       | >= 6.0  | Property-based testing framework |

## Running the Application

```bash
python run.py
```

The app starts on `http://localhost:5000` with debug mode enabled.

### Entry Point

`run.py` is the application entry point:

```python
from sedmob.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

## First Run Behavior

On first launch, Gneisswork automatically:

1. Creates the SQLite database file at `instance/gneisswork.db`
2. Runs all table migrations via `db.create_all()`
3. Seeds reference tables with standard geological classification data (lithologies, structures, grain sizes, bioturbation types, boundaries)

No manual database setup is required.

## Configuration

The app factory (`create_app`) sets these defaults:

| Setting                          | Default Value         | Description                    |
| -------------------------------- | --------------------- | ------------------------------ |
| `SQLALCHEMY_DATABASE_URI`        | `sqlite:///gneisswork.db` | SQLite database path           |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | `False`               | Disables modification tracking |
| `SECRET_KEY`                     | `dev-secret-key`      | Flask session signing key      |

You can override any setting by passing a config dict to `create_app()`:

```python
app = create_app({"SECRET_KEY": "your-production-key"})
```

## Docker

If you prefer containers over a local Python install, Gneisswork ships with a `Dockerfile` and `docker-compose.yml`.

```bash
docker compose up -d
```

This builds the image, starts the app on `http://localhost:5000` with Gunicorn, and persists data in two Docker volumes:

| Volume    | Container Path  | Purpose                   |
| --------- | --------------- | ------------------------- |
| `db-data` | `/app/instance` | SQLite database           |
| `uploads` | `/app/uploads`  | Uploaded photos and audio |

Common commands:

```bash
docker compose down          # Stop the container
docker compose up -d --build # Rebuild after code changes
docker compose logs -f       # Follow logs
```

The container restarts automatically (`unless-stopped` policy), so it comes back after a reboot.

## Running Tests

```bash
pytest
```

Tests use `pytest` with `pytest-flask` for Flask application context and test client fixtures.
