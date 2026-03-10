"""Config flow for Navien NWP500."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv
from nwp500 import NavienAuthClient, NavienAPIClient

from .const import DOMAIN, CONF_DEVICES

logger = logging.getLogger(__name__)

class NavienConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Navien NWP500."""

    def __init__(self):
        self.data = {}
        self.discovered_devices = {}

    async def async_step_user(self, user_input=None):
        """First step: Credentials."""
        errors = {}
        if user_input is not None:
            try:
                auth = NavienAuthClient(user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
                await auth.__aenter__()
                api = NavienAPIClient(auth)
                devices = await api.list_devices()
                await auth.__aexit__(None, None, None)

                if not devices:
                    errors["base"] = "no_devices_found"
                    logger.info("Navien account %s has no devices.", user_input[CONF_USERNAME])
                else:
                    self.data = user_input
                    # Map MAC to "Device Name (MAC)" for the checkbox list
                    self.discovered_devices = {
                        d.device_info.mac_address: f"{d.device_info.device_name} ({d.device_info.mac_address})" 
                        for d in devices
                    }
                    logger.debug("Discovered devices for %s: %s", user_input[CONF_USERNAME], self.discovered_devices)
                    return await self.async_step_select_devices()
            except Exception as ex:
                errors["base"] = "invalid_auth"
                logger.exception("Navien auth failed for user %s: %s", user_input.get(CONF_USERNAME), ex)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )

    async def async_step_select_devices(self, user_input=None):
        """Second step: Multi-select devices."""
        if user_input is not None:
            self.data.update(user_input)
            logger.debug("User selected devices: %s", user_input.get(CONF_DEVICES))
            return self.async_create_entry(title=self.data[CONF_USERNAME], data=self.data)

        return self.async_show_form(
            step_id="select_devices",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICES): cv.multi_select(self.discovered_devices),
            }),
        )