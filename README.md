# CoAP-based Environmental Monitoring System (Kalamassery)

An end-to-end CoAP (Constrained Application Protocol) Environmental Monitoring System built in Python. The system provides on-demand weather and air quality monitoring for **Kalamassery, Kerala** (Latitude: `10.0159`, Longitude: `76.3419`), featuring a CoAP Server, a Flask dynamic web dashboard, and InfluxDB Cloud storage integration.

---

## 🌟 Key Features

1. **On-Demand CoAP Server (`coap_server.py`)**:
   - Exposes two CoAP resources:
     - `coap://127.0.0.1:5683/weather`
     - `coap://127.0.0.1:5683/airquality`
   - Data is retrieved from external **Open-Meteo APIs ON DEMAND** only when a client request arrives.

2. **Required Environmental Data Metrics**:
   - **Weather Resource (`/weather`)**:
     - Temperature (`temperature_2m` in °C)
     - Relative Humidity (`relative_humidity_2m` in %)
     - Wind Speed (`wind_speed_10m` in km/h)
   - **Air Quality Resource (`/airquality`)**:
     - Particulate Matter 10 (`pm10` in μg/m³)
     - Fine Particulate Matter 2.5 (`pm2_5` in μg/m³)
     - Carbon Monoxide (`carbon_monoxide` in μg/m³)
     - Nitrogen Dioxide (`nitrogen_dioxide` in μg/m³)
     - European Air Quality Index (`european_aqi`)

3. **Modern Flask Web Dashboard (`app.py` & Frontend)**:
   - Dynamic real-time UI with dark aesthetic theme, glassmorphism cards, and Google Fonts.
   - Interactive visual charts powered by Chart.js.
   - European AQI visual status badge with color coding (Good, Fair, Moderate, Poor, Very Poor).
   - Auto-sync periodic polling toggle (Off, 10s, 30s, 60s).
   - Recent CoAP transaction log table.

4. **InfluxDB Cloud Data Storage (`influx_client.py`)**:
   - Stores retrieved environmental measurements with accurate UTC ISO timestamps into InfluxDB Cloud / InfluxDB instance.
   - Automatic local buffer fallback for offline / credential-free testing.

---

## 📁 Repository Structure

```
coap airquality/
├── config.py              # Central system configuration & coordinates
├── influx_client.py       # InfluxDB Cloud client & local buffer fallback
├── coap_server.py         # aiocoap Server for /weather & /airquality
├── coap_client.py         # CLI CoAP Client for direct testing
├── app.py                 # Flask Dashboard Web Application backend
├── templates/
│   └── index.html         # Responsive modern HTML5 dashboard
├── static/
│   ├── css/
│   │   └── style.css      # Dark theme UI stylesheet
│   └── js/
│       └── dashboard.js   # Client-side dynamic charts & CoAP interaction
├── test_coap_system.py    # Automated test suite
├── requirements.txt       # Dependencies list
├── .env.example           # Environment variables template
└── README.md              # System documentation
```

---

## 🚀 Getting Started

### 1. Installation

Ensure Python 3.9+ is installed. Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 2. Configuration (Optional for InfluxDB Cloud)

Copy `.env.example` to `.env` and enter your InfluxDB Cloud credentials:

```ini
INFLUXDB_URL=https://us-east-1-1.aws.cloud2.influxdata.com
INFLUXDB_TOKEN=your_influxdb_cloud_api_token
INFLUXDB_ORG=your_org_email
INFLUXDB_BUCKET=coap_environmental_data
```

*(Note: If no token is configured, the system automatically runs in **Local Buffer Mode**, storing points locally and allowing full web dashboard interaction.)*

---

## 🏃 Running the System

### Step 1: Start the CoAP Server
Open a terminal and run:

```bash
python coap_server.py
```
*Outputs:*
```
Starting CoAP Environmental Server on coap://127.0.0.1:5683
Serving resources:
 - coap://127.0.0.1:5683/weather
 - coap://127.0.0.1:5683/airquality
```

### Step 2: Test via CLI CoAP Client (Optional)
In a second terminal, send a CoAP GET request directly:

```bash
# Query /weather
python coap_client.py -r weather

# Query /airquality
python coap_client.py -r airquality
```

### Step 3: Launch the Web Dashboard
In a separate terminal, launch the Flask application:

```bash
python app.py
```

Open your web browser and navigate to:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🧪 Running Automated Tests

To execute the unit test suite and verify API endpoints and InfluxDB point building:

```bash
python test_coap_system.py
```

---

## 📡 API Reference & External Sources

- **Weather API (Kalamassery Location)**:
  `https://api.open-meteo.com/v1/forecast?latitude=10.0159&longitude=76.3419&current=temperature_2m,relative_humidity_2m,wind_speed_10m`
- **Air Quality API (Kalamassery Location)**:
  `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=10.0159&longitude=76.3419&current=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,european_aqi`
