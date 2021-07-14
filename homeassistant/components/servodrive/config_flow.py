"""Config flow for servodrive integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from pysdsbapi import Auth, BridgeAPI
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession, async_timeout

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    websession = async_get_clientsession(hass)
    host = data["host"]
    username = data["username"]

    try:
        async with async_timeout.timeout(5):
            logging.info(f"Try to connect to {host} with user {username}")
            auth = Auth(websession, host, username, data["password"])
            bridgeAPI = BridgeAPI(auth)
            bridge = await bridgeAPI.async_get_bridge()
            logging.info(
                f"Connection successful with {bridge.name}, version {bridge.bridgeAppVersion}"
            )

    except aiohttp.ClientResponseError as error:
        if error.status == 403:
            raise InvalidAuth from error
        raise CannotConnect from error
    except (aiohttp.ClientError, asyncio.TimeoutError) as error:
        raise CannotConnect from error

    return {"title": "SERVO-DRIVE"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for servodrive."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
