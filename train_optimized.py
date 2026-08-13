"""Train the joint J4/J6 emergency-priority PPO controller."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch.nn as nn
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from traffic_control_env import JointEmergencyTrafficEnv


PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_DIR = PROJECT_ROOT / "models" / "optimized"
LOG_DIR = PROJECT_ROOT / "data" / "training_logs" / "optimized"


def make_training_env() -> JointEmergencyTrafficEnv:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return JointEmergencyTrafficEnv(
        use_gui=False,
        num_seconds=1000,
        sumo_seed="random",
        out_csv_name=str(LOG_DIR / "joint_train"),
        terminate_on_ambulance=False,
    )


def train(total_timesteps: int = 100_000) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = MODEL_DIR / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    env = DummyVecEnv([make_training_env])
    env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.0)

    checkpoint_callback = CheckpointCallback(
        save_freq=10_000,
        save_path=str(checkpoint_dir),
        name_prefix="joint_traffic_agent",
        save_vecnormalize=True,
    )
    policy_kwargs = dict(
        activation_fn=nn.Tanh,
        net_arch=dict(pi=[256, 256], vf=[256, 256]),
    )
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        gamma=0.995,
        gae_lambda=0.95,
        n_steps=2048,
        batch_size=128,
        ent_coef=0.01,
        policy_kwargs=policy_kwargs,
        device="cpu",
    )

    print(f"Starting joint J4/J6 training for {total_timesteps:,} timesteps...")
    model.learn(total_timesteps=total_timesteps, callback=checkpoint_callback)
    model.save(MODEL_DIR / "joint_traffic_agent")
    env.save(MODEL_DIR / "vec_normalize.pkl")
    env.close()
    print(f"Model saved to {MODEL_DIR / 'joint_traffic_agent.zip'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timesteps", type=int, default=100_000)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(args.timesteps)
