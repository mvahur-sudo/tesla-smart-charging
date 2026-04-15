from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PlannerResult
from .entity import TeslaSmartChargingEntity


@dataclass(frozen=True, kw_only=True)
class TeslaChargingBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[PlannerResult], bool]


BINARY_SENSORS: tuple[TeslaChargingBinarySensorDescription, ...] = (
    TeslaChargingBinarySensorDescription(
        key="charge_allowed",
        name="Charge allowed",
        value_fn=lambda data: data.recommendation in {"charge", "charge_now"},
    ),
    TeslaChargingBinarySensorDescription(
        key="car_home",
        name="Car home",
        value_fn=lambda data: data.car_home,
    ),
    TeslaChargingBinarySensorDescription(
        key="plugged_in",
        name="Plugged in",
        value_fn=lambda data: data.plugged_in,
    ),
    TeslaChargingBinarySensorDescription(
        key="sauna_active",
        name="Sauna active",
        value_fn=lambda data: data.sauna_active,
    ),
    TeslaChargingBinarySensorDescription(
        key="tesla_limit_too_low",
        name="Tesla limit too low",
        value_fn=lambda data: data.tesla_limit_too_low,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        TeslaChargingBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )


class TeslaChargingBinarySensor(TeslaSmartChargingEntity, BinarySensorEntity):
    entity_description: TeslaChargingBinarySensorDescription

    def __init__(self, coordinator, description: TeslaChargingBinarySensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self):
        return self.coordinator.attrs()
