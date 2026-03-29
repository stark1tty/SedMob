---
layout: default
title: Web UI Guide
---

# Web UI Guide

Gneisswork's web interface is built with Jinja2 templates and inline CSS. All pages share a common layout defined in `base.html`.

## Navigation

The top navigation bar appears on every page:

- **Home** (`/`) — Profile list
- **Reference Data** (`/reference`) — Manage lithologies and structures
- **Settings** (`/settings`) — Database backup and restore

Flash messages (success/error notifications) are displayed below the nav bar.

## Pages

### Home Page

<a href="../media/screenshots/home.jpg"><img src="../media/screenshots/home.jpg" width="400" alt="Home page screenshot"></a>

**URL:** `/`
**Template:** `home.html`

Displays a list of all sedimentary log profiles in a table with:

| Column      | Description                        |
| ----------- | ---------------------------------- |
| Name        | Clickable link to edit the profile |
| Description | Profile description text           |
| Actions     | CSV export button for each profile |

A "Create new log" button at the top opens the new profile form. When profiles exist, an "Export All" button appears next to it, downloading a ZIP archive of all profiles as CSV files.

If no profiles exist, a "No logs yet." message is shown.

---

### Profile Form (Create / Edit)

**URLs:**
- New: `GET /profile/new`
- Edit: `GET /profile/<id>`
- Save: `POST /profile/new` or `POST /profile/<id>`

**Template:** `profile_form.html`

#### Profile Fields

| Field             | Type     | Required | Description                                                                                                                                                          |
| ----------------- | -------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Log Name          | Text     | Yes      | Unique name for the log                                                                                                                                              |
| Description       | Textarea | No       | Free-text description                                                                                                                                                |
| Direction         | Select   | No       | Borehole reversal: "Off" (default) or "On". Toggling this value reverses all existing bed positions using the formula `new_position = bed_count - old_position + 1`. |
| Latitude          | Text     | No       | GPS latitude                                                                                                                                                         |
| Longitude         | Text     | No       | GPS longitude                                                                                                                                                        |
| Altitude          | Text     | No       | GPS altitude                                                                                                                                                         |
| Accuracy          | Text     | No       | GPS accuracy in metres                                                                                                                                               |
| Altitude Accuracy | Text     | No       | GPS altitude accuracy in metres                                                                                                                                      |

#### GPS Location Capture

A "Get GPS Location" button appears on both the new and edit profile forms. Clicking it invokes the browser Geolocation API to auto-populate all five coordinate fields (latitude, longitude, altitude, accuracy, altitude accuracy). The fields remain editable so values can be corrected manually.

A status message next to the button shows the current state of the request ("Acquiring location…", "Location acquired", or an error description). If the browser does not support geolocation, the button is hidden and a message is shown instead.

#### Bed List (Edit Mode Only)

When editing an existing profile, a bed table is shown below the profile form:

| Column    | Description                    |
| --------- | ------------------------------ |
| #         | Position number                |
| Name      | Clickable link to edit the bed |
| Thickness | Bed thickness in cm            |
| Top       | Top boundary value             |
| Bottom    | Bottom boundary value          |
| Lithology | Primary lithology type         |

An "Add new bed" button opens the bed creation form.

#### Delete Profile

A "Delete Log" button at the bottom (edit mode only) deletes the profile and all its beds after a confirmation dialog.

#### Profile Photo (Edit Mode Only)

When editing a profile, a photo section allows uploading a single photo for the profile. If a photo exists, it is displayed with a delete button. Accepted formats: PNG, JPG, JPEG, GIF, WebP. Photos are stored in `uploads/<profile_id>/` with UUID-based filenames.

---

### Bed Form (Create / Edit)

**URLs:**
- New: `GET /profile/<id>/bed/new`
- Edit: `GET /profile/<id>/bed/<bed_id>`
- Save: `POST` to the same URLs

**Template:** `bed_form.html`

The bed form is the most detailed form in the app, organized into sections:

#### General Section

| Field         | Type     | Required | Description                    |
| ------------- | -------- | -------- | ------------------------------ |
| Bed Name      | Text     | No       | Label for the bed              |
| Thickness     | Text     | Yes      | Thickness in cm                |
| Facies        | Text     | No       | Facies classification          |
| Notes         | Textarea | No       | Free-text notes                |
| Paleocurrent  | Text     | No       | Paleocurrent direction         |
| Base Boundary | Select   | No       | Sharp, Erosion, or Gradational |

#### Lithology 1 / 2 / 3

Each lithology section has:

| Field      | Type   | Default | Description                              |
| ---------- | ------ | ------- | ---------------------------------------- |
| Group      | Select | —       | Lithology group (Basic, Carbonates, etc) |
| Type       | Select | —       | Specific lithology within the group      |
| Percentage | Number | 100/0/0 | Percentage of this lithology (0–100)     |

Lithology 1 defaults to 100%, Lithology 2 and 3 default to 0%. The three percentages must sum to 100%. When you change one percentage, the others auto-balance to maintain the 100% total. The server also validates that all three are integers in the range 0–100 summing to 100, rejecting the submission with an error message if not.

#### Grain Size — Clastic

| Field | Type   | Description                              |
| ----- | ------ | ---------------------------------------- |
| Base  | Select | Grain size at the base (clay to boulder) |
| Top   | Select | Grain size at the top                    |

Phi values are stored automatically based on the selected grain size.

#### Grain Size — Carbonate

| Field | Type   | Description                                         |
| ----- | ------ | --------------------------------------------------- |
| Base  | Select | Carbonate grain size at base (mudstone to rudstone) |
| Top   | Select | Carbonate grain size at top                         |

Phi values are stored automatically based on the selected grain size.

#### Bioturbation

| Field     | Type   | Description                 |
| --------- | ------ | --------------------------- |
| Type      | Select | Bioturbation classification |
| Intensity | Text   | Intensity description       |

#### Structures & Symbols

| Field      | Type | Description                           |
| ---------- | ---- | ------------------------------------- |
| Structures | Text | Comma-separated structure identifiers |
| Symbols    | Text | Comma-separated symbol identifiers    |

#### Actions

- **Save Bed** — Saves and redirects to the profile edit page
- **Cancel** — Returns to the profile edit page without saving
- **Delete Bed** (edit mode only) — Deletes the bed after confirmation

#### Bed Photos (Edit Mode Only)

When editing a bed, a photo gallery section appears below the form. Multiple photos can be uploaded per bed, each with an optional description. Photos are displayed in a gallery with delete buttons. Accepted formats: PNG, JPG, JPEG, GIF, WebP. Files are stored in `uploads/<profile_id>/<bed_id>/` with UUID-based filenames.

#### Bed Audio (Edit Mode Only)

When editing a bed, an audio section allows uploading a single audio recording per bed. If audio exists, a playback control and delete button are shown. Accepted formats: MP3, WAV, OGG, M4A, WebM. Files are stored in `uploads/<profile_id>/<bed_id>/` with UUID-based filenames.

---

### Settings (Backup & Restore)

<a href="../media/screenshots/settings.jpg"><img src="../media/screenshots/settings.jpg" width="400" alt="Settings page screenshot"></a>

**URL:** `/settings`
**Template:** `settings.html`

The settings page provides database backup and restore functionality:

#### Backup

A "Download Backup" button exports the entire database as a JSON file. The backup includes all profiles, beds, bed photos metadata, and reference data. The file is named `gneisswork_backup_<timestamp>.json`.

#### Restore

A file upload form accepts a previously exported JSON backup file. Restoring replaces all existing data with the contents of the backup file. A confirmation is required before proceeding. Uploaded files (photos, audio) are not included in the JSON backup — only database records.

#### Full Backup (Database + Files)

A "Download Full Backup" button exports the entire database and all uploaded files (photos, audio) as a single ZIP archive. The ZIP contains `database.json` (same format as the regular backup) plus an `uploads/` directory tree with all media files. The file is named `gneisswork_full_backup_<timestamp>.zip`.

#### Full Restore

A file upload form accepts a previously exported full backup ZIP. Restoring replaces all existing data in the database and all uploaded files on disk. The ZIP must contain a valid `database.json` entry. Any existing uploads directory is cleared and replaced with the contents from the archive.

#### Application Logs

A live log viewer displays recent server log output. Controls:

- **Start / Pause** — toggles polling of the `/logs` endpoint every 2 seconds
- **Clear** — clears the displayed log text

New log lines are appended automatically and the panel scrolls to the latest entry. The viewer starts paused by default.

---

### Reference Data Management

<a href="../media/screenshots/reference-data.jpg"><img src="../media/screenshots/reference-data.jpg" width="400" alt="Reference data page screenshot"></a>

**URL:** `/reference`
**Template:** `reference.html`

Two sections for managing classification data:

#### Lithology Groups & Types

- View all lithology groups with their child lithologies in a table
- Add a new lithology to an existing group, or create a new group by leaving the group selector blank
- Rename individual lithologies inline
- Rename lithology groups inline
- Delete individual lithologies
- Delete entire lithology groups (cascades to all items in the group)

#### Structure Groups & Types

- View all structure groups with their child structures
- Add a new structure to an existing group, or create a new group
- Rename individual structures inline
- Rename structure groups inline
- Delete individual structures
- Delete entire structure groups (cascades to all items in the group)

Validation: Names must contain only letters, digits, and spaces. Duplicate names are rejected.

---

## Bed Reordering

Beds can be reordered via a JSON POST to:

```
POST /profile/<id>/bed/reorder
```

The request body is a JSON array of bed IDs in the desired order:

```json
[3, 1, 2, 5, 4]
```

The server updates each bed's `position` field accordingly. This endpoint is designed for drag-and-drop UI integration.

## Styling

The app uses inline CSS in `base.html` with a card-based layout:

- Max width: 800px, centered
- Dark nav bar (`#2c3e50`)
- White cards with subtle shadows
- Responsive form inputs (100% width)
- Button classes: `.btn-primary` (blue), `.btn-danger` (red), `.btn-success` (green)
