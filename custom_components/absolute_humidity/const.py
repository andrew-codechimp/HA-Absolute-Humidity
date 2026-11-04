"""Constants for absolute_humidity."""

from logging import Logger, getLogger

from homeassistant.const import Platform

LOGGER: Logger = getLogger(__package__)

MIN_HA_VERSION = "2026.11.0"

DOMAIN = "absolute_humidity"

CONF_TEMPERATURE_ENTITY_ID = "temperature_entity_id"
CONF_HUMIDITY_ENTITY_ID = "humidity_entity_id"

ATTR_COMFORT = "comfort"
ATTR_CONDENSATION_RISK = "condensation_risk"

COMFORT_VERY_DRY_THRESHOLD = 5
COMFORT_DRY_THRESHOLD = 7
COMFORT_COMFORTABLE_THRESHOLD = 10
COMFORT_HUMID_THRESHOLD = 12

CONDENSATION_MODERATE_THRESHOLD = 10.4
CONDENSATION_HIGH_THRESHOLD = 12.1

PLATFORMS = [Platform.SENSOR]
