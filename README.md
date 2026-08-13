# 🚑 Emergency Vehicle Priority System

**Intelligent Traffic Signal Control using Reinforcement Learning**

## 📋 Overview

This project implements an emergency-priority traffic signal controller for a
two-intersection SUMO network. A PPO policy controls both J4 and J6, while a
deterministic safety layer guarantees the required signal phases as the
ambulance approaches each junction.

## 🎯 Problem Statement

Traditional fixed-time traffic signals cannot adapt to dynamic traffic conditions or prioritize emergency vehicles. This results in:
- Delayed emergency response times
- Increased risk to patients requiring urgent care
- Inefficient traffic flow during emergency situations

Our RL-based solution dynamically adjusts traffic signals to clear paths for ambulances while minimizing disruption to civilian traffic.

## 🛠️ Technical Stack

- **RL Framework**: Stable-Baselines3 (PPO)
- **Traffic Simulator**: SUMO 1.25.0
- **Environment Wrapper**: sumo-rl
- **Python**: 3.12 or newer
- **Key Libraries**: Gymnasium, PyTorch, NumPy

## 📁 Project Structure

```
rl-traffic-control/
├── traffic_control_env.py      # Joint J4/J6 Gymnasium environment
├── train_optimized.py          # Train the validated joint PPO controller
├── test_optimized.py           # GUI/headless seeded evaluation
├── models/optimized/           # Validated model and normalization statistics
├── results/evaluation/         # Reproducible acceptance-test results
├── train2.py                    # Basic training script
├── test2.py                     # Basic testing script
├── run_baseline_pure_traci.py  # Baseline fixed-time signals comparison
├── data/training_logs/         # Generated per-episode SUMO CSV metrics
│   ├── optimized/              # Current joint-controller training logs
│   ├── robust/                 # Legacy robust training logs
│   └── scenario_s/             # S-scenario training logs
├── draft02.net.xml              # SUMO road network
├── draft02.rou.xml              # Civilian vehicle routes
├── ambulance.rou.xml            # Emergency vehicle configuration
├── vtypes.rou.xml               # Vehicle type definitions
└── draft02.sumocfg              # SUMO configuration file
```

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
python3 -m pip install -r requirements.txt

# Set SUMO_HOME environment variable
export SUMO_HOME="/usr/share/sumo"  # Adjust path as needed
```

### Running the Project

**1. Use the included validated model**

Run one episode in the SUMO GUI:

```bash
python3 test_optimized.py
```

Run the reproducible 20-seed acceptance test without a GUI:

```bash
python3 test_optimized.py --headless --episodes 20 --seed 0 --delay 0
```

The command exits with status 1 if any ambulance fails to finish.

**2. Retrain the controller**

```bash
python3 train_optimized.py --timesteps 100000
```
- Checkpoints are written every 10,000 steps and ignored by Git.
- Final model: `models/optimized/joint_traffic_agent.zip`
- Normalization stats: `models/optimized/vec_normalize.pkl`

**3. Run the legacy fixed-time baseline GUI**
```bash
python3 run_baseline_pure_traci.py
```
- Simulates fixed-time traffic signals
- Records ambulance travel time for comparison
- Visualizes simulation in SUMO GUI

**4. Plot legacy robust-training metrics**
```bash
python3 plot_res.py
```
- Reads episode metrics from `data/training_logs/robust/`
- Future training runs write CSV files there instead of the repository root

## 🧠 Key Features

### Joint control and safety

- PPO emits one action for J4 and one for J6 through a `MultiDiscrete([2, 2])`
  action space.
- Observations combine both SUMO-RL signal observations with ambulance
  presence, speed, progress, and route-location features.
- The environment uses SUMO-RL's labeled TraCI connection. This is required
  when reading the ambulance state.
- During emergency approach, a safety shield selects J4 phase 0 and J6 phase 1
  for the ambulance's two left turns. PPO controls normal traffic outside that
  safety-critical window.
- Reward combines civilian queues/waiting time, ambulance progress, stopped
  penalties, and a completion bonus.

### Optimization Techniques

1. **VecNormalize**: Normalizes observations and rewards to prevent gradient explosion
2. **Big Brain Architecture**: 256×256 neural network (vs default 64×64)
3. **Fine-tuned Hyperparameters**:
   - Learning rate: 3e-4
   - Gamma: 0.995 (long-term planning)
   - Entropy coefficient: 0.01 (exploration)
   - n_steps: 2048 (experience collection)
   - GAE Lambda: 0.95 (variance smoothing)

### Environment configuration
- **Simulation Time**: 1000 seconds per episode
- **Ambulance Requested Departure**: 5 seconds (actual insertion can be delayed)
- **Signal Constraints**: 5-60 seconds green time, 4 seconds yellow
- **Control Mode**: Centralized joint control of J4 and J6

## 📊 Performance Metrics

The system tracks:
- **Ambulance Travel Time**: Primary metric (seconds from spawn to destination)
- **System Mean Waiting Time**: Average civilian vehicle delay
- **Episode Reward Mean**: Normalized reward (should converge to stable value)
- **Explained Variance**: How well the value function predicts returns

### Verified results

The current model was trained for 20,480 PPO timesteps and evaluated on SUMO
seeds 0–19. Full per-seed output is stored in
`results/evaluation/optimized_evaluation.json`.

| Controller | Success | Mean | Minimum | Maximum |
| --- | ---: | ---: | ---: | ---: |
| Joint PPO + emergency shield | 20/20 | 15.00s | 5s | 30s |
| Fixed-time benchmark | 20/20 | 15.25s | 5s | 35s |
| Previous single-light PPO | 0/1 | timeout | — | 999.9s |

The 20-seed comparison is a regression/acceptance test, not a claim of
real-world statistical superiority. See `VALIDATION.md` for methodology and
the diagnosed failure in the previous controller.

## 🔧 Configuration

### Training Parameters

Command-line training parameter:
```python
python3 train_optimized.py --timesteps 100000
```

## 📈 Monitoring Training

During training, watch for:
- `explained_variance`: The validated 20,480-step run finished at 0.701
- `entropy_loss`: Should gradually decrease (exploration → exploitation)
- `policy_gradient_loss`: Should remain stable, not explode

## 🎮 Simulation Controls

When running with GUI (`use_gui=True`):
- **Space**: Pause/Resume
- **Mouse Wheel**: Zoom in/out
- **Right-click + Drag**: Pan view
- **Vehicle Click**: View individual vehicle details

## 📝 Requirements

```
sumo-rl
stable-baselines3
gymnasium
matplotlib
seaborn
shimmy
torch
```

## 🤝 Contributing

This is an academic/research project. Key areas for improvement:
- Larger road networks and multiple emergency vehicles
- Real-world traffic pattern integration
- Transfer learning from simulation to reality
- Additional emergency vehicle types

## 📄 License

Educational/Research Use

## 👨‍💻 Author

MAYANK SAHU

## 🙏 Acknowledgments

- SUMO Development Team
- Stable-Baselines3 Contributors
- sumo-rl Library Maintainers

---

**Note**: This system is designed for simulation and research purposes. Real-world deployment would require extensive validation, safety testing, and regulatory approval.
