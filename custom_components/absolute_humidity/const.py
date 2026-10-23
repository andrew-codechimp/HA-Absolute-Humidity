"""Constants for absolute_humidity."""

from logging import Logger, getLogger

from homeassistant.const import Platform

LOGGER: Logger = getLogger(__package__)

MIN_HA_VERSION = "2026.11"

DOMAIN = "absolute_humidity"

PLATFORMS = [Platform.SENSOR]
