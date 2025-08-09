import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_PATTERNS_UPDATED
from .websocket_api import JellyfishClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    client: JellyfishClient = hass.data[DOMAIN][config_entry.entry_id]["client"]
    entities = {}
    added_zones = set()

    async def add_zone_select_entities():
        new_entities = []
        for zone_name in client.zones.keys():
            if zone_name not in added_zones:
                select_entity = JellyfishPatternSelect(client, zone_name)
                entities[zone_name] = select_entity
                new_entities.append(select_entity)
                added_zones.add(zone_name)
        if new_entities:
            async_add_entities(new_entities, True)

    async_dispatcher_connect(hass, SIGNAL_PATTERNS_UPDATED, add_zone_select_entities)
    await client.request_pattern_list()
    await add_zone_select_entities()

class JellyfishPatternSelect(SelectEntity):
    def __init__(self, client: JellyfishClient, zone_name: str):
        self._client = client
        self._zone_name = zone_name
        self._attr_name = f"Jellyfish {zone_name} Pattern"
        self._attr_options = self._get_patterns()
        self._attr_current_option = None
        self._unsub_patterns = None

    async def async_added_to_hass(self):
        self._unsub_patterns = async_dispatcher_connect(
            self.hass, SIGNAL_PATTERNS_UPDATED, self._handle_patterns_updated
        )
        await self._handle_patterns_updated()

    async def async_will_remove_from_hass(self):
        if self._unsub_patterns:
            self._unsub_patterns()
            self._unsub_patterns = None

    def _get_patterns(self):
        patterns = self._client.patterns
        _LOGGER.debug(f"JellyfishPatternSelect[{self._zone_name}] patterns: {patterns}")
        return [pat.get("name", "Unknown") for pat in patterns]

    async def _handle_patterns_updated(self):
        _LOGGER.debug(f"JellyfishPatternSelect[{self._zone_name}] handle_patterns_updated called")
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
