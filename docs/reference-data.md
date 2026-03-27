---
layout: default
title: Reference Data
---

# Reference Data

Gneisswork ships with pre-seeded geological classification data that populates dropdown menus throughout the application. This data is inserted on first run if the reference tables are empty.

Source: `sedmob/seed.py`

## Lithology Types & Lithologies

Lithologies are organized into groups:

### Basic (Group 1)

| Lithology       |
| --------------- |
| Mudstone        |
| Claystone       |
| Shale           |
| Siltstone       |
| Sandstone       |
| Conglomerate    |
| Coal            |
| Limestone       |
| Chert           |
| Volcaniclastic  |

### Carbonates (Group 2)

| Lithology          |
| ------------------ |
| Lime mudstone      |
| Wackestone         |
| Packstone          |
| Grainstone         |
| Halite             |
| Gypsum/Anhydrite   |
| Dolomite           |

### Other (Group 3)

| Lithology                        |
| -------------------------------- |
| Breccia                          |
| Matrix-supported conglomerate    |
| Clast-supported conglomerate     |
| Lava                             |
| Fine ash                         |
| Coarse ash                       |

---

## Structure Types & Structures

### Sedimentary Structures (Group 1)

| Structure                          |
| ---------------------------------- |
| Current ripple cross-lamination    |
| Wave ripple cross-lamination       |
| Planar cross bedding               |
| Trough cross bedding               |
| Horizontal planar lamination       |
| Hummocky cross stratification      |
| Swaley cross stratification        |
| Mudcracks                          |
| Synaeresis cracks                  |
| Convolute lamination               |
| Load casts                         |
| Water structures                   |
| Herring-bone cross bedding         |

### Fossils (Group 2)

| Structure        |
| ---------------- |
| Shells           |
| Bivalves         |
| Gastropods       |
| Cephalopods      |
| Brachiopods      |
| Echinoids        |
| Crinoids         |
| Solitary corals  |
| Colonial corals  |
| Foraminifera     |
| Algae            |
| Bryozoa          |
| Stromatolites    |
| Vertebrates      |
| Plant material   |
| Roots            |
| Logs             |
| Tree stumps      |
| Ostracods        |
| Radiolaria       |
| Sponges          |

### Trace Fossils (Group 3)

| Structure              |
| ---------------------- |
| Minor bioturbation     |
| Moderate bioturbation  |
| Intense bioturbation   |
| Tracks                 |
| Trails                 |
| Vertical burrows       |
| Horizontal burrows     |

### Other (Group 4)

| Structure                |
| ------------------------ |
| Nodules and concretions  |
| Intraclasts              |
| Mudclasts                |
| Flute marks              |
| Groove marks             |
| Scours                   |

---

## Clastic Grain Sizes

Uses the Wentworth grain size scale with phi (φ) values:

| Name             | Phi (φ) |
| ---------------- | ------- |
| clay             | 10.0    |
| clay/silt        | 8.0     |
| silt             | 6.0     |
| silt/vf          | 4.0     |
| vf               | 3.5     |
| vf/f             | 3.0     |
| f                | 2.5     |
| f/m              | 2.0     |
| m                | 1.5     |
| m/c              | 1.0     |
| c                | 0.5     |
| c/vc             | 0.0     |
| vc               | -0.5    |
| vc/granule       | -1.0    |
| granule          | -1.5    |
| granule/pebble   | -2.3    |
| pebble           | -3.0    |
| pebble/cobble    | -4.5    |
| cobble           | -6.0    |
| cobble/boulder   | -8.0    |
| boulder          | -10.0   |

Abbreviations: vf = very fine, f = fine, m = medium, c = coarse, vc = very coarse

---

## Carbonate Grain Sizes

Based on the Dunham classification:

| Name            | Phi (φ) |
| --------------- | ------- |
| mudstone        | 6.0     |
| wackestone      | 3.5     |
| packstone       | 1.5     |
| grainstone      | -0.5    |
| rudstone fine   | -1.5    |
| rudstone medium | -3.0    |
| rudstone        | -6.0    |

---

## Bioturbation Types

| Type                   |
| ---------------------- |
| Minor bioturbation     |
| Moderate bioturbation  |
| Intense bioturbation   |
| Tracks                 |
| Trails                 |
| Vertical burrows       |
| Horizontal burrows     |

---

## Boundary Types

| Type        |
| ----------- |
| Sharp       |
| Erosion     |
| Gradational |

---

## Customization

Reference data can be managed through the web UI at `/reference`:

- Add new lithologies to existing groups or create new groups
- Add new structures to existing groups or create new groups
- Delete individual lithologies or structures

Validation rules:
- Names must contain only letters, digits, and spaces
- Duplicate names within the same table are rejected
- Deleting a lithology or structure does not affect existing bed records (beds store values by name, not by foreign key)

Note: Grain sizes, bioturbation types, and boundaries are currently only editable via the database directly or by modifying `seed.py` before first run.
