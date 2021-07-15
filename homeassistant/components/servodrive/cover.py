"""Support for IKEA Tradfri covers."""
import logging

import pysdsbapi
import voluptuous as vol

from homeassistant.components.cover import (
    DEVICE_CLASS_DOOR,
    PLATFORM_SCHEMA,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    CoverEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    STATE_CLOSED,
    STATE_OPEN,
)
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
    }
)


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities):
    """Load SDS Modules."""

    bridgeAPI: pysdsbapi.BridgeAPI = hass.data[DOMAIN][entry.entry_id]

    # Verify that passed in configuration works
    # if not bridgeAPI.is_valid_login():
    #    _LOGGER.error("Could not connect to AwesomeLight hub")
    # return

    modules = await bridgeAPI.async_get_modules()
    async_add_entities(SDSModule(module) for module in modules)


class SDSModule(CoverEntity):
    """The platform class required by Home Assistant."""

    def __init__(self, module: pysdsbapi.Module):
        """Initialize an Module."""
        self._module = module
        self._name = module.name
        self._device_class = DEVICE_CLASS_DOOR
        self._icon = "mdi:dresser"

    @property
    def icon(self):
        """Return icon of cover."""
        return self._icon

    @property
    def device_class(self):
        """Return device class of cover."""
        return self._device_class

    @property
    def name(self):
        """Return friendly name of cover."""
        return self._name

    @property
    def state(self):
        """Return state of cover."""
        if self._module.state == "closed":
            return STATE_CLOSED
        else:
            return STATE_OPEN

    @property
    def current_cover_position(self):
        """Return the current position of the cover.

        None is unknown, 0 is closed, 100 is fully open.
        """
        position = None
        if self.state == STATE_CLOSED:
            position = 0

        if self.state == STATE_OPEN:
            position = 100

        return position

    @property
    def supported_features(self):
        """Flag supported features."""

        supported_features = 0

        supported_features |= SUPPORT_OPEN

        if self._module.canClose is True:
            supported_features |= SUPPORT_CLOSE

        return supported_features

    async def async_open_cover(self, **kwargs):
        """Open the cover."""

        await self._module.async_control("open")
        await self._module.async_update()

    async def async_close_cover(self, **kwargs):
        """Close cover."""

        await self._module.async_control("close")
        await self._module.async_update()

    async def async_update(self):
        """
        Fetch new state data.

        This is the only method that should fetch new data for Home Assistant.
        """

        await self._module.async_update()
