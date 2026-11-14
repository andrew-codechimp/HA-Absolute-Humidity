"""Custom integration to provide absolute_humidity helpers for Home Assistant.

For more details about this integration, please refer to
https://github.com/andrew-codechimp/HA-Absolute-Humidity
"""

from functools import partial

import probatio
from awesomeversion.awesomeversion import AwesomeVersion

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import __version__ as HA_VERSION  # noqa: N812
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError, HomeAssistantError
from homeassistant.helpers import (
    config_validation as cv,
    entity_registry as er,
)
from homeassistant.helpers.helper_integration import async_handle_source_entity_changes
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_loaded_integration
from homeassistant.util.json import load_json_object

from .const import (
    CONF_HUMIDITY_ENTITY_ID,
    CONF_TEMPERATURE_ENTITY_ID,
    DOMAIN,
    LOGGER,
    MIN_HA_VERSION,
    PLATFORMS,
)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type AbsoluteHumidityConfigEntry = ConfigEntry[dict[str, str]]


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

    await async_check_marketplace_installation(hass)

    return True


async def async_check_marketplace_installation(hass: HomeAssistant) -> None:
    """Warn when not installed through Marketplace."""
    if not hass.config_entries.async_entries(DOMAIN):
        return

    try:
        storage = await hass.async_add_executor_job(
            load_json_object,
            hass.config.path(".storage", "marketplace.repositories"),
        )
    except HomeAssistantError:
        LOGGER.debug("Unable to read Marketplace repositories", exc_info=True)
        return

    repositories = storage.get("data", {})
    if not isinstance(repositories, dict):
        return

    for repository in repositories.values():
        if not isinstance(repository, dict) or not isinstance(
            repository.get("installed", False), bool
        ):
            return
        if repository.get("domain") == DOMAIN and repository.get("installed") is True:
            return

    LOGGER.warning(
        "%s is manually installed and will not get automatic updates",
        async_get_loaded_integration(hass, DOMAIN).name,
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: AbsoluteHumidityConfigEntry
) -> None:
    """Set up from a config entry."""

    entity_registry = er.async_get(hass)
    source_ids: dict[str, str] = {}
    for key in (CONF_TEMPERATURE_ENTITY_ID, CONF_HUMIDITY_ENTITY_ID):
        try:
            source_ids[key] = er.async_validate_entity_id(
                entity_registry, entry.options[key]
            )
        except probatio.Invalid as err:
            raise ConfigEntryError(
                translation_domain=DOMAIN,
                translation_key="source_entity_not_found",
                translation_placeholders={"entity_id": entry.options[key]},
            ) from err

    entry.runtime_data = source_ids
    for key in source_ids:
        entry.async_on_unload(
            async_handle_source_entity_changes(
                hass,
                helper_config_entry_id=entry.entry_id,
                set_source_entity_id_or_uuid=partial(
                    _async_update_source, hass, entry, key
                ),
                source_device_id=None,
                source_entity_id_or_uuid=entry.options[key],
                source_entity_removed=_async_source_removed,
            )
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


async def _async_source_removed() -> None:
    """Keep the separately selected device link when a source is removed."""


@callback
def _async_update_source(
    hass: HomeAssistant,
    entry: AbsoluteHumidityConfigEntry,
    key: str,
    entity_id: str,
) -> None:
    """Update a renamed source and reload its state subscription."""
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, key: entity_id}
    )
    hass.config_entries.async_schedule_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: AbsoluteHumidityConfigEntry
) -> None:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms_or_raise(entry, PLATFORMS)
