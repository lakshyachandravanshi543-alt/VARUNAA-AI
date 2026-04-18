# AquaSense AI: River Cleaning Detective

## Overview
AquaSense AI is an advanced Smart Inference AI Detective designed to assess the health of Indian river systems.
Instead of relying on expansive, laboratory-grade chemical arrays, this system uses a Random Forest Machine Learning model to infer hidden macroscopic and microscopic pollutants by analyzing just 4 basic scalar inputs from typical IoT hardware:
1. **pH Level**
2. **Dissolved Oxygen (DO)**
3. **Turbidity**
4. **Temperature**

Using these four dimensions, the AI classifies complex overlapping chemical signatures with **99.50% global validation accuracy** and deduces precise **River Cleaning Strategies**.

## Features
- **Predictive Inference Engine:** Deduces complex states: Solid Waste (Plastics), Heavy Metals (Lead/Arsenic), Biological Sewage, Agricultural Fertilizers, and Petroleum Oil spills.
- **Hardware Integration:** Includes `hardware_sensor_code.ino`, ready to flash to an ESP32 to push live real-world electrical voltages into the AI.
- **Glassmorphic Web Dashboard:** A natively hosted Flask front-end utilizing modern UI/UX principles to visualize AI inference smoothly.
- **Live IoT Mode:** Auto-polling dashboard that syncs without manual input, mimicking a central command structure.

## Quick Start
1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Launch the Core Server:**
   ```bash
   python app.py
   ```
3. **Launch the Hardware Simulator (Optional - For Demoing):**
   ```bash
   python simulate_buoy.py
   ```
4. **Access:** Open a web browser to `http://127.0.0.1:5000/`.

## Evaluation Metrics Highlights
- **Petroleum/Oil Spill Prediction:** Precision `0.98`, Recall `0.99`, F1-Score `0.98`
- **Fertilizer Runoff Prediction:** Precision `0.99`, Recall `0.98`, F1-Score `0.99`
- **Heavy Metals, Sewage, Solid Waste, and Clean Water:** Achieved pristine Precision `1.00`, Recall `1.00`, and F1-Score `1.00` due to highly distinguishable synthetic signature clusters.
