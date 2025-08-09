import logging
from typing import Any

from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN
from .websocket_api import JellyfishClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    client: JellyfishClient = hass.data[DOMAIN][entry.entry_id]["client"]
    entities = []
    added_zones = set()

    async def add_zone_entities():
        for zone_name in client.zones.keys():
            if zone_name not in added_zones:
                entities.append(JellyfishZoneLight(client, zone_name))
                added_zones.add(zone_name)
        async_add_entities(list(entities), True)

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

    @property
    def unique_id(self):
        return f"jellyfish_zone_{self._zone_name}"

    @property
    def is_on(self):
        return self._is_on

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, "controller")},
            name="Jellyfish Controller"
        )

    async def async_turn_on(self, **kwargs: Any):
        await self._client.run_pattern(file="", zone_names=[self._zone_name], state=1)
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any):
        await self._client.run_pattern(file="", zone_names=[self._zone_name], state=0)
        self._is_on = False
        self.async_write_ha_state()
