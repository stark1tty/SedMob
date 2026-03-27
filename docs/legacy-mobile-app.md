---
layout: default
title: Legacy Mobile App
---

# Legacy Mobile App

The `.pwlw-sedmob/` directory contains the original SedMob application, a Cordova-based mobile app developed by [Pawel Wolniewicz](https://github.com/pwlw/SedMob). The current Flask web app is a rewrite of this original.

## Reference

Wolniewicz, P. (2014). SedMob: A mobile application for creating sedimentary logs in the field. *Computers & Geosciences*, 66, 211–218. [DOI: 10.1016/j.cageo.2014.02.004](https://doi.org/10.1016/j.cageo.2014.02.004)

A markdown conversion of the full paper is available at [`.dev/sedlog_paper.md`](https://github.com/stark1tty/Gneisswork/blob/main/.dev/sedlog_paper.md).

## Tech Stack

| Component  | Technology                    |
| ---------- | ----------------------------- |
| Framework  | Apache Cordova 2.7.0          |
| UI         | jQuery Mobile 1.3.1           |
| JS Library | jQuery 1.9.1                  |
| Database   | WebSQL (SQLite via browser)   |
| Testing    | Jasmine 1.2.0                 |

## File Structure

```
.pwlw-sedmob/
├── index.html              # Single-page app entry point
├── main.js                 # Cordova/Electron main process
├── master.css              # Custom styles
├── cordova-2.7.0.js        # Cordova framework
├── css/
│   ├── index.css           # App-specific CSS
│   └── jquery.mobile-1.3.1.min.css
├── js/
│   ├── index.js            # App initialization
│   ├── database.js         # Schema creation and seeding
│   ├── pagehome.js         # Profile list view
│   ├── pageprofile.js      # Profile management
│   ├── pagebed.js          # Bed form and CRUD
│   ├── pageedit.js         # Reference data editing
│   ├── pagesettings.js     # Settings, backup, sync
│   ├── helpers.js          # File system utilities
│   ├── jquery-1.9.1.min.js
│   ├── jquery-ui.min.js
│   ├── jquery.mobile-1.3.1.min.js
│   ├── jquery.ui.sortable.min.js
│   └── jquery.ui.touch-punch.min.js
├── res/                    # Platform-specific icons and splash screens
└── spec/                   # Jasmine test specs
```

## Architecture

The legacy app is a single-page application using jQuery Mobile's page system. All pages are defined as `div[data-role="page"]` elements within `index.html`, and jQuery Mobile handles transitions between them.

### Database Layer (`database.js`)

- Creates tables using WebSQL `executeSql` calls
- Schema mirrors the current SQLAlchemy models
- Seeds the same reference data as `sedmob/seed.py`
- Tables: `profiles`, `beds`, `bedphotos`, `typelithology`, `indexlithology`, `typestructure`, `indexstructure`, `grainclastic`, `graincarbonate`, `bioturbation`, `boundaries`

### Page Modules

Each page has its own JS module:

- `pagehome.js` — Profile list, selection, navigation
- `pageprofile.js` — Profile save/delete, bed list with drag-and-drop reordering (jQuery UI Sortable), geolocation capture
- `pagebed.js` — Bed form with dynamic lithology menus, percentage validation (ensures 3 lithologies sum to 100%), photo capture, audio recording
- `pageedit.js` — Add/edit/delete lithologies and structures
- `pagesettings.js` — Theme switching, database backup/restore, MySQL sync

## Features Not Yet in Flask Version

The legacy app had several features that haven't been ported to the Flask rewrite:

| Feature                    | Legacy App | Flask App | Notes                                    |
| -------------------------- | ---------- | --------- | ---------------------------------------- |
| Photo capture (per bed)    | Yes        | No        | Used Cordova camera API                  |
| Audio recording (per bed)  | Yes        | No        | Used Cordova media API                   |
| Bed photos table           | Yes        | No        | `bedphotos` table with descriptions      |
| Database backup/restore    | Yes        | No        | Exported SQL to device file system       |
| MySQL synchronization      | Yes        | No        | Synced to remote MySQL via PHP endpoint  |
| Theme switching            | Yes        | No        | High contrast mode toggle                |
| Geolocation auto-capture   | Yes        | No        | Used Cordova geolocation API             |
| Lithology % auto-balance   | Yes        | No        | JS enforced 3 lithologies summing to 100 |

## Database Schema Comparison

The legacy WebSQL schema and the Flask SQLAlchemy schema are functionally equivalent, with minor naming differences:

| Legacy Table       | Flask Model      | Notes                          |
| ------------------ | ---------------- | ------------------------------ |
| `profiles`         | `Profile`        | Same columns                   |
| `beds`             | `Bed`            | Column names use underscores in Flask (e.g., `lit1group` → `lit1_group`) |
| `bedphotos`        | —                | Not ported                     |
| `typelithology`    | `LithologyType`  | Same data                      |
| `indexlithology`   | `Lithology`      | Same data                      |
| `typestructure`    | `StructureType`  | Same data                      |
| `indexstructure`   | `Structure`      | Same data                      |
| `grainclastic`     | `GrainClastic`   | Same data                      |
| `graincarbonate`   | `GrainCarbonate` | Same data                      |
| `bioturbation`     | `Bioturbation`   | Same data                      |
| `boundaries`       | `Boundary`       | Same data                      |

## Migration Notes

If migrating data from the legacy app:

1. The reference data is identical between both versions
2. Profile and bed data can be mapped directly, adjusting column names (remove camelCase, add underscores)
3. The `bedphotos` table has no equivalent in the Flask version
4. Audio file paths stored in bed records won't be usable without the Cordova file system
