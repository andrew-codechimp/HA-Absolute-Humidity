"""Calculate absolute humidity from temperature and relative humidity."""

from math import exp

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_DEVICE_ID,
    PERCENTAGE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfDensity,
    UnitOfTemperature,
)
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util.unit_conversion import TemperatureConverter

from . import AbsoluteHumidityConfigEntry
from .const import (
    ATTR_COMFORT,
    ATTR_CONDENSATION_RISK,
    COMFORT_COMFORTABLE_THRESHOLD,
    COMFORT_DRY_THRESHOLD,
    COMFORT_HUMID_THRESHOLD,
    COMFORT_VERY_DRY_THRESHOLD,
    CONDENSATION_HIGH_THRESHOLD,
    CONDENSATION_MODERATE_THRESHOLD,
    CONF_HUMIDITY_ENTITY_ID,
    CONF_TEMPERATURE_ENTITY_ID,
)

MIN_TEMPERATURE = -45
MAX_TEMPERATURE = 60
MAX_RELATIVE_HUMIDITY = 100


def assess_comfort(absolute_humidity: float) -> str:
    """Assess comfort from absolute humidity in grams per cubic metre."""
    if absolute_humidity < COMFORT_VERY_DRY_THRESHOLD:
        return "very_dry"
    if absolute_humidity < COMFORT_DRY_THRESHOLD:
        return "dry"
    if absolute_humidity < COMFORT_COMFORTABLE_THRESHOLD:
        return "comfortable"
    if absolute_humidity <= COMFORT_HUMID_THRESHOLD:
        return "humid"
    return "very_humid"


def assess_condensation_risk(absolute_humidity: float) -> str:
    """Assess condensation risk from absolute humidity in grams per cubic metre."""
    if absolute_humidity >= CONDENSATION_HIGH_THRESHOLD:
        return "high"
    if absolute_humidity >= CONDENSATION_MODERATE_THRESHOLD:
        return "moderate"
    return "low"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AbsoluteHumidityConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up an absolute humidity sensor."""
    async_add_entities([AbsoluteHumiditySensor(hass, entry)])


class AbsoluteHumiditySensor(SensorEntity):
    """Absolute humidity with comfort and condensation risk indicators."""

    _attr_should_poll = False
    _attr_device_class = SensorDeviceClass.ABSOLUTE_HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfDensity.GRAMS_PER_CUBIC_METER
    _attr_suggested_display_precision = 2
    _attr_translation_key = "absolute_humidity"

    def __init__(self, hass: HomeAssistant, entry: AbsoluteHumidityConfigEntry) -> None:
        """Initialize the helper's identity and source references."""
        self._attr_name = entry.title
        self._attr_unique_id = entry.entry_id
        if device_id := entry.options.get(CONF_DEVICE_ID):
            self.device_entry = dr.async_get(hass).async_get(
                device_id, include_composite_devices=False
            )
        self._temperature_entity_id = entry.runtime_data[CONF_TEMPERATURE_ENTITY_ID]
        self._humidity_entity_id = entry.runtime_data[CONF_HUMIDITY_ENTITY_ID]

    async def async_added_to_hass(self) -> None:
        """Subscribe to both sources and calculate the initial value."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                {self._temperature_entity_id, self._humidity_entity_id},
                self._async_source_updated,
            )
        )
        self._async_update_value()

    @callback
    def async_entity_id_changed(self, old_entity_id: str) -> None:
        """Opt in to in-place changes of the helper's entity ID."""
        super().async_entity_id_changed(old_entity_id)

    @callback
    def _async_source_updated(self, event: Event[EventStateChangedData]) -> None:
        """Recalculate when either source changes."""
        self._async_update_value()
        self.async_write_ha_state()

    @callback
    def _async_update_value(self) -> None:
        """Update the measurement and clear stale values for invalid inputs."""
        self._attr_native_value = None
        self._attr_extra_state_attributes = {
            ATTR_COMFORT: None,
            ATTR_CONDENSATION_RISK: None,
        }
        temperature_state = self.hass.states.get(self._temperature_entity_id)
        humidity_state = self.hass.states.get(self._humidity_entity_id)
        if temperature_state is None or humidity_state is None:
            self._attr_available = False
            return
        self._attr_available = STATE_UNAVAILABLE not in (
            temperature_state.state,
            humidity_state.state,
        )
        if not self._attr_available:
            return

        if STATE_UNKNOWN in (temperature_state.state, humidity_state.state):
            return

        temperature_unit = temperature_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        if (
            temperature_unit not in TemperatureConverter.VALID_UNITS
            or humidity_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) != PERCENTAGE
        ):
            return

        try:
            temperature = float(temperature_state.state)
            humidity = float(humidity_state.state)
        except ValueError:
            return
        temperature = TemperatureConverter.convert(
            temperature, temperature_unit, UnitOfTemperature.CELSIUS
        )
        if not (
            MIN_TEMPERATURE <= temperature <= MAX_TEMPERATURE
            and 0 <= humidity <= MAX_RELATIVE_HUMIDITY
        ):
            return

        # Magnus saturation vapour pressure over water, in hPa.
        vapour_pressure = 6.112 * exp(17.62 * temperature / (243.12 + temperature))
        self._attr_native_value = (
            216.679 * vapour_pressure * humidity / (100 * (273.15 + temperature))
        )
        self._attr_extra_state_attributes = {
            ATTR_COMFORT: assess_comfort(self._attr_native_value),
            ATTR_CONDENSATION_RISK: assess_condensation_risk(self._attr_native_value),
        }
