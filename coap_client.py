import asyncio
import argparse
import json
import sys
import aiocoap
import config

async def request_resource(resource_name, host=None, port=None):
    host = host or config.COAP_HOST
    port = port or config.COAP_PORT
    uri = f"coap://{host}:{port}/{resource_name.lstrip('/')}"
    
    print(f"[CoAP Client] Sending GET request to {uri} ...")
    protocol = await aiocoap.Context.create_client_context()
    
    request = aiocoap.Message(code=aiocoap.GET, uri=uri)
    
    try:
        response = await protocol.request(request).response
        print(f"[CoAP Client] Response Code: {response.code}")
        payload_str = response.payload.decode('utf-8')
        try:
            parsed = json.loads(payload_str)
            print(json.dumps(parsed, indent=2))
            return parsed
        except json.JSONDecodeError:
            print(payload_str)
            return payload_str
    except Exception as e:
        print(f"[CoAP Client] Request failed: {e}")
        return None
    finally:
        await protocol.shutdown()

def main():
    parser = argparse.ArgumentParser(description="CoAP Environmental Monitoring Client")
    parser.add_argument(
        "-r", "--resource",
        choices=["weather", "airquality", "all"],
        default="all",
        help="Resource to query via CoAP (default: all)"
    )
    parser.add_argument("--host", default=config.COAP_HOST, help="CoAP Server host")
    parser.add_argument("--port", type=int, default=config.COAP_PORT, help="CoAP Server port")
    
    args = parser.parse_args()

    if args.resource == "all":
        asyncio.run(request_resource("weather", args.host, args.port))
        print("-" * 50)
        asyncio.run(request_resource("airquality", args.host, args.port))
    else:
        asyncio.run(request_resource(args.resource, args.host, args.port))

if __name__ == "__main__":
    main()
