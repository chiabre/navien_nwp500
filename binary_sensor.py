"""Binary sensor platform for Navien NWP500."""
from dataclasses import dataclass
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, LOGGER


@dataclass(frozen=True, kw_only=True)
class NavienBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Navien binary sensor entity."""


BINARY_SENSOR_TYPES: tuple[NavienBinarySensorEntityDescription, ...] = (
    # --- ENABLED BY DEFAULT ---
    NavienBinarySensorEntityDescription(
        key="operation_busy",
        name="System Status",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_registry_enabled_default=True,
    ),
    NavienBinarySensorEntityDescription(
        key="dhw_use",
        name="Hot Water Draw",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_registry_enabled_default=True,
    ),

    # --- DISABLED BY DEFAULT (DIAGNOSTICS) ---
    NavienBinarySensorEntityDescription(
        key="comp_use",
        name="Compressor Active",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    NavienBinarySensorEntityDescription(
        key="eva_fan_use",
        name="Evaporator Fan",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    NavienBinarySensorEntityDescription(
        key="recirc_operation_busy",
        name="Recirc Pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    NavienBinarySensorEntityDescription(
        key="anti_legionella_use",
        name="Anti-Legionella Active",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    NavienBinarySensorEntityDescription(
        key="eco_use",
        name="Eco Mode Active",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Navien binary sensors."""
    coordinators = entry.runtime_data.get("coordinators") or {}

    entities = [
        NavienBinarySensor(coord, description)
        for coord in coordinators.values()
        for description in BINARY_SENSOR_TYPES
    ]

    async_add_entities(entities)


class NavienBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Navien binary sensor."""
    entity_description: NavienBinarySensorEntityDescription
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
    def is_on(self):
        """Return true if the binary sensor is on."""
        status = self.coordinator.data.get("status")
        if not status:
            return None
        return bool(status.get(self.entity_description.key, False))

    @property
    def available(self):
        """Return if entity is available."""
        status = self.coordinator.data.get("status")
        return bool(status) and self.entity_description.key in status

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        LOGGER.debug(
                    "Navien Binary Sensor [%s] update received: %s", 
                    self.entity_id, 
                    self.is_on
                )
        self.hass.add_job(self.async_write_ha_state)