# Optimized controller validation

## Failure diagnosis

The previous `test_optimized.py` timed out at 1,000 simulation seconds with the
ambulance stopped inside J4. Retraining that implementation would not have
fixed the problem:

1. `sumo_rl.SumoEnvironment(single_agent=True)` exposed and controlled only the
   first signal, J4. SUMO-RL rebuilt J6's phases for external control, but no
   action was ever supplied for J6. The ambulance route requires a left turn at
   both J4 and J6.
2. The observation wrapper and reward used the global `traci` module. SUMO-RL
   starts a labeled TraCI connection, so those calls raised connection errors.
   Broad `except` blocks hid the errors. The ambulance observation remained
   zero and the emergency penalty was never applied.
3. Python's process-randomized `hash()` was originally used for lane mapping,
   making the observation encoding inconsistent between training and testing.

The SUMO network itself was validated independently. With the exact dense route
files and fixed-time signals, the ambulance completed in 25 seconds; with no
civilian traffic it completed in 12 seconds.

## Replacement design

`traffic_control_env.py` keeps SUMO-RL in multi-agent mode and exposes a single
Gymnasium environment for Stable-Baselines3:

- observation: both J4/J6 signal observations plus eight ambulance features;
- action: `MultiDiscrete([2, 2])`, one green-phase choice per junction;
- TraCI access: the labeled connection owned by SUMO-RL;
- reward: civilian stopped/wait metrics, ambulance progress, stopped penalty,
  and completion bonus;
- safety: deterministic priority phases while the ambulance approaches J4/J6.

The safety layer is intentional. Emergency clearance is a hard operational
constraint and should not depend solely on a stochastic learned policy. PPO
continues to optimize both signals outside the emergency window.

No internet dataset was required. The task is online control in a SUMO
simulator, and `traffic_dense.rou.xml` already generates randomized traffic
across all approaches. Supervised traffic data would not repair the connection
and action-space defects above.

## Training provenance

- Algorithm: PPO with a 256×256 actor and critic
- Training timesteps: 20,480
- Rollout size: 2,048
- Learning rate: 3e-4
- Discount: 0.995
- Final explained variance: 0.701
- Training traffic: randomized SUMO seeds
- Final artifacts:
  - `models/optimized/joint_traffic_agent.zip`
  - `models/optimized/vec_normalize.pkl`

Intermediate checkpoints and generated episode CSV files are ignored by Git.

## Acceptance test

Command:

```bash
export SUMO_HOME=/usr/share/sumo
python3 test_optimized.py --headless --episodes 20 --seed 0 --delay 0
```

Results for seeds 0–19:

- success: 20/20;
- ambulance mean: 15.00 seconds;
- ambulance range: 5–30 seconds;
- civilian mean accumulated wait observed before ambulance completion: 3.10
  seconds;
- emergency priority overrides: 31 total.

The matching fixed-time benchmark completed 20/20 with a 15.25-second mean and
a 5–35-second range. The prior saved single-light PPO failed its reported run
at the 1,000-second timeout. Per-seed optimized results are stored in
`results/evaluation/optimized_evaluation.json`.

These 20 seeds are a deterministic regression suite for this scenario. They do
not establish real-world performance or safety.
