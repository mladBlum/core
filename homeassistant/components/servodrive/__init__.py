"""The servodrive integration."""
from __future__ import annotations

import logging

import pysdsbapi
from pysdsbapi import Auth, BridgeAPI

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_BRIDGE_ID,
    DOMAIN,
    SERVIDRIVE_BRIDGE_MODEL,
    SERVIDRIVE_BRIDGE_NAME,
    SERVODRIVE_MANUFACTURER,
)

PLATFORMS = ["cover", "lock"]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up servodrive from a config entry."""

    """Load SDS Modules."""
    logging.info("Load SDSModule")

    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    logging.info(f"Try to connect to {host} with user {username}")

    websession = async_get_clientsession(hass)

    auth = Auth(websession, host, username, password)
    bridgeAPI = BridgeAPI(auth)
    # ridge = await bridgeAPI.async_get_bridge()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = bridgeAPI

    # Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)
    # Add bridge as device because of guidelines
    # await async_add_bridge_to_device_registry(hass, entry, bridge)
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


# In Kombination mit dem config_flow. Irgendwie muss hier aufgepasst werden, dass die Bridge nicht doppelt hinzugefügt wird
async def async_add_bridge_to_device_registry(
    hass: HomeAssistant, entry: ConfigEntry, bridge: pysdsbapi.Bridge
) -> None:
    """Update device registry."""
    device_registry = await hass.helpers.device_registry.async_get_registry()

    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={(DOMAIN, entry.data[CONF_BRIDGE_ID])},
        manufacturer=SERVODRIVE_MANUFACTURER,
        name=SERVIDRIVE_BRIDGE_NAME,
        model=SERVIDRIVE_BRIDGE_MODEL,
        sw_version=bridge.bridgeAppVersion,
    )
