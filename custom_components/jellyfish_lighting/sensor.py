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
                zone_sensor = JellyfishZoneDetailsSensor(client, zone_name)
                new_entities.extend([sensor, zone_sensor])
                added_zones.add(zone_name)
        # Add pattern catalog sensor only once
        if "pattern_catalog" not in entities:
            catalog_sensor = JellyfishPatternCatalogSensor(client)
            new_entities.append(catalog_sensor)
            entities["pattern_catalog"] = catalog_sensor
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
        self._pattern_data = None
        self._folder = None
        self._pattern_name = None
        self._unsub_zone = None
        self._unsub_pattern_data = None

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        # Expose full pattern data if available
        attrs = {}
        if self._pattern_data:
            attrs.update(self._pattern_data)
        attrs["folder"] = self._folder
        attrs["pattern_name"] = self._pattern_name
        return attrs

    async def async_added_to_hass(self):
        self._unsub_zone = async_dispatcher_connect(
            self.hass, SIGNAL_ZONES_UPDATED, self._handle_zone_update
        )
        self._unsub_pattern_data = async_dispatcher_connect(
            self.hass, SIGNAL_PATTERNS_UPDATED, self._handle_pattern_data_update
        )
        await self._handle_zone_update()

    async def async_will_remove_from_hass(self):
        if self._unsub_zone:
            self._unsub_zone()
        if self._unsub_pattern_data:
            self._unsub_pattern_data()

    async def _handle_zone_update(self):
        zone_data = self._client.zones.get(self._zone_name)
        if zone_data:
            self._state = zone_data.get("currentPattern", None)
            self._pattern_name = zone_data.get("currentPattern", None)
            # Find folder for pattern
            self._folder = None
            for pat in self._client.patterns:
                if pat.get("name") == self._pattern_name:
                    self._folder = pat.get("folders")
                    break
            if self._folder and self._pattern_name:
                await self._client.get_pattern_file_data(self._folder, self._pattern_name)
        else:
            self._state = None
            self._pattern_name = None
            self._folder = None
            self._pattern_data = None
        self.async_write_ha_state()

    async def _handle_pattern_data_update(self):
        # Find the latest patternFileData in client (if stored)
        # This assumes JellyfishClient stores the last received patternFileData
        pattern_file_data = getattr(self._client, "_last_pattern_file_data", None)
        if pattern_file_data and pattern_file_data.get("name") == self._pattern_name:
            self._pattern_data = pattern_file_data
        self.async_write_ha_state()

class JellyfishZoneDetailsSensor(SensorEntity):
    def __init__(self, client: JellyfishClient, zone_name: str):
        self._client = client
        self._zone_name = zone_name
        self._attr_name = f"Jellyfish {zone_name} Zone Details"
        self._attr_unique_id = f"jellyfish_zone_details_{zone_name}"
        self._state = None
        self._zone_data = None
        self._unsub_zone = None

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._zone_data or {}

    async def async_added_to_hass(self):
        self._unsub_zone = async_dispatcher_connect(
            self.hass, SIGNAL_ZONES_UPDATED, self._handle_zone_update
        )
        await self._handle_zone_update()

    async def async_will_remove_from_hass(self):
        if self._unsub_zone:
            self._unsub_zone()

    async def _handle_zone_update(self):
        zone_data = self._client.zones.get(self._zone_name)
        if zone_data:
            self._state = zone_data.get("numPixels", None)
            self._zone_data = zone_data
        else:
            self._state = None
            self._zone_data = None
        self.async_write_ha_state()

class JellyfishPatternCatalogSensor(SensorEntity):
    def __init__(self, client: JellyfishClient):
        self._client = client
        self._attr_name = "Jellyfish Pattern Catalog"
        self._attr_unique_id = "jellyfish_pattern_catalog"
        self._state = None
        self._catalog = None
        self._unsub_patterns = None

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._catalog or {}

    async def async_added_to_hass(self):
        self._unsub_patterns = async_dispatcher_connect(
            self.hass, SIGNAL_PATTERNS_UPDATED, self._handle_patterns_update
        )
        await self._handle_patterns_update()

    async def async_will_remove_from_hass(self):
        if self._unsub_patterns:
            self._unsub_patterns()

    async def _handle_patterns_update(self):
        patterns = self._client.patterns or []
        folders = {}
        for pat in patterns:
            folder = pat.get("folders", "Unknown")
            name = pat.get("name", "Unknown")
            folders.setdefault(folder, []).append(name)
        self._state = len(patterns)
        self._catalog = {"folders": folders, "total_patterns": len(patterns)}
        self.async_write_ha_state()
