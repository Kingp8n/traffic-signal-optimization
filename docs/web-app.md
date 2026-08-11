# Web Application

Traffic Studio is the browser-based way to build, validate, simulate, and
train traffic scenarios in this repository.

## Start options

### Docker

```bash
./scripts/run_web.sh
```

That runs the compose stack defined in `docker-compose.yml` and serves the
application on `http://localhost:8000`.

### Local development

Backend:

```bash
python3 -m venv .venv-web
.venv-web/bin/pip install -r web/backend/requirements.txt
TRAFFIC_STUDIO_WORKSPACE=/tmp/traffic-studio .venv-web/bin/uvicorn web.backend.app.main:app --reload
```

Frontend:

```bash
cd web/frontend
npm install
npm run dev
```

The frontend dev server runs on `http://localhost:5173` and proxies `/api` to
the backend.

## Main workflow

1. Create a scenario or load `sample_scenarios/two_junction_priority.json`.
2. Draw directed roads between junctions.
3. Add signal programs and movement-aware phases.
4. Define vehicle types, trips, flows, demand multipliers, incidents, and
   priority classes.
5. Validate the scenario.
6. Run a simulation or comparison job.
7. Inspect live events, replay output, and summary metrics.
8. Optionally train a scenario-bound PPO policy.

## Frontend structure

The UI is split into focused components:

- `NetworkCanvas.tsx` for visual graph editing;
- `ScenarioEditor.tsx` for junction and road structure;
- `DemandEditor.tsx` for traffic demand and vehicle data;
- `ImportPanel.tsx` for CSV/JSON/OSM/SUMO input;
- `SimulationPanel.tsx` for job control and results.

This is the part of the project that answers the original request to enter
intersection and vehicle data through a UI, CSV, JSON, or imported network
files.

## API endpoints

The backend exposes a small REST API plus a websocket stream.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Service health check |
| `GET` | `/api/scenarios` | List scenarios |
| `POST` | `/api/scenarios` | Create a scenario |
| `GET` | `/api/scenarios/{scenario_id}` | Fetch a scenario |
| `PUT` | `/api/scenarios/{scenario_id}` | Replace a scenario |
| `DELETE` | `/api/scenarios/{scenario_id}` | Delete a scenario |
| `POST` | `/api/scenarios/{scenario_id}/validate` | Validate and compile |
| `GET` | `/api/imports/csv/fields` | Supported CSV mappings |
| `POST` | `/api/imports/csv/preview` | Preview a CSV mapping |
| `POST` | `/api/imports/osm` | Import a scenario from an OSM bounding box |
| `POST` | `/api/imports/sumo` | Import a SUMO ZIP bundle |
| `POST` | `/api/simulations` | Start a simulation job |
| `POST` | `/api/comparisons` | Start a controller comparison matrix |
| `POST` | `/api/training` | Start PPO training |
| `GET` | `/api/jobs` | List jobs |
| `GET` | `/api/jobs/{job_id}` | Inspect a job |
| `POST` | `/api/jobs/{job_id}/cancel` | Request cancellation |
| `GET` | `/api/jobs/{job_id}/replay` | Download replay output |
| `WS` | `/api/jobs/{job_id}/stream` | Live job events |

OpenAPI docs are available at `http://localhost:8000/docs`.

## Import paths

### JSON

JSON import/export is full fidelity because the canonical schema is the
Pydantic model in `models.py`.

### CSV

CSV import is intentionally guided, not magical. The UI asks for a column map,
then the backend previews the converted rows and reports row-level issues.

### OSM

OSM import uses a bounding box, converts the selected area with `netconvert`,
and then translates the generated network into the canonical scenario format.

### SUMO bundle

SUMO import accepts a ZIP file containing exactly one `.sumocfg`, the
referenced network file, and route files. The importer rejects unsafe paths and
symbolic links.

## Priority and replay behavior

The live simulator supports:

- fixed-time control;
- actuated control;
- adaptive queue-responsive control;
- priority control with rank-based preemption;
- RL control when a matching model artifact is selected.

During a run, the backend streams events over websockets and also writes a
replay file so the run can be reviewed later.

## Storage

When running in Docker, scenario state and generated artifacts live in the
workspace volume. When running locally, set `TRAFFIC_STUDIO_WORKSPACE` to a
scratch directory such as `/tmp/traffic-studio`.

That keeps the repository tree clean and prevents simulation artifacts from
mixing with source control.
