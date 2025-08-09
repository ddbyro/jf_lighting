import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from .const import DOMAIN
from .websocket_api import JellyfishClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    client: JellyfishClient = hass.data[DOMAIN][entry.entry_id]["client"]
    entities = {}
    added_zones = set()

    async def add_zone_select_entities():
        new_entities = []
        for zone_name in client.zones.keys():
            if zone_name not in added_zones:
                # Find the corresponding light entity if needed
                select_entity = JellyfishPatternSelect(client, zone_name)
                entities[zone_name] = select_entity
                new_entities.append(select_entity)
                added_zones.add(zone_name)
        if new_entities:
            async_add_entities(new_entities, True)

    async_dispatcher_connect(hass, f"{DOMAIN}_zones_updated", add_zone_select_entities)
    await client.request_zones()
    await add_zone_select_entities()

class JellyfishPatternSelect(SelectEntity):
    def __init__(self, client: JellyfishClient, zone_name: str):
        self._client = client
        self._zone_name = zone_name
        self._attr_name = f"Jellyfish {zone_name} Pattern"
        self._attr_options = self._get_patterns()
        self._attr_current_option = None
        self._unsub = None

    async def async_added_to_hass(self):
        # Listen for pattern updates
        self._unsub = async_dispatcher_connect(
            self.hass, f"{DOMAIN}_patterns_updated", self._handle_patterns_updated
        )
        # Request patterns if not loaded
        if not self._client.patterns:
            await self._client.request_pattern_list()
        # Force initial update
        self._handle_patterns_updated()

    async def async_will_remove_from_hass(self):
        if self._unsub:
            self._unsub()
            self._unsub = None

    def _get_patterns(self):
        patterns = self._client.patterns
        return [pat.get("name", "Unknown") for pat in patterns]

    def _handle_patterns_updated(self):
        self._attr_options = self._get_patterns()
        self.async_write_ha_state()

    @property
    def unique_id(self):
        return f"jellyfish_pattern_select_{self._zone_name}"

    @property
    def options(self):
        return self._attr_options

    @property
    def current_option(self):
        return self._attr_current_option

    async def async_select_option(self, option: str):
        await self._client.run_pattern(file=option, zone_names=[self._zone_name], state=1)
        self._attr_current_option = option
        self.async_write_ha_state()
