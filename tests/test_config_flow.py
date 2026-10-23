"""Test creation and automatic options reloads."""

from unittest.mock import AsyncMock, patch

import pytest
from custom_components.absolute_humidity.const import (
    CONF_HUMIDITY_ENTITY_ID,
    CONF_TEMPERATURE_ENTITY_ID,
    DOMAIN,
)
from pytest_homeassistant.common import MockConfigEntry

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_DEVICE_ID, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr, entity_registry as er

from . import setup_integration
from .const import DEFAULT_NAME, ENTITY_ID, HUMIDITY_ENTITY_ID, TEMPERATURE_ENTITY_ID


async def test_user_flow(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test creation stores the helper name and both sources in options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_TEMPERATURE_ENTITY_ID: TEMPERATURE_ENTITY_ID,
            CONF_HUMIDITY_ENTITY_ID: HUMIDITY_ENTITY_ID,
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"] == {}
    assert result["options"] == {
        CONF_NAME: DEFAULT_NAME,
        CONF_TEMPERATURE_ENTITY_ID: TEMPERATURE_ENTITY_ID,
        CONF_HUMIDITY_ENTITY_ID: HUMIDITY_ENTITY_ID,
    }
    mock_setup_entry.assert_awaited_once()


@pytest.mark.usefixtures("mock_setup_entry")
async def test_user_device(
    hass: HomeAssistant, selected_device: dr.AnyDeviceEntry
) -> None:
    """Creation accepts and saves an optional existing device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_TEMPERATURE_ENTITY_ID: TEMPERATURE_ENTITY_ID,
            CONF_HUMIDITY_ENTITY_ID: HUMIDITY_ENTITY_ID,
            CONF_DEVICE_ID: selected_device.id,
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"][CONF_DEVICE_ID] == selected_device.id


async def test_user_invalid_device(hass: HomeAssistant, invalid_device_id: str) -> None:
    """Creation reports an unavailable device before saving."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_TEMPERATURE_ENTITY_ID: TEMPERATURE_ENTITY_ID,
            CONF_HUMIDITY_ENTITY_ID: HUMIDITY_ENTITY_ID,
            CONF_DEVICE_ID: invalid_device_id,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_device"}


async def test_options_invalid_device(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, invalid_device_id: str
) -> None:
    """Options reject a stale device selection without changing saved options."""
    mock_config_entry.add_to_hass(hass)
    original_options = dict(mock_config_entry.options)
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_TEMPERATURE_ENTITY_ID: TEMPERATURE_ENTITY_ID,
            CONF_HUMIDITY_ENTITY_ID: HUMIDITY_ENTITY_ID,
            CONF_DEVICE_ID: invalid_device_id,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_device"}
    assert mock_config_entry.options == original_options


@pytest.mark.usefixtures("source_sensors")
async def test_options_device_link(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    selected_device: dr.AnyDeviceEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Options attach and clear a device while preserving the sensor identity."""
    await setup_integration(hass, mock_config_entry)
    original_id = entity_registry.async_get(ENTITY_ID).id
    sources = {
        CONF_TEMPERATURE_ENTITY_ID: TEMPERATURE_ENTITY_ID,
        CONF_HUMIDITY_ENTITY_ID: HUMIDITY_ENTITY_ID,
    }
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    await hass.config_entries.options.async_configure(
        result["flow_id"], {**sources, CONF_DEVICE_ID: selected_device.id}
    )
    await hass.async_block_till_done()
    assert entity_registry.async_get(ENTITY_ID).device_id == selected_device.id
    assert entity_registry.async_get(ENTITY_ID).id == original_id

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    await hass.config_entries.options.async_configure(result["flow_id"], sources)
    await hass.async_block_till_done()
    assert CONF_DEVICE_ID not in mock_config_entry.options
    assert entity_registry.async_get(ENTITY_ID).device_id is None
    assert entity_registry.async_get(ENTITY_ID).id == original_id


@pytest.mark.parametrize("language", ["en", "fr"])
async def test_default_name(hass: HomeAssistant, language: str) -> None:
    """Load the English entity name, including fallback for untranslated languages."""
    hass.config.language = language
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    name_key = next(
        key for key in result["data_schema"].schema if key.schema == CONF_NAME
    )
    assert name_key.default() == "Absolute humidity"


@pytest.mark.usefixtures("mock_setup_entry")
@pytest.mark.parametrize(
    ("language", "translated_name"),
    [
        pytest.param("de", "Absolute Luftfeuchtigkeit", id="german"),
        pytest.param("nl", "Absolute luchtvochtigheid", id="dutch"),
    ],
)
async def test_translated_default_name(
    hass: HomeAssistant, language: str, translated_name: str
) -> None:
    """Use a localized suggestion as the saved helper name when accepted."""
    hass.config.language = language
    with patch(
        "custom_components.absolute_humidity.config_flow.translation.async_get_translations",
        return_value={
            f"component.{DOMAIN}.entity.sensor.absolute_humidity.name": translated_name
        },
    ) as get_translations:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        get_translations.assert_awaited_with(hass, language, "entity", {DOMAIN})
        name_key = next(
            key for key in result["data_schema"].schema if key.schema == CONF_NAME
        )
        assert name_key.default() == translated_name
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: name_key.default(),
                CONF_TEMPERATURE_ENTITY_ID: TEMPERATURE_ENTITY_ID,
                CONF_HUMIDITY_ENTITY_ID: HUMIDITY_ENTITY_ID,
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == translated_name
    assert result["options"][CONF_NAME] == translated_name


@pytest.mark.parametrize(
    ("source_key", "device_class"),
    [
        pytest.param(
            CONF_TEMPERATURE_ENTITY_ID, SensorDeviceClass.TEMPERATURE, id="temperature"
        ),
        pytest.param(
            CONF_HUMIDITY_ENTITY_ID, SensorDeviceClass.HUMIDITY, id="humidity"
        ),
    ],
)
async def test_source_selectors(
    hass: HomeAssistant, source_key: str, device_class: SensorDeviceClass
) -> None:
    """Test source selection is restricted to the required sensor device class."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["data_schema"].schema[source_key].config == {
        "domain": ["sensor"],
        "device_class": [device_class],
        "multiple": False,
        "reorder": False,
    }


async def test_options(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_setup_entry: AsyncMock
) -> None:
    """Test changed options automatically reload without changing identity or name."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    mock_setup_entry.reset_mock()
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    options = {
        CONF_TEMPERATURE_ENTITY_ID: "sensor.other_temperature",
        CONF_HUMIDITY_ENTITY_ID: "sensor.other_humidity",
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], options
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options == {CONF_NAME: DEFAULT_NAME, **options}
    assert mock_config_entry.title == DEFAULT_NAME
    assert not mock_config_entry.update_listeners
    mock_setup_entry.assert_awaited_once()
