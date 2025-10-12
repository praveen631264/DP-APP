
document.addEventListener('DOMContentLoaded', function() {

    const incidentList = document.getElementById('incident-list');
    const systemStatus = document.getElementById('system-status');
    const API_URL = '/api/v1/incidents';
    const REFRESH_INTERVAL = 5000; // 5 seconds

    const renderIncidents = (incidents) => {
        if (!incidents || incidents.length === 0) {
            incidentList.innerHTML = `<div class="loading">No incidents recorded. The system is clean.</div>`;
            return;
        }

        incidentList.innerHTML = incidents.map(incident => {
            const logData = JSON.parse(incident.log_line || '{}');
            const formattedTimestamp = new Date(incident.timestamp).toLocaleString();
            const statusClass = incident.status.toLowerCase().replace(/_/g, '-');

            return `
                <div class="incident-card">
                    <div class="header">
                        <span class="status ${statusClass}">${incident.status.replace(/_/g, ' ')}</span>
                        <span class="id">${incident.incident_id}</span>
                    </div>
                    <div class="body">
                        <p><strong>Timestamp:</strong> ${formattedTimestamp}</p>
                        <p><strong>Error Type:</strong> ${incident.error_type}</p>
                        <div class="log-details">
                           <strong>Log Message:</strong> ${logData.message || 'N/A'}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    };

    const fetchIncidents = async () => {
        try {
            const response = await fetch(API_URL);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const incidents = await response.json();
            renderIncidents(incidents);
            systemStatus.textContent = 'OK';
            systemStatus.className = 'status-ok';
        } catch (error) {
            console.error("Failed to fetch incidents:", error);
            incidentList.innerHTML = `<div class="loading">Error loading incidents. Could not connect to the server.</div>`;
            systemStatus.textContent = 'ERROR';
            systemStatus.className = 'status-error';
        }
    };

    // Initial fetch and then set interval
    fetchIncidents();
    setInterval(fetchIncidents, REFRESH_INTERVAL);
});
