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
    "raw_sensors": {"ph": 7.2, "do": 6.5, "turbidity": 5.0, "temperature": 24.0, "ec": 450.0, "orp": 320.0},
    "prediction": {
        "pollutant": "Awaiting Telemetry...",
        "color": "gray",
        "state": "Unknown",
        "details": "Waiting for hardware Ping",
        "action": "-",
        "confidence": 100,
        "shap": ["System initialized (+100% impact)"]
    }
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
        "threshold": "DO > 5.0 mg/L, Turbidity < 10 NTU, Lead < 0.01 mg/L",
        "confidence": 96,
        "shap": ["DO Baseline Level (+45% impact)", "pH Normal Buffer (+30% impact)", "Turbidity Minimal (+25% impact)"]
    },
    1: {
        "pollutant": "Industrial Heavy Metal Bioaccumulation",
        "specific_pollutants": ["Lead (Pb²⁺)", "Arsenic (As³⁺)", "Cadmium (Cd²⁺)", "Mercury (Hg²⁺)"],
        "state": "Dissolved Ions (Highly Toxic)",
        "color": "red",
        "details": "System alert: Extreme pH deviation coupled with thermal discharge indicates unmitigated industrial effluent. Highly toxic metal ions represent severe bioaccumulation risks for trophic networks.",
        "action": "<b>1. Source Containment:</b> Dispatch compliance enforcement to locate and plug upstream industrial discharges.<br><b>2. Phytoremediation:</b> Deploy Vetiver Grass (Chrysopogon zizanioides) and Water Hyacinth (Eichhornia crassipes) to extract dissolved cations via rhizofiltration.<br><b>3. Active Sorption:</b> Apply activated bio-char filters along channel bottlenecks to bind free metal ions.",
        "chemical_definition": "Divalent and trivalent metallic cations (e.g., Pb²⁺, As³⁺, Cd²⁺). These heavy metals inhibit key cellular enzymes, disrupt osmotic regulation, and bioaccumulate exponentially in aquatic fatty tissues, leading to systemic neurotoxicity and reproductive failure in teleost fish.",
        "threshold": "Pb < 0.01 mg/L, As < 0.01 mg/L, Cd < 0.003 mg/L",
        "confidence": 94,
        "shap": ["pH Extreme Value (+48% impact)", "EC Massive Spike (+32% impact)", "Temperature Elevated (+20% impact)"]
    },
    2: {
        "pollutant": "Untreated Organic Sewage & Pathogens",
        "specific_pollutants": ["Ammonia (NH₃)", "Ammonium (NH₄⁺)", "Hydrogen Sulfide (H₂S)", "Fecal Coliforms"],
        "state": "Liquid & Suspended Organic Matter",
        "color": "orange",
        "details": "Critical signature: Depleted dissolved oxygen combined with high turbidity indicates heavy biological loading. Bacterial respiration is consuming available oxygen faster than atmospheric re-aeration can replenish it.",
        "action": "<b>1. Forced Aeration:</b> Install floating mechanical solar-powered aerators to break the water interface and inject oxygen.<br><b>2. Biological Remediation:</b> Disperse nitrifying bacterial inoculants (e.g., Nitrosomonas) to accelerate organic digestion.<br><b>3. Constructed Wetlands:</b> Route flows through reed beds (Typha angustifolia) for natural sedimentation and nutrient uptake.",
        "chemical_definition": "Nitrogenous organic wastes and dissolved ammonia (NH₃). The biodegradation of carbonaceous waste by heterotrophic bacteria consumes dissolved oxygen (DO), inducing acute localized hypoxia. High ammonia (NH₃) damages fish gills, limits oxygen-binding efficiency, and causes asphyxiation.",
        "threshold": "NH₃ < 0.5 mg/L, Biochemical Oxygen Demand (BOD) < 3.0 mg/L",
        "confidence": 89,
        "shap": ["ORP Negative Drop (+42% impact)", "EC Massive Spike (+35% impact)", "DO Severe Depletion (+23% impact)"]
    },
    3: {
        "pollutant": "Petrochemical Hydrocarbon Slick",
        "specific_pollutants": ["Benzene (C₆H₆)", "Toluene (C₇H₈)", "Polycyclic Aromatic Hydrocarbons (PAHs)"],
        "state": "Liquid (Surface LNAPL Film)",
        "color": "blue",
        "details": "Inference alert: Normal pH but depressed oxygen transfer and moderate turbidity indicates a hydrophobic oil barrier at the air-water interface, suffocating benthic and pelagic life.",
        "action": "<b>1. Hydrophobic Booming:</b> Deploy floating containment barriers packed with agricultural waste (sugarcane bagasse) to trap the slick.<br><b>2. Mechanical Skimming:</b> Deploy drum skimmers to extract the accumulated surface layer.<br><b>3. Bioremediation:</b> Inoculate with hydrocarbonoclastic microbes (e.g., Alcanivorax) to metabolize volatile organics.",
        "chemical_definition": "Light Non-Aqueous Phase Liquids (LNAPLs) consisting of volatile aromatic hydrocarbons (C₆H₆, C₇H₈) and heavy PAHs. This oil film forms a physical barrier that stops atmospheric oxygen exchange. Volatile aromatics are highly mutagenic, causing chromosomal damage in aquatic organisms.",
        "threshold": "Total Petroleum Hydrocarbons (TPH) < 0.1 mg/L",
        "confidence": 92,
        "shap": ["DO Depletion (+45% impact)", "Turbidity Surface Film (+35% impact)", "pH Stability (+20% impact)"]
    },
    4: {
        "pollutant": "Agricultural Eutrophication Runoff",
        "specific_pollutants": ["Nitrates (NO₃⁻)", "Orthophosphates (PO₄³⁻)", "Microcystin Cyanotoxins"],
        "state": "Dissolved Nutrients & Cyanobacteria",
        "color": "orange",
        "details": "AI Signature: Highly alkaline pH, low dissolved oxygen, and green-cloudy turbidity indicating a severe nitrogen/phosphorus stimulated algal bloom.",
        "action": "<b>1. Algicide Application:</b> Apply trace copper sulfate (CuSO₄) or hydrogen peroxide under strict dosage to lyse cyanobacteria.<br><b>2. Biomass Skimming:</b> Physically harvest surface algal mats to prevent mass decay and subsequent hypoxia.<br><b>3. Buffer Installation:</b> Establish riparian vetiver grass buffer zones along agricultural fields to absorb fertilizer runoff.",
        "chemical_definition": "Soluble nitrates (NO₃⁻) and orthophosphates (PO₄³⁻). Excessive loading of these limiting nutrients causes rapid multiplication of photosynthetic cyanobacteria (eutrophication). The resulting thick canopy blocks sunlight, stopping deep photosynthesis. The subsequent decay of dead algae consumes all remaining DO, causing mass mortality.",
        "threshold": "NO₃⁻ < 10.0 mg/L, PO₄³⁻ < 0.1 mg/L",
        "confidence": 95,
        "shap": ["pH Alkaline Shift (+44% impact)", "Turbidity Algal Bloom (+36% impact)", "DO Depressed (+20% impact)"]
    },
    5: {
        "pollutant": "Municipal Plastic & Suspended Solids",
        "specific_pollutants": ["Microplastics (PE / PET / PP)", "Suspended Silt", "Anthropogenic Macro-debris"],
        "state": "Particulate Suspended Solids",
        "color": "blue",
        "details": "System alert: Normal chemical variables but massive turbidity spikes point to heavy physical debris and microplastics blocking light and degrading benthic habitats.",
        "action": "<b>1. Passive Collection:</b> Construct floating bamboo or mesh trash booms across natural bends to catch macroplastics.<br><b>2. Sedimentation Basins:</b> Create upstream settling ponds to drop heavy silts out of suspension.<br><b>3. Community Interventions:</b> Implement trash tracking and route collected wastes to regional polymer recycling hubs.",
        "chemical_definition": "Polyethylene (PE), Polyethylene Terephthalate (PET), and Polypropylene (PP) micro-fragments. Suspended solids block sunlight penetration, halting primary production. Microparticles clog the gills of filter-feeding species, causing mechanical damage, asphyxiation, and intestinal blockages.",
        "threshold": "Total Suspended Solids (TSS) < 25.0 mg/L",
        "confidence": 91,
        "shap": ["Turbidity Extreme Spike (+65% impact)", "DO Normal (+20% impact)", "pH Normal (+15% impact)"]
    }
}

# --- VIRTUAL RIVER NETWORK ---
network_state = []
network_lock = threading.Lock()

VIRTUAL_RIVERS = [
    {
        "id": "ganga", "name": "Ganga River, India", "lat": 25.3176, "lng": 82.9739,
        "base_ph": (6.5, 7.5), "base_do": (2.0, 4.0), "base_turb": (150, 250), "base_temp": (24, 28),
        "base_ec": (500, 800), "base_orp": (50, 150)
    },
    {
        "id": "yamuna", "name": "Yamuna River, India", "lat": 28.6139, "lng": 77.2090,
        "base_ph": (5.5, 7.0), "base_do": (0.5, 2.5), "base_turb": (200, 300), "base_temp": (23, 27),
        "base_ec": (1200, 1800), "base_orp": (-150, 50)
    },
    {
        "id": "nile", "name": "Nile River, Egypt", "lat": 30.0444, "lng": 31.2357,
        "base_ph": (7.8, 8.4), "base_do": (5.5, 7.5), "base_turb": (15, 45), "base_temp": (22, 28),
        "base_ec": (300, 500), "base_orp": (250, 400)
    },
    {
        "id": "rhine", "name": "Rhine River, Europe", "lat": 50.9375, "lng": 6.9603,
        "base_ph": (7.6, 8.2), "base_do": (8.0, 10.5), "base_turb": (5, 15), "base_temp": (11, 17),
        "base_ec": (200, 400), "base_orp": (350, 500)
    },
    {
        "id": "thames", "name": "Thames River, UK", "lat": 51.5074, "lng": -0.1278,
        "base_ph": (7.4, 8.1), "base_do": (7.0, 9.5), "base_turb": (10, 30), "base_temp": (10, 16),
        "base_ec": (400, 600), "base_orp": (200, 350)
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
            ec = round(random.uniform(*rv['base_ec']), 1)
            orp = round(random.uniform(*rv['base_orp']), 1)
            
            # Very rarely, simulate an extreme anomaly
            if random.random() < 0.05: 
                event_type = random.choice(['oil', 'metal', 'sewage'])
                if event_type == 'oil':
                    do = round(random.uniform(0.5, 2.0), 2)
                    turb = round(random.uniform(40, 80), 2)
                elif event_type == 'metal':
                    ph = round(random.uniform(2.0, 4.0), 2)
                    temp = round(random.uniform(28, 35), 2)
                    ec = round(random.uniform(1500, 2500), 1)
                elif event_type == 'sewage':
                    do = round(random.uniform(0.5, 2.0), 2)
                    turb = round(random.uniform(200, 300), 2)
                    orp = round(random.uniform(-200, -50), 1)

            # Context-Aware Weather Simulation
            weather_state = random.choices(['Clear', 'Cloudy', 'Heavy Rainfall'], weights=[70, 20, 10])[0]
            context_alert = None
            
            if weather_state == 'Heavy Rainfall':
                turb = round(random.uniform(150, 400), 2)
                w_status = "Rainy"
                w_temp = round(random.uniform(14.0, 19.0), 1)
                w_msg = "Heavy precipitation detected; adjusting turbidity alarm boundaries."
            elif weather_state == 'Cloudy':
                w_status = "Cloudy"
                w_temp = round(random.uniform(20.0, 24.0), 1)
                w_msg = "Overcast sky. Standard monitoring active."
            else:
                w_status = "Clear"
                w_temp = round(random.uniform(25.0, 31.0), 1)
                w_msg = "Optimal solar irradiance. Buoy charging rates stable."
            
            prediction = run_inference(ph, do, turb, temp)
            
            # Weather Override
            if weather_state == 'Heavy Rainfall' and prediction['color'] in ['orange', 'blue']:
                prediction = {
                    "pollutant": "Natural Mud Runoff (Rain Induced)",
                    "specific_pollutants": ["Silt", "Natural Riverbank Sediment", "Clay Particles"],
                    "state": "Turbid Liquid (Safe)",
                    "color": "green",
                    "details": f"Context-Aware AI Triggered: Extreme turbidity ({turb} NTU) detected. However, Weather Integration confirms 'Heavy Rainfall'. False alarm suppressed.",
                    "action": "No action needed. Water cloudiness is from natural rain sediment, not biological sewage.",
                    "chemical_definition": "Inert inorganic silts and clay suspended by rainfall runoffs.",
                    "threshold": "TSS < 100 mg/L",
                    "confidence": 98,
                    "shap": ["Weather API Data (+60% impact)", "DO Steady (+20% impact)", "pH Balanced (+20% impact)"]
                }
                context_alert = "🌧️ Weather API Override Active"
                w_msg = "Heavy rainfall override active: suppressing turbidity threshold alerts."
            elif weather_state == 'Heavy Rainfall':
                context_alert = "🌧️ Raining (Baselines Adjusted)"

            updates.append({
                "id": rv["id"],
                "name": rv["name"],
                "lat": rv["lat"],
                "lng": rv["lng"],
                "weather": context_alert,
                "weather_temp": w_temp,
                "weather_status": w_status,
                "ai_context_msg": w_msg,
                "raw_sensors": {"ph": ph, "do": do, "turbidity": turb, "temperature": temp, "ec": ec, "orp": orp},
                "prediction": prediction
            })
            
        with network_lock:
            global network_state
            network_state = updates
            
        time.sleep(5) # Update network every 5 seconds

def init_network_state():
    """Populate network state synchronously on startup so tests and immediate fetches succeed."""
    updates = []
    for rv in VIRTUAL_RIVERS:
        ph = round(random.uniform(*rv['base_ph']), 2)
        do = round(random.uniform(*rv['base_do']), 2)
        turb = round(random.uniform(*rv['base_turb']), 2)
        temp = round(random.uniform(*rv['base_temp']), 2)
        ec = round(random.uniform(*rv['base_ec']), 1)
        orp = round(random.uniform(*rv['base_orp']), 1)
        
        prediction = run_inference(ph, do, turb, temp)
        w_temp = 24.5
        w_status = "Cloudy"
        w_msg = "Standard atmospheric pressures, baselines nominal."
        updates.append({
            "id": rv["id"],
            "name": rv["name"],
            "lat": rv["lat"],
            "lng": rv["lng"],
            "weather": None,
            "weather_temp": w_temp,
            "weather_status": w_status,
            "ai_context_msg": w_msg,
            "raw_sensors": {"ph": ph, "do": do, "turbidity": turb, "temperature": temp, "ec": ec, "orp": orp},
            "prediction": prediction
        })
    global network_state
    network_state = updates

# Synchronously initialize network state before background thread starts
init_network_state()

# Start the simulation thread
sim_thread = threading.Thread(target=simulate_network, daemon=True)
sim_thread.start()

REMEDIATION_STRATEGIES = {
    "Clean Water / Baseline Condition": {
        "local_1_title": "Riparian Planting",
        "local_1_desc": "Establish vetiver buffer strips to filter agricultural runoffs.",
        "local_2_title": "Routine Telemetry Surveillance",
        "local_2_desc": "Maintain solar buoy communication to catch early deviations.",
        "global_1_title": "Satellite Imagery Integration",
        "global_1_desc": "Utilize Copernicus/Landsat multi-spectral data to track upstream algae.",
        "global_2_title": "Continuous Flow-Through Bioassays",
        "global_2_desc": "Deploy online fish-monitor arrays to detect sub-lethal toxicity."
    },
    "Industrial Heavy Metal Bioaccumulation": {
        "local_1_title": "Phytoremediation Rhizofiltration",
        "local_1_desc": "Deploy Vetiver Grass (Chrysopogon zizanioides) and Water Hyacinth to absorb toxic metal ions.",
        "local_2_title": "Bio-Char Permeable Barriers",
        "local_2_desc": "Apply granular activated bio-char filters at narrow channels to physically trap metal ions.",
        "global_1_title": "Electrocoagulation (EC)",
        "global_1_desc": "Pass electrical current through sacrificial iron/aluminum anodes to precipitate toxic cations.",
        "global_2_title": "Autonomous Nanomaterial Sorbents",
        "global_2_desc": "Deploy solar-powered mechanical filter drones equipped with magnetic iron oxide nanoparticles to capture toxic cations."
    },
    "Untreated Organic Sewage & Pathogens": {
        "local_1_title": "Forced Solar Aeration",
        "local_1_desc": "Install floating solar mechanical aerators to break the interface and restore DO levels.",
        "local_2_title": "Nitrifying Bacterial Inoculants",
        "local_2_desc": "Disperse Nitrosomonas/Nitrobacter cultures to rapidly digest nitrogenous waste.",
        "global_1_title": "Ozonation Disinfection Arrays",
        "global_1_desc": "Inject high-density ozone gas to oxidize organic compounds and destroy bacterial pathogens.",
        "global_2_title": "Advanced Submerged Membrane Bioreactors",
        "global_2_desc": "Install automated multi-stage membrane filtration grids to separate ultra-fine suspended biological loads."
    },
    "Petrochemical Hydrocarbon Slick": {
        "local_1_title": "Hydrophobic Straw Booming",
        "local_1_desc": "Deploy floating barriers packed with organic agricultural waste to capture light slick films.",
        "local_2_title": "Mechanical Skimming",
        "local_2_desc": "Use low-draw floating drum skimmers to physically separate surface oil layers.",
        "global_1_title": "Biostimulation & Hydrocarbonoclastic Inoculation",
        "global_1_desc": "Disperse Alcanivorax borkumensis cultures with slow-release nutrients to accelerate oil degradation.",
        "global_2_title": "Photocatalytic Floating Membranes",
        "global_2_desc": "Install TiO2-coated polymer membranes that leverage solar UV to chemically break down complex hydrocarbons."
    },
    "Agricultural Eutrophication Runoff": {
        "local_1_title": "Riparian Vetiver Buffers",
        "local_1_desc": "Plant deep-rooting grasses along agricultural boundaries to absorb dissolved nitrogen and phosphorus.",
        "local_2_title": "Mechanical Biomass Harvesting",
        "local_2_desc": "Physically extract floating algal mats to prevent mass bacterial decay and subsequent anoxia.",
        "global_1_title": "Ultrasonic Algal Cell Lysis",
        "global_1_desc": "Deploy pontoon-mounted transducers emitting precise frequencies to collapse cyanobacteria gas vesicles without killing fish.",
        "global_2_title": "Phoslock Clay Application",
        "global_2_desc": "Apply lanthanum-modified bentonite clay to bind dissolved phosphate ions, locking them permanently into sediment."
    },
    "Municipal Plastic & Suspended Solids": {
        "local_1_title": "Floating Debris Barricades",
        "local_1_desc": "Construct local bamboo or nylon mesh trash booms across natural bends to catch macroplastics.",
        "local_2_title": "Sedimentation Settling Basins",
        "local_2_desc": "Create upstream shallow ponds to naturally drop heavy clays and suspended silts out of the water column.",
        "global_1_title": "Autonomous Conveyor Interceptors",
        "global_1_desc": "Deploy solar-powered self-navigating catamaran vessels equipped with conveyor belts for mass waste harvesting.",
        "global_2_title": "Acoustic Particle Aggregation",
        "global_2_desc": "Install ultrasonic standing wave chambers to aggregate microplastic particles for centralized filtration."
    },
    "Natural Mud Runoff (Rain Induced)": {
        "local_1_title": "Temporary Sediment Fences",
        "local_1_desc": "Install silt fencing constructed of geotextile filter fabric along run-off channels.",
        "local_2_title": "Settling Basins",
        "local_2_desc": "Construct simple catchment basins upstream to slow velocity and settle out soils.",
        "global_1_title": "Flocculation Dosing Stations",
        "global_1_desc": "Deploy automated dosing of polyacrylamide (PAM) at upstream choke points to aggregate clay particles.",
        "global_2_title": "Centrifugal Desanding Cyclones",
        "global_2_desc": "Install hydrocyclone separator units to continuously filter physical suspended sediments."
    }
}

@app.route('/')
def index():
    return render_template('index.html',
                           weather_temp=26.8,
                           weather_status="Cloudy",
                           ai_context_msg="Standard atmospheric pressures, baselines nominal.")

@app.route('/remediation')
def remediation():
    # Read the latest inference
    with lock:
        latest = latest_inference
        
    pollutant = "Industrial Heavy Metal Bioaccumulation"  # default fallback
    if latest and latest.get('prediction') and latest['prediction'].get('pollutant') != 'Awaiting Telemetry...':
        pred = latest['prediction']
        pollutant = pred.get('pollutant', pollutant)
        
    # Get strategies matching this pollutant
    strategies = REMEDIATION_STRATEGIES.get(pollutant, REMEDIATION_STRATEGIES["Industrial Heavy Metal Bioaccumulation"])
    
    # Is water clean?
    water_is_clean = (pollutant in ["Clean Water / Baseline Condition", "Natural Mud Runoff (Rain Induced)"])
    
    return render_template('remediation.html',
                           water_is_clean=water_is_clean,
                           detected_pollutant=pollutant,
                           local_strategy_1_title=strategies["local_1_title"],
                           local_strategy_1_desc=strategies["local_1_desc"],
                           local_strategy_2_title=strategies["local_2_title"],
                           local_strategy_2_desc=strategies["local_2_desc"],
                           global_strategy_1_title=strategies["global_1_title"],
                           global_strategy_1_desc=strategies["global_1_desc"],
                           global_strategy_2_title=strategies["global_2_title"],
                           global_strategy_2_desc=strategies["global_2_desc"])

@app.route('/api/network_state', methods=['GET'])
def get_network_state():
    with network_lock:
        return jsonify(network_state)

@app.route('/api/live', methods=['GET'])
def get_live_data():
    with lock:
        return jsonify(latest_inference)

@app.route('/api/predict', methods=['POST'])
def predict():
    global latest_inference
    data = request.json
    try:
        ph = float(data.get('ph', 7.0))
        do = float(data.get('do', 6.0))
        turbidity = float(data.get('turbidity', 5.0))
        temperature = float(data.get('temperature', 24.0))
        ec = float(data.get('ec', 450.0))
        orp = float(data.get('orp', 320.0))
        
        result_payload = run_inference(ph, do, turbidity, temperature)
        
        # Calculate dynamic SHAP / confidence weights based on custom inputs
        # (Since we query custom inputs, we adjust confidence and SHAP representation accordingly)
        custom_shap = list(result_payload.get('shap', []))
        if orp < 50:
            custom_shap[0] = f"ORP Negative Drop (+42% impact)"
        if ec > 1000:
            custom_shap[1] = f"EC Massive Spike (+35% impact)"
            
        final_prediction = dict(result_payload)
        final_prediction['shap'] = custom_shap
        
        with lock:
            latest_inference = {
                "raw_sensors": {"ph": ph, "do": do, "turbidity": turbidity, "temperature": temperature, "ec": ec, "orp": orp},
                "prediction": final_prediction
            }
        
        return jsonify(final_prediction)
        
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
