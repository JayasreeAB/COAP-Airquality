import unittest
import asyncio
import json
import urllib.request
import config
from influx_client import InfluxDBManager
from coap_server import fetch_url_json

class TestCoAPEnvironmentalSystem(unittest.TestCase):

    def test_open_meteo_weather_api(self):
        """Test live Open-Meteo weather API structure for Kalamassery."""
        url = config.OPEN_METEO_WEATHER_URL
        data = fetch_url_json(url)
        self.assertIn("current", data)
        current = data["current"]
        
        self.assertIn("temperature_2m", current, "temperature_2m missing from weather API")
        self.assertIn("relative_humidity_2m", current, "relative_humidity_2m missing from weather API")
        self.assertIn("wind_speed_10m", current, "wind_speed_10m missing from weather API")
        
        print(f"\n[Test] Open-Meteo Weather Data: Temp={current['temperature_2m']}°C, Humidity={current['relative_humidity_2m']}%, Wind={current['wind_speed_10m']}km/h")

    def test_open_meteo_airquality_api(self):
        """Test live Open-Meteo air quality API structure for Kalamassery."""
        url = config.OPEN_METEO_AIRQUALITY_URL
        data = fetch_url_json(url)
        self.assertIn("current", data)
        current = data["current"]
        
        self.assertIn("pm10", current, "pm10 missing from air quality API")
        self.assertIn("pm2_5", current, "pm2_5 missing from air quality API")
        self.assertIn("carbon_monoxide", current, "carbon_monoxide missing from air quality API")
        self.assertIn("nitrogen_dioxide", current, "nitrogen_dioxide missing from air quality API")
        self.assertIn("european_aqi", current, "european_aqi missing from air quality API")
        
        print(f"\n[Test] Open-Meteo Air Quality Data: PM10={current['pm10']}, PM2.5={current['pm2_5']}, CO={current['carbon_monoxide']}, NO2={current['nitrogen_dioxide']}, AQI={current['european_aqi']}")

    def test_influxdb_manager_buffering(self):
        """Test InfluxDB manager point construction and fallback buffering."""
        manager = InfluxDBManager()
        
        sample_weather = {
            "temperature_2m": 31.5,
            "relative_humidity_2m": 72.0,
            "wind_speed_10m": 12.4,
            "timestamp": "2026-09-05T10:00:00+00:00"
        }
        res_w = manager.write_weather_data(sample_weather)
        self.assertIn(res_w["status"], ["buffered_locally", "success"])
        
        sample_aq = {
            "pm10": 25.4,
            "pm2_5": 14.2,
            "carbon_monoxide": 210.0,
            "nitrogen_dioxide": 18.5,
            "european_aqi": 2,
            "timestamp": "2026-09-05T10:00:00+00:00"
        }
        res_aq = manager.write_airquality_data(sample_aq)
        self.assertIn(res_aq["status"], ["buffered_locally", "success"])
        
        self.assertGreaterEqual(len(manager.local_buffer), 2)
        print(f"\n[Test] InfluxDB local buffering verified successfully. Buffer size: {len(manager.local_buffer)}")

if __name__ == '__main__':
    unittest.main()
