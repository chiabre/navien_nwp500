"""DataUpdateCoordinator for Navien NWP500."""
import asyncio
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN, LOGGER

class NavienCoordinator(DataUpdateCoordinator):
    """Manages data for a specific Navien device."""

    def __init__(self, hass, api, auth, device):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{device.device_info.mac_address}",
            update_interval=None,
        )
        self.api = api
        self.auth = auth
        self.device = device
        self.mac_address = device.device_info.mac_address
        self.device_name = device.device_info.device_name
        
        self.status_model = None
        self._first_data_received = asyncio.Event()

    async def _async_update_data(self):
        """Blocks during setup until the first MQTT packet is received."""
        if not self._first_data_received.is_set():
            try:
                async with asyncio.timeout(15):
                    await self._first_data_received.wait()
            except TimeoutError:
                LOGGER.warning(
                    "Timeout waiting for initial MQTT data for %s", 
                    self.mac_address
                )
        
        return {
            "status": self.status_model,
        }

    def update_from_mqtt(self, status):
        """Handle updated data from MQTT client."""
        if not status:
            return

        # 1. Define all keys exposed by sensors/binary_sensors
        keys = [
            "dhw_temperature",
            "dhw_temperature_setting",
            "tank_upper_temperature",
            "tank_lower_temperature",
            "current_inlet_temperature",
            "current_inst_power",
            "dhw_charge_per",
            "error_code",
            "operation_busy",
            "dhw_use",
            "dhw_use_sustained",
            "comp_use",
            "heat_upper_use",
            "heat_lower_use",
            "freeze_protection_use",
            "ambient_temperature",
            "outside_temperature",
            "wifi_rssi",
            "sub_error_code",
            "anti_legionella_use",
            "anti_legionella_operation_busy",
            "operation_mode",
            "dhw_operation_setting",
            "current_heat_use",
        ]

        # 2. Convert status object → dictionary
        new_status_dict = {}
        for key in keys:
            val = getattr(status, key, None)

            # Convert Enum values to string names
            if hasattr(val, "name"):
                new_status_dict[key] = val.name
            else:
                new_status_dict[key] = val

        # 3. Full debug payload dump
        LOGGER.debug(
            "Navien [%s] MQTT status payload: %s",
            self.mac_address,
            new_status_dict,
        )

        # 4. Skip update if nothing actually changed
        if new_status_dict == self.status_model:
            LOGGER.debug("Navien [%s] MQTT received but no data changed", self.mac_address)
            return

        LOGGER.debug("Navien [%s] Data changed: %s", self.mac_address, new_status_dict)

        # 5. Store new state
        self.status_model = new_status_dict

        if not self._first_data_received.is_set():
            self._first_data_received.set()

        # 6. Notify HA entities
        self.hass.add_job(self.async_set_updated_data, {"status": self.status_model})