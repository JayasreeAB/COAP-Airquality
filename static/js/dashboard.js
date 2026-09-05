// Dashboard State Variables
let weatherChartInstance = null;
let airQualityChartInstance = null;
let autoRefreshTimer = null;

const chartMaxPoints = 15;
const historyData = {
    timestamps: [],
    temperature: [],
    humidity: [],
    windSpeed: [],
    pm10: [],
    pm25: [],
    co: [],
    no2: []
};

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    checkInfluxStatus();
    loadHistoryTable();
    // Auto fetch initial data on load
    fetchAllData();
});

// Toast Alert Engine
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let iconClass = 'fa-info-circle';
    if (type === 'success') iconClass = 'fa-check-circle';
    if (type === 'error') iconClass = 'fa-exclamation-triangle';
    
    toast.innerHTML = `<i class="fa-solid ${iconClass}"></i> <span>${message}</span>`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Format ISO Timestamps for Display
function formatTimestamp(isoStr) {
    if (!isoStr) return new Date().toLocaleTimeString();
    const dt = new Date(isoStr);
    return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// European AQI Evaluator
function getAqiBadgeInfo(aqiVal) {
    const val = parseInt(aqiVal);
    if (isNaN(val)) return { text: 'Unknown', class: 'aqi-unknown', desc: 'No index available' };
    if (val === 1) return { text: '1 - Good', class: 'aqi-good', desc: 'Air quality is considered satisfactory' };
    if (val === 2) return { text: '2 - Fair', class: 'aqi-fair', desc: 'Air quality is acceptable' };
    if (val === 3) return { text: '3 - Moderate', class: 'aqi-moderate', desc: 'Moderate pollution level' };
    if (val === 4) return { text: '4 - Poor', class: 'aqi-poor', desc: 'Air quality may affect sensitive groups' };
    if (val >= 5) return { text: `${val} - Very Poor`, class: 'aqi-verypoor', desc: 'Health alert: high risk level' };
    return { text: `${val}`, class: 'aqi-fair', desc: 'European AQI metric' };
}

// Update Metric UI Cards
function updateWeatherUI(data) {
    if (!data) return;
    document.getElementById('valTemperature').innerHTML = `${data.temperature_2m ?? '--'} <span class="unit">${data.temperature_unit || '°C'}</span>`;
    document.getElementById('valHumidity').innerHTML = `${data.relative_humidity_2m ?? '--'} <span class="unit">${data.humidity_unit || '%'}</span>`;
    document.getElementById('valWindSpeed').innerHTML = `${data.wind_speed_10m ?? '--'} <span class="unit">${data.wind_speed_unit || 'km/h'}</span>`;
    
    document.getElementById('lastSyncTime').innerText = formatTimestamp(data.timestamp);
    
    // Add to chart
    const label = formatTimestamp(data.timestamp);
    addChartDataPoint('weather', label, {
        temp: data.temperature_2m,
        hum: data.relative_humidity_2m,
        wind: data.wind_speed_10m
    });
}

function updateAirQualityUI(data) {
    if (!data) return;
    document.getElementById('valPm10').innerHTML = `${data.pm10 ?? '--'} <span class="unit">${data.pm10_unit || 'μg/m³'}</span>`;
    document.getElementById('valPm25').innerHTML = `${data.pm2_5 ?? '--'} <span class="unit">${data.pm2_5_unit || 'μg/m³'}</span>`;
    document.getElementById('valCo').innerHTML = `${data.carbon_monoxide ?? '--'} <span class="unit">${data.co_unit || 'μg/m³'}</span>`;
    document.getElementById('valNo2').innerHTML = `${data.nitrogen_dioxide ?? '--'} <span class="unit">${data.no2_unit || 'μg/m³'}</span>`;
    
    document.getElementById('valAqi').innerText = data.european_aqi ?? '--';
    
    const badgeInfo = getAqiBadgeInfo(data.european_aqi);
    const badgeElem = document.getElementById('valAqiBadge');
    badgeElem.innerText = badgeInfo.text;
    badgeElem.className = `aqi-badge ${badgeInfo.class}`;
    document.getElementById('valAqiDesc').innerText = badgeInfo.desc;
    
    // Add to chart
    const label = formatTimestamp(data.timestamp);
    addChartDataPoint('airquality', label, {
        pm10: data.pm10,
        pm25: data.pm2_5,
        co: data.carbon_monoxide,
        no2: data.nitrogen_dioxide
    });
}

// Chart Initialization
function initCharts() {
    const ctxW = document.getElementById('weatherChart').getContext('2d');
    weatherChartInstance = new Chart(ctxW, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: [],
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    tension: 0.35,
                    fill: true,
                    yAxisID: 'y'
                },
                {
                    label: 'Humidity (%)',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    tension: 0.35,
                    yAxisID: 'y1'
                },
                {
                    label: 'Wind Speed (km/h)',
                    data: [],
                    borderColor: '#14b8a6',
                    backgroundColor: 'transparent',
                    tension: 0.35,
                    yAxisID: 'y'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' }, position: 'left' },
                y1: { grid: { drawOnChartArea: false }, ticks: { color: '#3b82f6' }, position: 'right' }
            },
            plugins: { legend: { labels: { color: '#f1f5f9' } } }
        }
    });

    const ctxAQ = document.getElementById('airQualityChart').getContext('2d');
    airQualityChartInstance = new Chart(ctxAQ, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'PM2.5 (μg/m³)',
                    data: [],
                    borderColor: '#f97316',
                    backgroundColor: 'rgba(249, 115, 22, 0.1)',
                    tension: 0.35,
                    fill: true
                },
                {
                    label: 'PM10 (μg/m³)',
                    data: [],
                    borderColor: '#a855f7',
                    backgroundColor: 'transparent',
                    tension: 0.35
                },
                {
                    label: 'CO (μg/m³)',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'transparent',
                    tension: 0.35
                },
                {
                    label: 'NO₂ (μg/m³)',
                    data: [],
                    borderColor: '#f59e0b',
                    backgroundColor: 'transparent',
                    tension: 0.35
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
            },
            plugins: { legend: { labels: { color: '#f1f5f9' } } }
        }
    });
}

function addChartDataPoint(type, timeLabel, vals) {
    if (type === 'weather' && weatherChartInstance) {
        const labels = weatherChartInstance.data.labels;
        if (labels.length >= chartMaxPoints) labels.shift();
        labels.push(timeLabel);

        const ds = weatherChartInstance.data.datasets;
        if (ds[0].data.length >= chartMaxPoints) ds[0].data.shift();
        ds[0].data.push(vals.temp);

        if (ds[1].data.length >= chartMaxPoints) ds[1].data.shift();
        ds[1].data.push(vals.hum);

        if (ds[2].data.length >= chartMaxPoints) ds[2].data.shift();
        ds[2].data.push(vals.wind);

        weatherChartInstance.update();
    }

    if (type === 'airquality' && airQualityChartInstance) {
        const labels = airQualityChartInstance.data.labels;
        if (labels.length >= chartMaxPoints) labels.shift();
        labels.push(timeLabel);

        const ds = airQualityChartInstance.data.datasets;
        if (ds[0].data.length >= chartMaxPoints) ds[0].data.shift();
        ds[0].data.push(vals.pm25);

        if (ds[1].data.length >= chartMaxPoints) ds[1].data.shift();
        ds[1].data.push(vals.pm10);

        if (ds[2].data.length >= chartMaxPoints) ds[2].data.shift();
        ds[2].data.push(vals.co);

        if (ds[3].data.length >= chartMaxPoints) ds[3].data.shift();
        ds[3].data.push(vals.no2);

        airQualityChartInstance.update();
    }
}

// API CoAP Fetch Functions
async function fetchWeatherOnly() {
    showToast('Requesting /weather via CoAP GET...', 'info');
    try {
        const res = await fetch('/api/fetch/weather', { method: 'POST' });
        const result = await res.json();
        if (result.status === 'success') {
            updateWeatherUI(result.data);
            showToast(`Received Weather via CoAP! (${result.data.temperature_2m}°C)`, 'success');
            loadHistoryTable();
        } else {
            showToast(result.message || 'Failed to fetch weather via CoAP', 'error');
        }
    } catch (e) {
        showToast('Network error contacting Flask backend', 'error');
    }
}

async function fetchAirQualityOnly() {
    showToast('Requesting /airquality via CoAP GET...', 'info');
    try {
        const res = await fetch('/api/fetch/airquality', { method: 'POST' });
        const result = await res.json();
        if (result.status === 'success') {
            updateAirQualityUI(result.data);
            showToast(`Received Air Quality via CoAP! (AQI: ${result.data.european_aqi})`, 'success');
            loadHistoryTable();
        } else {
            showToast(result.message || 'Failed to fetch air quality via CoAP', 'error');
        }
    } catch (e) {
        showToast('Network error contacting Flask backend', 'error');
    }
}

async function fetchAllData() {
    const btn = document.getElementById('btnSyncAll');
    if (btn) btn.disabled = true;
    
    showToast('Triggering on-demand CoAP GET for /weather & /airquality...', 'info');
    try {
        const res = await fetch('/api/fetch/all', { method: 'POST' });
        const result = await res.json();
        if (result.status === 'success') {
            if (result.data.weather) updateWeatherUI(result.data.weather);
            if (result.data.airquality) updateAirQualityUI(result.data.airquality);
            showToast('All Environmental Data Synced via CoAP & Saved to InfluxDB!', 'success');
            loadHistoryTable();
        } else {
            showToast(result.message || 'Failed to fetch data via CoAP', 'error');
        }
    } catch (e) {
        showToast('Network error: ensure CoAP server & Flask app are running', 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
}

// Auto Refresh Mechanism
function toggleAutoRefresh(seconds) {
    if (autoRefreshTimer) {
        clearInterval(autoRefreshTimer);
        autoRefreshTimer = null;
    }
    const sec = parseInt(seconds);
    if (sec > 0) {
        showToast(`Auto sync activated: every ${sec} seconds`, 'info');
        autoRefreshTimer = setInterval(() => {
            fetchAllData();
        }, sec * 1000);
    } else {
        showToast('Auto sync disabled', 'info');
    }
}

// History Table Renderer
async function loadHistoryTable() {
    try {
        const res = await fetch('/api/history');
        const data = await res.json();
        const tbody = document.getElementById('historyTableBody');
        tbody.innerHTML = '';

        if (!data.history || data.history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-msg">No CoAP data fetched yet. Click "Fetch All via CoAP" to retrieve live metrics.</td></tr>';
            return;
        }

        data.history.forEach(item => {
            const tr = document.createElement('tr');
            
            let summaryText = '';
            if (item.type === 'Weather') {
                summaryText = `Temp: ${item.data.temperature_2m}°C | Hum: ${item.data.relative_humidity_2m}% | Wind: ${item.data.wind_speed_10m}km/h`;
            } else {
                summaryText = `PM2.5: ${item.data.pm2_5}μg/m³ | PM10: ${item.data.pm10}μg/m³ | AQI: ${item.data.european_aqi}`;
            }

            const influxStatusBadge = item.influx_status === 'success' 
                ? '<span class="status-dot success"></span> Synced to Cloud'
                : '<span class="status-dot warning"></span> Buffered Locally';

            tr.innerHTML = `
                <td><code>${formatTimestamp(item.timestamp)}</code></td>
                <td><span class="endpoint-badge">${item.type === 'Weather' ? '/weather' : '/airquality'}</span></td>
                <td>${summaryText}</td>
                <td>${influxStatusBadge}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error('Failed to load history table:', e);
    }
}

// InfluxDB Modal & Configuration
async function checkInfluxStatus() {
    try {
        const res = await fetch('/api/influx/status');
        const info = await res.json();
        
        const pillText = document.getElementById('influxStatusText');
        const pillDot = document.querySelector('#influxStatusPill .status-dot');
        const modalMsg = document.getElementById('modalConnMessage');
        
        if (info.connection.configured && info.connection.status === 'pass') {
            pillText.innerText = 'InfluxDB Cloud: Connected';
            pillDot.className = 'status-dot success';
            modalMsg.innerText = `Connected (${info.url})`;
            modalMsg.style.color = '#34d399';
        } else if (!info.connection.configured) {
            pillText.innerText = 'InfluxDB: Local Buffer Mode';
            pillDot.className = 'status-dot warning';
            modalMsg.innerText = info.connection.message;
            modalMsg.style.color = '#fbbf24';
        } else {
            pillText.innerText = 'InfluxDB: Error';
            pillDot.className = 'status-dot danger';
            modalMsg.innerText = info.connection.message;
            modalMsg.style.color = '#f87171';
        }
        
        document.getElementById('cfgInfluxUrl').value = info.url || '';
        document.getElementById('cfgInfluxOrg').value = info.org || '';
        document.getElementById('cfgInfluxBucket').value = info.bucket || '';
    } catch (e) {
        console.error('Influx status check error:', e);
    }
}

function openInfluxModal() {
    document.getElementById('influxModal').classList.add('active');
    checkInfluxStatus();
}

function closeInfluxModal() {
    document.getElementById('influxModal').classList.remove('active');
}

async function saveInfluxConfig() {
    const payload = {
        url: document.getElementById('cfgInfluxUrl').value,
        token: document.getElementById('cfgInfluxToken').value,
        org: document.getElementById('cfgInfluxOrg').value,
        bucket: document.getElementById('cfgInfluxBucket').value
    };
    
    try {
        const res = await fetch('/api/influx/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        showToast('InfluxDB settings updated successfully!', 'success');
        checkInfluxStatus();
        closeInfluxModal();
    } catch (e) {
        showToast('Failed to update InfluxDB settings', 'error');
    }
}
