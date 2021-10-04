"""The servodrive integration."""
from __future__ import annotations

import asyncio
import logging

import pysdsbapi
from pysdsbapi import Auth, BridgeAPI

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    SERVIDRIVE_BRIDGE_MODEL,
    SERVIDRIVE_BRIDGE_NAME,
    SERVODRIVE_MANUFACTURER,
)

MAX_POLLING_INTERVAL = 3  # in seconds
MAX_FAST_POLLING_COUNT = 2

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
    bridge = await bridgeAPI.async_get_bridge()

    # Try to handle the state update by ourself
    # refresh_interval = 2
    # servodriveHandler = ServodriveHandler(hass, refresh_interval)
    # servodriveHandler.start_periodic_request()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = bridgeAPI

    # Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    # Add bridge as device because of guidelines
    await async_add_bridge_to_device_registry(hass, entry, bridge)
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_add_bridge_to_device_registry(
    hass: HomeAssistant, entry: ConfigEntry, bridge: pysdsbapi.Bridge
) -> None:
    """Update device registry."""
    device_registry = await hass.helpers.device_registry.async_get_registry()

    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={(DOMAIN, bridge.bridgeId)},
        manufacturer=SERVODRIVE_MANUFACTURER,
        name=SERVIDRIVE_BRIDGE_NAME,
        model=SERVIDRIVE_BRIDGE_MODEL,
        sw_version=bridge.bridgeAppVersion,
    )


class ServodriveHandler:
    """Handles SERVO-DRIVE state refresh."""

    def __init__(self, hass, refresh_interval):
        """Initialize SERVO-DRIVE connection."""

        self._update_listeners = []
        self._hass = hass

        # Ensure at least MAX_POLLING_INTERVAL seconds delay
        self._refresh_interval = max(MAX_POLLING_INTERVAL, refresh_interval)
        self._fast_polling_count = MAX_FAST_POLLING_COUNT
        self._polling_task = None

    def start_periodic_request(self):
        """Start periodic data polling."""
        self._polling_task = self._hass.loop.create_task(self._periodic_request())

    async def _periodic_request(self):
        """Send  periodic update requests."""
        # await self.request_data()
        logging.info("Would do update!!!!")

        if self._fast_polling_count < MAX_FAST_POLLING_COUNT:
            self._fast_polling_count += 1
            _LOGGER.debug("Periodic data request executed, now wait for 2 seconds")
            await asyncio.sleep(2)
        else:
            _LOGGER.debug(
                "Periodic data request executed, now wait for %s seconds",
                self._refresh_interval,
            )
            await asyncio.sleep(self._refresh_interval)

        _LOGGER.debug("Periodic data request rescheduled")
        self._polling_task = self._hass.loop.create_task(self._periodic_request())
