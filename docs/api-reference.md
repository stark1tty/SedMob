---
layout: default
title: API Reference
---

# API Reference

SedMob includes a read-only REST API for programmatic access to profile and bed data. The API is implemented as a Flask Blueprint registered at the `/api` prefix.

Source: `sedmob/api.py`

## Base URL

```
http://localhost:5000/api
```

## Authentication

None. The API is designed for local use and has no authentication layer.

## Endpoints

### List All Profiles

```
GET /api/profiles
```

Returns an array of all profiles with their metadata (no nested beds).

**Response:**

```json
[
  {
    "id": 1,
    "name": "Outcrop A",
    "description": "Jurassic section",
    "direction": "off",
    "latitude": "51.4321",
    "longitude": "-0.5678",
    "altitude": "120",
    "accuracy": "5",
    "altitude_accuracy": "10",
    "photo": ""
  }
]
```

---

### Get Profile Detail

```
GET /api/profiles/<profile_id>
```

Returns a single profile with all its beds nested in a `beds` array, ordered by position.

**Parameters:**

| Name         | Type | Location | Description         |
| ------------ | ---- | -------- | ------------------- |
| `profile_id` | int  | URL path | Profile primary key |

**Response:**

```json
{
  "id": 1,
  "name": "Outcrop A",
  "description": "Jurassic section",
  "direction": "off",
  "latitude": "51.4321",
  "longitude": "-0.5678",
  "altitude": "120",
  "accuracy": "5",
  "altitude_accuracy": "10",
  "photo": "",
  "beds": [
    {
      "id": 1,
      "profile_id": 1,
      "position": 1,
      "name": "Bed 1",
      "thickness": "25",
      "facies": "",
      "notes": "",
      "boundary": "Sharp",
      "paleocurrent": "",
      "lit1_group": "Basic",
      "lit1_type": "Sandstone",
      "lit1_percentage": "100",
      "lit2_group": "",
      "lit2_type": "",
      "lit2_percentage": "0",
      "lit3_group": "",
      "lit3_type": "",
      "lit3_percentage": "0",
      "size_clastic_base": "f",
      "phi_clastic_base": "2.5",
      "size_clastic_top": "vf",
      "phi_clastic_top": "3.5",
      "size_carbo_base": "",
      "phi_carbo_base": "",
      "size_carbo_top": "",
      "phi_carbo_top": "",
      "bioturbation_type": "",
      "bioturbation_intensity": "",
      "structures": "",
      "bed_symbols": "",
      "top": "",
      "bottom": "",
      "audio": ""
    }
  ]
}
```

**Errors:**

| Status | Condition              |
| ------ | ---------------------- |
| 404    | Profile does not exist |

---

### List Beds for a Profile

```
GET /api/profiles/<profile_id>/beds
```

Returns all beds for a given profile, ordered by position. Does not include profile metadata.

**Parameters:**

| Name         | Type | Location | Description         |
| ------------ | ---- | -------- | ------------------- |
| `profile_id` | int  | URL path | Profile primary key |

**Response:**

```json
[
  {
    "id": 1,
    "profile_id": 1,
    "position": 1,
    "name": "Bed 1",
    "thickness": "25",
    ...
  }
]
```

**Errors:**

| Status | Condition              |
| ------ | ---------------------- |
| 404    | Profile does not exist |

---

### Get Bed Detail

```
GET /api/profiles/<profile_id>/beds/<bed_id>
```

Returns a single bed. Validates that the bed belongs to the specified profile.

**Parameters:**

| Name         | Type | Location | Description         |
| ------------ | ---- | -------- | ------------------- |
| `profile_id` | int  | URL path | Profile primary key |
| `bed_id`     | int  | URL path | Bed primary key     |

**Response:** Single bed object (same schema as in the beds list).

**Errors:**

| Status | Condition                                        |
| ------ | ------------------------------------------------ |
| 404    | Bed does not exist or does not belong to profile |

---

## Notes

- All responses use `Content-Type: application/json`
- The API is read-only — there are no POST, PUT, PATCH, or DELETE endpoints
- All bed fields are returned as strings (including numeric values like thickness and percentages)
- The `to_dict()` method on each model serializes all table columns automatically

## Example Usage

```bash
# List all profiles
curl http://localhost:5000/api/profiles

# Get a specific profile with beds
curl http://localhost:5000/api/profiles/1

# Get beds only
curl http://localhost:5000/api/profiles/1/beds

# Get a specific bed
curl http://localhost:5000/api/profiles/1/beds/3
```
