import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, CONF_ACCOUNT_ID, CONF_EMAIL, CONF_HOST

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform."""
    _LOGGER.debug("async_setup_entry called for SmartHub Energy Sensor")

    data = hass.data[DOMAIN][config_entry.entry_id]
    api = data["api"]
    poll_interval = data["poll_interval"]

    # Create a coordinator to manage polling
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="SmartHub Energy",
        update_method=api.get_energy_data,
        update_interval=timedelta(minutes=poll_interval),
    )

    # Fetch initial data
    await coordinator.async_refresh()

    # Create and add the sensor
    sensors = [SmartHubEnergySensor(coordinator, config_entry)]
    async_add_entities(sensors)
    _LOGGER.debug("Sensor entities added.")


class SmartHubEnergySensor(CoordinatorEntity, SensorEntity):
    """Representation of the SmartHub Energy sensor."""

    def __init__(self, coordinator, config_entry):
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.config = config_entry.data
        self._base_unique_id = (
            config_entry.unique_id
            or config_entry.entry_id
            or f"{self.config[CONF_EMAIL]}_{self.config[CONF_HOST]}_{self.config[CONF_ACCOUNT_ID]}")

        _LOGGER.debug(f"SmartHubEnergySensor initialized with base_unique_id: {self._base_unique_id}")

    @property
    def name(self):
        """Return the name of the sensor."""
        # You might want to make the name more dynamic based on parts of the unique ID
        # For instance, if you want to include the account ID in the name:
        # try:
        #     parts = self._base_unique_id.split('_')
        #     if len(parts) >= 3:
        #         return f"SmartHub Energy Sensor (Account: {parts[2]})"
        # except Exception:
        #     pass # Fallback to generic name if split fails
        return "SmartHub Energy Sensor"

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        # Combine the base_unique_id (from config_entry) with a sensor-specific identifier
        # This ensures the sensor itself has a unique ID within the Home Assistant instance.
        if not self._base_unique_id:
            _LOGGER.error("unique_id requested but _base_unique_id is None. This should not happen.")
            return None # Or raise an exception, though None is usually handled gracefully by HA

        return f"{self._base_unique_id}_energy_usage"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        # Ensure that self.coordinator.data is not None before accessing it
        if self.coordinator.data is not None:
            return self.coordinator.data.get("current_energy_usage")

        _LOGGER.debug("Coordinator data is None or 'current_energy_usage' not found. Returning None for state.")
        return None # Return None if data is not available

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SensorDeviceClass.ENERGY

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return SensorStateClass.TOTAL_INCREASING

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:power-plug"

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return "kWh"

    @property
    def device_info(self):
        """Return information about the device."""
        if not self._base_unique_id:
            _LOGGER.warning("base_unique_id is missing, cannot create device_info for sensor.")
            return None # Cannot create a device without a base identifier

        _LOGGER.debug(f"Attempting to parse device_info from base_unique_id: '{self._base_unique_id}'")

        host_name = self.config.get(CONF_HOST, "Unknown Host")
        account_id = self.config.get(CONF_ACCOUNT_ID, "Unknown Account")
        configuration_url = f"https://{host_name}/" if host_name != "Unknown Host" else None

        _LOGGER.debug(f"Device Info - Host: {host_name}, Account ID: {account_id}, Config URL: {configuration_url}")

        return {
            "identifiers": {(DOMAIN, self._base_unique_id)},
            "name": f"{host_name} ({account_id})", # Naming the device with the account ID for clarity
            "manufacturer": "gagata",
            "model": "Energy Monitor",
            "configuration_url": configuration_url,
        }
