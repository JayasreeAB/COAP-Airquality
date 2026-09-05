import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# Kalamassery Location Coordinates
LATITUDE = 10.0159
LONGITUDE = 76.3419

# Open-Meteo API Endpoints
OPEN_METEO_WEATHER_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
OPEN_METEO_AIRQUALITY_URL = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={LATITUDE}&longitude={LONGITUDE}&current=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,european_aqi"

# CoAP Server Settings
COAP_HOST = os.getenv("COAP_HOST", "127.0.0.1")
COAP_PORT = int(os.getenv("COAP_PORT", "5683"))

# InfluxDB Cloud / Database Configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "https://us-east-1-1.aws.cloud2.influxdata.com")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "YOUR_INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "YOUR_INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "coap_environmental_data")

# Dashboard Settings
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
