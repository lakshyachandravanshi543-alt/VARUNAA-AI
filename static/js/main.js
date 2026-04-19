document.addEventListener('DOMContentLoaded', () => {
    
    const resultsContainer = document.getElementById('results-display');
    const liveToggle = document.getElementById('live-mode-toggle');
    const mapContainer = document.getElementById('map');
    const manualInputContainer = document.getElementById('manual-input-container');
    const toggleDesc = document.getElementById('toggle-desc');
    
    // CSV History Log tracking
    let historyLog = [];
    
    // UI Update logic
    function renderResult(dataObj) {
        if (!dataObj || !dataObj.prediction) return;
        const result = dataObj.prediction;
        
        let headerTitle = dataObj.name ? `📌 ${dataObj.name}` : "📡 Live Physical Hardware Ping";
        
        // Log to history for CSV download
        historyLog.push({
            timestamp: new Date().toISOString(),
            riverName: dataObj.name || "Local Hardware Node",
            ph: dataObj.raw_sensors.ph,
            do: dataObj.raw_sensors.do.toFixed(1),
            turbidity: dataObj.raw_sensors.turbidity,
            temp: dataObj.raw_sensors.temperature,
            prediction: result.pollutant
        });
        if(historyLog.length > 150) historyLog.shift(); // keep last 150 logs
        
        let marineStatus = "";
        let marineColor = "";
        let doLevel = parseFloat(dataObj.raw_sensors.do);

        if (doLevel > 5.5) {
            marineStatus = "🐟 Thriving Habitat: Oxygen levels support all local fish (Rohu, Catla) and sensitive aquatic species.";
            marineColor = "#10b981";
        } else if (doLevel >= 3.0) {
            marineStatus = "⚠️ Hypoxic Stress: Fish are struggling to breathe. Sensitive species are migrating away or dying.";
            marineColor = "#f59e0b";
        } else {
            marineStatus = "💀 CRITICAL (Asphyxiation Zone): Lethal oxygen depletion. Imminent localized mass fish-kill event.";
            marineColor = "#ef4444";
        }
        
        resultsContainer.className = `results-container status-${result.color}`;
        resultsContainer.innerHTML = `
            <div style="font-size:1.1rem; color:#cbd5e1; margin-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px;">
                ${headerTitle}
            </div>
            ${dataObj.weather ? `<div style="background: rgba(59, 130, 246, 0.2); border: 1px solid #3b82f6; color: #60a5fa; padding: 8px 12px; border-radius: 8px; font-weight: bold; margin-bottom: 15px; font-size: 0.9rem; text-align: center;">${dataObj.weather}</div>` : ''}
            <div class="result-status" style="font-size: 1.8rem;">${result.pollutant}</div>
            <div style="font-weight: bold; margin-bottom: 1rem; color: #cbd5e1; letter-spacing: 1px;">POLLUTANT STATE: <span style="color:white;">${result.state}</span></div>
            
            <div style="display:flex; justify-content:center; gap: 15px; margin-bottom: 1rem; background: rgba(0,0,0,0.4); padding: 10px; border-radius: 8px;">
                <span><b>pH:</b> ${dataObj.raw_sensors.ph}</span>
                <span><b>DO:</b> ${dataObj.raw_sensors.do.toFixed(1)} mg/L</span>
                <span><b>Turb:</b> ${dataObj.raw_sensors.turbidity} NTU</span>
                <span><b>Temp:</b> ${dataObj.raw_sensors.temperature}°C</span>
            </div>

            <div style="margin-bottom: 1.5rem; padding: 12px; background: rgba(0,0,0,0.3); border-left: 4px solid ${marineColor}; border-radius: 6px;">
                <div style="font-size: 0.85rem; color: #cbd5e1; text-transform: uppercase; font-weight: bold; margin-bottom: 5px;">Marine Life Viability Index</div>
                <div style="color: ${marineColor}; font-weight: 600; font-size: 0.95rem;">${marineStatus}</div>
            </div>

            <div class="result-message" style="margin-bottom: 1rem;">${result.details}</div>
            <div style="padding: 15px; background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; border-radius: 8px; font-weight: bold; margin-top: 15px; color: #10b981;">
                RIVER CLEANING STRATEGY: ${result.action}
            </div>
        `;
    }

    // --- MAP INITIALIZATION ---
    // Use CartoDB Dark Matter tiles for a sleek AI detective look
    const map = L.map('map').setView([20, 0], 2);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    let markers = {};
    let selectedRiverId = null;

    // --- CUSTOM MAP ICONS ---
    const getIcon = (color) => {
        let hex = "#ef4444";
        if(color === 'green') hex = "#10b981";
        if(color === 'orange') hex = "#f59e0b";
        if(color === 'blue') hex = "#3b82f6";
        
        return L.divIcon({
            className: 'custom-div-icon',
            html: `<div style="background-color:${hex}; width:20px; height:20px; border-radius:50%; border: 3px solid white; box-shadow: 0 0 10px ${hex};"></div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
    }

    let pollingInterval = null;
    let isPhysicalMode = false;

    async function pollNetworkState() {
        if(isPhysicalMode) return;
        try {
            const response = await fetch('/api/network_state');
            const data = await response.json();
            
            // Update map markers
            data.forEach(river => {
                if(!markers[river.id]) {
                    // Create marker if it doesn't exist
                    markers[river.id] = L.marker([river.lat, river.lng])
                        .addTo(map)
                        .on('click', () => {
                            selectedRiverId = river.id;
                            renderResult(river);
                        });
                }
                
                // Update marker color based on AI prediction
                markers[river.id].setIcon(getIcon(river.prediction.color));
                markers[river.id].bindTooltip(`<b>${river.name}</b><br>Status: ${river.prediction.pollutant}`, {direction: 'top'});

                // If this is the currently selected river, update the side panel live
                if (selectedRiverId === river.id) {
                    renderResult(river);
                }
            });

            // If no river selected yet, auto-select the first one
            if(!selectedRiverId && data.length > 0) {
                selectedRiverId = data[0].id;
                renderResult(data[0]);
                map.flyTo([data[0].lat, data[0].lng], 5);
            }

        } catch(e) {
            console.error("Failed to poll network state", e);
        }
    }

    async function pollPhysicalState() {
        if(!isPhysicalMode) return;
        try {
            const response = await fetch('/api/live');
            const data = await response.json();
            renderResult(data);
        } catch(e) {
            console.error("Failed to poll physical state", e);
        }
    }

    // Startup
    pollNetworkState();
    pollingInterval = setInterval(pollNetworkState, 5000);

    // --- MODE TOGGLE LOGIC ---
    liveToggle.addEventListener('change', (e) => {
        isPhysicalMode = e.target.checked;
        clearInterval(pollingInterval);

        if (isPhysicalMode) {
            // Switch to Physical Mode
            mapContainer.style.display = 'none';
            manualInputContainer.style.display = 'block';
            toggleDesc.innerHTML = `Currently listening to <b>Live Local Hardware (esp32/simulate_buoy.py)</b> via '/api/predict'.`;
            
            resultsContainer.innerHTML = `<p class="placeholder-text">Waiting for hardware Ping...</p>`;
            resultsContainer.className = 'results-container empty';
            
            pollingInterval = setInterval(pollPhysicalState, 2000);
        } else {
            // Switch to Virtual Network Mode
            mapContainer.style.display = 'block';
            manualInputContainer.style.display = 'none';
            map.invalidateSize(); // Fix Leaflet render bug when container is un-hidden
            toggleDesc.innerHTML = `Currently showing <b>Global Virtual River Network (Digital Twin Map)</b>. Toggle to switch to single local physical hardware stream.`;
            
            selectedRiverId = null; // reset selection
            pollingInterval = setInterval(pollNetworkState, 5000);
            pollNetworkState(); // immediate call
        }
    });

    // Sync sliders for manual override in physical mode
    const fields = ['ph', 'do', 'turbidity', 'temperature'];
    fields.forEach(id => {
        const slider = document.getElementById(`${id}-slider`);
        const numInput = document.getElementById(id);
        if(slider && numInput) {
            slider.addEventListener('input', (e) => numInput.value = e.target.value);
            numInput.addEventListener('input', (e) => slider.value = e.target.value);
        }
    });

    // CSV Download Functionality
    document.getElementById('download-csv-btn').addEventListener('click', () => {
        if(historyLog.length === 0) {
            alert("Waiting for sensor data. Give the system a few seconds to log physical data.");
            return;
        }
        
        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "Timestamp,Node/River,pH,DO (mg/L),Turbidity (NTU),Temperature (C),AI_Inference\n";
        
        historyLog.forEach(row => {
            csvContent += `${row.timestamp},"${row.riverName}",${row.ph},${row.do},${row.turbidity},${row.temp},"${row.prediction}"\n`;
        });
        
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `AquaSense_Compliance_Log_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    document.getElementById('prediction-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {};
        fields.forEach(f => data[f] = document.getElementById(f).value);

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            // In physical mode, the dashboard will catch this via the polling anyway, 
            // but we can manually force an update here for visual zip.
        } catch (error) {
            console.error('Error:', error);
        }
    });

    // --- EPI CHART INITIALIZATION ---
    const ctx = document.getElementById('epiChart');
    if(ctx) {
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Finland', 'UK', 'USA', 'India', 'Pakistan', 'Chad'],
                datasets: [{
                    label: 'Water Quality Score (100 is best)',
                    data: [98, 85, 78, 24, 21, 15],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.6)',
                        'rgba(59, 130, 246, 0.6)',
                        'rgba(59, 130, 246, 0.6)',
                        'rgba(245, 158, 11, 0.6)',
                        'rgba(239, 68, 68, 0.6)',
                        'rgba(239, 68, 68, 0.6)'
                    ],
                    borderColor: [
                        'rgba(16, 185, 129, 1)',
                        'rgba(59, 130, 246, 1)',
                        'rgba(59, 130, 246, 1)',
                        'rgba(245, 158, 11, 1)',
                        'rgba(239, 68, 68, 1)',
                        'rgba(239, 68, 68, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#a0aabf' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#a0aabf' }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#ffffff' } },
                    title: {
                        display: true,
                        text: 'Global EPI Water Scores (2024)',
                        color: '#ffffff'
                    }
                }
            }
        });
    }


    // --- MARINE IMPACT CHART INITIALIZATION ---
    const marineCtx = document.getElementById('marineChart');
    if(marineCtx) {
        new Chart(marineCtx, {
            type: 'line',
            data: {
                labels: ['2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024'],
                datasets: [
                    {
                        label: 'Average Pollutant Concentration (mg/L)',
                        data: [45, 52, 60, 68, 75, 85, 78, 95, 110, 125, 140],
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Marine Population Viability (%)',
                        data: [90, 88, 82, 75, 68, 60, 65, 50, 42, 35, 28],
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { 
                        type: 'linear', display: true, position: 'left',
                        title: { display: true, text: 'Pollutants (mg/L)', color: '#ef4444' },
                        ticks: { color: '#ef4444' }, grid: { color: 'rgba(255,255,255,0.05)' } 
                    },
                    y1: { 
                        type: 'linear', display: true, position: 'right',
                        title: { display: true, text: 'Population Viability (%)', color: '#3b82f6' },
                        ticks: { color: '#3b82f6' }, grid: { drawOnChartArea: false } 
                    }
                },
                plugins: { legend: { labels: { color: '#cbd5e1' } } }
            }
        });
    }
});
