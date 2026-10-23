"""Test helper lifecycle and source registry changes."""

import pytest
from custom_components.absolute_humidity.const import (
    CONF_HUMIDITY_ENTITY_ID,
    CONF_TEMPERATURE_ENTITY_ID,
)
from pytest_homeassistant.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, PERCENTAGE, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import setup_integration
from .const import ENTITY_ID, HUMIDITY_ENTITY_ID, TEMPERATURE_ENTITY_ID

pytestmark = pytest.mark.usefixtures("source_sensors")


async def test_unload_and_reload(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Unloaded helpers stop updating and reloading uses current inputs."""
    await setup_integration(hass, mock_config_entry)
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    hass.states.async_set(
        HUMIDITY_ENTITY_ID, "80", {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).attributes["condensation_risk"] == "high"


@pytest.mark.parametrize(
    ("source_key", "source_id", "new_id", "other_key", "other_id"),
    [
        pytest.param(
            CONF_TEMPERATURE_ENTITY_ID,
            TEMPERATURE_ENTITY_ID,
            "sensor.renamed_temperature",
            CONF_HUMIDITY_ENTITY_ID,
            HUMIDITY_ENTITY_ID,
            id="temperature",
        ),
        pytest.param(
            CONF_HUMIDITY_ENTITY_ID,
            HUMIDITY_ENTITY_ID,
            "sensor.renamed_humidity",
            CONF_TEMPERATURE_ENTITY_ID,
            TEMPERATURE_ENTITY_ID,
            id="humidity",
        ),
    ],
)
async def test_source_rename(
    *,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    source_key: str,
    source_id: str,
    new_id: str,
    other_key: str,
    other_id: str,
) -> None:
    """Renaming either source preserves the other reference and rebinds updates."""
    await setup_integration(hass, mock_config_entry)
    previous = hass.states.get(source_id)
    entity_registry.async_update_entity(source_id, new_entity_id=new_id)
    hass.states.async_remove(source_id)
    hass.states.async_set(new_id, previous.state, previous.attributes)
    await hass.async_block_till_done()
    assert mock_config_entry.options[source_key] == new_id
    assert mock_config_entry.options[other_key] == other_id
    assert float(hass.states.get(ENTITY_ID).state) == pytest.approx(8.62, abs=0.02)
    hass.states.async_set(new_id, "invalid", previous.attributes)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "unknown"
    hass.states.async_set(source_id, previous.state, previous.attributes)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "unknown"


async def test_registry_uuid_sources(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Resolve stored registry UUIDs and retain them when a source is renamed."""
    temperature_uuid = entity_registry.async_get(TEMPERATURE_ENTITY_ID).id
    humidity_uuid = entity_registry.async_get(HUMIDITY_ENTITY_ID).id
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={
            **mock_config_entry.options,
            CONF_TEMPERATURE_ENTITY_ID: temperature_uuid,
            CONF_HUMIDITY_ENTITY_ID: humidity_uuid,
        },
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    previous = hass.states.get(HUMIDITY_ENTITY_ID)
    new_id = "sensor.renamed_humidity"
    entity_registry.async_update_entity(HUMIDITY_ENTITY_ID, new_entity_id=new_id)
    hass.states.async_remove(HUMIDITY_ENTITY_ID)
    hass.states.async_set(new_id, "90", previous.attributes)
    await hass.async_block_till_done()
    assert mock_config_entry.options[CONF_TEMPERATURE_ENTITY_ID] == temperature_uuid
    assert mock_config_entry.options[CONF_HUMIDITY_ENTITY_ID] == humidity_uuid
    assert hass.states.get(ENTITY_ID).attributes["condensation_risk"] == "high"


async def test_helper_rename(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Repeated in-place renames preserve identity, updates, and cleanup."""
    await setup_integration(hass, mock_config_entry)
    original = entity_registry.async_get(ENTITY_ID)
    renamed_id = "sensor.renamed_absolute_humidity"
    entity_registry.async_update_entity(ENTITY_ID, new_entity_id=renamed_id)
    await hass.async_block_till_done()
    final_id = "sensor.final_absolute_humidity"
    entity_registry.async_update_entity(renamed_id, new_entity_id=final_id)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID) is None
    assert hass.states.get(renamed_id) is None
    assert entity_registry.async_get(final_id).id == original.id
    hass.states.async_set(
        HUMIDITY_ENTITY_ID, "90", {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )
    await hass.async_block_till_done()
    assert hass.states.get(final_id).attributes["condensation_risk"] == "high"
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    hass.states.async_set(
        HUMIDITY_ENTITY_ID, "50", {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )
    await hass.async_block_till_done()
    assert hass.states.get(final_id).state == STATE_UNAVAILABLE


async def test_source_registry_removal(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Removing a source leaves the helper available for source replacement."""
    await setup_integration(hass, mock_config_entry)
    entity_registry.async_remove(HUMIDITY_ENTITY_ID)
    hass.states.async_remove(HUMIDITY_ENTITY_ID)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE


async def test_options_replace_source(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """An options reload changes sources without replacing the output entity."""
    await setup_integration(hass, mock_config_entry)
    new_id = "sensor.other_humidity"
    hass.states.async_set(new_id, "90", {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE})
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_TEMPERATURE_ENTITY_ID: TEMPERATURE_ENTITY_ID,
            CONF_HUMIDITY_ENTITY_ID: new_id,
        },
    )
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).attributes["condensation_risk"] == "high"
    hass.states.async_set(HUMIDITY_ENTITY_ID, "invalid")
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).attributes["condensation_risk"] == "high"


@pytest.mark.parametrize(
    "mock_config_entry",
    [{CONF_TEMPERATURE_ENTITY_ID: "missing-registry-uuid"}],
    indirect=True,
)
async def test_missing_registry_uuid(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """An unresolved registry UUID reports a setup error rather than crashing."""
    mock_config_entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
