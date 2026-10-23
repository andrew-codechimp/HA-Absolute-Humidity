"""Config and options flows for the absolute humidity helper."""

from collections.abc import Mapping
from typing import Any, cast

import probatio

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN, SensorDeviceClass
from homeassistant.const import CONF_DEVICE_ID, CONF_NAME
from homeassistant.helpers import device_registry as dr, selector, translation
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaCommonFlowHandler,
    SchemaConfigFlowHandler,
    SchemaFlowError,
    SchemaFlowFormStep,
)

from .const import (
    CONF_HUMIDITY_ENTITY_ID,
    CONF_TEMPERATURE_ENTITY_ID,
    DOMAIN,
)

OPTIONS_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_TEMPERATURE_ENTITY_ID): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN, device_class=SensorDeviceClass.TEMPERATURE
            )
        ),
        probatio.Required(CONF_HUMIDITY_ENTITY_ID): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN, device_class=SensorDeviceClass.HUMIDITY
            )
        ),
        probatio.Optional(CONF_DEVICE_ID): selector.DeviceSelector(),
    }
)


async def async_validate_input(
    handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
) -> dict[str, Any]:
    """Accept an optional link to an existing main or child device."""
    if not (device_id := user_input.get(CONF_DEVICE_ID)):
        user_input.pop(CONF_DEVICE_ID, None)
    elif (
        dr.async_get(handler.parent_handler.hass).async_get(
            device_id, include_composite_devices=False
        )
        is None
    ):
        raise SchemaFlowError("invalid_device")
    return user_input


async def async_config_schema(handler: SchemaCommonFlowHandler) -> probatio.Schema:
    """Suggest a helper name in the server's configured language."""
    hass = handler.parent_handler.hass
    translations = await translation.async_get_translations(
        hass, hass.config.language, "entity", {DOMAIN}
    )
    return probatio.Schema(
        {
            probatio.Required(
                CONF_NAME,
                default=translations[
                    f"component.{DOMAIN}.entity.sensor.absolute_humidity.name"
                ],
            ): selector.TextSelector()
        }
    ).extend(OPTIONS_SCHEMA.schema)


class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle creation and configuration of absolute humidity helpers."""

    config_flow = {
        "user": SchemaFlowFormStep(
            async_config_schema, validate_user_input=async_validate_input
        )
    }
    options_flow = {
        "init": SchemaFlowFormStep(
            OPTIONS_SCHEMA, validate_user_input=async_validate_input
        )
    }
    options_flow_reloads = True

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return the helper's name."""
        return cast(str, options[CONF_NAME])
