import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, PLATFORMS, DEFAULT_PORT, SERVICE_RUN_PATTERN, SERVICE_RUN_PATTERN_ADV, SERVICE_GET_PATTERN_DATA, SIGNAL_PATTERNS_UPDATED
from .websocket_api import JellyfishClient

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    host = config_entry.data.get(CONF_HOST)
    port = config_entry.data.get(CONF_PORT, DEFAULT_PORT)
    client = JellyfishClient(hass, host, port)
    await client.connect()

    hass.data[DOMAIN][config_entry.entry_id] = {
        "client": client,
        "entry": config_entry
    }

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # Register services
    async def async_run_pattern(call):
        await client.run_pattern(
            file=call.data.get("file", ""),
            zone_names=call.data.get("zone_names", []),
            state=call.data.get("state", 1),
        )

    async def async_run_pattern_adv(call):
        await client.run_pattern_advanced(
            data=call.data.get("data", ""),
            zone_names=call.data.get("zone_names", []),
            state=call.data.get("state", 1),
        )

    async def async_get_pattern_data(call):
        folder = call.data.get("folder")
        filename = call.data.get("filename")
        return await client.get_pattern_file_data(folder, filename)

    async def async_set_zone_pattern(call):
        zone = call.data.get("zone")
        pattern = call.data.get("pattern")
        # Find the entity for the zone
        for entry_id, data in hass.data[DOMAIN].items():
            client = data["client"]
            for zone_name in client.zones.keys():
                if zone_name == zone:
                    # Find the entity instance
                    for entity in hass.data[DOMAIN][entry_id].get("entities", []):
                        if getattr(entity, "_zone_name", None) == zone:
                            await entity.async_set_pattern(pattern)
                            return
        _LOGGER.warning(f"Zone '{zone}' not found for pattern set")

    hass.services.async_register(DOMAIN, SERVICE_RUN_PATTERN, async_run_pattern)
    hass.services.async_register(DOMAIN, SERVICE_RUN_PATTERN_ADV, async_run_pattern_adv)
    hass.services.async_register(DOMAIN, SERVICE_GET_PATTERN_DATA, async_get_pattern_data)
    hass.services.async_register(DOMAIN, "set_zone_pattern", async_set_zone_pattern)

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

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if not data:
        return True
    client: JellyfishClient = data["client"]
    await client.disconnect()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

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
