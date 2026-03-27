---
layout: default
title: CSV Export
---

# CSV Export

SedMob can export any profile to CSV format, designed for compatibility with [SedLog](https://sedlog.rhul.ac.uk/) desktop software for graphical log visualization.

## Export URL

```
GET /profile/<profile_id>/export
```

This triggers a file download with the filename `<profile_name>_export.csv` (spaces replaced with underscores).

## CSV Columns

The export includes one header row followed by one row per bed, ordered by position.

| #   | Column Header          | Bed Field                | Description                       |
| --- | ---------------------- | ------------------------ | --------------------------------- |
| 1   | Position               | `position`               | Bed order (1-based)               |
| 2   | Name                   | `name`                   | Bed name/label                    |
| 3   | Thickness              | `thickness`              | Thickness in cm                   |
| 4   | Facies                 | `facies`                 | Facies classification             |
| 5   | Notes                  | `notes`                  | Free-text notes                   |
| 6   | Boundary               | `boundary`               | Base boundary type                |
| 7   | Paleocurrent           | `paleocurrent`           | Paleocurrent direction            |
| 8   | Lit1 Group             | `lit1_group`             | Lithology 1 group name            |
| 9   | Lit1 Type              | `lit1_type`              | Lithology 1 type name             |
| 10  | Lit1 %                 | `lit1_percentage`        | Lithology 1 percentage            |
| 11  | Lit2 Group             | `lit2_group`             | Lithology 2 group name            |
| 12  | Lit2 Type              | `lit2_type`              | Lithology 2 type name             |
| 13  | Lit2 %                 | `lit2_percentage`        | Lithology 2 percentage            |
| 14  | Lit3 Group             | `lit3_group`             | Lithology 3 group name            |
| 15  | Lit3 Type              | `lit3_type`              | Lithology 3 type name             |
| 16  | Lit3 %                 | `lit3_percentage`        | Lithology 3 percentage            |
| 17  | Clastic Base Size      | `size_clastic_base`      | Clastic grain size name at base   |
| 18  | Clastic Base Phi       | `phi_clastic_base`       | Clastic phi value at base         |
| 19  | Clastic Top Size       | `size_clastic_top`       | Clastic grain size name at top    |
| 20  | Clastic Top Phi        | `phi_clastic_top`        | Clastic phi value at top          |
| 21  | Carbonate Base Size    | `size_carbo_base`        | Carbonate grain size name at base |
| 22  | Carbonate Base Phi     | `phi_carbo_base`         | Carbonate phi value at base       |
| 23  | Carbonate Top Size     | `size_carbo_top`         | Carbonate grain size name at top  |
| 24  | Carbonate Top Phi      | `phi_carbo_top`          | Carbonate phi value at top        |
| 25  | Bioturbation Type      | `bioturbation_type`      | Bioturbation classification       |
| 26  | Bioturbation Intensity | `bioturbation_intensity` | Bioturbation intensity            |
| 27  | Structures             | `structures`             | Comma-separated structure names   |
| 28  | Symbols                | `bed_symbols`            | Comma-separated symbol names      |

## Example Output

```csv
Position,Name,Thickness,Facies,Notes,Boundary,Paleocurrent,Lit1 Group,Lit1 Type,Lit1 %,...
1,Bed A,25,,,"Sharp",,Basic,Sandstone,100,...
2,Bed B,10,,,"Gradational",,Carbonates,Limestone,80,...
```

## SedLog Compatibility

The CSV format is designed to be importable into SedLog for generating graphical sedimentary logs. Key compatibility notes:

- Grain sizes use standard phi scale values recognized by SedLog
- Lithology names match standard SedLog classification schemes
- Bed ordering follows stratigraphic convention (position 1 = bottom of section)
- The `direction` field on the profile controls whether the log is displayed in normal or reversed (borehole) order

## Programmatic Export

You can also use the API to fetch profile data as JSON and build custom exports:

```bash
curl http://localhost:5000/api/profiles/1 | python -m json.tool
```
