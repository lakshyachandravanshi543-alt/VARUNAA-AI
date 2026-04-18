import requests
import time
import random
import json

# Your Flask Server URL
FLASK_SERVER = "http://127.0.0.1:5000/api/predict"

def generate_hardware_anomaly():
    """Generates drifting hardware values simulating a moving river buoy"""
    
    # We'll cycle through scenarios to see the dashboard change.
    scenarios = [
        # 1. Clean Water Flow
        {"ph": round(random.uniform(7.0, 7.5), 1), "do": round(random.uniform(7.0, 8.5), 1), "turbidity": round(random.uniform(2.0, 8.0), 1), "temperature": round(random.uniform(22.0, 24.0), 1)},
        # 2. Heavy Metal Discharge spikes
        {"ph": round(random.uniform(2.5, 4.0), 1), "do": round(random.uniform(5.0, 6.0), 1), "turbidity": round(random.uniform(15.0, 25.0), 1), "temperature": round(random.uniform(28.0, 31.0), 1)},
        # 3. Oil Slick passing by
        {"ph": round(random.uniform(6.5, 7.5), 1), "do": round(random.uniform(1.0, 2.5), 1), "turbidity": round(random.uniform(40.0, 60.0), 1), "temperature": round(random.uniform(23.0, 25.0), 1)},
        # 4. Dense Sewage/Garbage flow
        {"ph": round(random.uniform(6.0, 7.0), 1), "do": round(random.uniform(0.5, 2.0), 1), "turbidity": round(random.uniform(150.0, 250.0), 1), "temperature": round(random.uniform(24.0, 26.0), 1)}
    ]
    
    # Pick a random scenario to simulate a sudden water quality change
    return random.choice(scenarios)

print("Starting IoT River Buoy Simulator...")
print("Turn on the 'Enable Live IoT Sensor Stream' toggle in your dashboard!")

while True:
    try:
        # Simulate hardware gathering physical data
        physical_data = generate_hardware_anomaly()
        
        # Send to server just like the ESP32 would
        print(f"\n[Hardware] Submitting sensor ping: {physical_data}")
        response = requests.post(
            FLASK_SERVER, 
            headers={"Content-Type": "application/json"},
            data=json.dumps(physical_data)
        )
        
        if response.status_code == 200:
            print("[Backend] Successfully processed by AI Engine.")
        else:
            print(f"[Backend] Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n[Hardware] Connection failed. Is the Flask app running?")
        
    # Wait 8 seconds before sending the next river ping
    time.sleep(8)
