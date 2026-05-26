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

        // Section A: Raw parameters
        metricPh.innerText = parseFloat(rawSensors.ph).toFixed(2);
        metricDo.innerText = `${parseFloat(rawSensors.do).toFixed(1)} mg/L`;
        metricTurb.innerText = `${Math.round(rawSensors.turbidity)} NTU`;
        metricTemp.innerText = `${parseFloat(rawSensors.temperature).toFixed(1)}°C`;
        
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

    // --- DIRECTORY INFERENCE QUERY ---
    generateReportBtn.addEventListener('click', async () => {
        const selectedId = riverSelect.value;
        if (!selectedId) {
            alert('Please select a river system from the directory first.');
            return;
        }

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
                // Short timeout for realistic Apple-style dashboard inference load transition
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
