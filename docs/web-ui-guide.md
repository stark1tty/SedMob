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

Flash messages (success/error notifications) are displayed below the nav bar.

## Pages

### Home Page

**URL:** `/`
**Template:** `home.html`

Displays a list of all sedimentary log profiles in a table with:

| Column      | Description                        |
| ----------- | ---------------------------------- |
| Name        | Clickable link to edit the profile |
| Description | Profile description text           |
| Actions     | CSV export button for each profile |

A "Create new log" button at the top opens the new profile form.

If no profiles exist, a "No logs yet." message is shown.

---

### Profile Form (Create / Edit)

**URLs:**
- New: `GET /profile/new`
- Edit: `GET /profile/<id>`
- Save: `POST /profile/new` or `POST /profile/<id>`

**Template:** `profile_form.html`

#### Profile Fields

| Field       | Type     | Required | Description                                |
| ----------- | -------- | -------- | ------------------------------------------ |
| Log Name    | Text     | Yes      | Unique name for the log                    |
| Description | Textarea | No       | Free-text description                      |
| Direction   | Select   | No       | Borehole reversal: "Off" (default) or "On" |
| Latitude    | Text     | No       | GPS latitude                               |
| Longitude   | Text     | No       | GPS longitude                              |
| Altitude    | Text     | No       | GPS altitude                               |

#### Bed List (Edit Mode Only)

When editing an existing profile, a bed table is shown below the profile form:

| Column    | Description                    |
| --------- | ------------------------------ |
| #         | Position number                |
| Name      | Clickable link to edit the bed |
| Thickness | Bed thickness in cm            |
| Lithology | Primary lithology type         |

An "Add new bed" button opens the bed creation form.

#### Delete Profile

A "Delete Log" button at the bottom (edit mode only) deletes the profile and all its beds after a confirmation dialog.

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

Lithology 1 defaults to 100%, Lithology 2 and 3 default to 0%. The three percentages should sum to 100.

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

---

### Reference Data Management

**URL:** `/reference`
**Template:** `reference.html`

Two sections for managing classification data:

#### Lithology Groups & Types

- View all lithology groups with their child lithologies in a table
- Add a new lithology to an existing group, or create a new group by leaving the group selector blank
- Delete individual lithologies

#### Structure Groups & Types

- View all structure groups with their child structures
- Add a new structure to an existing group, or create a new group
- Delete individual structures

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
