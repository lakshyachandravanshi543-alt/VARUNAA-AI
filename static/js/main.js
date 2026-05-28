document.addEventListener('DOMContentLoaded', () => {
    
    // UI Elements
    const riverSelect = document.getElementById('river-select');
    const generateReportBtn = document.getElementById('generate-report-btn');
    
    const reportLoader = document.getElementById('report-loader');
    const reportSection = document.getElementById('scientific-inference-section');
    
    // Report Detail Fields
    const reportBadge = document.getElementById('report-badge');
    const reportRiverName = document.getElementById('report-river-name');
    const reportTimestamp = document.getElementById('report-timestamp');
    
    const metricPh = document.getElementById('metric-ph');
    const metricDo = document.getElementById('metric-do');
    const metricTurb = document.getElementById('metric-turb');
    const metricTemp = document.getElementById('metric-temp');
    const metricEc = document.getElementById('metric-ec');
    const metricOrp = document.getElementById('metric-orp');
    
    const statusPh = document.getElementById('status-ph');
    const statusDo = document.getElementById('status-do');
    const statusTurb = document.getElementById('status-turb');
    const statusTemp = document.getElementById('status-temp');
    const statusEc = document.getElementById('status-ec');
    const statusOrp = document.getElementById('status-orp');
    
    const xaiPredictedClass = document.getElementById('xai-predicted-class');
    const confidencePercentageVal = document.getElementById('confidence-percentage-val');
    const confidenceBarFill = document.getElementById('confidence-bar-fill');
    
    const shapListContainer = document.getElementById('shap-list-container');
    const remediationContent = document.getElementById('remediation-content');
    const downloadCsvBtn = document.getElementById('download-csv-btn');

    // Local report log history for CSV exporting
    let currentReportLog = null;

    // --- LEAFLET MAP INTEGRATION (Clean Light Voyager Style) ---
    const map = L.map('map').setView([25, 30], 2);
    
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    let markers = {};
    const riverCoords = {
        ganga: [25.3176, 82.9739],     // India
        yamuna: [28.6139, 77.2090],    // India
        nile: [30.0444, 31.2357],      // Egypt
        rhine: [50.9375, 6.9603],      // Germany
        thames: [51.5074, -0.1278]     // UK
    };

    const getMarkerIcon = (color) => {
        let hex = "#0071e3"; // azure default
        if (color === 'green') hex = "#30d158";
        if (color === 'orange') hex = "#ff9f0a";
        if (color === 'red') hex = "#ff453a";
        if (color === 'blue') hex = "#0a84ff";

        return L.divIcon({
            className: 'custom-div-icon',
            html: `<div style="background-color:${hex}; width:16px; height:16px; border-radius:50%; border: 3px solid white; box-shadow: none;"></div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });
    };

    // Initialize markers
    Object.keys(riverCoords).forEach(id => {
        markers[id] = L.marker(riverCoords[id], { icon: getMarkerIcon('blue') })
            .addTo(map)
            .on('click', () => {
                riverSelect.value = id;
                triggerReportGeneration(id);
            });
    });

    async function updateMapMarkers() {
        try {
            const response = await fetch('/api/network_state');
            if (response.ok) {
                const data = await response.json();
                data.forEach(river => {
                    if (markers[river.id]) {
                        markers[river.id].setIcon(getMarkerIcon(river.prediction.color));
                        markers[river.id].bindTooltip(`<b>${river.name}</b><br>AI Verdict: ${river.prediction.pollutant}`, { direction: 'top' });
                    }
                });
            }
        } catch (e) {
            console.error("Failed to update map markers", e);
        }
    }

    // Update map markers instantly and start polling
    updateMapMarkers();
    setInterval(updateMapMarkers, 5000);

    // --- CHART.JS WATER CRISIS PLOT ---
    const ctx = document.getElementById('crisis-chart');
    if (ctx) {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026'],
                labels: ['2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026'],
                datasets: [{
                    label: 'Global Water Quality Index (WQI)',
                    data: [82.5, 80.1, 78.4, 76.9, 74.2, 73.0, 70.5, 68.1, 65.4, 61.2, 57.8],
                    borderColor: '#1d1d1f',         // Ink
                    backgroundColor: 'rgba(29, 29, 31, 0.03)',
                    borderWidth: 2.5,
                    pointBackgroundColor: '#86868b', // Graphite
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 1.5,
                    pointRadius: 4.5,
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        min: 40,
                        max: 100,
                        grid: { color: 'rgba(0,0,0,0.05)' },
                        ticks: { color: '#86868b', font: { family: 'Inter', size: 10 } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#86868b', font: { family: 'Inter', size: 10 } }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // --- 6D COMPARATIVE METRICS VALIDATION ---
    const checkMetricsThresholds = (rawSensors) => {
        // Safe limits config
        const thresholds = {
            ph: { min: 6.5, max: 8.5 },
            do: { min: 5.0, max: 12.0 },
            turb: { min: 0.0, max: 25.0 },
            temp: { min: 10.0, max: 25.0 },
            ec: { min: 100.0, max: 1000.0 },
            orp: { min: 200.0, max: 600.0 }
        };

        const metrics = {
            ph: { val: parseFloat(rawSensors.ph), card: document.getElementById('metric-card-ph'), msg: statusPh },
            do: { val: parseFloat(rawSensors.do), card: document.getElementById('metric-card-do'), msg: statusDo },
            turb: { val: parseFloat(rawSensors.turbidity), card: document.getElementById('metric-card-turb'), msg: statusTurb },
            temp: { val: parseFloat(rawSensors.temperature), card: document.getElementById('metric-card-temp'), msg: statusTemp },
            ec: { val: parseFloat(rawSensors.ec), card: document.getElementById('metric-card-ec'), msg: statusEc },
            orp: { val: parseFloat(rawSensors.orp), card: document.getElementById('metric-card-orp'), msg: statusOrp }
        };

        Object.keys(metrics).forEach(key => {
            const m = metrics[key];
            const bounds = thresholds[key];
            
            if (m.val < bounds.min || m.val > bounds.max) {
                m.card.classList.add('out-of-range');
                m.msg.innerText = `Danger: Out of safe bounds!`;
            } else {
                m.card.classList.remove('out-of-range');
                m.msg.innerText = `Normal Safe Range`;
            }
        });
    };

    // --- SCIENTIFIC DATA RENDER ---
    const displayReport = (title, rawSensors, prediction, weatherAlert, weatherTemp, weatherStatus, aiContextMsg) => {
        // Hide loader
        reportLoader.style.display = 'none';
        
        // Update Weather Context Widget details
        const tempValEl = document.getElementById('weather-temp-val');
        const statusValEl = document.getElementById('weather-status-val');
        const aiMsgValEl = document.getElementById('ai-context-msg-val');
        const iconEl = document.getElementById('weather-widget-icon');
        
        if (tempValEl && weatherTemp !== undefined) {
            tempValEl.innerText = weatherTemp;
        }
        if (statusValEl && weatherStatus) {
            statusValEl.innerText = weatherStatus;
        }
        if (aiMsgValEl && aiContextMsg) {
            aiMsgValEl.innerText = aiContextMsg;
        }
        if (iconEl && weatherStatus) {
            iconEl.innerText = (weatherStatus === 'Rainy' || weatherStatus === 'Rain') ? '🌧️' : ((weatherStatus === 'Cloudy' || weatherStatus === 'Overcast') ? '☁️' : '☀️');
        }
        
        // Setup meta details
        reportRiverName.innerText = `Live Scientific Inference: ${title}`;
        const now = new Date();
        reportTimestamp.innerText = `Inference Timestamp: ${now.toLocaleDateString()} ${now.toLocaleTimeString()} | Status: Active Telemetry`;
        
        // Badge color mapping
        reportBadge.className = 'badge'; // reset
        if (prediction.color === 'green') {
            reportBadge.classList.add('badge-green');
            reportBadge.innerText = 'Safe Baseline';
        } else if (prediction.color === 'red') {
            reportBadge.classList.add('badge-red');
            reportBadge.innerText = 'Critical Hazard';
        } else if (prediction.color === 'orange') {
            reportBadge.classList.add('badge-orange');
            reportBadge.innerText = 'High Pollution';
        } else {
            reportBadge.classList.add('badge-blue');
            reportBadge.innerText = 'Caution Required';
        }
        
        if (weatherAlert) {
            reportBadge.innerText += ` | ${weatherAlert}`;
        }

        // Section A: Raw parameters (6D Metrics Grid)
        metricPh.innerText = parseFloat(rawSensors.ph).toFixed(2);
        metricDo.innerText = parseFloat(rawSensors.do).toFixed(2);
        metricTurb.innerText = Math.round(rawSensors.turbidity);
        metricTemp.innerText = parseFloat(rawSensors.temperature).toFixed(1);
        metricEc.innerText = parseFloat(rawSensors.ec).toFixed(1);
        metricOrp.innerText = parseFloat(rawSensors.orp).toFixed(1);
        
        // Check safe thresholds and apply conditional out-of-range styling
        checkMetricsThresholds(rawSensors);
        
        // Section B: AI Confidence Probability
        xaiPredictedClass.innerText = `Prediction: ${prediction.pollutant}`;
        const confidence = prediction.confidence || 89;
        confidencePercentageVal.innerText = `${confidence}% AI Confidence Probability`;
        confidenceBarFill.style.width = `${confidence}%`;
        
        // Section C: Explainable AI SHAP Breakdown
        shapListContainer.innerHTML = '';
        (prediction.shap || []).forEach(shapText => {
            const li = document.createElement('li');
            li.className = 'shap-item';
            li.innerText = shapText;
            shapListContainer.appendChild(li);
        });
        
        // Section D: Remediation Strategy
        remediationContent.innerHTML = prediction.action || 'No critical remediation required at this telemetry index.';
        
        // Update the remediation plan link dynamically with query parameters
        const viewRemediationBtn = document.querySelector('.dashboard-footer-action a');
        if (viewRemediationBtn) {
            viewRemediationBtn.href = `/remediation?ph=${rawSensors.ph}&do=${rawSensors.do}&turbidity=${rawSensors.turbidity}&temperature=${rawSensors.temperature}&ec=${rawSensors.ec}&orp=${rawSensors.orp}&pollutant=${encodeURIComponent(prediction.pollutant)}`;
        }
        
        // Reveal Section
        reportSection.style.display = 'block';
        reportSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Save state for CSV downloading
        currentReportLog = {
            title: title,
            ph: rawSensors.ph,
            do: rawSensors.do,
            turbidity: rawSensors.turbidity,
            temp: rawSensors.temperature,
            ec: rawSensors.ec,
            orp: rawSensors.orp,
            verdict: prediction.pollutant,
            confidence: confidence,
            timestamp: now.toISOString()
        };
    };

    // --- DIRECTORY INFERENCE QUERY TRIGGER ---
    const triggerReportGeneration = async (selectedId) => {
        // Show Loader
        reportSection.style.display = 'none';
        reportLoader.style.display = 'flex';

        try {
            const response = await fetch('/api/network_state');
            if (!response.ok) throw new Error('API server returned error.');
            
            const data = await response.json();
            const selectedRiver = data.find(r => r.id === selectedId);
            
            if (selectedRiver) {
                // Focus map on the selected river coordinates
                if (riverCoords[selectedId]) {
                    map.flyTo(riverCoords[selectedId], 5, { duration: 1.5 });
                }
                
                // POST to /api/predict to update server-side latest_inference state in background
                fetch('/api/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ph: parseFloat(selectedRiver.raw_sensors.ph),
                        do: parseFloat(selectedRiver.raw_sensors.do),
                        turbidity: parseFloat(selectedRiver.raw_sensors.turbidity),
                        temperature: parseFloat(selectedRiver.raw_sensors.temperature),
                        ec: parseFloat(selectedRiver.raw_sensors.ec),
                        orp: parseFloat(selectedRiver.raw_sensors.orp)
                    })
                }).catch(err => console.error("Failed to sync latest inference state with server:", err));
                
                setTimeout(() => {
                    displayReport(
                        selectedRiver.name,
                        selectedRiver.raw_sensors,
                        selectedRiver.prediction,
                        selectedRiver.weather,
                        selectedRiver.weather_temp,
                        selectedRiver.weather_status,
                        selectedRiver.ai_context_msg
                    );
                }, 600);
            } else {
                throw new Error('River data not found in telemetry array.');
            }
        } catch (error) {
            reportLoader.style.display = 'none';
            alert(`Error querying inference array: ${error.message}`);
        }
    };

    generateReportBtn.addEventListener('click', () => {
        const selectedId = riverSelect.value;
        if (!selectedId) {
            alert('Please select a river system from the directory first.');
            return;
        }
        triggerReportGeneration(selectedId);
    });

    // --- CSV LOG EXPORTER ---
    downloadCsvBtn.addEventListener('click', () => {
        if (!currentReportLog) return;
        
        const header = "Timestamp,Location,pH,DO (mg/L),Turbidity (NTU),Temperature (C),EC (uS/cm),ORP (mV),AI Inference,Confidence (%)\n";
        const row = `"${currentReportLog.timestamp}","${currentReportLog.title}",${currentReportLog.ph},${currentReportLog.do},${currentReportLog.turbidity},${currentReportLog.temp},${currentReportLog.ec},${currentReportLog.orp},"${currentReportLog.verdict}",${currentReportLog.confidence}\n`;
        
        const csvContent = "data:text/csv;charset=utf-8," + encodeURIComponent(header + row);
        
        const link = document.createElement("a");
        link.setAttribute("href", csvContent);
        link.setAttribute("download", `Varuna_Scientific_Report_${currentReportLog.title.replace(/\s+/g, '_')}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

});
