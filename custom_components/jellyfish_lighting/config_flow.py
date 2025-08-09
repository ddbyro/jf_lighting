"""
Config flow for Jellyfish Lighting integration
"""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_API_KEY
from .const import DOMAIN

class JellyfishLightingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Optionally: Validate connection here
            return self.async_create_entry(title="Jellyfish Lighting", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_API_KEY): str,
            }),
            errors=errors,
        )

