"""
Jellyfish Lighting Home Assistant Integration
"""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DOMAIN = "jellyfish_lighting"

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """
    Set up the Jellyfish Lighting integration.
    """
    # Placeholder for setup logic
    _LOGGER.info("Setting up Jellyfish Lighting integration")
    return True

async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    try:
        # Try to forward config entry to the light platform (modern HA)
        forward = getattr(hass, "async_forward_entry_setup", None)
        if forward:
            await forward(entry, "light")
        else:
            # Fallback: store config entry data for platform setup
            hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data
        return True
    except Exception as e:
        _LOGGER.error(f"Error setting up Jellyfish Lighting entry: {e}")
        return False

async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    unload = getattr(hass, "async_forward_entry_unload", None)
    if unload:
        return await unload(entry, "light")
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
