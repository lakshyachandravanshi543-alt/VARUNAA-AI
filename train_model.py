# SYNTHETIC DATASET — Field validation pending.
# Do not cite accuracy figures in regulatory submissions without NABL lab co-validation.

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

np.random.seed(42)

CLASS_PARAMS = {
    0: {
        "name": "Clean Water",
        "n": 500,
        "ph": (6.8, 7.8), "do": (6, 9), "turbidity": (2, 12),
        "temp": (18, 26), "ec": (200, 600), "orp": (200, 400)
    },
    1: {
        "name": "Heavy Metal",
        "n": 500,
        "ph": (2.5, 5.5), "do": (1, 4), "turbidity": (5, 20),
        "temp": (28, 38), "ec": (1500, 3000), "orp": (-50, 150)
    },
    2: {
        "name": "Sewage",
        "n": 500,
        "ph": (5.5, 7.5), "do": (0.2, 3), "turbidity": (80, 300),
        "temp": (22, 30), "ec": (800, 1800), "orp": (-250, -50)
    },
    3: {
        "name": "Oil/Hydrocarbon",
        "n": 500,
        "ph": (6.5, 7.5), "do": (0.5, 2.5), "turbidity": (20, 80),
        "temp": (20, 28), "ec": (300, 700), "orp": (50, 250)
    },
    4: {
        "name": "Eutrophication",
        "n": 500,
        "ph": (8.5, 10), "do": (1, 4), "turbidity": (30, 120),
        "temp": (24, 32), "ec": (600, 1200), "orp": (-100, 100)
    },
    5: {
        "name": "Plastics/Solids",
        "n": 500,
        "ph": (6.5, 8.0), "do": (4, 7), "turbidity": (80, 400),
        "temp": (18, 28), "ec": (200, 600), "orp": (150, 350)
    }
}

FEATURES = ['ph', 'do', 'turbidity', 'temperature', 'ec', 'orp']


def generate_samples(class_id, params):
    n = params["n"]
    rows = []
    for _ in range(n):
        sample = {}
        for feat, key in [
            ('ph', 'ph'), ('do', 'do'), ('turbidity', 'turbidity'),
            ('temperature', 'temp'), ('ec', 'ec'), ('orp', 'orp')
        ]:
            lo, hi = params[key]
            mean = (lo + hi) / 2
            std = (hi - lo) * 0.03  # Gaussian noise: std = 0.03 * feature range
            val = float(np.clip(np.random.normal(mean, std + (hi - lo) / 5), lo, hi))
            sample[feat] = val
        sample['label'] = class_id
        rows.append(sample)
    return rows


# --- Generate dataset ---
all_rows = []
for class_id, params in CLASS_PARAMS.items():
    all_rows.extend(generate_samples(class_id, params))

df = pd.DataFrame(all_rows)
X = df[FEATURES]
y = df['label']

# --- Train/test split ---
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# --- Fit StandardScaler ---
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# --- Train RandomForest ---
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    random_state=42
)
model.fit(X_train_scaled, y_train)

# --- Evaluate ---
y_pred = model.predict(X_test_scaled)
target_names = [CLASS_PARAMS[i]["name"] for i in sorted(CLASS_PARAMS)]
print("\n=== Classification Report ===")
print(classification_report(y_test, y_pred, target_names=target_names))

# --- Save artifacts ---
os.makedirs("model", exist_ok=True)
joblib.dump(model, "model/model.joblib")
joblib.dump(scaler, "model/scaler.joblib")
print("Saved model/model.joblib and model/scaler.joblib")
