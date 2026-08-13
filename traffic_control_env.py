"""Joint SUMO-RL environment for emergency vehicle priority control."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np
import sumo_rl


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_NET_FILE = PROJECT_ROOT / "draft02.net.xml"
DEFAULT_ROUTE_FILES = (
    PROJECT_ROOT / "vtypes.rou.xml",
    PROJECT_ROOT / "traffic_dense.rou.xml",
    PROJECT_ROOT / "ambulance_s.rou.xml",
)
AMBULANCE_ID = "hero_ambulance"


class JointEmergencyTrafficEnv(gym.Env):
    """Expose both traffic lights as one Gymnasium environment.

    ``sumo_rl.SumoEnvironment(single_agent=True)`` only controls the first
    traffic light in a multi-intersection network. This wrapper keeps SUMO-RL
    in multi-agent mode, then combines the J4 and J6 observations/actions for
    Stable-Baselines3.

    A small safety shield overrides the policy while the ambulance approaches
    either junction. Emergency priority must be deterministic; PPO remains
    responsible for normal traffic flow at all other times.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        *,
        use_gui: bool = False,
        num_seconds: int = 1000,
        sumo_seed: int | str = "random",
        out_csv_name: str | None = None,
        terminate_on_ambulance: bool = False,
        sumo_warnings: bool = False,
    ) -> None:
        super().__init__()
        route_files = ",".join(str(path) for path in DEFAULT_ROUTE_FILES)
        self.sumo_env = sumo_rl.SumoEnvironment(
            net_file=str(DEFAULT_NET_FILE),
            route_file=route_files,
            out_csv_name=out_csv_name,
            use_gui=use_gui,
            num_seconds=num_seconds,
            fixed_ts=False,
            yellow_time=4,
            min_green=5,
            max_green=60,
            single_agent=False,
            reward_fn="queue",
            sumo_seed=sumo_seed,
            sumo_warnings=sumo_warnings,
        )
        self.ts_ids = tuple(self.sumo_env.ts_ids)
        if set(self.ts_ids) != {"J4", "J6"}:
            raise ValueError(f"Expected traffic lights J4 and J6, found {self.ts_ids}")

        self.action_space = gym.spaces.MultiDiscrete(
            [self.sumo_env.action_spaces(ts_id).n for ts_id in self.ts_ids]
        )

        signal_spaces = [self.sumo_env.observation_spaces(ts_id) for ts_id in self.ts_ids]
        signal_low = np.concatenate([space.low for space in signal_spaces]).astype(np.float32)
        signal_high = np.concatenate([space.high for space in signal_spaces]).astype(np.float32)
        # presence, speed, stopped, distance, and four route-location flags
        emergency_low = np.zeros(8, dtype=np.float32)
        emergency_high = np.ones(8, dtype=np.float32)
        self.observation_space = gym.spaces.Box(
            low=np.concatenate([signal_low, emergency_low]),
            high=np.concatenate([signal_high, emergency_high]),
            dtype=np.float32,
        )

        self.use_gui = use_gui
        self.terminate_on_ambulance = terminate_on_ambulance
        self._ambulance_seen = False
        self._ambulance_start_time: float | None = None
        self._ambulance_finish_time: float | None = None
        self._previous_distance = 0.0
        self._priority_overrides = 0

    @property
    def sumo(self):
        """Return the labeled TraCI connection owned by SUMO-RL."""
        return self.sumo_env.sumo

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        observations = self.sumo_env.reset(seed=seed)
        self._ambulance_seen = False
        self._ambulance_start_time = None
        self._ambulance_finish_time = None
        self._previous_distance = 0.0
        self._priority_overrides = 0
        return self._build_observation(observations), {}

    def step(
        self, action: np.ndarray
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        policy_action = np.asarray(action, dtype=np.int64).reshape(-1)
        if policy_action.size != len(self.ts_ids):
            raise ValueError(
                f"Expected {len(self.ts_ids)} actions for {self.ts_ids}, got {policy_action}"
            )

        applied_action, override = self._apply_emergency_priority(policy_action)
        action_dict = {
            ts_id: int(applied_action[index]) for index, ts_id in enumerate(self.ts_ids)
        }
        observations, _, dones, info = self.sumo_env.step(action_dict)

        ambulance = self._ambulance_state()
        reward, completed = self._compute_reward(ambulance, info)
        truncated = bool(dones["__all__"])
        terminated = bool(completed and self.terminate_on_ambulance)

        info.update(
            {
                "policy_action": policy_action.tolist(),
                "applied_action": applied_action.tolist(),
                "emergency_override": override,
                "priority_overrides": self._priority_overrides,
                "ambulance_present": ambulance["present"],
                "ambulance_road": ambulance["road"],
                "ambulance_speed": ambulance["speed"],
                "ambulance_distance": ambulance["distance"],
                "ambulance_completed": completed,
                "ambulance_start_time": self._ambulance_start_time,
                "ambulance_finish_time": self._ambulance_finish_time,
                "ambulance_duration": self.ambulance_duration,
            }
        )
        return (
            self._build_observation(observations),
            float(reward),
            terminated,
            truncated,
            info,
        )

    @property
    def ambulance_duration(self) -> float | None:
        if self._ambulance_start_time is None or self._ambulance_finish_time is None:
            return None
        return self._ambulance_finish_time - self._ambulance_start_time

    def _apply_emergency_priority(
        self, policy_action: np.ndarray
    ) -> tuple[np.ndarray, bool]:
        applied = policy_action.copy()
        ambulance = self._ambulance_state()
        if not ambulance["present"]:
            return applied, False

        road = ambulance["road"]
        index = {ts_id: idx for idx, ts_id in enumerate(self.ts_ids)}
        overridden = False

        # The ambulance turns left from north at J4 (green phase 0), then left
        # from west at J6 (green phase 1). Prepare J6 while it clears J4.
        if road == "-E2" or road.startswith(":J4"):
            overridden |= applied[index["J4"]] != 0
            overridden |= applied[index["J6"]] != 1
            applied[index["J4"]] = 0
            applied[index["J6"]] = 1
        elif road == "E3" or road.startswith(":J6"):
            overridden |= applied[index["J6"]] != 1
            applied[index["J6"]] = 1

        if overridden:
            self._priority_overrides += 1
        return applied, bool(overridden)

    def _ambulance_state(self) -> dict[str, Any]:
        if self.sumo is None:
            return {"present": False, "road": "", "speed": 0.0, "distance": 0.0}
        vehicles = self.sumo.vehicle.getIDList()
        if AMBULANCE_ID not in vehicles:
            return {"present": False, "road": "", "speed": 0.0, "distance": 0.0}
        return {
            "present": True,
            "road": self.sumo.vehicle.getRoadID(AMBULANCE_ID),
            "speed": float(self.sumo.vehicle.getSpeed(AMBULANCE_ID)),
            "distance": float(self.sumo.vehicle.getDistance(AMBULANCE_ID)),
        }

    def _compute_reward(
        self, ambulance: dict[str, Any], info: dict[str, Any]
    ) -> tuple[float, bool]:
        reward = -0.15 * float(info.get("system_total_stopped", 0.0))
        reward -= 0.03 * float(info.get("system_mean_waiting_time", 0.0))
        completed = False

        if ambulance["present"]:
            if not self._ambulance_seen:
                self._ambulance_seen = True
                self._ambulance_start_time = float(self.sumo_env.sim_step)
            progress = max(0.0, ambulance["distance"] - self._previous_distance)
            reward += 2.0 * progress
            reward -= 1.0
            if ambulance["speed"] < 1.0:
                reward -= 20.0
            self._previous_distance = ambulance["distance"]
        elif self._ambulance_seen and self._ambulance_finish_time is None:
            self._ambulance_finish_time = float(self.sumo_env.sim_step)
            reward += 250.0
            completed = True

        return reward, completed

    def _build_observation(self, observations: dict[str, np.ndarray]) -> np.ndarray:
        signal_observation = np.concatenate(
            [np.asarray(observations[ts_id], dtype=np.float32) for ts_id in self.ts_ids]
        )
        ambulance = self._ambulance_state()
        road = ambulance["road"]
        emergency_observation = np.array(
            [
                float(ambulance["present"]),
                min(ambulance["speed"] / 30.0, 1.0),
                float(ambulance["present"] and ambulance["speed"] < 1.0),
                min(ambulance["distance"] / 100.0, 1.0),
                float(road == "-E2" or road.startswith(":J4")),
                float(road == "E3"),
                float(road.startswith(":J6")),
                float(road == "E5"),
            ],
            dtype=np.float32,
        )
        return np.concatenate([signal_observation, emergency_observation]).astype(np.float32)

    def close(self) -> None:
        self.sumo_env.close()
