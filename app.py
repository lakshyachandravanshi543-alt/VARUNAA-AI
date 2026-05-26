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
        "pollutant": "Clean Water / Baseline Condition",
        "specific_pollutants": ["Dissolved Oxygen (O₂)", "Trace Carbonates (CO₃²⁻)", "Dissolved Silica (SiO₂)"],
        "state": "Liquid (Clear)",
        "color": "green",
        "details": "The system detected optimal pH, healthy dissolved oxygen, and minimal turbidity. Water parameters remain within normal baseline ranges for freshwater ecosystems. Dissolved oxygen levels support robust respiration across sensitive aquatic trophic levels.",
        "action": "Maintain routine baseline surveillance. Protect riparian vegetation to sustain thermal insulation and natural filtration gradients.",
        "chemical_definition": "Natural H₂O containing balanced dissolved gases and trace mineral carbonates. No abnormal synthetic or heavy organic pollutant signatures are detected.",
        "threshold": "DO > 5.0 mg/L, Turbidity < 10 NTU, Lead < 0.01 mg/L"
    },
    1: {
        "pollutant": "Industrial Heavy Metal Bioaccumulation",
        "specific_pollutants": ["Lead (Pb²⁺)", "Arsenic (As³⁺)", "Cadmium (Cd²⁺)", "Mercury (Hg²⁺)"],
        "state": "Dissolved Ions (Highly Toxic)",
        "color": "red",
        "details": "System alert: Extreme pH deviation coupled with thermal discharge indicates unmitigated industrial effluent. Highly toxic metal ions represent severe bioaccumulation risks for trophic networks.",
        "action": "<b>1. Source Containment:</b> Dispatch compliance enforcement to locate and plug upstream industrial discharges.<br><b>2. Phytoremediation:</b> Deploy Vetiver Grass (Chrysopogon zizanioides) and Water Hyacinth (Eichhornia crassipes) to extract dissolved cations via rhizofiltration.<br><b>3. Active Sorption:</b> Apply activated bio-char filters along channel bottlenecks to bind free metal ions.",
        "chemical_definition": "Divalent and trivalent metallic cations (e.g., Pb²⁺, As³⁺, Cd²⁺). These heavy metals inhibit key cellular enzymes, disrupt osmotic regulation, and bioaccumulate exponentially in aquatic fatty tissues, leading to systemic neurotoxicity and reproductive failure in teleost fish.",
        "threshold": "Pb < 0.01 mg/L, As < 0.01 mg/L, Cd < 0.003 mg/L"
    },
    2: {
        "pollutant": "Untreated Organic Sewage & Pathogens",
        "specific_pollutants": ["Ammonia (NH₃)", "Ammonium (NH₄⁺)", "Hydrogen Sulfide (H₂S)", "Fecal Coliforms"],
        "state": "Liquid & Suspended Organic Matter",
        "color": "orange",
        "details": "Critical signature: Depleted dissolved oxygen combined with high turbidity indicates heavy biological loading. Bacterial respiration is consuming available oxygen faster than atmospheric re-aeration can replenish it.",
        "action": "<b>1. Forced Aeration:</b> Install floating mechanical solar-powered aerators to break the water interface and inject oxygen.<br><b>2. Biological Remediation:</b> Disperse nitrifying bacterial inoculants (e.g., Nitrosomonas) to accelerate organic digestion.<br><b>3. Constructed Wetlands:</b> Route flows through reed beds (Typha angustifolia) for natural sedimentation and nutrient uptake.",
        "chemical_definition": "Nitrogenous organic wastes and dissolved ammonia (NH₃). The biodegradation of carbonaceous waste by heterotrophic bacteria consumes dissolved oxygen (DO), inducing acute localized hypoxia. High ammonia (NH₃) damages fish gills, limits oxygen-binding efficiency, and causes asphyxiation.",
        "threshold": "NH₃ < 0.5 mg/L, Biochemical Oxygen Demand (BOD) < 3.0 mg/L"
    },
    3: {
        "pollutant": "Petrochemical Hydrocarbon Slick",
        "specific_pollutants": ["Benzene (C₆H₆)", "Toluene (C₇H₈)", "Polycyclic Aromatic Hydrocarbons (PAHs)"],
        "state": "Liquid (Surface LNAPL Film)",
        "color": "blue",
        "details": "Inference alert: Normal pH but depressed oxygen transfer and moderate turbidity indicates a hydrophobic oil barrier at the air-water interface, suffocating benthic and pelagic life.",
        "action": "<b>1. Hydrophobic Booming:</b> Deploy floating containment barriers packed with agricultural waste (sugarcane bagasse) to trap the slick.<br><b>2. Mechanical Skimming:</b> Deploy drum skimmers to extract the accumulated surface layer.<br><b>3. Bioremediation:</b> Inoculate with hydrocarbonoclastic microbes (e.g., Alcanivorax) to metabolize volatile organics.",
        "chemical_definition": "Light Non-Aqueous Phase Liquids (LNAPLs) consisting of volatile aromatic hydrocarbons (C₆H₆, C₇H₈) and heavy PAHs. This oil film forms a physical barrier that stops atmospheric oxygen exchange. Volatile aromatics are highly mutagenic, causing chromosomal damage in aquatic organisms.",
        "threshold": "Total Petroleum Hydrocarbons (TPH) < 0.1 mg/L"
    },
    4: {
        "pollutant": "Agricultural Eutrophication Runoff",
        "specific_pollutants": ["Nitrates (NO₃⁻)", "Orthophosphates (PO₄³⁻)", "Microcystin Cyanotoxins"],
        "state": "Dissolved Nutrients & Cyanobacteria",
        "color": "orange",
        "details": "AI Signature: Highly alkaline pH, low dissolved oxygen, and green-cloudy turbidity indicating a severe nitrogen/phosphorus stimulated algal bloom.",
        "action": "<b>1. Algicide Application:</b> Apply trace copper sulfate (CuSO₄) or hydrogen peroxide under strict dosage to lyse cyanobacteria.<br><b>2. Biomass Skimming:</b> Physically harvest surface algal mats to prevent mass decay and subsequent hypoxia.<br><b>3. Buffer Installation:</b> Establish riparian vetiver grass buffer zones along agricultural fields to absorb fertilizer runoff.",
        "chemical_definition": "Soluble nitrates (NO₃⁻) and orthophosphates (PO₄³⁻). Excessive loading of these limiting nutrients causes rapid multiplication of photosynthetic cyanobacteria (eutrophication). The resulting thick canopy blocks sunlight, stopping deep photosynthesis. The subsequent decay of dead algae consumes all remaining DO, causing mass mortality.",
        "threshold": "NO₃⁻ < 10.0 mg/L, PO₄³⁻ < 0.1 mg/L"
    },
    5: {
        "pollutant": "Municipal Plastic & Suspended Solids",
        "specific_pollutants": ["Microplastics (PE / PET / PP)", "Suspended Silt", "Anthropogenic Macro-debris"],
        "state": "Particulate Suspended Solids",
        "color": "blue",
        "details": "System alert: Normal chemical variables but massive turbidity spikes point to heavy physical debris and microplastics blocking light and degrading benthic habitats.",
        "action": "<b>1. Passive Collection:</b> Construct floating bamboo or mesh trash booms across natural bends to catch macroplastics.<br><b>2. Sedimentation Basins:</b> Create upstream settling ponds to drop heavy silts out of suspension.<br><b>3. Community Interventions:</b> Implement trash tracking and route collected wastes to regional polymer recycling hubs.",
        "chemical_definition": "Polyethylene (PE), Polyethylene Terephthalate (PET), and Polypropylene (PP) micro-fragments. Suspended solids block sunlight penetration, halting primary production. Microparticles clog the gills of filter-feeding species, causing mechanical damage, asphyxiation, and intestinal blockages.",
        "threshold": "Total Suspended Solids (TSS) < 25.0 mg/L"
    }
}

# --- VIRTUAL RIVER NETWORK ---
network_state = {}
network_lock = threading.Lock()

VIRTUAL_RIVERS = [
    {
        "id": "nile", "name": "Nile River, Egypt", "lat": 30.0444, "lng": 31.2357,
        "base_ph": (7.8, 8.4), "base_do": (5.5, 7.5), "base_turb": (15, 45), "base_temp": (22, 28)
    },
    {
        "id": "rhine", "name": "Rhine River, Europe", "lat": 50.9375, "lng": 6.9603,
        "base_ph": (7.6, 8.2), "base_do": (8.0, 10.5), "base_turb": (5, 15), "base_temp": (11, 17)
    },
    {
        "id": "thames", "name": "Thames River, UK", "lat": 51.5074, "lng": -0.1278,
        "base_ph": (7.4, 8.1), "base_do": (7.0, 9.5), "base_turb": (10, 30), "base_temp": (10, 16)
    }
]

def run_inference(ph, do, turbidity, temp):
    """Helper to run the ML model."""
    if not model or not scaler:
        return CLASSES.get(0)
    import pandas as pd
    features = pd.DataFrame(
        [[float(ph), float(do), float(turbidity), float(temp)]], 
        columns=['ph', 'do', 'turbidity', 'temperature']
    )
    features_scaled = scaler.transform(features)
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
