"""
Jellyfish Lighting Light Entity for Home Assistant
"""
import logging
from homeassistant.components.light import LightEntity, SUPPORT_COLOR, SUPPORT_EFFECT
from homeassistant.const import CONF_HOST, CONF_API_KEY
from .api import JellyfishLightingAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    host = config.get(CONF_HOST)
    api_key = config.get(CONF_API_KEY)
    api = JellyfishLightingAPI(host, api_key)
    async_add_entities([JellyfishLight(api)])

async def async_setup_entry(hass, entry, async_add_entities):
    host = entry.data.get("host")
    api_key = entry.data.get("api_key")
    api = JellyfishLightingAPI(host, api_key)
    async_add_entities([JellyfishLight(api)])

class JellyfishLight(LightEntity):
    def __init__(self, api: JellyfishLightingAPI):
        self._api = api
        self._is_on = False
        self._rgb_color = (255, 255, 255)
        self._effect = None
        self._available_effects = []
        self._name = "Jellyfish Lighting"

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._is_on

    @property
    def rgb_color(self):
        return self._rgb_color

    @property
    def effect_list(self):
        return self._available_effects

    @property
    def effect(self):
        return self._effect

    @property
    def supported_features(self):
        return SUPPORT_COLOR | SUPPORT_EFFECT

    async def async_turn_on(self, **kwargs):
        if "rgb_color" in kwargs:
            r, g, b = kwargs["rgb_color"]
            await self._api.set_color(r, g, b)
            self._rgb_color = (r, g, b)
        if "effect" in kwargs:
            await self._api.set_effect(kwargs["effect"])
            self._effect = kwargs["effect"]
        await self._api.set_power(True)
        self._is_on = True
        await self.async_update()

    async def async_turn_off(self, **kwargs):
        await self._api.set_power(False)
        self._is_on = False
        await self.async_update()

    async def async_update(self):
        status = await self._api.get_status()
        if status:
            self._is_on = status.get("on", self._is_on)
            color = status.get("color", {})
            self._rgb_color = (
                color.get("r", 255),
                color.get("g", 255),
                color.get("b", 255)
            )
            self._effect = status.get("effect", self._effect)
        effects = await self._api.get_effects()
        if effects:
            self._available_effects = effects.get("effects", [])
