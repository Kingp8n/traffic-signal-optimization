"""Evaluate the joint emergency-priority PPO controller."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from traffic_control_env import JointEmergencyTrafficEnv


PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_DIR = PROJECT_ROOT / "models" / "optimized"
RESULT_DIR = PROJECT_ROOT / "results" / "evaluation"


def evaluate(
    *,
    episodes: int = 1,
    seed: int = 0,
    use_gui: bool = True,
    delay: float = 0.03,
) -> list[dict]:
    model_path = MODEL_DIR / "joint_traffic_agent.zip"
    normalize_path = MODEL_DIR / "vec_normalize.pkl"
    if not model_path.exists() or not normalize_path.exists():
        raise FileNotFoundError(
            "Joint model is missing. Run `python3 train_optimized.py` first."
        )

    raw_env = JointEmergencyTrafficEnv(
        use_gui=use_gui,
        num_seconds=1000,
        sumo_seed=seed,
        terminate_on_ambulance=True,
    )
    env = DummyVecEnv([lambda: raw_env])
    env = VecNormalize.load(normalize_path, env)
    env.training = False
    env.norm_reward = False
    model = PPO.load(model_path, device="cpu")

    results: list[dict] = []
    try:
        for episode in range(episodes):
            episode_seed = seed + episode
            env.seed(episode_seed)
            observation = env.reset()
            done = False
            final_info: dict = {}
            max_wait_by_vehicle: dict[str, float] = {}

            print(f"Episode {episode + 1}/{episodes}, SUMO seed {episode_seed}")
            while not done:
                action, _ = model.predict(observation, deterministic=True)
                observation, _, dones, infos = env.step(action)
                done = bool(dones[0])
                final_info = infos[0]

                if raw_env.sumo is not None:
                    for vehicle_id in raw_env.sumo.vehicle.getIDList():
                        if vehicle_id != "hero_ambulance":
                            waiting = raw_env.sumo.vehicle.getAccumulatedWaitingTime(vehicle_id)
                            max_wait_by_vehicle[vehicle_id] = max(
                                waiting, max_wait_by_vehicle.get(vehicle_id, 0.0)
                            )
                if use_gui and delay > 0:
                    time.sleep(delay)

            duration = final_info.get("ambulance_duration")
            result = {
                "episode": episode + 1,
                "seed": episode_seed,
                "success": bool(final_info.get("ambulance_completed")),
                "ambulance_duration_seconds": duration,
                "civilian_average_wait_seconds": (
                    sum(max_wait_by_vehicle.values()) / len(max_wait_by_vehicle)
                    if max_wait_by_vehicle
                    else 0.0
                ),
                "priority_overrides": final_info.get("priority_overrides", 0),
                "simulation_finish_time": final_info.get("ambulance_finish_time"),
            }
            results.append(result)
            status = "PASS" if result["success"] else "FAIL"
            print(
                f"{status}: ambulance={duration}s, "
                f"civilian average wait={result['civilian_average_wait_seconds']:.2f}s"
            )
    finally:
        env.close()

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULT_DIR / "optimized_evaluation.json"
    output_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Results saved to {output_path}")
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--delay", type=float, default=0.03)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    evaluation = evaluate(
        episodes=args.episodes,
        seed=args.seed,
        use_gui=not args.headless,
        delay=args.delay,
    )
    if not all(result["success"] for result in evaluation):
        raise SystemExit(1)
