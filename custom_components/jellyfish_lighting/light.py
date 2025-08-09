import logging
from typing import Any

from homeassistant.components.light import LightEntity, SUPPORT_BRIGHTNESS, ATTR_BRIGHTNESS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .websocket_api import JellyfishClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    client: JellyfishClient = hass.data[DOMAIN][entry.entry_id]["client"]
    # request the zones and patterns at setup
    await client.request_zones()
    await client.request_pattern_list()

    # wait a short moment to let controller respond (in practice you can wait or subscribe to dispatcher)
    await hass.async_add_executor_job(lambda: None)

    # Create zone lights from client.zones
    entities = []
    for zone_name in client.zones.keys():
        entities.append(JellyfishZoneLight(client, zone_name))
    async_add_entities(entities, True)

class JellyfishZoneLight(LightEntity):
    def __init__(self, client: JellyfishClient, zone_name: str):
        self._client = client
        self._zone_name = zone_name
        self._attr_name = f"Jellyfish {zone_name}"
        self._is_on = False
        self._brightness = 255

    @property
    def unique_id(self):
        return f"jellyfish_zone_{self._zone_name}"

    @property
    def is_on(self):
        return self._is_on

    @property
    def supported_features(self):
        return SUPPORT_BRIGHTNESS

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, "controller")},
            name="Jellyfish Controller"
        )

    async def async_turn_on(self, **kwargs: Any):
        # If brightness provided, convert 0-255 from HA to percentage 0-100
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is not None:
            percent = int((brightness / 255) * 100)
            # Build a simple runData JSON: use a basic type with brightness and keep others defaults
            rundata = {
                "colors": [255, 255, 255],
                "spaceBetweenPixels": 1,
                "effectBetweenPixels": "No Color Transformation",
                "type": "Color",
                "skip": 1,
                "numOfLeds": 1,
                "runData": {"speed": 50, "brightness": percent, "effect": "No Effect", "effectValue": 0, "rgbAdj": [100,100,100]},
                "direction": "Right"
            }
            await self._client.run_pattern_advanced(json.dumps(rundata), [self._zone_name], state=1)
            self._brightness = brightness
            self._is_on = True
            self.async_write_ha_state()
            return

        # Otherwise run last known pattern on this zone (or all)
        await self._client.run_pattern(file="", zone_names=[self._zone_name], state=1)
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any):
        await self._client.run_pattern(file="", zone_names=[self._zone_name], state=0)
        self._is_on = False
        self.async_write_ha_state()
