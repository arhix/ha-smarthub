from homeassistant import config_entries
import voluptuous as vol
from .api import SmartHubAPI
from .const import (
    DOMAIN, CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL,
    CONF_EMAIL, CONF_PASSWORD, CONF_ACCOUNT_ID, CONF_LOCATION_ID, CONF_HOST)

import logging
_LOGGER = logging.getLogger(__name__)

class SmartHubConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SmartHub."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Generate a unique ID from input that should uniquely identify this account/host
            # This is crucial for Home Assistant to manage the integration instance.
            unique_id = f"{user_input[CONF_EMAIL]}_{user_input[CONF_HOST]}_{user_input[CONF_ACCOUNT_ID]}"
            
            # Set the unique ID for this config entry.
            # If an entry with this unique ID already exists, abort the flow.
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured() # Check if already configured

            try:
                # Validate credentials by attempting to get a token
                api = SmartHubAPI(
                    email=user_input[CONF_EMAIL],
                    password=user_input[CONF_PASSWORD],
                    account_id=user_input[CONF_ACCOUNT_ID],
                    location_id=user_input[CONF_LOCATION_ID],
                    host=user_input[CONF_HOST],
                )
                
                # Note: If SmartHubAPI.get_token is not truly async (e.g., uses blocking requests),
                # hass.async_add_executor_job is correct. If it's pure aiohttp/httpx async,
                # you can just await it directly: `await api.get_token()`.
                # Given api.py uses aiohttp, you can likely do:
                await api.get_token()

                # Debug log for successful connection
                _LOGGER.debug("Successfully validated credentials in config_flow and set unique_id: %s", unique_id)

                # Create an entry with the user-provided data
                # The unique_id is now automatically associated with this entry
                return self.async_create_entry(title="SmartHub", data=user_input)

            except Exception as e: # Catch specific exceptions for better error handling
                _LOGGER.error("Error validating credentials in config_flow: %s", e)
                errors["base"] = "cannot_connect"

        # Show the form again if validation failed or it's the first time
        schema = vol.Schema(
            {
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(CONF_ACCOUNT_ID): str,
            vol.Required(CONF_LOCATION_ID): str,
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
