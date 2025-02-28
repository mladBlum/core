"""Support for Nanoleaf Lights."""
from __future__ import annotations

import logging

from aiohttp import ServerDisconnectedError
from aionanoleaf import Unavailable
import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
    ATTR_TRANSITION,
    PLATFORM_SCHEMA,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_COLOR_TEMP,
    SUPPORT_EFFECT,
    SUPPORT_TRANSITION,
    LightEntity,
)
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import color as color_util
from homeassistant.util.color import (
    color_temperature_mired_to_kelvin as mired_to_kelvin,
)

from .const import DEVICE, DOMAIN, NAME, SERIAL_NO

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Nanoleaf"

ICON = "mdi:triangle-outline"

SUPPORT_NANOLEAF = (
    SUPPORT_BRIGHTNESS
    | SUPPORT_COLOR_TEMP
    | SUPPORT_EFFECT
    | SUPPORT_COLOR
    | SUPPORT_TRANSITION
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Import Nanoleaf light platform."""
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={CONF_HOST: config[CONF_HOST], CONF_TOKEN: config[CONF_TOKEN]},
        )
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Nanoleaf light."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NanoleafLight(data[DEVICE], data[NAME], data[SERIAL_NO])], True)


class NanoleafLight(LightEntity):
    """Representation of a Nanoleaf Light."""

    def __init__(self, light, name, unique_id):
        """Initialize an Nanoleaf light."""
        self._unique_id = unique_id
        self._available = True
        self._brightness = None
        self._color_temp = None
        self._effect = None
        self._effects_list = None
        self._light = light
        self._name = name
        self._hs_color = None
        self._state = None

    @property
    def available(self):
        """Return availability."""
        return self._available

    @property
    def brightness(self):
        """Return the brightness of the light."""
        if self._brightness is not None:
            return int(self._brightness * 2.55)
        return None

    @property
    def color_temp(self):
        """Return the current color temperature."""
        if self._color_temp is not None:
            return color_util.color_temperature_kelvin_to_mired(self._color_temp)
        return None

    @property
    def effect(self):
        """Return the current effect."""
        return self._effect

    @property
    def effect_list(self):
        """Return the list of supported effects."""
        return self._effects_list

    @property
    def min_mireds(self):
        """Return the coldest color_temp that this light supports."""
        return 154

    @property
    def max_mireds(self):
        """Return the warmest color_temp that this light supports."""
        return 833

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return ICON

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._light.is_on

    @property
    def hs_color(self):
        """Return the color in HS."""
        return self._hs_color

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_NANOLEAF

    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        hs_color = kwargs.get(ATTR_HS_COLOR)
        color_temp_mired = kwargs.get(ATTR_COLOR_TEMP)
        effect = kwargs.get(ATTR_EFFECT)
        transition = kwargs.get(ATTR_TRANSITION)

        if hs_color:
            hue, saturation = hs_color
            await self._light.set_hue(int(hue))
            await self._light.set_saturation(int(saturation))
        if color_temp_mired:
            await self._light.set_color_temperature(mired_to_kelvin(color_temp_mired))
        if transition:
            if brightness:  # tune to the required brightness in n seconds
                await self._light.set_brightness(
                    int(brightness / 2.55), transition=int(kwargs[ATTR_TRANSITION])
                )
            else:  # If brightness is not specified, assume full brightness
                await self._light.set_brightness(
                    100, transition=int(kwargs[ATTR_TRANSITION])
                )
        else:  # If no transition is occurring, turn on the light
            await self._light.turn_on()
            if brightness:
                await self._light.set_brightness(int(brightness / 2.55))
        if effect:
            if effect not in self._effects_list:
                raise ValueError(
                    f"Attempting to apply effect not in the effect list: '{effect}'"
                )
            await self._light.set_effect(effect)

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        transition = kwargs.get(ATTR_TRANSITION)
        if transition:
            await self._light.set_brightness(0, transition=int(transition))
        else:
            await self._light.turn_off()

    async def async_update(self) -> None:
        """Fetch new state data for this light."""
        try:
            await self._light.get_info()
        except ServerDisconnectedError:
            # Retry the request once if the device disconnected
            await self._light.get_info()
        except Unavailable:
            self._available = False
            return
        self._available = True
        self._brightness = self._light.brightness
        self._effects_list = self._light.effects_list
        # Nanoleaf api returns non-existent effect named "*Solid*" when light set to solid color.
        # This causes various issues with scening (see https://github.com/home-assistant/core/issues/36359).
        # Until fixed at the library level, we should ensure the effect exists before saving to light properties
        self._effect = (
            self._light.effect if self._light.effect in self._effects_list else None
        )
        if self._effect is None:
            self._color_temp = self._light.color_temperature
            self._hs_color = self._light.hue, self._light.saturation
        else:
            self._color_temp = None
            self._hs_color = None
        self._state = self._light.is_on
