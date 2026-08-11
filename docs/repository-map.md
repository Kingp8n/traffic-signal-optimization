# Repository Map

This repository contains two closely related systems:

1. a legacy SUMO reinforcement-learning project at the repository root;
2. a newer browser-based Traffic Studio application in `web/`.

## Top-level files

| Path | Purpose |
| --- | --- |
| `README.md` | Legacy project overview and command examples |
| `ARCHITECTURE.md` | Older architecture notes for the multi-agent traffic concept |
| `VALIDATION.md` | Why the old optimized controller failed and how the replacement was validated |
| `WEB_APP.md` | High-level description of the browser workbench |
| `PRESENTATION.md`, `PPT.md` | Presentation notes |
| `train_optimized.py`, `test_optimized.py` | Validated legacy two-junction PPO training and evaluation |
| `train.py`, `train2.py`, `train_robust.py`, `train_scenario_s.py` | Historical training flows |
| `test2.py`, `test_agent.py`, `test_checkpoint.py`, `test_diagnosis.py`, `test_scenario_s.py` | Legacy test and diagnosis scripts |
| `run_baseline.py`, `run_baseline_pure_traci.py` | Baseline controllers and comparisons |
| `plot_res.py`, `plot_reward.py`, `plot_scenario_s.py` | Metric plotting utilities |
| `traffic_control_env.py` | Scenario-specific Gymnasium environment for the legacy controller |
| `sample_scenarios/` | Example Traffic Studio scenario files |

## `web/backend`

| Path | Purpose |
| --- | --- |
| `web/backend/app/models.py` | Canonical scenario schema and API models |
| `web/backend/app/compiler.py` | Scenario validation and SUMO artifact generation |
| `web/backend/app/importers.py` | CSV, OSM, and SUMO bundle import helpers |
| `web/backend/app/simulation.py` | Runtime simulation jobs, priority control, and replay streaming |
| `web/backend/app/training.py` | Scenario-bound PPO training and inference compatibility checks |
| `web/backend/app/storage.py` | SQLite metadata and artifact storage |
| `web/backend/app/main.py` | FastAPI routes, static serving, and websocket streaming |
| `web/backend/tests/` | Backend unit tests |

## `web/frontend`

| Path | Purpose |
| --- | --- |
| `web/frontend/src/App.tsx` | Main UI shell |
| `web/frontend/src/components/ScenarioEditor.tsx` | Scenario editor for junctions, roads, and signals |
| `web/frontend/src/components/DemandEditor.tsx` | Vehicle, trip, and flow editing |
| `web/frontend/src/components/ImportPanel.tsx` | JSON / CSV / OSM / SUMO import UI |
| `web/frontend/src/components/SimulationPanel.tsx` | Run control, live status, and results |
| `web/frontend/src/components/NetworkCanvas.tsx` | Visual network editor/canvas |
| `web/frontend/src/lib/api.ts` | API client |
| `web/frontend/src/types.ts` | Frontend types |

## Data and artifacts

| Path | Purpose |
| --- | --- |
| `data/README.md` | Training log layout |
| `data/traffic.csv`, `data/traffic_dataset.csv` | Example traffic datasets |
| `models/optimized/` | Validated legacy joint PPO model and normalization stats |
| `models_s/`, `modelsops/`, `modelsop/`, `models_robust/` | Other model runs, checkpoints, and metrics |
| `results/evaluation/` | Stored evaluation summaries |

## Runtime and deployment

| Path | Purpose |
| --- | --- |
| `Dockerfile` | Container build for the web application |
| `docker-compose.yml` | Local service orchestration |
| `scripts/run_web.sh` | Convenience launcher for Docker Compose |
| `.gitignore` | Ignore rules for generated state and build output |

## Current conventions

- Root-level SUMO assets are still used by the legacy controller flows.
- The web app stores scenario state, simulation artifacts, replays, and
  training output in the configured workspace directory.
- Generated frontend build output and Python caches are ignored by Git.
