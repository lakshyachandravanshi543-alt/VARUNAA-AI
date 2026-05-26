document.addEventListener('DOMContentLoaded', () => {
    
    // UI Elements
    const tabDirectory = document.getElementById('tab-directory');
    const tabCustom = document.getElementById('tab-custom');
    
    const panelDirectory = document.getElementById('directory-panel');
    const panelCustom = document.getElementById('custom-panel');
    
    const riverSelect = document.getElementById('river-select');
    const generateReportBtn = document.getElementById('generate-report-btn');
    
    const customProbeForm = document.getElementById('custom-probe-form');
    const reportLoader = document.getElementById('report-loader');
    const reportSection = document.getElementById('scientific-report-section');
    
    // Report Detail Fields
    const reportBadge = document.getElementById('report-badge');
    const reportRiverName = document.getElementById('report-river-name');
    const reportTimestamp = document.getElementById('report-timestamp');
    
    const metricPh = document.getElementById('metric-ph');
    const metricDo = document.getElementById('metric-do');
    const metricTurb = document.getElementById('metric-turb');
    const metricTemp = document.getElementById('metric-temp');
    
    const pollutantsList = document.getElementById('pollutants-list');
    const remediationContent = document.getElementById('remediation-content');
    const downloadCsvBtn = document.getElementById('download-csv-btn');

    // Local report log history for CSV exporting
    let currentReportLog = null;

    // --- TAB NAVIGATION SWITCHING ---
    const switchTab = (activeTab, inactiveTab, activePanel, inactivePanel) => {
        activeTab.classList.add('active');
        activeTab.setAttribute('aria-selected', 'true');
        inactiveTab.classList.remove('active');
        inactiveTab.setAttribute('aria-selected', 'false');
        
        activePanel.style.display = 'block';
        activePanel.classList.add('active');
        inactivePanel.style.display = 'none';
        inactivePanel.classList.remove('active');
        
        // Hide report when switching tabs to reset UX state
        reportSection.style.display = 'none';
    };

    tabDirectory.addEventListener('click', () => {
        switchTab(tabDirectory, tabCustom, panelDirectory, panelCustom);
    });

    tabCustom.addEventListener('click', () => {
        switchTab(tabCustom, tabDirectory, panelCustom, panelDirectory);
    });

    // --- RANGE SLIDER SYNC ---
    const fields = ['ph', 'do', 'turbidity', 'temperature'];
    fields.forEach(id => {
        const slider = document.getElementById(`${id}-slider`);
        const numInput = document.getElementById(id);
        if (slider && numInput) {
            // Sync slider to text input
            slider.addEventListener('input', (e) => {
                numInput.value = e.target.value;
            });
            // Sync text input to slider
            numInput.addEventListener('input', (e) => {
                let val = parseFloat(e.target.value);
                if (!isNaN(val)) {
                    slider.value = val;
                }
            });
        }
    });

    // --- LEAFLET MAP INTEGRATION (Clean Light Voyager Style) ---
    const map = L.map('map').setView([35, 10], 2.5);
    
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    let markers = {};
    const riverCoords = {
        nile: [30.0444, 31.2357],      // Egypt
        rhine: [50.9375, 6.9603],      // Germany
        thames: [51.5074, -0.1278]     // London
    };

    const getMarkerIcon = (color) => {
        let hex = "#0071e3"; // azure default
        if (color === 'green') hex = "#30d158";
        if (color === 'orange') hex = "#ff9f0a";
        if (color === 'red') hex = "#ff453a";
        if (color === 'blue') hex = "#0a84ff";

        return L.divIcon({
            className: 'custom-div-icon',
            html: `<div style="background-color:${hex}; width:16px; height:16px; border-radius:50%; border: 3px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.15);"></div>`,
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

    // --- COMPARATIVE METRICS VALIDATION ---
    const checkMetricsThresholds = (rawSensors) => {
        // Threshold configs
        const thresholds = {
            ph: { min: 6.5, max: 8.5 },
            do: { min: 5.0, max: 12.0 },
            turb: { min: 0.0, max: 25.0 },
            temp: { min: 10.0, max: 25.0 }
        };

        const phVal = parseFloat(rawSensors.ph);
        const doVal = parseFloat(rawSensors.do);
        const turbVal = parseFloat(rawSensors.turbidity);
        const tempVal = parseFloat(rawSensors.temperature);

        // pH Validation
        const cardPh = document.getElementById('metric-card-ph');
        if (phVal < thresholds.ph.min || phVal > thresholds.ph.max) {
            cardPh.classList.add('out-of-range');
        } else {
            cardPh.classList.remove('out-of-range');
        }

        // DO Validation
        const cardDo = document.getElementById('metric-card-do');
        if (doVal < thresholds.do.min || doVal > thresholds.do.max) {
            cardDo.classList.add('out-of-range');
        } else {
            cardDo.classList.remove('out-of-range');
        }

        // Turbidity Validation
        const cardTurb = document.getElementById('metric-card-turb');
        if (turbVal < thresholds.turb.min || turbVal > thresholds.turb.max) {
            cardTurb.classList.add('out-of-range');
        } else {
            cardTurb.classList.remove('out-of-range');
        }

        // Temperature Validation
        const cardTemp = document.getElementById('metric-card-temp');
        if (tempVal < thresholds.temp.min || tempVal > thresholds.temp.max) {
            cardTemp.classList.add('out-of-range');
        } else {
            cardTemp.classList.remove('out-of-range');
        }
    };

    // --- SCIENTIFIC DATA RENDER ---
    const displayReport = (title, rawSensors, prediction, weatherAlert) => {
        // Hide loader
        reportLoader.style.display = 'none';
        
        // Setup meta details
        reportRiverName.innerText = title;
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

        // Section A: Raw parameters (Comparative Analysis)
        metricPh.innerText = parseFloat(rawSensors.ph).toFixed(2);
        metricDo.innerText = `${parseFloat(rawSensors.do).toFixed(1)} mg/L`;
        metricTurb.innerText = `${Math.round(rawSensors.turbidity)} NTU`;
        metricTemp.innerText = `${parseFloat(rawSensors.temperature).toFixed(1)}°C`;
        
        // Apply out-of-range alerts and styling classes
        checkMetricsThresholds(rawSensors);
        
        // Section B: Detected Pollutants
        pollutantsList.innerHTML = '';
        const card = document.createElement('div');
        card.className = 'pollutant-card';
        
        // Scientific compound listing
        const chemList = (prediction.specific_pollutants || []).join(', ');
        
        card.innerHTML = `
            <div class="pollutant-header">
                <span class="pollutant-cat">${prediction.pollutant}</span>
                <span class="pollutant-formula">${prediction.state || 'Liquid'}</span>
            </div>
            <p class="pollutant-sci-def">
                <strong>Ecosystem Profile:</strong> ${prediction.chemical_definition || prediction.details}
            </p>
            <div class="pollutant-limits">
                <div class="limit-item"><strong>Chemical Compounds Detected:</strong> ${chemList}</div>
                <div class="limit-item"><strong>Permissible Regulatory Limits:</strong> ${prediction.threshold || 'N/A'}</div>
            </div>
        `;
        pollutantsList.appendChild(card);
        
        // Section C: Actionable Remediation
        remediationContent.innerHTML = prediction.action || 'No critical remediation required at this telemetry index.';
        
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
            verdict: prediction.pollutant,
            compounds: chemList,
            timestamp: now.toISOString()
        };
    };

    // --- DIRECTORY INFERENCE QUERY TRIGGER ---
    const triggerReportGeneration = async (selectedId) => {
        // Show Loader
        reportSection.style.display = 'none';
        reportLoader.style.display = 'flex';

        try {
            // Query network state API from app.py
            const response = await fetch('/api/network_state');
            if (!response.ok) throw new Error('API server returned error.');
            
            const data = await response.json();
            const selectedRiver = data.find(r => r.id === selectedId);
            
            if (selectedRiver) {
                // Focus map on the selected river coordinates
                map.flyTo(riverCoords[selectedId], 5, { duration: 1.5 });
                
                setTimeout(() => {
                    displayReport(
                        selectedRiver.name,
                        selectedRiver.raw_sensors,
                        selectedRiver.prediction,
                        selectedRiver.weather
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

    // --- CUSTOM PROBE FORM SUBMIT ---
    customProbeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Gather input data
        const payload = {
            ph: parseFloat(document.getElementById('ph').value),
            do: parseFloat(document.getElementById('do').value),
            turbidity: parseFloat(document.getElementById('turbidity').value),
            temperature: parseFloat(document.getElementById('temperature').value)
        };

        // Show Loader
        reportSection.style.display = 'none';
        reportLoader.style.display = 'flex';

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error('Server classification model failed.');
            const prediction = await response.json();
            
            setTimeout(() => {
                displayReport(
                    "Custom Probe Location",
                    payload,
                    prediction,
                    null
                );
            }, 600);

        } catch (error) {
            reportLoader.style.display = 'none';
            alert(`Error classifying custom inputs: ${error.message}`);
        }
    });

    // --- CSV LOG EXPORTER ---
    downloadCsvBtn.addEventListener('click', () => {
        if (!currentReportLog) return;
        
        const header = "Timestamp,Location,pH,DO (mg/L),Turbidity (NTU),Temperature (C),AI Inference,Compounds Detected\n";
        const row = `"${currentReportLog.timestamp}","${currentReportLog.title}",${currentReportLog.ph},${currentReportLog.do},${currentReportLog.turbidity},${currentReportLog.temp},"${currentReportLog.verdict}","${currentReportLog.compounds}"\n`;
        
        const csvContent = "data:text/csv;charset=utf-8," + encodeURIComponent(header + row);
        
        const link = document.createElement("a");
        link.setAttribute("href", csvContent);
        link.setAttribute("download", `Varuna_Scientific_Report_${currentReportLog.title.replace(/\s+/g, '_')}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

});
