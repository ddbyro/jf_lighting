import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers import service

from .const import DOMAIN, CONF_HOST, CONF_PORT
from .jellyfish_client import JellyfishClient

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    jellyfish_config = config.get(DOMAIN)
    if not jellyfish_config or CONF_HOST not in jellyfish_config:
        _LOGGER.error("No host configured for Jellyfish Lighting")
        return False

    host = jellyfish_config[CONF_HOST]
    port = jellyfish_config.get(CONF_PORT, 9000)

    client = JellyfishClient(hass, host, port)
    await client.connect()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["client"] = client

    async def async_run_pattern_service(call):
        pattern = hass.states.get("input_select.jellyfish_patterns")
        zones = hass.states.get("input_select.jellyfish_zones")
        if not pattern or not zones:
            _LOGGER.error("Input selects for patterns or zones missing")
            return
        selected_pattern = pattern.state
        selected_zone = zones.state
        state_val = call.data.get("state", 1)
        await client.run_pattern(selected_pattern, [selected_zone], state_val)

    hass.services.async_register(DOMAIN, "run_pattern", async_run_pattern_service)

    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    client = hass.data[DOMAIN].get("client")
    if client:
        await client.disconnect()
    return True
