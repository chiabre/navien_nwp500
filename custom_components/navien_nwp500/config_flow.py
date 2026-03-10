"""Config flow for Navien NWP500."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from nwp500 import NavienAuthClient, NavienAPIClient

from .const import DOMAIN, CONF_DEVICES

_LOGGER = logging.getLogger(__name__)

class NavienConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Navien NWP500."""

    VERSION = 1

    def __init__(self):
        self.data = {}
        self.discovered_devices = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NavienOptionsFlowHandler()

    async def async_step_user(self, user_input=None):
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
                else:
                    self.data = user_input
                    self.discovered_devices = {
                        d.device_info.mac_address: f"{d.device_info.device_name} ({d.device_info.mac_address})" 
                        for d in devices
                    }
                    return await self.async_step_select_devices()
            except Exception:
                _LOGGER.exception("Navien auth failed")
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )

    async def async_step_select_devices(self, user_input=None):
        if user_input is not None:
            self.data.update(user_input)
            return self.async_create_entry(title=self.data[CONF_USERNAME], data=self.data)

        return self.async_show_form(
            step_id="select_devices",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICES): cv.multi_select(self.discovered_devices),
                vol.Required("scan_interval", default=60): NumberSelector(
                    NumberSelectorConfig(
                        min=30, max=599, mode=NumberSelectorMode.BOX, unit_of_measurement="seconds"
                    )
                ),
            }),
        )

class NavienOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            "scan_interval", self.config_entry.data.get("scan_interval", 60)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("scan_interval", default=current_interval): NumberSelector(
                    NumberSelectorConfig(
                        min=30, max=599, mode=NumberSelectorMode.BOX, unit_of_measurement="seconds"
                    )
                ),
            }),
        )