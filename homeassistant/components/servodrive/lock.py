"""Support for servo drive locks."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Final

import pysdsbapi
import voluptuous as vol

from homeassistant.components.lock import PLATFORM_SCHEMA, SUPPORT_OPEN, LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, STATE_CLOSED
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
    }
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL: Final = timedelta(seconds=15)


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities):
    """Load SDS Modules."""

    bridgeAPI: pysdsbapi.BridgeAPI = hass.data[DOMAIN][entry.entry_id]
    modules = await bridgeAPI.async_get_modules()
    async_add_entities(
        [SDSLock(module) for module in modules if module.type == "lock"],
        update_before_add=True,
    )


class SDSLock(LockEntity):
    """Representation of a Sesame device."""

    def __init__(self, lock: pysdsbapi.Module) -> None:
        """Initialize an SDSlock Module."""
        self._module: pysdsbapi.Module = lock

        # Cached properties
        self._name = lock.name

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._name

    @property
    def is_locked(self) -> bool:
        """Return True if the device is currently locked, else False."""
        return self._module.state == STATE_CLOSED

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_OPEN

    async def async_lock(self, **kwargs):
        """Lock the device."""
        await self._module.async_control("close")

    async def async_unlock(self, **kwargs):
        """Unlock the device."""
        await self._module.async_control("open")

    async def async_update(self):
        """Update the internal state of the device."""
        # await self._module.async_update()
