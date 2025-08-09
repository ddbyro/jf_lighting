"""
Jellyfish Lighting API Client
"""
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class JellyfishLightingAPI:
    def __init__(self, host: str, api_key: str = None):
        self.host = host
        self.api_key = api_key
        self.base_url = f"http://{host}/api"
        self.session = aiohttp.ClientSession()

    async def _request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            async with self.session.request(method, url, headers=headers, **kwargs) as resp:
                resp.raise_for_status()
                return await resp.json()
        except Exception as e:
            _LOGGER.error(f"API request error: {e}")
            return None

    async def get_status(self):
        return await self._request("GET", "status")

    async def set_power(self, on: bool):
        return await self._request("POST", "power", json={"on": on})

    async def set_color(self, r: int, g: int, b: int):
        return await self._request("POST", "color", json={"r": r, "g": g, "b": b})

    async def set_effect(self, effect_name: str, params: dict = None):
        data = {"effect": effect_name}
        if params:
            data.update(params)
        return await self._request("POST", "effect", json=data)

    async def get_effects(self):
        return await self._request("GET", "effects")

    async def get_groups(self):
        return await self._request("GET", "groups")

    async def get_group_status(self, group_id):
        return await self._request("GET", f"groups/{group_id}/status")

    async def set_group_power(self, group_id, on: bool):
        return await self._request("POST", f"groups/{group_id}/power", json={"on": on})

    async def set_group_color(self, group_id, r: int, g: int, b: int):
        return await self._request("POST", f"groups/{group_id}/color", json={"r": r, "g": g, "b": b})

    async def set_group_effect(self, group_id, effect_name: str, params: dict = None):
        data = {"effect": effect_name}
        if params:
            data.update(params)
        return await self._request("POST", f"groups/{group_id}/effect", json=data)

    async def get_group_effects(self, group_id):
        return await self._request("GET", f"groups/{group_id}/effects")

    async def close(self):
        await self.session.close()
