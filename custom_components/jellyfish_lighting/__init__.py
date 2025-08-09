import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN, PLATFORMS, DEFAULT_PORT, SERVICE_RUN_PATTERN, SERVICE_RUN_PATTERN_ADV, SERVICE_GET_PATTERN_DATA
from .websocket_api import JellyfishClient

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    host = entry.data.get(CONF_HOST)
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    client = JellyfishClient(hass, host, port)
    await client.connect()

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "entry": entry
    }

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

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

    hass.services.async_register(DOMAIN, SERVICE_RUN_PATTERN, async_run_pattern)
    hass.services.async_register(DOMAIN, SERVICE_RUN_PATTERN_ADV, async_run_pattern_adv)
    hass.services.async_register(DOMAIN, SERVICE_GET_PATTERN_DATA, async_get_pattern_data)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if not data:
        return True
    client: JellyfishClient = data["client"]
    await client.disconnect()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
