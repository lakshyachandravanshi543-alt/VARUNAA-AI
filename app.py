from flask import Flask, request, jsonify, render_template
import joblib
import os
import threading

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/live', methods=['GET'])
def get_live_data():
    """Endpoint for the dashboard to poll the most recent data automatically"""
    with lock:
        return jsonify(latest_inference)

@app.route('/api/predict', methods=['POST'])
def predict():
    global latest_inference
    if not model or not scaler:
        return jsonify({'error': 'AI Model is not trained yet!'}), 500

    data = request.json
    
    try:
        # Expected input: ph, do, turbidity, temperature
        features = [
            float(data.get('ph', 7.0)),
            float(data.get('do', 6.0)),
            float(data.get('turbidity', 5.0)),
            float(data.get('temperature', 24.0))
        ]
        
        # Scale and predict
        features_scaled = scaler.transform([features])
        prediction = model.predict(features_scaled)[0]
        
        # Highly detailed pollution mappings
        classes = {
            0: {
                "pollutant": "Clean Water / No Major Impurities Found",
                "state": "Liquid (Clear)",
                "color": "green",
                "details": "The AI detected normal pH, healthy dissolved oxygen, and minimal turbidity. No significant pollutants match this chemical signature.",
                "action": "Safe for standard uses."
            },
            1: {
                "pollutant": "Industrial Heavy Metals (Lead/Arsenic/Chromium)",
                "state": "Dissolved Liquid (Toxic)",
                "color": "red",
                "details": "AI Signature Match: Extreme pH combined with elevated temperatures and slight turbidity strongly indicates industrial factory discharge containing toxic heavy metals.",
                "action": "DANGER: Toxic to human and aquatic life. Do not consume or use for agriculture."
            },
            2: {
                "pollutant": "Untreated Biological Sewage",
                "state": "Liquid & Suspended Solids",
                "color": "orange",
                "details": "AI Signature Match: Dangerously depleted oxygen combined with heavy turbidity indicates bacteria breaking down massive amounts of biological waste (feces/sewage).",
                "action": "High risk of pathogenic diseases. Avoid contact. Implement biological filtration."
            },
            3: {
                "pollutant": "Petroleum / Oil Spill",
                "state": "Liquid (Surface Slick)",
                "color": "blue",
                "details": "AI Signature Match: Severely blocked oxygen transfer but moderate turbidity indicates a layer of oil capping the water surface and suffocating the river.",
                "action": "Deploy physical skimmers immediately to prevent complete aquatic suffocation."
            },
            4: {
                "pollutant": "Agricultural Fertilizer Runoff",
                "state": "Dissolved Liquid / Algal Bloom",
                "color": "orange",
                "details": "AI Signature Match: Highly alkaline (basic) pH, reduced oxygen, and thick green cloudy turbidity indicates fertilizer causing extreme algal blooms.",
                "action": "Eutrophication alert. Investigate nearby farming runoff."
            },
            5: {
                "pollutant": "Plastics & Municipal Solid Waste",
                "state": "Solid Waste / Microplastics",
                "color": "blue",
                "details": "AI Signature Match: Normal pH and oxygen, but massive turbidity spikes indicate the presence of physical garbage and dense suspended microplastics blocking light.",
                "action": "Requires physical filtration nets and macroscopic garbage removal."
            }
        }
        
        result_payload = classes.get(int(prediction), {"pollutant": "Unknown", "color": "gray", "state": "Unknown", "details": "Anomaly undetected.", "action": "none"})
        
        # Update global state for Live IoT streaming
        with lock:
            latest_inference = {
                "raw_sensors": {
                    "ph": features[0],
                    "do": features[1],
                    "turbidity": features[2],
                    "temperature": features[3]
                },
                "prediction": result_payload
            }
        
        return jsonify(result_payload)
        
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
