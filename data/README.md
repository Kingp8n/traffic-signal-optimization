# Generated training data

SUMO episode metrics are kept out of the project root:

- `training_logs/robust/` contains `robust_train_conn*_ep*.csv` files from
  `train_robust.py` and `train_optimized.py`.
- `training_logs/scenario_s/` contains `traffic_result_s_conn*_ep*.csv` files
  from `train_scenario_s.py`.
- `training_logs/basic/` contains metrics from the original `train.py` flow.
- `evaluation_logs/basic/` contains optional CSV output from the original test
  and diagnosis scripts.

The plotting scripts read these locations directly. The training scripts create
the directories automatically when needed.
