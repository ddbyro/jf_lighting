"""
Jellyfish Lighting Light Entity for Home Assistant
"""
import logging
from homeassistant.components.light import LightEntity, SUPPORT_COLOR, SUPPORT_EFFECT
from homeassistant.const import CONF_HOST, CONF_API_KEY
from .api import JellyfishLightingAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    host = config.get(CONF_HOST)
    api_key = config.get(CONF_API_KEY)
    api = JellyfishLightingAPI(host, api_key)
    async_add_entities([JellyfishLight(api)])

class JellyfishLighting:
    def __init__(self, host, api_key=None):
        self.api = JellyfishLightingAPI(host, api_key)

    async def get_groups(self):
        # Fetch groups/zones from the API
        try:
            groups = await self.api._request("GET", "groups")
            return groups.get("groups", []) if groups else []
        except Exception as e:
            _LOGGER.error(f"Error fetching Jellyfish Lighting groups: {e}")
            return []

    async def close(self):
        await self.api.close()

async def async_setup_entry(hass, entry, async_add_entities):
    entry_data = hass.data[DOMAIN][entry.entry_id] if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN] else entry.data
    host = entry_data.get("host")
    api_key = entry_data.get("api_key")
    lighting = JellyfishLighting(host, api_key)
    groups = await lighting.get_groups()
    entities = []
    if groups:
        for group in groups:
            entities.append(JellyfishLight(lighting.api, group))
    else:
        # fallback: single light if no groups
        entities.append(JellyfishLight(lighting.api, None))
    async_add_entities(entities)

class JellyfishLight(LightEntity):
    def __init__(self, api: JellyfishLightingAPI, group: dict = None):
        self._api = api
        self._group = group
        self._is_on = False
        self._rgb_color = (255, 255, 255)
        self._effect = None
        self._available_effects = []
        self._name = group["name"] if group else "Jellyfish Lighting"
        self._group_id = group["id"] if group and "id" in group else None

    async def async_added_to_hass(self):
        await self.async_update()

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return f"jellyfish_{self._group_id}" if self._group_id else None

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
        try:
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
        except Exception as e:
            _LOGGER.error(f"Error turning on Jellyfish Lighting: {e}")

    async def async_turn_off(self, **kwargs):
        try:
            await self._api.set_power(False)
            self._is_on = False
            await self.async_update()
        except Exception as e:
            _LOGGER.error(f"Error turning off Jellyfish Lighting: {e}")

    async def async_update(self):
        try:
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
        except Exception as e:
            _LOGGER.error(f"Error updating Jellyfish Lighting: {e}")
