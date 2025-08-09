import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN, SIGNAL_ZONES_UPDATED
from .websocket_api import JellyfishClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    client: JellyfishClient = hass.data[DOMAIN][config_entry.entry_id]["client"]
    entities = {}
    added_zones = set()

    async def add_zone_sensors():
        new_entities = []
        for zone_name in client.zones.keys():
            if zone_name not in added_zones:
                sensor = JellyfishCurrentPatternSensor(client, zone_name)
                entities[zone_name] = sensor
                new_entities.append(sensor)
                added_zones.add(zone_name)
        if new_entities:
            async_add_entities(new_entities, True)

    async_dispatcher_connect(hass, SIGNAL_ZONES_UPDATED, add_zone_sensors)
    await client.request_zones()
    await add_zone_sensors()

class JellyfishCurrentPatternSensor(SensorEntity):
    def __init__(self, client: JellyfishClient, zone_name: str):
        self._client = client
        self._zone_name = zone_name
        self._attr_name = f"Jellyfish {zone_name} Current Pattern"
        self._attr_unique_id = f"jellyfish_current_pattern_{zone_name}"
        self._state = None

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def state(self):
        return self._state

    async def async_added_to_hass(self):
        self._unsub_zone = async_dispatcher_connect(
            self.hass, SIGNAL_ZONES_UPDATED, self._handle_zone_update
        )
        await self._handle_zone_update()

    async def async_will_remove_from_hass(self):
        if hasattr(self, '_unsub_zone') and self._unsub_zone:
            self._unsub_zone()

    async def _handle_zone_update(self):
        zone_data = self._client.zones.get(self._zone_name)
        if zone_data:
            self._state = zone_data.get("currentPattern", None)
        else:
            self._state = None
        self.async_write_ha_state()

