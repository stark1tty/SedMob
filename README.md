# <img src="media/icon/sedlog-badge.png" alt="Gneisswork icon" width="32" height="32" style="background: #24292e; border-radius: 6px; padding: 2px; vertical-align: middle;"> Gneisswork

<img src="media/banner/core.jpg" alt="Gneisswork Banner" width="500"/>

[![GitHub Pages](https://github.com/stark1tty/Gneisswork/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/stark1tty/Gneisswork/actions/workflows/pages/pages-build-deployment)
[![Build Android APK](https://github.com/stark1tty/Gneisswork/actions/workflows/build-apk.yml/badge.svg)](https://github.com/stark1tty/Gneisswork/actions/workflows/build-apk.yml)

**Gneisswork**: A free and open-source web application for field geological and sedimentological core logging.

## Introduction

Gneisswork lets geologists create sedimentary logs in the field using any device with a browser. Create unlimited logs, record detailed bed-by-bed data, and export to CSV compatible with [SedLog](https://sedlog.rhul.ac.uk/) for desktop visualization.

## Features

- Create and manage multiple sedimentary log profiles with GPS metadata
- Record detailed bed data: lithology (up to 3 components), grain size (clastic and carbonate), sedimentary structures, bioturbation, boundaries, paleocurrents, and facies
- Drag-and-drop bed reordering
- CSV export compatible with SedLog
- Customizable reference data (lithologies, structures, grain sizes, boundaries)
- Pre-seeded with standard sedimentological classification schemes
- SQLite database, no external services required

## Getting Started

### Android APK (Mobile Field Use)

Download the latest APK from the [Releases page](https://github.com/stark1tty/Gneisswork/releases) or build artifacts from the [Actions tab](https://github.com/stark1tty/Gneisswork/actions/workflows/build-apk.yml).

**Installation:**
1. Download `gneisswork-*.apk` to your Android device
2. Enable "Install from Unknown Sources" in Android settings
3. Install the APK
4. Launch Gneisswork - the app runs completely offline!

The APK is a standalone app (~50-80 MB) with Python, Flask, and SQLite bundled. Perfect for field logging without internet.

📖 See [docs/ANDROID_BUILD.md](docs/ANDROID_BUILD.md) for building from source.

### Web App (Desktop/Server)

#### Requirements

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/stark1tty/Gneisswork.git
cd Gneisswork

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r sedmob/requirements.txt

# Run the application
python run.py
```

The app will be available at `http://localhost:5000`.

### Running Tests

```bash
pytest
```

## JSON API

Gneisswork includes a read-only REST API at `/api` for programmatic access to your data.

| Endpoint                               | Description                     |
| -------------------------------------- | ------------------------------- |
| `GET /api/profiles`                    | List all profiles               |
| `GET /api/profiles/<id>`               | Single profile with nested beds |
| `GET /api/profiles/<id>/beds`          | All beds for a profile          |
| `GET /api/profiles/<id>/beds/<bed_id>` | Single bed detail               |

All endpoints return JSON. Example:

```bash
curl http://localhost:5000/api/profiles
```

## Roadmap

### Missing from original app (conversion gaps)

- [ ] Bed photo management — BedPhoto model, upload, display gallery, delete (original: `bedphotos` table)
- [ ] Profile photo upload — Upload/display a photo per profile (original: camera capture)
- [ ] Bulk CSV export — Export all profiles at once from the home page (original: "Export all logs in CSV format")
- [ ] Reference data rename/edit — Rename lithologies, structures, and their groups (original: `butsavesymbol`)
- [ ] Reference data group delete — Delete lithology/structure groups with cascade (original: `butdelsymbol` for groups)
- [ ] Reference data import/export — Export and import custom lithologies and structures as a shareable file (original: export/import custom symbols between installations)
- [x] Grain size phi value storage — Store phi values alongside grain size names in bed form (original: stored both)
- [ ] Lithology percentage auto-balancing — Client-side JS to keep lit1+lit2+lit3 = 100% (original: `pagebed.js`)
- [ ] Database backup & restore — Export/import full database as downloadable file (original: SQL dump to file)
- [ ] Bed audio upload — Upload audio notes per bed (original: Cordova audio recording)
- [ ] Browser geolocation — Capture GPS coordinates on profile creation (original: `navigator.geolocation`)
- [ ] Bed direction reversal — Actually reverse bed positions when direction is toggled (original: reversed in DB)
- [ ] High-contrast field mode — Increase UI contrast for outdoor sunlight readability (original: contrast enhancement toggle in preferences)

### Future enhancements

- [ ] GPS "Get Location" button — Capture current device coordinates into Lat/Long/Alt fields on the profile form
- [ ] Variable popup descriptions — Info popups explaining each field/variable on the bed and profile forms
- [ ] Reference data descriptions — Add a description/definition field to reference data items (lithologies, structures, etc.)
- [ ] Dark mode / UI improvements
- [ ] Default menu options for standard sedimentological recording (including Tröels-Smith 1955)
- [ ] Colour recording menu
- [ ] Core metadata fields (client, project, etc.)
- [ ] Additional export options (Dropbox, email, RockWorks)
- [ ] SedLog-style graphical previews
- [ ] New sheet types: day sheets, trench pits, test pits, misc notes
- [ ] Test project

## Background

Gneisswork was originally developed as a Cordova-based mobile app by [Pawel Wolniewicz](https://github.com/pwlw/SedMob). This version is a rewrite as a Python/Flask web application, designed to run on any device with a browser.

## References

Wolniewicz, P. (2014). SedMob: A mobile application for creating sedimentary logs in the field. *Computers & Geosciences*, 66, 211-218. [https://doi.org/10.1016/j.cageo.2014.02.004](https://doi.org/10.1016/j.cageo.2014.02.004)

Zervas, D., Nichols, G.J., Hall, R., Smyth, H.R., Lüthje, C., & Murtagh, F. (2009). SedLog: A shareware program for drawing graphic logs and log data manipulation. *Computers & Geosciences*, 35(10), 2151-2159. [https://sedlog.rhul.ac.uk/](https://sedlog.rhul.ac.uk/)

## Citing Gneisswork

If you use Gneisswork in your research or publications, please cite the appropriate version:

```bibtex
% This web application version
@software{gneisswork_web_2024,
  author = {stark1tty},
  title = {Gneisswork: Web Application for Field Geological Core Logging},
  year = {2024},
  url = {https://github.com/stark1tty/Gneisswork},
  note = {Python/Flask web application}
}

% Original mobile application (SedMob)
@software{sedmob_mobile_2014,
  author = {Wolniewicz, Pawel},
  title = {SedMob: Mobile Application for Sedimentary Logging},
  year = {2014},
  url = {https://github.com/pwlw/SedMob},
  note = {Cordova-based mobile application}
}

% SedMob research paper
@article{wolniewicz2014sedmob,
  author = {Wolniewicz, Pawel},
  title = {SedMob: A mobile application for creating sedimentary logs in the field},
  journal = {Computers \& Geosciences},
  volume = {66},
  pages = {211--218},
  year = {2014},
  doi = {10.1016/j.cageo.2014.02.004},
  url = {https://doi.org/10.1016/j.cageo.2014.02.004}
}

% SedLog desktop application (Gneisswork exports are compatible)
@article{zervas2009sedlog,
  author = {Zervas, D. and Nichols, G. J. and Hall, R. and Smyth, H. R. and L{\"u}thje, C. and Murtagh, F.},
  title = {SedLog: A shareware program for drawing graphic logs and log data manipulation},
  journal = {Computers \& Geosciences},
  volume = {35},
  number = {10},
  pages = {2151--2159},
  year = {2009},
  doi = {10.1016/j.cageo.2009.02.009},
  url = {https://sedlog.rhul.ac.uk/}
}
```

## License

This project is licensed under the [GNU General Public License v2.0](LICENSE) (or later), the same license as the original [SedMob](https://github.com/pwlw/SedMob) project by Pawel Wolniewicz.
