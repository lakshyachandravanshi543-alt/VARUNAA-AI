import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os

# Create a synthetic dataset representing physical sensor readings and their hidden pollutants
np.random.seed(42)
num_samples = 3000

# AI Model output classes:
# 0: Clean Water
# 1: Heavy Metals (Liquid/Dissolved)
# 2: Untreated Sewage & Biological Waste (Liquid & Suspended Solids)
# 3: Petroleum Oil Spill (Liquid)
# 4: Agricultural Fertilizer Runoff (Liquid)
# 5: Plastics & Municipal Solid Waste (Solid)

def generate_sample(pollutant_class):
    if pollutant_class == 0: # Clean Water
        ph = np.random.uniform(6.5, 8.0)
        do = np.random.uniform(6.0, 10.0)    # High Oxygen
        turbidity = np.random.uniform(0.0, 10.0) # Very clear
        temperature = np.random.uniform(20.0, 25.0)

    elif pollutant_class == 1: # Heavy Metals (often accompanied by extreme pH from industrial discharge)
        ph = np.random.choice([np.random.uniform(2.0, 5.0), np.random.uniform(9.0, 12.0)])
        do = np.random.uniform(4.0, 7.0)
        turbidity = np.random.uniform(10.0, 30.0) # Slightly murky
        temperature = np.random.uniform(25.0, 32.0) # Factory coolant discharge heat

    elif pollutant_class == 2: # Sewage (Eats up oxygen rapidly, very cloudy)
        ph = np.random.uniform(5.5, 7.5)
        do = np.random.uniform(0.5, 3.0)      # Dangerously low oxygen
        turbidity = np.random.uniform(80.0, 300.0) # Very Cloudy
        temperature = np.random.uniform(22.0, 28.0)

    elif pollutant_class == 3: # Oil Spill (Blocks oxygen from air, slightly cloudy depending on mix)
        ph = np.random.uniform(6.0, 8.0)
        do = np.random.uniform(1.0, 4.0)
        turbidity = np.random.uniform(30.0, 80.0)
        temperature = np.random.uniform(22.0, 28.0)

    elif pollutant_class == 4: # Fertilizer / Algal Blooms (Nitrates cause algae which blocks light)
        ph = np.random.uniform(7.5, 9.5) # Algae makes water alkaline
        do = np.random.uniform(2.0, 5.0)
        turbidity = np.random.uniform(50.0, 150.0) # Green cloudiness
        temperature = np.random.uniform(24.0, 30.0)

    else: # Plastics & Solid Waste (Doesn't affect pH/DO much, but highly turbid with physical debris)
        ph = np.random.uniform(6.5, 8.0)
        do = np.random.uniform(5.0, 8.0)
        turbidity = np.random.uniform(100.0, 400.0) # Heavy physical debris blocking light
        temperature = np.random.uniform(20.0, 26.0)

    return [ph, do, turbidity, temperature, pollutant_class]

data = []
for _ in range(num_samples):
    cls = np.random.choice([0, 1, 2, 3, 4, 5])
    data.append(generate_sample(cls))

cols = ['ph', 'do', 'turbidity', 'temperature', 'pollutant_class']
df = pd.DataFrame(data, columns=cols)

# Features & Labels
X = df.drop('pollutant_class', axis=1)
y = df['pollutant_class']

from sklearn.metrics import classification_report
# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# StandardScaler
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train Classifier
rf_clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
rf_clf.fit(X_train_scaled, y_train)

score = rf_clf.score(X_test_scaled, y_test)
print(f"Smart Inference Model trained! Accuracy: {score * 100:.2f}%")

# Generate Detailed Metrics
y_pred = rf_clf.predict(X_test_scaled)
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=[
    "Clean Water", 
    "Heavy Metals (Pb/As/Cr)", 
    "Sewage & Bio-Waste", 
    "Petroleum/Oil", 
    "Fertilizer (Nitrates/Phosphates)", 
    "Solid Waste/Microplastics"
]))

# Save model and scaler
script_dir = os.path.dirname(os.path.abspath(__file__))
joblib.dump(rf_clf, os.path.join(script_dir, 'model.joblib'))
joblib.dump(scaler, os.path.join(script_dir, 'scaler.joblib'))

print("New Model successfully saved.")
