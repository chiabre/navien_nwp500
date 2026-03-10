"""Sensor platform for Navien NWP500."""
from dataclasses import dataclass
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfPower,
    PERCENTAGE,
    UnitOfTemperature,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, LOGGER


@dataclass(frozen=True, kw_only=True)
class NavienSensorEntityDescription(SensorEntityDescription):
    """Describes Navien sensor entity."""


SENSOR_TYPES: tuple[NavienSensorEntityDescription, ...] = (
    # --- ENABLED BY DEFAULT ---
    NavienSensorEntityDescription(
        key="dhw_temperature",
        name="Water Temperature",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=True,
    ),
    NavienSensorEntityDescription(
        key="dhw_temperature_setting",
        name="Target Temperature",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=True,
    ),
    NavienSensorEntityDescription(
        key="current_inst_power",
        name="Power Draw",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=True,
    ),
    NavienSensorEntityDescription(
        key="dhw_charge_per",
        name="Tank Charge",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=True,
    ),
    NavienSensorEntityDescription(
        key="operation_mode",
        name="Operation Mode",
        device_class=SensorDeviceClass.ENUM,
        entity_registry_enabled_default=True,
    ),
    NavienSensorEntityDescription(
        key="dhw_operation_setting",
        name="Operation Setting",
        device_class=SensorDeviceClass.ENUM,
        entity_registry_enabled_default=True,
    ),
    NavienSensorEntityDescription(
        key="current_heat_use",
        name="Active Heat Source",
        device_class=SensorDeviceClass.ENUM,
        entity_registry_enabled_default=True,
    ),

    # --- DISABLED BY DEFAULT (DIAGNOSTICS) ---
    NavienSensorEntityDescription(
        key="tank_upper_temperature",
        name="Upper Tank Temp",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    NavienSensorEntityDescription(
        key="tank_lower_temperature",
        name="Lower Tank Temp",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    NavienSensorEntityDescription(
        key="ambient_temperature",
        name="Intake Air Temp",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    NavienSensorEntityDescription(
        key="outside_temperature",
        name="Outside Temp",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    NavienSensorEntityDescription(
        key="current_inlet_temperature",
        name="Inlet Water Temp",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    NavienSensorEntityDescription(
        key="wifi_rssi",
        name="WiFi Signal",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    NavienSensorEntityDescription(
        key="error_code",
        name="Error Code",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Navien sensors."""
    coordinators = entry.runtime_data["coordinators"]

    entities = [
        NavienSensor(coord, description)
        for coord in coordinators.values()
        for description in SENSOR_TYPES
    ]

    async_add_entities(entities)


class NavienSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Navien sensor."""
    entity_description: NavienSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description

        self._attr_unique_id = f"{coordinator.mac_address}_{description.key}"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": coordinator.device_name,
            "manufacturer": "Navien",
            "model": "NWP500",
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        status = self.coordinator.data.get("status")
        if not status:
            return None
        return status.get(self.entity_description.key)

    @property
    def available(self):
        """Return if entity is available."""
        status = self.coordinator.data.get("status")
        return bool(status) and self.entity_description.key in status

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # DEBUG: Confirm the sensor is actually being told to update
        LOGGER.debug(
            "Navien Sensor [%s] received update. New value: %s", 
            self.entity_id, 
            self.coordinator.data.get("status", {}).get(self.entity_description.key)
        )
        self.hass.add_job(self.async_write_ha_state)