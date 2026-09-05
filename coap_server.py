import asyncio
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
import aiocoap
import aiocoap.resource as resource
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("CoAPServer")

def fetch_url_json(url):
    """Synchronous HTTP GET helper to fetch JSON from external APIs."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CoAP-Environmental-Monitoring-System/1.0"}
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        if response.status == 200:
            return json.loads(response.read().decode('utf-8'))
        else:
            raise Exception(f"HTTP request failed with status code {response.status}")

class WeatherResource(resource.Resource):
    """
    CoAP Resource for /weather
    Retrieves weather data from Open-Meteo API ON DEMAND when requested.
    Location: Kalamassery (Lat: 10.0159, Lon: 76.3419)
    """
    async def render_get(self, request):
        logger.info("[CoAP Server] Received GET request on resource /weather")
        try:
            # On-demand retrieval from Open-Meteo Weather API
            loop = asyncio.get_event_loop()
            raw_data = await loop.run_in_executor(None, fetch_url_json, config.OPEN_METEO_WEATHER_URL)
            
            current = raw_data.get("current", {})
            units = raw_data.get("current_units", {})
            
            payload_data = {
                "resource": "/weather",
                "location": "Kalamassery",
                "latitude": config.LATITUDE,
                "longitude": config.LONGITUDE,
                "temperature_2m": current.get("temperature_2m"),
                "temperature_unit": units.get("temperature_2m", "°C"),
                "relative_humidity_2m": current.get("relative_humidity_2m"),
                "humidity_unit": units.get("relative_humidity_2m", "%"),
                "wind_speed_10m": current.get("wind_speed_10m"),
                "wind_speed_unit": units.get("wind_speed_10m", "km/h"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "success"
            }
            
            logger.info(f"[CoAP Server] Successfully fetched weather data: Temp={payload_data['temperature_2m']}{payload_data['temperature_unit']}, Humidity={payload_data['relative_humidity_2m']}{payload_data['humidity_unit']}, Wind={payload_data['wind_speed_10m']}{payload_data['wind_speed_unit']}")
            
            payload_bytes = json.dumps(payload_data, indent=2).encode('utf-8')
            # Content format 50 = application/json
            return aiocoap.Message(payload=payload_bytes, content_format=50)

        except Exception as e:
            logger.error(f"[CoAP Server] Error fetching /weather data: {e}")
            error_payload = {
                "resource": "/weather",
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            return aiocoap.Message(
                code=aiocoap.INTERNAL_SERVER_ERROR,
                payload=json.dumps(error_payload).encode('utf-8'),
                content_format=50
            )

class AirQualityResource(resource.Resource):
    """
    CoAP Resource for /airquality
    Retrieves air quality data from Open-Meteo API ON DEMAND when requested.
    Location: Kalamassery (Lat: 10.0159, Lon: 76.3419)
    """
    async def render_get(self, request):
        logger.info("[CoAP Server] Received GET request on resource /airquality")
        try:
            # On-demand retrieval from Open-Meteo Air Quality API
            loop = asyncio.get_event_loop()
            raw_data = await loop.run_in_executor(None, fetch_url_json, config.OPEN_METEO_AIRQUALITY_URL)
            
            current = raw_data.get("current", {})
            units = raw_data.get("current_units", {})
            
            payload_data = {
                "resource": "/airquality",
                "location": "Kalamassery",
                "latitude": config.LATITUDE,
                "longitude": config.LONGITUDE,
                "pm10": current.get("pm10"),
                "pm10_unit": units.get("pm10", "μg/m³"),
                "pm2_5": current.get("pm2_5"),
                "pm2_5_unit": units.get("pm2_5", "μg/m³"),
                "carbon_monoxide": current.get("carbon_monoxide"),
                "co_unit": units.get("carbon_monoxide", "μg/m³"),
                "nitrogen_dioxide": current.get("nitrogen_dioxide"),
                "no2_unit": units.get("nitrogen_dioxide", "μg/m³"),
                "european_aqi": current.get("european_aqi"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "success"
            }
            
            logger.info(f"[CoAP Server] Successfully fetched air quality data: PM10={payload_data['pm10']}, PM2.5={payload_data['pm2_5']}, CO={payload_data['carbon_monoxide']}, NO2={payload_data['nitrogen_dioxide']}, AQI={payload_data['european_aqi']}")
            
            payload_bytes = json.dumps(payload_data, indent=2).encode('utf-8')
            # Content format 50 = application/json
            return aiocoap.Message(payload=payload_bytes, content_format=50)

        except Exception as e:
            logger.error(f"[CoAP Server] Error fetching /airquality data: {e}")
            error_payload = {
                "resource": "/airquality",
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            return aiocoap.Message(
                code=aiocoap.INTERNAL_SERVER_ERROR,
                payload=json.dumps(error_payload).encode('utf-8'),
                content_format=50
            )

async def main():
    # Construct root resource tree
    root = resource.Site()
    root.add_resource(['weather'], WeatherResource())
    root.add_resource(['airquality'], AirQualityResource())

    host = config.COAP_HOST
    port = config.COAP_PORT

    logger.info(f"Starting CoAP Environmental Server on coap://{host}:{port}")
    logger.info("Serving resources:")
    logger.info(f" - coap://{host}:{port}/weather")
    logger.info(f" - coap://{host}:{port}/airquality")

    await aiocoap.Context.create_server_context(root, bind=(host, port))
    
    # Run forever
    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("CoAP Server stopped by user.")
