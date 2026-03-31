# Multi agent traffic signal optimization system for minimal vehicle congestion

# 1. High-Level System Architecture

```text
Camera / Sensors
        │
        ▼
Computer Vision Pipeline
(vehicle detection & classification)
        │
        ▼
Traffic State Builder
(converts detections → structured features)
        │
        ▼
Multi-Agent RL Controller
(each intersection = agent)
        │
        ▼
Signal Timing Decision
        │
        ▼
Traffic Signal Controller API
        │
        ▼
Physical Traffic Lights
```

For **training**, the real system is replaced by a **traffic simulator**.

Typical simulator used:
**SUMO**

---

# 2. System Components

## 2.1 Traffic State Extraction Layer

This converts raw sensor data into a **numerical state vector** for RL.

Inputs:

* Camera feeds
* Loop sensors
* GPS vehicle data

Computer vision models detect:

* vehicle count
* vehicle types
* queue length
* emergency vehicles

Example detection models:

* **YOLOv8**
* **Mask R-CNN**

Output example:

```json
{
  "intersection_id": "I23",
  "lane_1_vehicle_count": 15,
  "lane_2_vehicle_count": 12,
  "queue_length": 20,
  "ambulance_detected": false,
  "heavy_vehicle_count": 3
}
```

---

# 3. Reinforcement Learning Model Design

This is the **core of the system**.

Each intersection = **agent**.

Algorithms commonly used:

* **Deep Q-Network**
* **Proximal Policy Optimization**
* **Multi-Agent Reinforcement Learning**

---

# 4. RL Environment Definition

Reinforcement learning requires defining:

```
State
Action
Reward
Environment
Policy
```

---

# 5. State Space (Traffic State)

The **state vector** represents current traffic conditions.

Example:

```text
S = [
vehicle_count_lane_1
vehicle_count_lane_2
vehicle_count_lane_3
vehicle_count_lane_4
queue_length
average_waiting_time
current_signal_phase
neighbor_intersection_flow
time_of_day
rush_hour_flag
ambulance_flag
]
```

Example numeric vector:

```text
[12, 8, 5, 15, 20, 18, 2, 7, 18.5, 1, 0]
```

Explanation:

| Feature        | Meaning                                    |
| -------------- | ------------------------------------------ |
| vehicle count  | cars waiting per lane                      |
| queue length   | total queued vehicles                      |
| neighbor flow  | vehicles entering from nearby intersection |
| rush hour      | 0 or 1                                     |
| ambulance flag | emergency detected                         |

Typical **state dimension**

```
20–50 features
```

---

# 6. Action Space

Actions represent **signal changes**.

Example action space:

```text
A0 → keep current signal
A1 → switch to north-south green
A2 → switch to east-west green
A3 → extend green by 10 seconds
A4 → give priority to emergency lane
```

Example discrete actions:

```
0–4
```

More advanced systems use **continuous actions**.

Example:

```
green_time = 10–60 seconds
```

---

# 7. Reward Function (Most Important)

The reward tells the model **what good traffic flow means**.

Common reward formula:

```
Reward = -(total_waiting_time + queue_length + congestion)
```

Example:

```
R = - (0.5 * waiting_time + 0.3 * queue_length + 0.2 * delay)
```

Additional rewards:

Emergency vehicle priority:

```
+50 if ambulance cleared quickly
```

Congestion penalty:

```
-100 if queue exceeds threshold
```

Goal:

```
maximize traffic throughput
minimize waiting time
```

---

# 8. Multi-Intersection Coordination

Because intersections interact, agents share information.

Road network is represented as a **graph**.

Nodes = intersections
Edges = roads

Example:

```
A ─── B ─── C
│
D
```

Agents exchange data:

```
cars leaving A → entering B
```

State augmentation:

```
neighbor_queue_lengths
neighbor_signal_phase
```

This allows coordination.

---

# 9. Data Requirements

You need **three main datasets**.

---

## 9.1 Historical Traffic Data

Needed to initialize the simulator.

Fields:

| field           | description       |
| --------------- | ----------------- |
| timestamp       | time              |
| intersection_id | location          |
| vehicle_count   | vehicles per lane |
| avg_speed       | traffic speed     |
| queue_length    | waiting vehicles  |

Typical resolution:

```
5–60 seconds
```

---

## 9.2 Road Network Data

Required for simulation.

Fields:

| feature           | example |
| ----------------- | ------- |
| road length       | 120m    |
| lanes             | 3       |
| speed limit       | 50 km/h |
| intersection type | 4-way   |

Source:

* OpenStreetMap

---

## 9.3 Camera Training Data

Used for vehicle detection.

Annotations needed:

```
car
bus
truck
bike
ambulance
```

Datasets:

* UA-DETRAC
* Cityscapes
* BDD100K

---

# 10. Training Pipeline

Training uses **simulation first**.

Steps:

### Step 1

Build traffic network in

**SUMO**

---

### Step 2

Generate traffic flows.

Example:

```
rush hour traffic
normal traffic
accident scenarios
```

---

### Step 3

Define RL environment.

Observation:

```
traffic state
```

Action:

```
signal change
```

Reward:

```
traffic delay reduction
```

---

### Step 4

Train RL model.

Frameworks:

* PyTorch
* Stable Baselines3
* Ray RLlib

Training loop:

```
observe state
take action
simulate traffic
calculate reward
update policy
```

---

# 11. Neural Network Architecture

Example policy network:

Input:

```
state vector (30 features)
```

Architecture:

```
Input Layer (30)

Dense 128
ReLU

Dense 128
ReLU

Dense 64
ReLU

Output Layer (actions)
Softmax
```

---

# 12. Multi-Agent Training Architecture

Training setup:

```
Agent 1 (intersection A)
Agent 2 (intersection B)
Agent 3 (intersection C)
```

Shared parameters:

```
shared policy network
```

Benefits:

* faster training
* coordination

---

# 13. Real-Time Deployment Architecture

Production system:

```
Cameras
   │
Edge Computer
   │
Vehicle detection model
   │
Traffic State API
   │
Central RL Controller
   │
Traffic Signal Controller
```

Latency requirement:

```
<1 second decision time
```

---

# 14. Evaluation Metrics

To measure performance:

| metric               | meaning               |
| -------------------- | --------------------- |
| Average waiting time | seconds per vehicle   |
| Queue length         | number of cars        |
| Travel time          | time to cross network |
| Throughput           | vehicles/hour         |

---

# 15. Hardware Requirements

Edge hardware near intersection:

* GPU edge device (Jetson)
* camera feed processing

Central training server:

* GPU cluster

---

# 16. Expected Improvement

Research systems report:

```
20–40% reduction in traffic delay
```

compared to fixed traffic lights.

---

💡 **Most important takeaway**

This project is actually a **Multi-Agent Reinforcement Learning problem on a traffic graph**, where agents must **cooperate to minimize global congestion**.
