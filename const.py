"""Constants for the Navien NWP500 integration."""
import logging
from typing import Final
from homeassistant.const import Platform

LOGGER: Final[logging.Logger] = logging.getLogger(__package__)
DOMAIN: Final[str] = "navien_nwp500"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

# Configuration Keys
CONF_DEVICES: Final = "devices"
