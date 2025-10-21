from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .api import SmartHubAPI
from .const import (
    DOMAIN, CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, 
    CONF_EMAIL, CONF_PASSWORD, CONF_ACCOUNT_ID, CONF_LOCATION_ID, CONF_HOST
)

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the integration from a config entry."""
    config = entry.data

    # Initialize the API object
    api = SmartHubAPI(
        email=config[CONF_EMAIL],
        password=config[CONF_PASSWORD],
        account_id=config[CONF_ACCOUNT_ID],
        location_id=config[CONF_LOCATION_ID],
        host=config[CONF_HOST],
    )

    # Store the API instance in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "poll_interval": config.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
    }

    # Debug log to confirm what is being stored
    _LOGGER.debug("Stored API instance in hass.data: %s", type(hass.data[DOMAIN][entry.entry_id]))

    # Forward setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    if await hass.config_entries.async_unload_platforms(entry, ["sensor"]):
        hass.data[DOMAIN].pop(entry.entry_id, None)
        return True
    return False
