---
layout: default
title: API Reference
---

# API Reference

Gneisswork includes a read-only REST API for programmatic access to profile and bed data. The API is implemented as a Flask Blueprint registered at the `/api` prefix.

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

**Response:** Single bed object with a nested `photos` array containing all attached bed photos.

```json
{
  "id": 1,
  "profile_id": 1,
  "position": 1,
  "name": "Bed 1",
  "thickness": "25",
  "...": "...",
  "photos": [
    {
      "id": 1,
      "bed_id": 1,
      "profile_id": 1,
      "filename": "a1b2c3d4.jpg",
      "description": "Cross-bedding detail",
      "created_at": "2025-06-15 10:30:00"
    }
  ]
}
```

**Errors:**

| Status | Condition                                        |
| ------ | ------------------------------------------------ |
| 404    | Bed does not exist or does not belong to profile |

---

### List Photos for a Bed

```
GET /api/profiles/<profile_id>/beds/<bed_id>/photos
```

Returns all photos attached to a bed.

**Parameters:**

| Name         | Type | Location | Description         |
| ------------ | ---- | -------- | ------------------- |
| `profile_id` | int  | URL path | Profile primary key |
| `bed_id`     | int  | URL path | Bed primary key     |

**Response:**

```json
[
  {
    "id": 1,
    "bed_id": 1,
    "profile_id": 1,
    "filename": "a1b2c3d4.jpg",
    "description": "Cross-bedding detail",
    "created_at": "2025-06-15 10:30:00"
  }
]
```

**Errors:**

| Status | Condition                                                        |
| ------ | ---------------------------------------------------------------- |
| 404    | Profile or bed does not exist, or bed does not belong to profile |

---

### Get Photo Detail

```
GET /api/profiles/<profile_id>/beds/<bed_id>/photos/<photo_id>
```

Returns a single bed photo. Validates that the photo belongs to the specified bed and profile.

**Parameters:**

| Name         | Type | Location | Description         |
| ------------ | ---- | -------- | ------------------- |
| `profile_id` | int  | URL path | Profile primary key |
| `bed_id`     | int  | URL path | Bed primary key     |
| `photo_id`   | int  | URL path | Photo primary key   |

**Response:** Single photo object (same schema as in the photos list).

**Errors:**

| Status | Condition                                                    |
| ------ | ------------------------------------------------------------ |
| 404    | Profile, bed, or photo does not exist, or ownership mismatch |

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

# Get a specific bed (includes photos)
curl http://localhost:5000/api/profiles/1/beds/3

# Get photos for a bed
curl http://localhost:5000/api/profiles/1/beds/3/photos

# Get a specific photo
curl http://localhost:5000/api/profiles/1/beds/3/photos/1
```
