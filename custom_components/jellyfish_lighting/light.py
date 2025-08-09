import logging
from typing import Any

from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN
from .websocket_api import JellyfishClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    client: JellyfishClient = hass.data[DOMAIN][entry.entry_id]["client"]
    entities = {}
    select_entities = {}
    added_zones = set()

    async def add_zone_entities():
        new_entities = []
        new_select_entities = []
        for zone_name in client.zones.keys():
            if zone_name not in added_zones:
                entity = JellyfishZoneLight(client, zone_name)
                select_entity = JellyfishPatternSelect(client, zone_name, entity)
                entities[zone_name] = entity
                select_entities[zone_name] = select_entity
                new_entities.append(entity)
                new_select_entities.append(select_entity)
                added_zones.add(zone_name)
        if new_entities:
            async_add_entities(new_entities, True)
        if new_select_entities:
            async_add_entities(new_select_entities, True)

    # Subscribe to zone updates with async callback
    async_dispatcher_connect(hass, f"{DOMAIN}_zones_updated", add_zone_entities)
    # Initial request
    await client.request_zones()
    await add_zone_entities()

class JellyfishZoneLight(LightEntity):
    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    def __init__(self, client: JellyfishClient, zone_name: str):
        self._client = client
        self._zone_name = zone_name
        self._attr_name = f"Jellyfish {zone_name}"
        self._is_on = False
        self._pattern = None

    @property
    def unique_id(self):
        return f"jellyfish_zone_{self._zone_name}"

    @property
    def is_on(self):
        return self._is_on

    @property
    def extra_state_attributes(self):
        # Expose available patterns and current pattern
        patterns = self._client.patterns
        folders = {}
        for pat in patterns:
            folder = pat.get("folders", "Unknown")
            name = pat.get("name", "Unknown")
            folders.setdefault(folder, []).append(name)
        return {
            "available_folders": list(folders.keys()),
            "available_patterns": folders,
            "current_pattern": self._pattern,
        }

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, "controller")},
            name="Jellyfish Controller"
        )

    async def async_turn_on(self, **kwargs: Any):
        # Use last selected pattern or default
        pattern = self._pattern or ""
        await self._client.run_pattern(file=pattern, zone_names=[self._zone_name], state=1)
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any):
        await self._client.run_pattern(file="", zone_names=[self._zone_name], state=0)
        self._is_on = False
        self.async_write_ha_state()

    async def async_set_pattern(self, pattern: str):
        self._pattern = pattern
        await self._client.run_pattern(file=pattern, zone_names=[self._zone_name], state=1)
        self._is_on = True
        self.async_write_ha_state()

class JellyfishPatternSelect(SelectEntity):
    def __init__(self, client: JellyfishClient, zone_name: str, light_entity: JellyfishZoneLight):
        self._client = client
        self._zone_name = zone_name
        self._light_entity = light_entity
        self._attr_name = f"Jellyfish {zone_name} Pattern"
        self._attr_options = self._get_patterns()
        self._attr_current_option = None

    def _get_patterns(self):
        patterns = self._client.patterns
        return [pat.get("name", "Unknown") for pat in patterns]

    @property
    def unique_id(self):
        return f"jellyfish_pattern_select_{self._zone_name}"

    @property
    def options(self):
        return self._get_patterns()

    @property
    def current_option(self):
        return self._light_entity._pattern

    async def async_select_option(self, option: str):
        await self._light_entity.async_set_pattern(option)
        self._attr_current_option = option
        self.async_write_ha_state()
