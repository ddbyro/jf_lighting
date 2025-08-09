"""
Jellyfish Lighting API Client
"""
import websocket
import json
import logging

_LOGGER = logging.getLogger(__name__)

class JellyfishLightingAPI:
    def __init__(self, host: str, api_key: str = None):
        self.host = host
        self.api_key = api_key
        self.ws_url = f"ws://{host}:9000/ws"

    def _send_ws(self, payload):
        try:
            ws = websocket.WebSocket()
            ws.connect(self.ws_url)
            ws.send(json.dumps(payload))
            resp = ws.recv()
            ws.close()
            return json.loads(resp)
        except Exception as e:
            _LOGGER.error(f"WebSocket error: {e}")
            return None

    def get_state(self):
        payload = {"cmd": "toCtlrGet", "get": [["ledPower"]]}
        resp = self._send_ws(payload)
        return resp["ledPower"] if resp and "ledPower" in resp else None

    def get_patterns(self):
        payload = {"cmd": "toCtlrGet", "get": [["patternFileList"]]}
        resp = self._send_ws(payload)
        return resp["patternFileList"] if resp and "patternFileList" in resp else []

    def get_groups(self):
        # Build a list of dicts with group name and id (if available)
        patterns = self.get_patterns()
        groups = {}
        for pattern in patterns:
            folder = pattern.get("folders")
            if folder:
                if folder not in groups:
                    groups[folder] = {"name": folder, "patterns": []}
                groups[folder]["patterns"].append(pattern["name"])
        # Log discovered groups for debugging
        _LOGGER.info(f"Discovered Jellyfish Lighting groups: {list(groups.values())}")
        return list(groups.values())

    def set_power(self, state: int, zone_name=None):
        payload = {
            "cmd": "toCtlrSet",
            "runPattern": {
                "file": "",
                "data": "",
                "id": zone_name if zone_name else "Zone",
                "state": state,
                "zoneName": [zone_name] if zone_name else ["Zone"]
            }
        }
        return self._send_ws(payload)

    def set_pattern(self, pattern_name, state=1, zone_name=None):
        payload = {
            "cmd": "toCtlrSet",
            "runPattern": {
                "file": pattern_name,
                "data": "",
                "id": zone_name if zone_name else "Zone",
                "state": state,
                "zoneName": [zone_name] if zone_name else ["Zone"]
            }
        }
        return self._send_ws(payload)

    # Add more methods as needed for color/effect if supported by the controller
