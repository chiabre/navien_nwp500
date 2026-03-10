"""Initialize the Navien NWP500 component."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from nwp500 import NavienAuthClient, NavienAPIClient, NavienMqttClient

from .const import (
    DOMAIN,
    LOGGER,
    PLATFORMS,
    CONF_DEVICES,
)
from .coordinator import NavienCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Navien NWP500."""
    # 1. Initialize runtime_data IMMEDIATELY so sensors don't crash
    entry.runtime_data = {
        "coordinators": {},
        "mqtt_clients": [],
        "auth": None,
    }

    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    selected_macs = entry.data[CONF_DEVICES]

    # Get the interval from the config flow (seconds)
    period_seconds = entry.options.get("scan_interval", entry.data.get("scan_interval", 60))

    LOGGER.info("Initializing Navien NWP500 integration")

    auth = NavienAuthClient(username, password)
    entry.runtime_data["auth"] = auth
    
    try:
        await auth.__aenter__()
        api = NavienAPIClient(auth)
        all_devices = await api.list_devices()
    except Exception as err:
        LOGGER.error("Failed to initialize Navien API: %s", err)
        try:
            await auth.__aexit__(None, None, None)
        except Exception:
            pass
        raise ConfigEntryNotReady from err

    for mac in selected_macs:
        device = next((d for d in all_devices if d.device_info.mac_address == mac), None)
        if not device:
            LOGGER.warning("Device %s not found in account", mac)
            continue

        mqtt = NavienMqttClient(auth)
        
        mqtt.on("connection_interrupted", lambda err, m=mac: LOGGER.warning("Navien MQTT [%s] lost: %s", m, err))
        mqtt.on("connection_resumed", lambda rc, sp, m=mac: LOGGER.info("Navien MQTT [%s] restored", m))
        
        coordinator = NavienCoordinator(hass, api, auth, device)

        def make_callback(coord):
            return lambda status: coord.update_from_mqtt(status)

        try:
            await mqtt.connect()
            await mqtt.control.signal_app_connection(device)
            await mqtt.subscribe_device_status(device, make_callback(coordinator))
            
            import nwp500
            await mqtt.start_periodic_requests(
                device, 
                request_type=nwp500.PeriodicRequestType.DEVICE_STATUS, 
                period_seconds=period_seconds
            )
            
            await mqtt.control.request_device_status(device)
            await coordinator.async_config_entry_first_refresh()
            
        except Exception as err:
            LOGGER.error("MQTT Error for %s: %s", mac, err)
            continue

        # 2. Add to the existing dictionary
        entry.runtime_data["coordinators"][mac] = coordinator
        entry.runtime_data["mqtt_clients"].append(mqtt)

    # Use the supported listener for 2026.3
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Shutdown Navien integration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = entry.runtime_data
        for mqtt in data.get("mqtt_clients", []):
            try:
                await mqtt.disconnect()
            except Exception:
                pass
        try:
            if data["auth"]:
                await data["auth"].__aexit__(None, None, None)
        except Exception:
            pass
    return unload_ok