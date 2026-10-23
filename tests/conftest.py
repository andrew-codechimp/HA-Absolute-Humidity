"""Shared fixtures for the absolute humidity helper."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from custom_components.absolute_humidity.const import (
    CONF_HUMIDITY_ENTITY_ID,
    CONF_TEMPERATURE_ENTITY_ID,
    DOMAIN,
)
from freezegun.api import FrozenDateTimeFactory
from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.syrupy import HomeAssistantSnapshotExtension
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_DEVICE_ID,
    CONF_NAME,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import DEFAULT_NAME, HUMIDITY_ENTITY_ID, TEMPERATURE_ENTITY_ID


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Use Home Assistant's snapshot serializer."""
    return snapshot.use_extension(HomeAssistantSnapshotExtension)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable the custom integration loader."""


@pytest.fixture(autouse=True)
def freeze_setup_time(freezer: FrozenDateTimeFactory) -> None:
    """Keep entity timestamps stable in snapshots."""
    freezer.move_to("2026-10-23T12:00:00+00:00")


@pytest.fixture
def mock_config_entry(request: pytest.FixtureRequest) -> MockConfigEntry:
    """Create a named helper with optional source overrides."""
    return MockConfigEntry(
        domain=DOMAIN,
        entry_id="absolute-humidity-entry",
        title=DEFAULT_NAME,
        data={},
        options={
            CONF_NAME: DEFAULT_NAME,
            CONF_TEMPERATURE_ENTITY_ID: TEMPERATURE_ENTITY_ID,
            CONF_HUMIDITY_ENTITY_ID: HUMIDITY_ENTITY_ID,
            **getattr(request, "param", {}),
        },
    )


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Isolate form tests from sensor setup."""
    with patch(
        "custom_components.absolute_humidity.async_setup_entry", return_value=None
    ) as mock_setup:
        yield mock_setup


@pytest.fixture
def selected_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    request: pytest.FixtureRequest,
) -> dr.AnyDeviceEntry:
    """Create an independently owned main or child device for the helper."""
    source_entry = MockConfigEntry(domain="test")
    source_entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=source_entry.entry_id,
        identifiers={("test", "selected-device")},
        name="Environmental monitor",
    )
    if getattr(request, "param", "main") == "child":
        return device_registry.async_get_or_create_child(
            config_entry_id=source_entry.entry_id,
            parent_device_id=device.id,
            identifiers={("test", "selected-child")},
            name="Room sensor",
        )
    return device


@pytest.fixture
def linked_config_entry(
    mock_config_entry: MockConfigEntry, selected_device: dr.AnyDeviceEntry
) -> MockConfigEntry:
    """Configure the optional device link before setting up the helper."""
    return MockConfigEntry(
        domain=DOMAIN,
        entry_id=mock_config_entry.entry_id,
        title=mock_config_entry.title,
        data={},
        options={**mock_config_entry.options, CONF_DEVICE_ID: selected_device.id},
    )


@pytest.fixture
def invalid_device_id() -> str:
    """Represent a device which no longer exists."""
    return "missing-device"


@pytest.fixture
def source_sensors(hass: HomeAssistant, entity_registry: er.EntityRegistry) -> None:
    """Register source sensors and publish initial readings."""
    entity_registry.async_get_or_create(
        "sensor",
        "test",
        "temperature",
        suggested_object_id="temperature",
        original_device_class=SensorDeviceClass.TEMPERATURE,
    )
    entity_registry.async_get_or_create(
        "sensor",
        "test",
        "humidity",
        suggested_object_id="humidity",
        original_device_class=SensorDeviceClass.HUMIDITY,
    )
    hass.states.async_set(
        TEMPERATURE_ENTITY_ID,
        "20",
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
            ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        },
    )
    hass.states.async_set(
        HUMIDITY_ENTITY_ID,
        "50",
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.HUMIDITY,
            ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE,
        },
    )
