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

    def get_groups(self):
        # Use synchronous call since websocket-client is blocking
        return self.api.get_groups()

    def close(self):
        pass  # No persistent connection to close

async def async_setup_entry(hass, entry, async_add_entities):
    entry_data = hass.data[DOMAIN][entry.entry_id] if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN] else entry.data
    host = entry_data.get("host")
    api_key = entry_data.get("api_key")
    lighting = JellyfishLighting(host, api_key)
    groups = lighting.get_groups()
    entities = []
    if groups:
        for group in groups:
            entities.append(JellyfishLight(lighting.api, group))
    else:
        entities.append(JellyfishLight(lighting.api, None))
    async_add_entities(entities)

class JellyfishLight(LightEntity):
    def __init__(self, api: JellyfishLightingAPI, group: str = None):
        self._api = api
        self._group = group
        self._is_on = False
        self._rgb_color = (255, 255, 255)
        self._effect = None
        self._available_effects = []
        self._name = group if group else "Jellyfish Lighting"
        self._group_id = group if group else None

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
            state = 1
            zone_name = self._group_id
            if "effect" in kwargs:
                pattern = kwargs["effect"]
                self._api.set_pattern(pattern, state, zone_name)
                self._effect = pattern
            else:
                self._api.set_power(state, zone_name)
            self._is_on = True
            await self.async_update()
        except Exception as e:
            _LOGGER.error(f"Error turning on Jellyfish Lighting: {e}")

    async def async_turn_off(self, **kwargs):
        try:
            state = 0
            zone_name = self._group_id
            self._api.set_power(state, zone_name)
            self._is_on = False
            await self.async_update()
        except Exception as e:
            _LOGGER.error(f"Error turning off Jellyfish Lighting: {e}")

    async def async_update(self):
        try:
            zone_name = self._group_id
            power = self._api.get_state()
            self._is_on = power == True
            patterns = self._api.get_patterns()
            self._available_effects = [p["name"] for p in patterns if p.get("folders") == zone_name] if zone_name else [p["name"] for p in patterns]
            # No direct color support in API, so leave as last set
        except Exception as e:
            _LOGGER.error(f"Error updating Jellyfish Lighting: {e}")
