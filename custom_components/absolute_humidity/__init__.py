"""Custom integration to provide absolute_humidity helpers for Home Assistant.

For more details about this integration, please refer to
https://github.com/andrew-codechimp/HA-Absolute-Humidity
"""

from __future__ import annotations

import probatio
from awesomeversion.awesomeversion import AwesomeVersion

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import __version__ as HA_VERSION  # noqa: N812
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    LOGGER,
    MIN_HA_VERSION,
    PLATFORMS,
)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(
    hass: HomeAssistant,
    config: ConfigType,
) -> bool:
    """Integration setup."""

    if AwesomeVersion(HA_VERSION) < AwesomeVersion(MIN_HA_VERSION):  # pragma: no cover
        msg = (
            "This integration requires at least Home Assistant version "
            f"{MIN_HA_VERSION}, you are running version {HA_VERSION}. "
            "Please upgrade Home Assistant to continue using this integration."
        )
        LOGGER.critical(msg)
        return False

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""

    entity_registry = er.async_get(hass)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
