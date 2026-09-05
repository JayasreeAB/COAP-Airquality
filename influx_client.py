import logging
from datetime import datetime, timezone
import config

try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUX_AVAILABLE = True
except ImportError:
    INFLUX_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("InfluxDBManager")

class InfluxDBManager:
    """Handles data storage to InfluxDB Cloud / local InfluxDB instance."""
    
    def __init__(self, url=None, token=None, org=None, bucket=None):
        self.url = url or config.INFLUXDB_URL
        self.token = token or config.INFLUXDB_TOKEN
        self.org = org or config.INFLUXDB_ORG
        self.bucket = bucket or config.INFLUXDB_BUCKET
        self.local_buffer = []

    def _is_configured(self):
        return (
            INFLUX_AVAILABLE 
            and self.token 
            and self.token != "YOUR_INFLUXDB_TOKEN"
            and self.org != "YOUR_INFLUXDB_ORG"
        )

    def write_weather_data(self, weather_data):
        """
        Writes weather data to InfluxDB measurement 'weather'.
        Expected weather_data structure:
        {
            "temperature_2m": float,
            "relative_humidity_2m": float,
            "wind_speed_10m": float,
            "timestamp": ISO-string or datetime
        }
        """
        ts = weather_data.get("timestamp")
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts)
            except ValueError:
                dt = datetime.now(timezone.utc)
        elif isinstance(ts, datetime):
            dt = ts
        else:
            dt = datetime.now(timezone.utc)

        record_entry = {
            "measurement": "weather",
            "location": "Kalamassery",
            "temperature_2m": float(weather_data.get("temperature_2m", 0.0)),
            "relative_humidity_2m": float(weather_data.get("relative_humidity_2m", 0.0)),
            "wind_speed_10m": float(weather_data.get("wind_speed_10m", 0.0)),
            "timestamp": dt.isoformat()
        }
        self.local_buffer.append(record_entry)

        if not self._is_configured():
            logger.info(f"[Local Buffer] Weather data stored locally: {record_entry}")
            return {"status": "buffered_locally", "entry": record_entry}

        try:
            with InfluxDBClient(url=self.url, token=self.token, org=self.org) as client:
                write_api = client.write_api(write_options=SYNCHRONOUS)
                point = (
                    Point("weather")
                    .tag("location", "Kalamassery")
                    .field("temperature_2m", record_entry["temperature_2m"])
                    .field("relative_humidity_2m", record_entry["relative_humidity_2m"])
                    .field("wind_speed_10m", record_entry["wind_speed_10m"])
                    .time(dt, WritePrecision.NS)
                )
                write_api.write(bucket=self.bucket, org=self.org, record=point)
                logger.info(f"[InfluxDB Cloud] Successfully wrote weather data point for Kalamassery at {dt.isoformat()}")
                return {"status": "success", "point": record_entry}
        except Exception as e:
            logger.error(f"[InfluxDB Cloud] Failed to write weather data: {e}")
            return {"status": "error", "error": str(e), "entry": record_entry}

    def write_airquality_data(self, aq_data):
        """
        Writes air quality data to InfluxDB measurement 'air_quality'.
        Expected aq_data structure:
        {
            "pm10": float,
            "pm2_5": float,
            "carbon_monoxide": float,
            "nitrogen_dioxide": float,
            "european_aqi": int/float,
            "timestamp": ISO-string or datetime
        }
        """
        ts = aq_data.get("timestamp")
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts)
            except ValueError:
                dt = datetime.now(timezone.utc)
        elif isinstance(ts, datetime):
            dt = ts
        else:
            dt = datetime.now(timezone.utc)

        record_entry = {
            "measurement": "air_quality",
            "location": "Kalamassery",
            "pm10": float(aq_data.get("pm10", 0.0)),
            "pm2_5": float(aq_data.get("pm2_5", 0.0)),
            "carbon_monoxide": float(aq_data.get("carbon_monoxide", 0.0)),
            "nitrogen_dioxide": float(aq_data.get("nitrogen_dioxide", 0.0)),
            "european_aqi": float(aq_data.get("european_aqi", 0.0)),
            "timestamp": dt.isoformat()
        }
        self.local_buffer.append(record_entry)

        if not self._is_configured():
            logger.info(f"[Local Buffer] Air quality data stored locally: {record_entry}")
            return {"status": "buffered_locally", "entry": record_entry}

        try:
            with InfluxDBClient(url=self.url, token=self.token, org=self.org) as client:
                write_api = client.write_api(write_options=SYNCHRONOUS)
                point = (
                    Point("air_quality")
                    .tag("location", "Kalamassery")
                    .field("pm10", record_entry["pm10"])
                    .field("pm2_5", record_entry["pm2_5"])
                    .field("carbon_monoxide", record_entry["carbon_monoxide"])
                    .field("nitrogen_dioxide", record_entry["nitrogen_dioxide"])
                    .field("european_aqi", record_entry["european_aqi"])
                    .time(dt, WritePrecision.NS)
                )
                write_api.write(bucket=self.bucket, org=self.org, record=point)
                logger.info(f"[InfluxDB Cloud] Successfully wrote air quality point for Kalamassery at {dt.isoformat()}")
                return {"status": "success", "point": record_entry}
        except Exception as e:
            logger.error(f"[InfluxDB Cloud] Failed to write air quality data: {e}")
            return {"status": "error", "error": str(e), "entry": record_entry}

    def check_connection(self):
        """Checks if InfluxDB client can reach the specified instance."""
        if not self._is_configured():
            return {
                "configured": False,
                "status": "Not Configured",
                "message": "Default placeholder token in use. Provide valid INFLUXDB_TOKEN & ORG to push to InfluxDB Cloud."
            }
        try:
            with InfluxDBClient(url=self.url, token=self.token, org=self.org) as client:
                health = client.health()
                return {
                    "configured": True,
                    "status": health.status,
                    "message": health.message or "Connected to InfluxDB Cloud"
                }
        except Exception as e:
            return {
                "configured": True,
                "status": "Connection Error",
                "message": str(e)
            }

# Default singleton instance
db_manager = InfluxDBManager()
