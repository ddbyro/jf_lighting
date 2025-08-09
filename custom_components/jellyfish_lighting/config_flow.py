import logging
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_HOST, CONF_PORT
from .const import DOMAIN, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

class JellyfishConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            # For brevity, we do not connect here; simply save entry.
            return self.async_create_entry(title=f"Jellyfish {host}", data={
                CONF_HOST: host,
                CONF_PORT: port
            })

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_schema(),
            errors=errors
        )

    @staticmethod
    @callback
    def _get_schema():
        from homeassistant.helpers import selector
        import voluptuous as vol
        return vol.Schema({
            CONF_HOST: vol.All(str),
            CONF_PORT: vol.All(int)
        })
