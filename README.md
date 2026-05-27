# Varuna AI: Enterprise-Grade Water Health Inference Engine

## Overview
**Varuna AI** is a state-of-the-art Edge Inference Engine designed to reconstruct complex chemical pollution fingerprints from river systems. 

Rather than deploying expensive, delicate laboratory chemical arrays, Varuna AI leverages a paired **Isolation Forest** (for anomaly rejection) and **Random Forest Machine Learning model** to infer multi-dimensional pollution markers using **6 basic IoT parameters**:
1. **pH Level**
2. **Dissolved Oxygen (DO)**
3. **Turbidity**
4. **Temperature**
5. **Electrical Conductivity (EC)**
6. **Oxidation-Reduction Potential (ORP)**

By mapping the non-linear correlations across these 6 scalar parameters, Varuna AI identifies synthetic signatures with **99.50% global validation accuracy**, enabling immediate, targeted, cost-effective environmental remediation.

---

## Key Features & Architecture

### 1. Minimalist Apple MacBook Neo UI/UX
*   **Design Language:** Fog canvas background (`#f5f5f7`), Snow white card surfaces (`#ffffff`), and Azure primary call-to-actions (`#0071e3`).
*   **Strict Constraints:** Exactly `28px` border radius for cards, `999px` border radius for buttons, and **ZERO box-shadows** system-wide (relying entirely on flat tonal contrast).
*   **Massive Typography:** Styled with Google Font *Inter*, utilizing massive display headings with negative letter-tracking (`-2px`) for an editorial, modern aesthetic.

### 2. Local Weather Context Widget
*   Integrates dynamic context-aware weather properties (`weather_temp`, `weather_status`, `ai_context_msg`) directly into the Live Inference dashboard.
*   The AI adapts alarm boundaries dynamically (e.g., suppressing false alerts from natural mud runoff during heavy rainfall).

### 3. Dynamic Remediation Action Plan (`/remediation`)
*   Serves as a strict Flask Jinja2 template with conditional `if/else` rendering states:
    *   **Clean State (`water_is_clean`):** Shows a single centered white card with a green success badge stating *"Water Quality Optimal"*.
    *   **Polluted State:** Displays tailored mitigation plans in a 2-column grid comparing *"Cost-Effective Deployment"* (e.g., Phytoremediation, Bio-char barriers) with *"Advanced Global Technologies"* (e.g., Electrocoagulation, Nanobubble generators).
*   Generates a dynamic PDF text compliance log download matching the detected pollutant index.

### 4. Edge Hardware Specs & Industrial Upgrades (`/hardware`)
*   Detailed walkthrough of **The Portable Smart Wand** BOM (Bill of Materials) kept under **₹8,500**:
    1.  **Core Brain:** ESP32 DevKitC v4 edge AI processing.
    2.  **Digital Validation:** DS18B20 digital temperature probe.
    3.  **Optical Clarity:** Slotted infrared turbidity sensor.
    4.  **TDS Analyzer:** Gold two-pin conductivity probe.
    5.  **Acidity Probe:** Analog BNC pH sensor module.
    6.  **Oxidation Monitor:** Analog ORP sensor module.
    7.  **Power & Ruggedization:** Dual 18650 Li-ion cells housed in an IP67 PVC chassis.
*   **Industrial Scalability Upgrades:**
    -   **Anti-Biofouling Management:** Automated mechanical wipers and ultrasonic transducers to prevent bio-buildup, ensuring zero sensor drift during remote deployments.
    -   **Long-Range Telemetry (LoRaWAN):** Integrated LoRaWAN/NB-IoT module to transmit 6-dimensional telemetry data up to 15 kilometers without relying on local municipal Wi-Fi.

---

## Quick Start

### 1. Local Environment Setup
Install dependencies:
```bash
pip install -r requirements.txt
```

Launch the Flask application:
```bash
python app.py
```
Open a browser and navigate to `http://127.0.0.1:5000/`.

### 2. Automated Testing
Run the unit test suite validating routing, network state endpoints, dynamic template variables, and the Random Forest classification payload:
```bash
python -m unittest test_app.py
```

### 3. Deploying to Google Cloud Run
If deploying to your Google Cloud Run account, navigate to the workspace directory and execute:
```bash
gcloud config set project test121-493806
gcloud builds submit --tag gcr.io/test121-493806/water-quality-ai
gcloud run deploy water-quality-ai --image gcr.io/test121-493806/water-quality-ai --platform managed --region us-central1 --allow-unauthenticated --concurrency 8 --port 8080
```
Alternatively, execute the local deployment script:
```bash
./deploy.sh
```

---

## Model Evaluation Metrics
*   **Petroleum Hydrocarbon Slick Prediction:** Precision `0.98`, Recall `0.99`, F1-Score `0.98`
*   **Agricultural Eutrophication Runoff Prediction:** Precision `0.99`, Recall `0.98`, F1-Score `0.99`
*   **Heavy Metals, Sewage, Plastics, and Clean Water:** Achieved Precision `1.00`, Recall `1.00`, and F1-Score `1.00` due to highly distinguishable synthetic signature clusters.
