# System Architecture

The repository now has two layers that solve adjacent problems.

## 1. Legacy SUMO controller pipeline

This is the original two-junction emergency-priority project.

Flow:

1. `draft02.net.xml`, `draft02.rou.xml`, `ambulance.rou.xml`, `vtypes.rou.xml`,
   and `draft02.sumocfg` define the fixed scenario.
2. `traffic_control_env.py` exposes the simulation as a Gymnasium environment.
3. `train_optimized.py` trains a PPO policy.
4. `test_optimized.py` evaluates the saved policy in SUMO GUI or headless mode.
5. `run_baseline_pure_traci.py` provides a fixed-time comparison baseline.

The legacy controller is intentionally narrow: it targets the J4/J6 corridor
that already exists in the repo.

## 2. Traffic Studio web workbench

The web stack is the general-purpose scenario editor and simulator.

### Backend

`web/backend/app/main.py` exposes the FastAPI application.

It is composed of these modules:

- `models.py` defines the canonical scenario schema and API contracts.
- `compiler.py` turns a validated scenario into SUMO inputs and checks them.
- `importers.py` converts CSV, OSM, and SUMO bundles into canonical scenarios.
- `simulation.py` runs background simulation jobs and priority control.
- `training.py` trains scenario-bound PPO models and validates model metadata.
- `storage.py` persists scenarios, jobs, replays, and artifacts.

### Frontend

The React frontend in `web/frontend/src/` provides:

- a canvas editor for junctions and roads;
- editors for signal programs, vehicle types, trips, flows, and incidents;
- import flows for CSV, JSON, OSM, and SUMO ZIP bundles;
- a simulation panel for live runs, comparison runs, and PPO training;
- replay and job-status streaming through the backend websocket.

## Core data flow

```text
Scenario editor / import
        ->
Canonical scenario model
        ->
Validation and SUMO compilation
        ->
Simulation or training job
        ->
Live events + replay + persisted artifacts
        ->
Browser UI and downloadable outputs
```

## Why the scenario model matters

`web/backend/app/models.py` is the source of truth for the web system. It
enforces:

- unique identifiers;
- valid road and junction references;
- consistent demand routes;
- valid priority class references;
- bounded numeric ranges for lanes, speeds, capacities, and timings.

That means the UI can stay flexible, but the backend still rejects invalid
network topology before SUMO is launched.

## Safety and control model

The runtime controller in `web/backend/app/simulation.py` implements a
priority-aware policy with safe transitions.

Important behaviors:

- emergency requests can trigger green extension or preemption;
- the controller inserts yellow and all-red clearance before priority green;
- requests are rank-ordered across emergency classes;
- priority holds are bounded by `max_hold_seconds`;
- the system can fall back to fixed, actuated, or adaptive control modes.

## Training model boundaries

`web/backend/app/training.py` treats each scenario as a distinct RL problem.

The saved artifact is only valid when these metadata fields match:

- network signature;
- ordered traffic-light IDs;
- observation size;
- action sizes.

That prevents accidental reuse of a policy on a different network layout.
