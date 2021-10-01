"""Base class for SERVODRIVE."""
from __future__ import annotations

import logging

import pysdsbapi

from homeassistant.helpers.entity import Entity

from .const import DOMAIN, SERVODRIVE_MANUFACTURER, SERVODRIVE_MODEL_PREFIX

_LOGGER = logging.getLogger(__name__)


class ServodriveBase(Entity):
    """Base class for Servodrive.

    All devices and groups should ultimately inherit from this class.
    """

    _attr_should_poll = False

    def __init__(self, module: pysdsbapi.Module, bridge: pysdsbapi.Bridge) -> None:
        """Initialize an Module."""
        self._module: pysdsbapi.Module = module
        self._bridge: pysdsbapi.Bridge = bridge

    @property
    def unique_id(self) -> str:
        """Return unique_id of cover."""
        return f"servodrive_{self._module.type}_{self._module.id}"


class ServodriveDevice(ServodriveBase, Entity):
    """A SERVODRIVE device."""

    def __init__(self, module: pysdsbapi.Module, bridge: pysdsbapi.Bridge):
        """Set up the SERVODRIVE device."""
        super().__init__(module, bridge)

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.unique_id)
            },
            "name": self.name,
            "manufacturer": SERVODRIVE_MANUFACTURER,
            "model": f"{SERVODRIVE_MODEL_PREFIX} {self._module.type}",
            "sw_version": "1.0.0",
            "via_device": (DOMAIN, self._bridge.bridgeId),
        }

    @property
    def should_poll(self) -> bool:
        """Return should_poll setting of cover."""
        return True

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return True

    @property
    def available(self):
        """TODO Return True if device is available."""
        # return self.gateway.available and self._device.reachable
        return True
