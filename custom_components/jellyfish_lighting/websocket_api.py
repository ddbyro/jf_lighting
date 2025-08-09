import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from aiohttp import ClientSession, ClientWebSocketResponse, WSServerHandshakeError

from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, SIGNAL_PATTERNS_UPDATED, SIGNAL_ZONES_UPDATED

from homeassistant.helpers.dispatcher import async_dispatcher_send


_LOGGER = logging.getLogger(__name__)

class JellyfishClient:
    def __init__(self, hass: HomeAssistant, host: str, port: int = 9000):
        self.hass = hass
        self.host = host
        self.port = port
        self._ws: Optional[ClientWebSocketResponse] = None
        self._session: Optional[ClientSession] = None
        self._read_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._patterns = []
        self._zones = {}
        self._connected_event = asyncio.Event()

    @property
    def patterns(self):
        return self._patterns

    @property
    def zones(self):
        return self._zones

    async def connect(self):
        if self._session is None:
            self._session = ClientSession()
        await self._connect_ws()

    async def _connect_ws(self):
        if self._session is None:
            self._session = ClientSession()
        url = f"ws://{self.host}:{self.port}/ws"
        try:
            _LOGGER.debug("Connecting to Jellyfish controller at %s", url)
            self._ws = await self._session.ws_connect(url, heartbeat=30)
            self._connected_event.set()
            _LOGGER.info("Connected to Jellyfish controller %s", url)
            self._read_task = asyncio.create_task(self._read_loop())
        except Exception as exc:
            _LOGGER.warning("Failed to connect to %s: %s", url, exc)
            self._schedule_reconnect()

    def _schedule_reconnect(self, delay: int = 5):
        if self._reconnect_task and not self._reconnect_task.done():
            return
        self._reconnect_task = asyncio.create_task(self._reconnect_loop(delay))

    async def _reconnect_loop(self, delay: int):
        await asyncio.sleep(delay)
        await self._connect_ws()

    async def disconnect(self):
        if self._read_task:
            self._read_task.cancel()
        if self._ws:
            await self._ws.close()
            self._ws = None
        if self._session:
            await self._session.close()
            self._session = None
        self._connected_event.clear()

    async def _read_loop(self):
        try:
            async for msg in self._ws:
                if msg.type == 3:  # binary
                    continue
                if msg.type == 1:  # text
                    await self._handle_message(msg.data)
        except asyncio.CancelledError:
            return
        except Exception as exc:
            _LOGGER.exception("Websocket read loop error: %s", exc)
        finally:
            _LOGGER.warning("Websocket disconnected, scheduling reconnect")
            self._connected_event.clear()
            self._schedule_reconnect()

    async def _handle_message(self, raw: str):
        try:
            payload = json.loads(raw)
        except Exception:
            _LOGGER.debug("Non-JSON from controller: %s", raw)
            return

        cmd = payload.get("cmd")
        if cmd == "fromCtlr":
            if "patternFileList" in payload:
                self._patterns = payload["patternFileList"]
                async_dispatcher_send(self.hass, SIGNAL_PATTERNS_UPDATED)
            if "zones" in payload:
                self._zones = payload["zones"]
                async_dispatcher_send(self.hass, SIGNAL_ZONES_UPDATED)

    async def _send(self, payload: Dict[str, Any]):
        await self._connected_event.wait()
        if not self._ws:
            _LOGGER.error("Websocket not connected")
            return
        try:
            await self._ws.send_str(json.dumps(payload))
        except Exception as exc:
            _LOGGER.exception("Failed to send payload: %s", exc)

    # Convenience methods:
    async def request_pattern_list(self):
        await self._send({"cmd": "toCtlrGet", "get": [["patternFileList"]]})

    async def request_zones(self):
        await self._send({"cmd": "toCtlrGet", "get": [["zones"]]})

    async def run_pattern(self, file: str, zone_names: List[str], state: int = 1):
        payload = {
            "cmd": "toCtlrSet",
            "runPattern": {
                "file": file,
                "data": "",
                "id": "",
                "state": state,
                "zoneName": zone_names
            }
        }
        await self._send(payload)

    async def run_pattern_advanced(self, data: str, zone_names: List[str], state: int = 1):
        payload = {
            "cmd": "toCtlrSet",
            "runPattern": {
                "file": "",
                "data": data,
                "id": "",
                "state": state,
                "zoneName": zone_names
            }
        }
        await self._send(payload)

    async def get_pattern_file_data(self, folder: str, filename: str):
        payload = {"cmd": "toCtlrGet", "get": [["patternFileData", folder, filename]]}
        await self._send(payload)
        # Not waiting for response here; controller will send fromCtlr containing patternFileData
        return True
