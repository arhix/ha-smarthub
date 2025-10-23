import logging
from datetime import timedelta

from homeassistant.const import UnitOfVolume, UnitOfEnergy
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
        name="SmartHub Coop",
        update_method=api.get_data,
        update_interval=timedelta(minutes=poll_interval),
    )

    # Fetch initial data
    await coordinator.async_refresh()

    # Create and add the sensors
    sensors = [
        SmartHubEnergySensor(coordinator, config_entry),
        SmartHubGasSensor(coordinator, config_entry),
    ]
    async_add_entities(sensors)
    _LOGGER.debug("Sensor entities added.")


class SmartHubUsageSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for SmartHub usage sensors (energy, gas)."""

    def __init__(self, coordinator, config_entry):
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.config = config_entry.data
        self._base_unique_id = (
            config_entry.unique_id
            or config_entry.entry_id
            or f"{self.config[CONF_EMAIL]}_{self.config[CONF_HOST]}_{self.config[CONF_ACCOUNT_ID]}")

        _LOGGER.debug(f"{self.__class__.__name__} initialized with base_unique_id: {self._base_unique_id}")

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
        return f"SmartHub {self.device_class.title()} Sensor"

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        # Combine the base_unique_id (from config_entry) with a sensor-specific identifier
        # This ensures the sensor itself has a unique ID within the Home Assistant instance.
        if not self._base_unique_id:
            _LOGGER.error("unique_id requested but _base_unique_id is None. This should not happen.")
            return None # Or raise an exception, though None is usually handled gracefully by HA

        return f"{self._base_unique_id}_{self.device_class}_usage"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        # Ensure that self.coordinator.data is not None before accessing it
        if self.coordinator.data is not None:
            return self.coordinator.data.get(self.sensor_key)

        _LOGGER.debug(f"Coordinator data is None or '{self.sensor_key}' not found. Returning None for state.")
        return None # Return None if data is not available

    @property
    def device_class(self):
        """Return the device class of the sensor. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement device_class")
    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return SensorStateClass.TOTAL_INCREASING

    @property
    def sensor_key(self):
        """Return the key to look up in coordinator data. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement sensor_key")

    @property
    def icon(self):
        """Return the icon to use in the frontend. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement icon")

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement native_unit_of_measurement")

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
            "model": "SmartHub Monitor",
            "configuration_url": configuration_url,
        }


class SmartHubEnergySensor(SmartHubUsageSensorBase):
    """Representation of the SmartHub Energy sensor."""

    @property
    def sensor_key(self):
        """Return the key for coordinator data lookup."""
        return "current_energy_usage"

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SensorDeviceClass.ENERGY

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:power-plug"

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return UnitOfEnergy.KILO_WATT_HOUR


class SmartHubGasSensor(SmartHubUsageSensorBase):
    """Representation of the SmartHub Gas sensor."""

    @property
    def sensor_key(self):
        """Return the key for coordinator data lookup."""
        return "current_gas_usage"

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SensorDeviceClass.GAS

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:gas-cylinder"

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return UnitOfVolume.CUBIC_METERS
