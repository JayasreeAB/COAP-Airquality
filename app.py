import asyncio
import json
import logging
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify, request
import aiocoap
import config
from influx_client import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FlaskDashboard")

app = Flask(__name__)

# Global log history for local UI table display
history_log = []

async def fetch_coap_resource(resource_path):
    """Asynchronously issues CoAP GET request to server."""
    host = config.COAP_HOST
    port = config.COAP_PORT
    uri = f"coap://{host}:{port}/{resource_path.lstrip('/')}"
    
    logger.info(f"[Flask Backend] Querying CoAP resource: {uri}")
    context = await aiocoap.Context.create_client_context()
    
    try:
        coap_req = aiocoap.Message(code=aiocoap.GET, uri=uri)
        response = await context.request(coap_req).response
        payload_str = response.payload.decode('utf-8')
        data = json.loads(payload_str)
        return {"success": True, "code": str(response.code), "data": data}
    except Exception as e:
        logger.error(f"[Flask Backend] CoAP fetch error for {uri}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        await context.shutdown()

def run_coap_fetch(resource_path):
    """Helper to run async CoAP fetch in synchronous Flask route."""
    try:
        return asyncio.run(fetch_coap_resource(resource_path))
    except Exception as e:
        # Fallback if event loop already active in current thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(fetch_coap_resource(resource_path))
        finally:
            loop.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/fetch/weather', methods=['POST'])
def get_weather():
    result = run_coap_fetch('weather')
    if result.get("success"):
        weather_data = result["data"]
        # Save to InfluxDB Cloud
        db_res = db_manager.write_weather_data(weather_data)
        
        history_entry = {
            "type": "Weather",
            "timestamp": weather_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "data": weather_data,
            "influx_status": db_res.get("status")
        }
        history_log.insert(0, history_entry)
        
        return jsonify({
            "status": "success",
            "coap_code": result["code"],
            "data": weather_data,
            "influx": db_res
        })
    else:
        return jsonify({
            "status": "error",
            "message": f"CoAP Request Failed: {result.get('error')}"
        }), 500

@app.route('/api/fetch/airquality', methods=['POST'])
def get_airquality():
    result = run_coap_fetch('airquality')
    if result.get("success"):
        aq_data = result["data"]
        # Save to InfluxDB Cloud
        db_res = db_manager.write_airquality_data(aq_data)
        
        history_entry = {
            "type": "Air Quality",
            "timestamp": aq_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "data": aq_data,
            "influx_status": db_res.get("status")
        }
        history_log.insert(0, history_entry)
        
        return jsonify({
            "status": "success",
            "coap_code": result["code"],
            "data": aq_data,
            "influx": db_res
        })
    else:
        return jsonify({
            "status": "error",
            "message": f"CoAP Request Failed: {result.get('error')}"
        }), 500

@app.route('/api/fetch/all', methods=['POST'])
def get_all():
    weather_res = run_coap_fetch('weather')
    aq_res = run_coap_fetch('airquality')
    
    response_payload = {
        "weather": None,
        "airquality": None,
        "influx_weather": None,
        "influx_airquality": None
    }
    
    if weather_res.get("success"):
        w_data = weather_res["data"]
        response_payload["weather"] = w_data
        response_payload["influx_weather"] = db_manager.write_weather_data(w_data)
        history_log.insert(0, {
            "type": "Weather",
            "timestamp": w_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "data": w_data,
            "influx_status": response_payload["influx_weather"].get("status")
        })

    if aq_res.get("success"):
        aq_data = aq_res["data"]
        response_payload["airquality"] = aq_data
        response_payload["influx_airquality"] = db_manager.write_airquality_data(aq_data)
        history_log.insert(0, {
            "type": "Air Quality",
            "timestamp": aq_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "data": aq_data,
            "influx_status": response_payload["influx_airquality"].get("status")
        })

    if weather_res.get("success") or aq_res.get("success"):
        return jsonify({
            "status": "success",
            "data": response_payload
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Both weather and air quality CoAP requests failed. Ensure CoAP server is running."
        }), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify({
        "status": "success",
        "history": history_log[:50]
    })

@app.route('/api/influx/status', methods=['GET'])
def get_influx_status():
    status = db_manager.check_connection()
    return jsonify({
        "url": db_manager.url,
        "org": db_manager.org,
        "bucket": db_manager.bucket,
        "connection": status
    })

@app.route('/api/influx/config', methods=['POST'])
def update_influx_config():
    data = request.json or {}
    if "url" in data:
        db_manager.url = data["url"]
    if "token" in data:
        db_manager.token = data["token"]
    if "org" in data:
        db_manager.org = data["org"]
    if "bucket" in data:
        db_manager.bucket = data["bucket"]
        
    status = db_manager.check_connection()
    return jsonify({
        "status": "updated",
        "connection": status
    })

if __name__ == '__main__':
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=True)
