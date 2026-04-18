document.addEventListener('DOMContentLoaded', () => {
    
    // Sync sliders and number inputs dynamically for the 4 physical sensors
    const fields = ['ph', 'do', 'turbidity', 'temperature'];
    
    fields.forEach(id => {
        const slider = document.getElementById(`${id}-slider`);
        const numInput = document.getElementById(id);

        if(slider && numInput) {
            slider.addEventListener('input', (e) => {
                numInput.value = e.target.value;
            });

            numInput.addEventListener('input', (e) => {
                slider.value = e.target.value;
            });
        }
    });

    const form = document.getElementById('prediction-form');
    const resultsContainer = document.getElementById('results-display');
    const btn = document.querySelector('.analyze-btn');

    // --- Core UI Update Function ---
    function renderResult(result) {
        resultsContainer.className = `results-container status-${result.color}`;
        resultsContainer.innerHTML = `
            <div class="result-status" style="font-size: 1.8rem;">${result.pollutant}</div>
            <div style="font-weight: bold; margin-bottom: 1rem; color: #cbd5e1; letter-spacing: 1px;">POLLUTANT STATE: <span style="color:white;">${result.state}</span></div>
            <div class="result-message" style="margin-bottom: 1rem;">${result.details}</div>
            <div style="padding: 15px; background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; border-radius: 8px; font-weight: bold; margin-top: 15px; color: #10b981;">
                RIVER CLEANING STRATEGY: ${result.action}
            </div>
        `;
    }

    // --- Manual Submission ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // UI Loading state
        const originalBtnText = btn.textContent;
        btn.textContent = 'AI is deducing hidden pollutants...';
        btn.disabled = true;

        // Gather basic sensor data
        const data = {};
        fields.forEach(f => {
            data[f] = document.getElementById(f).value;
        });

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Server error occurred');

            renderResult(result);
            
            if (window.innerWidth <= 900) {
                document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
            }

        } catch (error) {
            console.error('Error:', error);
            resultsContainer.className = 'results-container';
            resultsContainer.innerHTML = `<div class="result-status" style="color: #ef4444;">Error</div><div class="result-message">${error.message}</div>`;
        } finally {
            btn.textContent = originalBtnText;
            btn.disabled = false;
        }
    });

    // --- Live IoT Stream Mode ---
    const liveToggle = document.getElementById('live-mode-toggle');
    const inputPanel = document.querySelector('.input-panel');
    let pollingInterval = null;

    liveToggle.addEventListener('change', (e) => {
        if (e.target.checked) {
            // Enable Live Mode
            inputPanel.style.opacity = '0.4';
            inputPanel.style.pointerEvents = 'none'; // Disable manual input
            
            pollingInterval = setInterval(async () => {
                try {
                    const response = await fetch('/api/live');
                    const data = await response.json();

                    // Update the Sliders and Inputs visibly to match hardware data
                    fields.forEach(f => {
                        const val = data.raw_sensors[f];
                        if (val !== undefined) {
                            document.getElementById(f).value = val;
                            document.getElementById(`${f}-slider`).value = val;
                        }
                    });

                    // Render the AI Payload
                    renderResult(data.prediction);
                } catch (error) {
                    console.error("Live Stream polling failed", error);
                }
            }, 2000); // Poll every 2 seconds
        } else {
            // Disable Live Mode
            inputPanel.style.opacity = '1';
            inputPanel.style.pointerEvents = 'auto'; // Enable manual input
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    });
});
