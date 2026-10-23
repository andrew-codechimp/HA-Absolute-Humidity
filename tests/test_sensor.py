"""Test humidity calculations, indicators, and invalid-source recovery."""

import pytest
from pytest_homeassistant.common import MockConfigEntry, snapshot_platform
from syrupy.assertion import SnapshotAssertion

from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import setup_integration
from .const import ENTITY_ID, HUMIDITY_ENTITY_ID, TEMPERATURE_ENTITY_ID

pytestmark = pytest.mark.usefixtures("source_sensors")


async def test_entity(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Snapshot the initial measurement, metadata, and indicator attributes."""
    await setup_integration(hass, mock_config_entry)
    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


@pytest.mark.parametrize(
    ("temperature", "humidity", "expected"),
    [
        pytest.param("20", "50", 8.62, id="room"),
        pytest.param("0", "100", 4.85, id="freezing-saturated"),
        pytest.param("30", "80", 24.21, id="warm-humid"),
        pytest.param("-10", "50", 1.18, id="below-freezing"),
        pytest.param("20", "0", 0.0, id="dry-air"),
    ],
)
async def test_calculation(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    temperature: str,
    humidity: str,
    expected: float,
) -> None:
    """Test reference conditions in grams per cubic metre."""
    hass.states.async_set(
        TEMPERATURE_ENTITY_ID,
        temperature,
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    hass.states.async_set(
        HUMIDITY_ENTITY_ID, humidity, {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )
    await setup_integration(hass, mock_config_entry)
    assert float(hass.states.get(ENTITY_ID).state) == pytest.approx(expected, abs=0.02)


@pytest.mark.parametrize(
    ("value", "unit"),
    [
        pytest.param("20", UnitOfTemperature.CELSIUS, id="celsius"),
        pytest.param("68", UnitOfTemperature.FAHRENHEIT, id="fahrenheit"),
        pytest.param("293.15", UnitOfTemperature.KELVIN, id="kelvin"),
    ],
)
async def test_temperature_units(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    value: str,
    unit: UnitOfTemperature,
) -> None:
    """Equivalent source temperatures produce the same absolute humidity."""
    hass.states.async_set(
        TEMPERATURE_ENTITY_ID, value, {ATTR_UNIT_OF_MEASUREMENT: unit}
    )
    await setup_integration(hass, mock_config_entry)
    assert float(hass.states.get(ENTITY_ID).state) == pytest.approx(8.62, abs=0.02)


@pytest.mark.parametrize(
    ("entity_id", "value", "unit", "expected"),
    [
        pytest.param(
            TEMPERATURE_ENTITY_ID,
            "25",
            UnitOfTemperature.CELSIUS,
            11.48,
            id="temperature",
        ),
        pytest.param(HUMIDITY_ENTITY_ID, "60", PERCENTAGE, 10.35, id="humidity"),
    ],
)
async def test_source_updates(
    *,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_id: str,
    value: str,
    unit: str,
    expected: float,
) -> None:
    """Changes to either source recalculate the sensor immediately."""
    await setup_integration(hass, mock_config_entry)
    hass.states.async_set(entity_id, value, {ATTR_UNIT_OF_MEASUREMENT: unit})
    await hass.async_block_till_done()
    assert float(hass.states.get(ENTITY_ID).state) == pytest.approx(expected, abs=0.02)


@pytest.mark.parametrize(
    ("temperature", "humidity", "risk"),
    [
        pytest.param("20", "0", "low", id="zero"),
        pytest.param("20", "40", "low", id="around-seven"),
        pytest.param("20", "50", "low", id="around-eight-point-six"),
        pytest.param("20", "61", "moderate", id="above-ten-point-four"),
        pytest.param("20", "71", "high", id="above-twelve-point-one"),
        pytest.param("20", "80", "high", id="warm-air"),
        pytest.param("10", "80", "low", id="same-relative-humidity-colder-air"),
    ],
)
async def test_condensation_risk(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    temperature: str,
    humidity: str,
    risk: str,
) -> None:
    """Condensation risk follows absolute humidity calculated from both sources."""
    await setup_integration(hass, mock_config_entry)
    hass.states.async_set(
        TEMPERATURE_ENTITY_ID,
        temperature,
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    hass.states.async_set(
        HUMIDITY_ENTITY_ID, humidity, {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )
    await hass.async_block_till_done()
    attributes = hass.states.get(ENTITY_ID).attributes
    assert attributes["condensation_risk"] == risk


@pytest.mark.parametrize(
    ("temperature", "humidity", "comfort"),
    [
        pytest.param("20", "20", "very_dry", id="very-dry"),
        pytest.param("20", "40", "dry", id="dry"),
        pytest.param("20", "50", "comfortable", id="comfortable"),
        pytest.param("20", "60", "humid", id="humid"),
        pytest.param("20", "80", "very_humid", id="very-humid"),
        pytest.param("10", "50", "very_dry", id="same-relative-humidity-colder-air"),
    ],
)
async def test_comfort(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    temperature: str,
    humidity: str,
    comfort: str,
) -> None:
    """Comfort follows the absolute humidity calculated from both sources."""
    await setup_integration(hass, mock_config_entry)
    hass.states.async_set(
        TEMPERATURE_ENTITY_ID,
        temperature,
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    hass.states.async_set(
        HUMIDITY_ENTITY_ID, humidity, {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).attributes["comfort"] == comfort


@pytest.mark.parametrize("source_id", [TEMPERATURE_ENTITY_ID, HUMIDITY_ENTITY_ID])
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(STATE_UNAVAILABLE, STATE_UNAVAILABLE, id="unavailable"),
        pytest.param(STATE_UNKNOWN, STATE_UNKNOWN, id="unknown"),
        pytest.param("invalid", STATE_UNKNOWN, id="not-numeric"),
        pytest.param("nan", STATE_UNKNOWN, id="nan"),
        pytest.param("inf", STATE_UNKNOWN, id="infinity"),
    ],
)
async def test_invalid_readings(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    source_id: str,
    value: str,
    expected: str,
) -> None:
    """Clear stale values and attributes, then recover on a valid report."""
    await setup_integration(hass, mock_config_entry)
    previous = hass.states.get(source_id)
    hass.states.async_set(source_id, value, previous.attributes)
    await hass.async_block_till_done()
    result = hass.states.get(ENTITY_ID)
    assert result.state == expected
    assert result.attributes.get("comfort") is None
    assert result.attributes.get("condensation_risk") is None
    hass.states.async_set(source_id, previous.state, previous.attributes)
    await hass.async_block_till_done()
    assert float(hass.states.get(ENTITY_ID).state) == pytest.approx(8.62, abs=0.02)


@pytest.mark.parametrize(
    ("source_id", "value", "unit"),
    [
        pytest.param(
            TEMPERATURE_ENTITY_ID,
            "-273.15",
            UnitOfTemperature.CELSIUS,
            id="absolute-zero",
        ),
        pytest.param(
            TEMPERATURE_ENTITY_ID,
            "-243.12",
            UnitOfTemperature.CELSIUS,
            id="magnus-singularity",
        ),
        pytest.param(
            TEMPERATURE_ENTITY_ID, "-46", UnitOfTemperature.CELSIUS, id="too-cold"
        ),
        pytest.param(
            TEMPERATURE_ENTITY_ID, "61", UnitOfTemperature.CELSIUS, id="too-hot"
        ),
        pytest.param(HUMIDITY_ENTITY_ID, "-1", PERCENTAGE, id="negative-humidity"),
        pytest.param(HUMIDITY_ENTITY_ID, "101", PERCENTAGE, id="above-saturation"),
        pytest.param(TEMPERATURE_ENTITY_ID, "20", None, id="missing-temperature-unit"),
        pytest.param(
            TEMPERATURE_ENTITY_ID, "20", "invalid", id="invalid-temperature-unit"
        ),
        pytest.param(HUMIDITY_ENTITY_ID, "50", None, id="missing-humidity-unit"),
        pytest.param(
            HUMIDITY_ENTITY_ID, "50", "g/m³", id="absolute-instead-of-relative"
        ),
    ],
)
async def test_invalid_units_or_ranges(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    source_id: str,
    value: str,
    unit: str | None,
) -> None:
    """Reject unsupported units and readings outside the formula's range."""
    await setup_integration(hass, mock_config_entry)
    hass.states.async_set(source_id, value, {ATTR_UNIT_OF_MEASUREMENT: unit})
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == STATE_UNKNOWN


@pytest.mark.parametrize("source_id", [TEMPERATURE_ENTITY_ID, HUMIDITY_ENTITY_ID])
async def test_missing_source(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, source_id: str
) -> None:
    """Missing sources are unavailable at startup and recover without reloading."""
    previous = hass.states.get(source_id)
    hass.states.async_remove(source_id)
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE
    hass.states.async_set(source_id, previous.state, previous.attributes)
    await hass.async_block_till_done()
    assert float(hass.states.get(ENTITY_ID).state) == pytest.approx(8.62, abs=0.02)
    hass.states.async_remove(source_id)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE


async def test_attribute_only_change(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Changing units with the same state string recalculates the result."""
    await setup_integration(hass, mock_config_entry)
    hass.states.async_set(
        TEMPERATURE_ENTITY_ID,
        "20",
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.KELVIN},
    )
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == STATE_UNKNOWN
    hass.states.async_set(
        TEMPERATURE_ENTITY_ID,
        "20",
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    await hass.async_block_till_done()
    assert float(hass.states.get(ENTITY_ID).state) == pytest.approx(8.62, abs=0.02)
