from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_BATTERY_MIN_DEFAULT,
    CONF_BATTERY_MIN_MONDAY,
    CONF_BATTERY_MIN_THURSDAY,
    CONF_BATTERY_MIN_WEEKEND,
    CONF_GRID_POWER_ENTITY,
    CONF_HOME_STATE,
    CONF_MAX_PRICE_CENTS,
    CONF_MODE_ENTITY,
    CONF_NAME,
    CONF_NETWORK_FEE_CENTS,
    CONF_OTHER_FEES_CENTS,
    CONF_PRICE_ENTITY,
    CONF_PRICE_TODAY_ENTITY,
    CONF_PRICE_TOMORROW_ENTITY,
    CONF_SAUNA_BOOLEAN_ENTITY,
    CONF_SAUNA_POWER_ENTITY,
    CONF_SAUNA_POWER_THRESHOLD_W,
    CONF_SOLAR_MIN_SURPLUS_W,
    CONF_SOLAR_POWER_ENTITY,
    CONF_TESLA_BATTERY_ENTITY,
    CONF_TESLA_CHARGE_LIMIT_ENTITY,
    CONF_TESLA_LOCATION_ENTITY,
    CONF_TESLA_PLUGGED_ENTITY,
    CONF_THURSDAY_EVENT_ENTITY,
    CONF_THURSDAY_EVENT_TIME,
    CONF_WALL_POWER_ENTITY,
    CONF_WORKDAY_CUTOFF,
    DEFAULT_BATTERY_MIN_DEFAULT,
    DEFAULT_BATTERY_MIN_MONDAY,
    DEFAULT_BATTERY_MIN_THURSDAY,
    DEFAULT_BATTERY_MIN_WEEKEND,
    DEFAULT_HOME_STATE,
    DEFAULT_MAX_PRICE_CENTS,
    DEFAULT_NAME,
    DEFAULT_NETWORK_FEE_CENTS,
    DEFAULT_OTHER_FEES_CENTS,
    DEFAULT_SAUNA_POWER_THRESHOLD_W,
    DEFAULT_SOLAR_MIN_SURPLUS_W,
    DEFAULT_THURSDAY_EVENT_TIME,
    DEFAULT_WORKDAY_CUTOFF,
    DOMAIN,
)


def _entity_selector(domain: str | None = None) -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain=domain, multiple=False)
    )


STEP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): selector.TextSelector(),
        vol.Required(CONF_PRICE_ENTITY): _entity_selector("sensor"),
        vol.Optional(CONF_PRICE_TODAY_ENTITY): _entity_selector("sensor"),
        vol.Optional(CONF_PRICE_TOMORROW_ENTITY): _entity_selector("sensor"),
        vol.Required(CONF_TESLA_BATTERY_ENTITY): _entity_selector("sensor"),
        vol.Required(CONF_TESLA_LOCATION_ENTITY): _entity_selector("device_tracker"),
        vol.Required(CONF_TESLA_PLUGGED_ENTITY): _entity_selector("binary_sensor"),
        vol.Optional(CONF_TESLA_CHARGE_LIMIT_ENTITY): _entity_selector("number"),
        vol.Required(CONF_SOLAR_POWER_ENTITY): _entity_selector("sensor"),
        vol.Required(CONF_GRID_POWER_ENTITY): _entity_selector("sensor"),
        vol.Optional(CONF_WALL_POWER_ENTITY): _entity_selector("sensor"),
        vol.Optional(CONF_SAUNA_POWER_ENTITY): _entity_selector("sensor"),
        vol.Optional(CONF_SAUNA_BOOLEAN_ENTITY): _entity_selector("input_boolean"),
        vol.Optional(CONF_MODE_ENTITY): _entity_selector("input_select"),
        vol.Optional(CONF_THURSDAY_EVENT_ENTITY): _entity_selector(),
        vol.Optional(CONF_HOME_STATE, default=DEFAULT_HOME_STATE): selector.TextSelector(),
        vol.Optional(
            CONF_MAX_PRICE_CENTS, default=DEFAULT_MAX_PRICE_CENTS
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=0.1)
        ),
        vol.Optional(
            CONF_NETWORK_FEE_CENTS, default=DEFAULT_NETWORK_FEE_CENTS
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=0.1)
        ),
        vol.Optional(
            CONF_OTHER_FEES_CENTS, default=DEFAULT_OTHER_FEES_CENTS
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=0.1)
        ),
        vol.Optional(
            CONF_SOLAR_MIN_SURPLUS_W, default=DEFAULT_SOLAR_MIN_SURPLUS_W
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=10000, step=50)
        ),
        vol.Optional(
            CONF_SAUNA_POWER_THRESHOLD_W, default=DEFAULT_SAUNA_POWER_THRESHOLD_W
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=10000, step=50)
        ),
        vol.Optional(
            CONF_BATTERY_MIN_MONDAY, default=DEFAULT_BATTERY_MIN_MONDAY
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=1)
        ),
        vol.Optional(
            CONF_BATTERY_MIN_THURSDAY, default=DEFAULT_BATTERY_MIN_THURSDAY
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=1)
        ),
        vol.Optional(
            CONF_BATTERY_MIN_DEFAULT, default=DEFAULT_BATTERY_MIN_DEFAULT
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=1)
        ),
        vol.Optional(
            CONF_BATTERY_MIN_WEEKEND, default=DEFAULT_BATTERY_MIN_WEEKEND
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=1)
        ),
        vol.Optional(
            CONF_WORKDAY_CUTOFF, default=DEFAULT_WORKDAY_CUTOFF
        ): selector.TimeSelector(),
        vol.Optional(
            CONF_THURSDAY_EVENT_TIME, default=DEFAULT_THURSDAY_EVENT_TIME
        ): selector.TimeSelector(),
    }
)


class TeslaSmartChargingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_NAME])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        return self.async_show_form(step_id="user", data_schema=STEP_SCHEMA)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return TeslaSmartChargingOptionsFlow(config_entry)


class TeslaSmartChargingOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = {}
        for key, field in STEP_SCHEMA.schema.items():
            default = self.config_entry.options.get(
                key.schema if hasattr(key, "schema") else key,
                self.config_entry.data.get(key.schema if hasattr(key, "schema") else key),
            )
            schema[vol.Optional(key.schema if hasattr(key, "schema") else key, default=default)] = field

        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema))
