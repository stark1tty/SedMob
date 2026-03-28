# <img src="media/icon/sedlog-badge.png" alt="Gneisswork icon" width="32" height="32" style="background: #24292e; border-radius: 6px; padding: 2px; vertical-align: middle;"> Gneisswork

[![GitHub Pages](https://github.com/stark1tty/Gneisswork/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/stark1tty/Gneisswork/actions/workflows/pages/pages-build-deployment)
[![Build Android APK](https://github.com/stark1tty/Gneisswork/actions/workflows/build-apk.yml/badge.svg)](https://github.com/stark1tty/Gneisswork/actions/workflows/build-apk.yml)

A free and open-source web application for field geological and sedimentological core logging. Create sedimentary logs in the field using any device with a browser.

## Features

- Create and manage multiple sedimentary log profiles with GPS metadata
- Record detailed bed data: lithology (up to 3 components), grain size, sedimentary structures, bioturbation, boundaries, paleocurrents, and facies
- Profile and bed photo uploads, bed audio recordings
- Drag-and-drop bed reordering
- CSV export compatible with [SedLog](https://sedlog.rhul.ac.uk/), plus bulk export (ZIP)
- Customizable reference data with standard sedimentological schemes pre-loaded
- Database backup and restore, read-only JSON API
- SQLite database, no external services required

📖 Full documentation at [gneisswork.app/docs](https://gneisswork.app/docs/)

## Quick Start

### Android (Field Use)

Download the latest APK from the [Releases page](https://github.com/stark1tty/Gneisswork/releases). Install it, and the app runs completely offline — Python, Flask, and SQLite are all bundled in.

📖 [Building from source](docs/ANDROID_BUILD.md)

### Web App

```bash
git clone https://github.com/stark1tty/Gneisswork.git
cd Gneisswork
python -m venv .venv
source .venv/bin/activate
pip install -r sedmob/requirements.txt
python run.py
```

Open `http://localhost:5000`.

### Docker

```bash
git clone https://github.com/stark1tty/Gneisswork.git
cd Gneisswork
docker compose up -d
```

📖 [Getting Started guide](docs/getting-started.md) for full details including configuration and testing.

## Documentation

| Topic                                      | Description                                  |
| ------------------------------------------ | -------------------------------------------- |
| [Getting Started](docs/getting-started.md) | Installation, configuration, Docker, testing |
| [Web UI Guide](docs/web-ui-guide.md)       | Using the web interface                      |
| [API Reference](docs/api-reference.md)     | Read-only REST API at `/api`                 |
| [Data Models](docs/data-models.md)         | Database schema                              |
| [CSV Export](docs/csv-export.md)           | Export format and SedLog compatibility       |
| [Reference Data](docs/reference-data.md)   | Customizing lithologies and structures       |
| [Architecture](docs/architecture.md)       | Technical overview                           |
| [Contributing](docs/contributing.md)       | Development workflow                         |
| [Roadmap](docs/roadmap.md)                 | Planned features and progress                |

## Background

Originally developed as a Cordova mobile app by [Pawel Wolniewicz](https://github.com/pwlw/SedMob), described in:

> Wolniewicz, P. (2014). SedMob: A mobile application for creating sedimentary logs in the field. *Computers & Geosciences*, 66, 211-218. [doi:10.1016/j.cageo.2014.02.004](https://doi.org/10.1016/j.cageo.2014.02.004)

This version is a Python/Flask rewrite designed to run on any device with a browser.

📖 [Citing Gneisswork](docs/citing.md) — BibTeX entries for academic use.

## License

[GNU General Public License v2.0](LICENSE) (or later), the same license as the original [SedMob](https://github.com/pwlw/SedMob) project.
