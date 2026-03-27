---
layout: default
title: CSV Export
---

# CSV Export

Gneisswork can export any profile to CSV format, designed for compatibility with [SedLog](https://sedlog.rhul.ac.uk/) desktop software for graphical log visualization.

## Export URL

```
GET /profile/<profile_id>/export
```

This triggers a file download with the filename `<profile_name>_export.csv` (spaces replaced with underscores).

## CSV Columns

The export includes one header row followed by one row per bed, ordered by position. Columns 1–25 use SedLog-compatible headers (matching the original SedMob Cordova app) so that exported files can be opened directly in SedLog. Columns 26–40 are Gneisswork extras that SedLog ignores.

### SedLog-Compatible Columns (1–25)

| #   | Column Header        | Bed Field                      | Description                     |
| --- | -------------------- | ------------------------------ | ------------------------------- |
| 1   | THICKNESS (CM)       | `thickness`                    | Thickness in cm                 |
| 2   | BASE BOUNDARY        | `boundary`                     | Base boundary type              |
| 3   | LITHOLOGY            | `lit1_type`                    | Lithology 1 type name           |
| 4   | LITHOLOGY %          | `lit1_percentage`              | Lithology 1 percentage          |
| 5   | LITHOLOGY2           | `lit2_type`                    | Lithology 2 type name           |
| 6   | LITHOLOGY2 %         | `lit2_percentage`              | Lithology 2 percentage          |
| 7   | LITHOLOGY3           | `lit3_type`                    | Lithology 3 type name           |
| 8   | LITHOLOGY3 %         | `lit3_percentage`              | Lithology 3 percentage          |
| 9   | GRAIN SIZE BASE      | clastic or carbonate base size | Merged grain size name at base  |
| 10  | PHI VALUES BASE      | clastic or carbonate base phi  | Merged phi value at base        |
| 11  | GRAIN SIZE TOP       | clastic or carbonate top size  | Merged grain size name at top   |
| 12  | PHI VALUES TOP       | clastic or carbonate top phi   | Merged phi value at top         |
| 13  | SYMBOLS IN BED       | `bed_symbols`                  | Comma-separated symbol names    |
| 14  | SYMBOLS/STRUCTURES   | `structures`                   | Comma-separated structure names |
| 15  | NOTES COLUMN         | `notes`                        | Free-text notes                 |
| 16  | BIOTURBATION TYPE    | `bioturbation_type`            | Bioturbation classification     |
| 17  | INTENSITY            | `bioturbation_intensity`       | Bioturbation intensity          |
| 18  | PALAEOCURRENT VALUES | `paleocurrent`                 | Paleocurrent direction          |
| 19  | FACIES               | `facies`                       | Facies classification           |
| 20  | OTHER1 TEXT          | —                              | Empty (SedLog placeholder)      |
| 21  | OTHER1 SYMBOL        | —                              | Empty (SedLog placeholder)      |
| 22  | OTHER2 TEXT          | —                              | Empty (SedLog placeholder)      |
| 23  | OTHER2 SYMBOL        | —                              | Empty (SedLog placeholder)      |
| 24  | OTHER3 TEXT          | —                              | Empty (SedLog placeholder)      |
| 25  | OTHER3 SYMBOL        | —                              | Empty (SedLog placeholder)      |

Empty values in columns 1–19 are exported as `<none>` to match SedLog conventions.

### Gneisswork Extra Columns (26–40)

| #   | Column Header          | Bed Field                | Description                       |
| --- | ---------------------- | ------------------------ | --------------------------------- |
| 26  | Position               | `position`               | Bed order (1-based)               |
| 27  | Name                   | `name`                   | Bed name/label                    |
| 28  | Top                    | `top`                    | Top boundary description          |
| 29  | Bottom                 | `bottom`                 | Bottom boundary description       |
| 30  | Lit1 Group             | `lit1_group`             | Lithology 1 group name            |
| 31  | Lit2 Group             | `lit2_group`             | Lithology 2 group name            |
| 32  | Lit3 Group             | `lit3_group`             | Lithology 3 group name            |
| 33  | Clastic Base Size      | `size_clastic_base`      | Clastic grain size name at base   |
| 34  | Clastic Base Phi       | `phi_clastic_base`       | Clastic phi value at base         |
| 35  | Clastic Top Size       | `size_clastic_top`       | Clastic grain size name at top    |
| 36  | Clastic Top Phi        | `phi_clastic_top`        | Clastic phi value at top          |
| 37  | Carbonate Base Size    | `size_carbo_base`        | Carbonate grain size name at base |
| 38  | Carbonate Base Phi     | `phi_carbo_base`         | Carbonate phi value at base       |
| 39  | Carbonate Top Size     | `size_carbo_top`         | Carbonate grain size name at top  |
| 40  | Carbonate Top Phi      | `phi_carbo_top`          | Carbonate phi value at top        |

## Example Output

```csv
THICKNESS (CM),BASE BOUNDARY,LITHOLOGY,LITHOLOGY %,...,Position,Name,...
25,Sharp,Sandstone,100,...,1,Bed A,...
10,Gradational,Limestone,80,...,2,Bed B,...
```

## SedLog Compatibility

The first 25 columns use the exact SedLog-compatible headers from the original SedMob Cordova app ([Wolniewicz, 2014](https://doi.org/10.1016/j.cageo.2014.02.004)), so exported files can be opened directly in SedLog for graphic log generation. SedLog ignores any extra columns beyond its expected 25, so the Gneisswork extras in columns 26–40 are safe to include.

### Grain size merging

SedLog expects a single pair of grain size columns (base/top), not separate clastic and carbonate columns. The export uses clastic values when present, falling back to carbonate values otherwise — matching the original app's behavior. The separate clastic and carbonate values are preserved in the Gneisswork extra columns (33–40).

### Key compatibility notes:

- Grain sizes use standard phi scale values recognized by SedLog
- Lithology names match standard SedLog classification schemes
- Bed ordering follows stratigraphic convention (position 1 = bottom of section)
- The `direction` field on the profile controls whether the log is displayed in normal or reversed (borehole) order

## Programmatic Export

You can also use the API to fetch profile data as JSON and build custom exports:

```bash
curl http://localhost:5000/api/profiles/1 | python -m json.tool
```
