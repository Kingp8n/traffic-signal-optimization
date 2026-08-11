# Scenario Schema

The web application uses a versioned canonical scenario format.

`schema_version` is currently `"1.0"`.

## Top-level structure

```json
{
  "schema_version": "1.0",
  "id": "two-junction-priority",
  "name": "Two-junction emergency corridor",
  "description": "...",
  "coordinate_system": "abstract",
  "junctions": [],
  "roads": [],
  "signal_programs": [],
  "vehicle_types": [],
  "trips": [],
  "flows": [],
  "demand_multipliers": [],
  "priority_classes": [],
  "incidents": [],
  "settings": {}
}
```

The schema is defined in `web/backend/app/models.py`.

## Entity reference

### Junctions

Fields:

- `id`
- `x`, `y`
- `kind`: `priority`, `traffic_light`, or `unregulated`

Rules:

- identifiers must be unique;
- a scenario needs at least 2 junctions;
- traffic-light junctions are used for signal programs and control.

### Roads

Fields:

- `id`
- `from_junction`
- `to_junction`
- `lanes`
- `speed_mps`
- `priority`
- `shape`
- `allowed_vehicle_classes`

Rules:

- roads must connect two different existing junctions;
- lanes are bounded between 1 and 8;
- speeds are bounded above;
- road references are validated before compile.

### Signal programs

Fields:

- `junction_id`
- `controller`: `fixed`, `actuated`, `adaptive`, or `priority`
- `yellow_seconds`
- `all_red_seconds`
- `phases`

Each phase has:

- `name`
- `duration`
- `min_duration`
- `max_duration`
- optional SUMO phase `state`
- permitted movements

The compiler can generate signal plans from the movement set and then apply
yellow/all-red clearance automatically.

### Vehicle types

Fields:

- `id`
- `label`
- `vehicle_class`
- `length_m`
- `min_gap_m`
- `max_speed_mps`
- `accel_mps2`
- `decel_mps2`
- `driver_imperfection`
- `speed_factor`
- `speed_deviation`
- `emission_class`
- `capacity`
- `color`
- `shape`
- `priority_class`
- `advanced`

Use this collection to model realistic vehicles such as:

- passenger cars;
- buses;
- ambulances;
- government vehicles;
- custom classes for local research.

### Trips

Trips are single vehicles with a fixed departure and a fixed route.

Fields:

- `id`
- `vehicle_type`
- `depart`
- `from_road`
- `to_road`
- `via`
- `priority_class`

### Flows

Flows are recurring demand generators.

Fields:

- `id`
- `vehicle_type`
- `begin`
- `end`
- `vehicles_per_hour`
- `from_road`
- `to_road`
- `via`
- `priority_class`

Flows must have `end > begin`.

### Demand multipliers

Demand multipliers are time-window scaling factors:

- `begin`
- `end`
- `multiplier`

They are useful for rush-hour or event surges.

### Priority classes

Fields:

- `id`
- `label`
- `rank`
- `strategy`
- `detection_distance_m`
- `green_extension_seconds`
- `max_hold_seconds`
- `color`

Strategies:

- `none`
- `green_extension`
- `phase_request`
- `preemption`

The sample scenario uses priority, government, and transit classes to show how
different classes can behave differently.

### Incidents

Incidents model temporary disruptions:

- `speed_reduction`
- `lane_closure`
- `capacity_reduction`

Fields:

- `id`
- `road_id`
- `begin`
- `end`
- `kind`
- `value`

### Settings

Fields:

- `duration_seconds`
- `step_length_seconds`
- `seed`
- `controller`
- `traffic_hand`
- `replay_interval_seconds`

## Validation rules

The backend checks more than JSON shape.

It also validates:

- duplicate IDs;
- unknown references;
- roads that loop back to the same junction;
- empty or disconnected junctions;
- missing traffic demand;
- excessive signalized scale for the v1 target;
- compatibility between a saved model and the scenario it was trained for.

## CSV import mapping

`web/backend/app/importers.py` accepts CSV input for these entities:

- `junctions`
- `roads`
- `vehicle_types`
- `trips`
- `flows`

The canonical column names are defined in `CSV_FIELDS` in that module. The
importer is intentionally strict: it validates the uploaded CSV size, parses
numbers, and reports row-level issues before anything is saved.

## Example scenario

`sample_scenarios/two_junction_priority.json` is the bundled example used by
the web app on startup. It contains:

- two traffic-light junctions;
- a pair of priority junctions;
- mixed passenger, bus, and ambulance vehicle types;
- both trips and flows;
- three priority classes;
- a 300-second left-hand driving simulation.
