# Training and Evaluation

This repository has two training/evaluation paths.

## Legacy optimized controller

The validated command is:

```bash
python3 train_optimized.py --timesteps 100000
```

The matching evaluation command is:

```bash
python3 test_optimized.py --headless --episodes 20 --seed 0 --delay 0
```

The legacy optimized model artifacts are stored in:

- `models/optimized/joint_traffic_agent.zip`
- `models/optimized/vec_normalize.pkl`

## What the legacy validation proved

The replacement controller fixed the failure mode in the earlier single-signal
policy:

- it controls both relevant signals, not just one;
- it uses the labeled TraCI connection instead of the global default;
- it keeps emergency clearance deterministic when an ambulance is approaching;
- it validates route and signal compatibility before accepting a model.

See `VALIDATION.md` for the failure diagnosis and acceptance-test summary.

## Scenario-bound web training

The web app can train a PPO model for any valid scenario.

The training endpoint is:

```text
POST /api/training
```

The training code in `web/backend/app/training.py` compiles a fresh SUMO
network from the selected scenario and records metadata with the model.

### Saved metadata

Every saved artifact is tied to:

- `network_signature`
- ordered traffic-light IDs
- observation size
- action sizes
- scenario ID and seed
- training step count

If any of those change, the model is rejected as incompatible.

## Why this is important

Traffic control models are scenario-specific. A policy trained on one layout
should not be reused on a different network unless the lane graph, signal
layout, and observation/action schemas match exactly.

## Useful checks

```bash
python -m pytest web/backend/tests
cd web/frontend && npm test && npm run build
docker compose config -q
```

If the project is being worked on locally, the fastest end-to-end health check
is still to run the web app and load the sample scenario in the browser.
