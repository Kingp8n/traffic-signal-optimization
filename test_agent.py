import gymnasium as gym
from stable_baselines3 import PPO
import sumo_rl
import traci
import os

def test_model():
    print("🚀 Loading Trained Model...")
    csv_dir = os.path.join("data", "evaluation_logs", "basic")
    os.makedirs(csv_dir, exist_ok=True)
    
    # 1. Setup the Environment
    env = sumo_rl.SumoEnvironment(
        net_file="draft02.net.xml",
        route_file="vtypes.rou.xml,draft02.rou.xml,ambulance.rou.xml",
        out_csv_name=os.path.join(csv_dir, "test_results"),
        use_gui=True,              
        num_seconds=600,
        fixed_ts=False,            
        yellow_time=4,
        min_green=5,
        max_green=60,
        single_agent=True
    )

    # 2. Load the Agent
    model_path = os.path.join("models", "rl", "my_traffic_agent.zip")
    
    # Check if the main zip exists, otherwise try the backup
    if not os.path.exists(model_path):
        print(f"⚠️ '{model_path}' not found. Checking models folder...")
        # Try to find the latest checkpoint in 'models/'
        if os.path.exists("models"):
            files = [f for f in os.listdir("models") if f.endswith(".zip")]
            if files:
                # Find the one with the highest step count
                latest = max(files, key=lambda x: int(x.split('_')[2])) 
                model_path = os.path.join("models", latest)
                print(f"🔄 Found checkpoint: {model_path}")
            else:
                print("❌ No models found! Did training finish?")
                return

    model = PPO.load(model_path)
    print(f"✅ Model loaded from: {model_path}")

    # 3. Handle Reset (Auto-detect 1 vs 2 values)
    reset_result = env.reset()
    if isinstance(reset_result, tuple):
        obs = reset_result[0]
    else:
        obs = reset_result
    
    done = False
    ambulance_start = 0
    ambulance_end = 0
    
    print("🚦 Starting AI Evaluation Run...")
    
    try:
        traci.gui.setSchema("View #0", "real world")
    except:
        pass

    while not done:
        # Predict Action
        action, _ = model.predict(obs, deterministic=True)
        
        # 4. Handle Step (Auto-detect 4 vs 5 values) -- THE FIX
        step_result = env.step(action)
        
        if len(step_result) == 5:
            # New Gym API: (obs, reward, terminated, truncated, info)
            obs, reward, terminated, truncated, info = step_result
            done = terminated or truncated
        else:
            # Old Gym API: (obs, reward, done, info)
            obs, reward, done, info = step_result
        
        # Track Ambulance
        try:
            veh_list = traci.vehicle.getIDList()
            if "hero_ambulance" in veh_list:
                if ambulance_start == 0:
                    ambulance_start = traci.simulation.getTime()
                    print(f"🚑 Ambulance entered at: {ambulance_start}")
            
            if ambulance_start > 0 and "hero_ambulance" not in veh_list and ambulance_end == 0:
                ambulance_end = traci.simulation.getTime()
                duration = ambulance_end - ambulance_start
                print(f"🏁 AI Agent Finished! Total Time: {duration} seconds")
                # We can stop early if the ambulance is done, or let it finish
                # done = True 
        except:
            pass

    env.close()

if __name__ == "__main__":
    test_model()
