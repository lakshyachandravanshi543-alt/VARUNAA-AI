from flask import Flask, request, jsonify, render_template
import joblib
import os
import threading
import time
import random

app = Flask(__name__)

# Load Model and Scaler
model_path = os.path.join(os.path.dirname(__file__), 'model', 'model.joblib')
scaler_path = os.path.join(os.path.dirname(__file__), 'model', 'scaler.joblib')

if os.path.exists(model_path) and os.path.exists(scaler_path):
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
else:
    model = None
    scaler = None
    print("Warning: Model or scaler not found. Please train the model first.")

# Global state to hold the most recent physical reading and its prediction
latest_inference = {
    "raw_sensors": {"ph": 7.0, "do": 6.5, "turbidity": 5.0, "temperature": 24.0},
    "prediction": {"pollutant": "Awaiting Physical Sensor Data...", "color": "gray", "state": "Unknown", "details": "Waiting for hardware Ping", "action": "-"}
}
lock = threading.Lock()

# Highly detailed pollution mappings shared across all instances
CLASSES = {
    0: {
        "pollutant": "Clean Water / No Major Impurities Found",
        "specific_pollutants": ["None specific"],
        "state": "Liquid (Clear)",
        "color": "green",
        "details": "The AI detected normal pH, healthy dissolved oxygen, and minimal turbidity. No significant pollutants match this chemical signature.",
        "action": "Safe for standard uses. Continue basic monitoring."
    },
    1: {
        "pollutant": "Industrial Heavy Metals",
        "specific_pollutants": ["Lead (Pb)", "Arsenic (As)", "Mercury", "Cadmium", "Industrial Acids"],
        "state": "Dissolved Liquid (Toxic)",
        "color": "red",
        "details": "AI Signature Match: Extreme pH combined with elevated temperatures and slight turbidity strongly indicates industrial factory discharge containing toxic heavy metals.",
        "action": "<b>1. Source Isolation:</b> Dispatch municipal team to halt upstream factory discharge.<br><b>2. Phytoremediation:</b> Deploy Water Hyacinth (Eichhornia crassipes) or Vetiver grass along banks to naturally absorb heavy metal ions.<br><b>3. Biosorbents:</b> Disperse crushed coconut shells and sugarcane bagasse into the water column to bind with free heavy metals rapidly."
    },
    2: {
        "pollutant": "Untreated Biological Sewage",
        "specific_pollutants": ["Fecal Coliforms", "E. coli Bacteria", "Ammonia", "Raw Organic Waste"],
        "state": "Liquid & Suspended Solids",
        "color": "orange",
        "details": "AI Signature Match: Dangerously depleted oxygen combined with heavy turbidity indicates bacteria breaking down massive amounts of biological waste (feces/sewage).",
        "action": "<b>1. Artificial Aeration:</b> Deploy floating solar aerators to instantly restore Dissolved Oxygen and stop fish kills.<br><b>2. Constructed Wetlands:</b> Implement Root Zone Treatment Systems using native reeds to filter solids.<br><b>3. Bio-Augmentation:</b> Release Effective Microorganisms (EM) or Bokashi mud balls to safely accelerate the breakdown of organic sewage."
    },
    3: {
        "pollutant": "Petroleum / Oil Spill",
        "specific_pollutants": ["Crude Oil Substrates", "Diesel/Motor Oil", "Petrochemical Greases"],
        "state": "Liquid (Surface Slick)",
        "color": "blue",
        "details": "AI Signature Match: Severely blocked oxygen transfer but moderate turbidity indicates a layer of oil capping the water surface and suffocating the river.",
        "action": "<b>1. Containment Booms:</b> Deploy cheap, natural floating booms made of sugarcane bagasse or human hair mats to trap the slick.<br><b>2. Absorption:</b> Spread Coir pith (coconut fiber) across the surface to naturally soak up the petroleum.<br><b>3. Oil Skimming:</b> Physically extract the absorbed clumps before they sink."
    },
    4: {
        "pollutant": "Agricultural Fertilizer Runoff",
        "specific_pollutants": ["Nitrates", "Phosphorus", "Toxic Cyanobacteria (Algal Bloom)"],
        "state": "Dissolved Liquid / Algal Bloom",
        "color": "orange",
        "details": "AI Signature Match: Highly alkaline (basic) pH, reduced oxygen, and thick green cloudy turbidity indicates fertilizer causing extreme algal blooms.",
        "action": "<b>1. Mechanical Harvesting:</b> Skim the thick algae off the surface to restore sunlight penetration.<br><b>2. Biological Control:</b> Introduce endemic algae-eating carp species (like native Rohu) to control regrowth.<br><b>3. Repurposing:</b> Convert the harvested toxic algae into safe agricultural compost or biogas fuel."
    },
    5: {
        "pollutant": "Plastics & Municipal Solid Waste",
        "specific_pollutants": ["Macro-plastics (Bags/Bottles)", "Suspended Microplastics", "Solid Urban Rubble"],
        "state": "Solid Waste / Microplastics",
        "color": "blue",
        "details": "AI Signature Match: Normal pH and oxygen, but massive turbidity spikes indicate the presence of physical garbage and dense suspended microplastics blocking light.",
        "action": "<b>1. Physical Barriers:</b> Construct low-cost bamboo trash booms across natural river bends to trap macro-plastics.<br><b>2. Civic Engagement:</b> Organize community 'Shramdaan' (volunteer cleanups) to haul trapped waste to banks.<br><b>3. Upcycling:</b> Route extracted plastics to local road-building or brick-making enterprises."
    }
}

# --- VIRTUAL RIVER NETWORK ---
# Simulated live data for specific rivers to create a "Digital Twin" Map
network_state = {}
network_lock = threading.Lock()

VIRTUAL_RIVERS = [
    {
        "id": "ganges_1", "name": "Ganges River (Varanasi, India)", "lat": 25.3176, "lng": 82.9739,
        "base_ph": (6.5, 7.5), "base_do": (2.0, 4.0), "base_turb": (150, 250), "base_temp": (24, 28)
    },
    {
        "id": "thames_1", "name": "River Thames (London, UK)", "lat": 51.5072, "lng": -0.1276,
        "base_ph": (7.0, 8.0), "base_do": (6.0, 9.0), "base_turb": (5, 15), "base_temp": (10, 15)
    },
    {
        "id": "mississippi_1", "name": "Mississippi River (NOLA, USA)", "lat": 29.9511, "lng": -90.0715,
        "base_ph": (6.8, 7.8), "base_do": (5.0, 7.0), "base_turb": (60, 120), "base_temp": (20, 26)
    },
    {
        "id": "rhine_1", "name": "Rhine River (Cologne, Germany)", "lat": 50.9375, "lng": 6.9603,
        "base_ph": (7.2, 8.2), "base_do": (7.0, 10.0), "base_turb": (2, 8), "base_temp": (12, 18)
    }
]

def run_inference(ph, do, turbidity, temp):
    """Helper to run the ML model."""
    if not model or not scaler:
        return CLASSES.get(0)
    features = [float(ph), float(do), float(turbidity), float(temp)]
    features_scaled = scaler.transform([features])
    prediction = model.predict(features_scaled)[0]
    return CLASSES.get(int(prediction), CLASSES[0])

def simulate_network():
    """Background thread simulating live sensor data for the virtual rivers."""
    while True:
        updates = []
        for rv in VIRTUAL_RIVERS:
            # Generate baseline fluctuating data
            ph = round(random.uniform(*rv['base_ph']), 2)
            do = round(random.uniform(*rv['base_do']), 2)
            turb = round(random.uniform(*rv['base_turb']), 2)
            temp = round(random.uniform(*rv['base_temp']), 2)
            
            # Very rarely, simulate an extreme anomaly so the map changes dynamically
            if random.random() < 0.05: # 5% chance of anomaly per tick
                event_type = random.choice(['oil', 'metal', 'sewage'])
                if event_type == 'oil':
                    do = round(random.uniform(0.5, 2.0), 2)
                    turb = round(random.uniform(40, 80), 2)
                elif event_type == 'metal':
                    ph = round(random.uniform(2.0, 4.0), 2)
                    temp = round(random.uniform(28, 35), 2)
                elif event_type == 'sewage':
                    do = round(random.uniform(0.5, 2.0), 2)
                    turb = round(random.uniform(200, 300), 2)

            # --- Context-Aware AI (Weather API Simulation) ---
            weather_state = random.choices(['Clear', 'Cloudy', 'Heavy Rainfall'], weights=[70, 20, 10])[0]
            
            if weather_state == 'Heavy Rainfall':
                # Natural rain causes mud runoff (high turbidity) naturally, masking normal levels
                turb = round(random.uniform(150, 400), 2)
            
            prediction = run_inference(ph, do, turb, temp)
            
            # If the AI detects a turbidity spike caused by Rain, it uses Context-Aware Overrides
            context_alert = None
            if weather_state == 'Heavy Rainfall' and prediction['color'] in ['orange', 'blue']:
                # Override the AI prediction because it knows it is just natural rain mud!
                prediction = {
                    "pollutant": "Natural Mud Runoff (Rain Induced)",
                    "specific_pollutants": ["Silt", "Natural Riverbank Sediment", "Clay Particles"],
                    "state": "Turbid Liquid (Safe)",
                    "color": "green",
                    "details": f"Context-Aware AI Triggered: Extreme turbidity ({turb} NTU) detected. However, Weather Integration confirms 'Heavy Rainfall'. False alarm suppressed.",
                    "action": "No action needed. Water cloudiness is from natural rain sediment, not biological sewage."
                }
                context_alert = "🌧️ Weather API Override Active"
            elif weather_state == 'Heavy Rainfall':
                context_alert = "🌧️ Raining (Baselines Adjusted)"

            updates.append({
                "id": rv["id"],
                "name": rv["name"],
                "lat": rv["lat"],
                "lng": rv["lng"],
                "weather": context_alert,
                "raw_sensors": {"ph": ph, "do": do, "turbidity": turb, "temperature": temp},
                "prediction": prediction
            })
            
        with network_lock:
            global network_state
            network_state = updates
            
        time.sleep(5) # Update network every 5 seconds

# Start the simulation thread
sim_thread = threading.Thread(target=simulate_network, daemon=True)
sim_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/network_state', methods=['GET'])
def get_network_state():
    """Endpoint to get live simulated data for all virtual buoys globally."""
    with network_lock:
        return jsonify(network_state)

@app.route('/api/live', methods=['GET'])
def get_live_data():
    """Endpoint for the dashboard to poll the most recent PHYSICAL data automatically"""
    with lock:
        return jsonify(latest_inference)

@app.route('/api/predict', methods=['POST'])
def predict():
    """Endpoint receiving single physical data pings (or manual tests)"""
    global latest_inference
    data = request.json
    try:
        ph = float(data.get('ph', 7.0))
        do = float(data.get('do', 6.0))
        turbidity = float(data.get('turbidity', 5.0))
        temperature = float(data.get('temperature', 24.0))
        
        result_payload = run_inference(ph, do, turbidity, temperature)
        
        # Update global state for Live IoT streaming
        with lock:
            latest_inference = {
                "raw_sensors": {"ph": ph, "do": do, "turbidity": turbidity, "temperature": temperature},
                "prediction": result_payload
            }
        
        return jsonify(result_payload)
        
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
