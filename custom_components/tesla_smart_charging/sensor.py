from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from homeassistant.components.sensor import SensorEntityDescription, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PlannerResult
from .entity import TeslaSmartChargingEntity


@dataclass(frozen=True, kw_only=True)
class TeslaChargingSensorDescription(SensorEntityDescription):
    value_fn: Callable[[PlannerResult], object]


SENSORS: tuple[TeslaChargingSensorDescription, ...] = (
    TeslaChargingSensorDescription(
        key="real_price_cents",
        name="Real price",
        native_unit_of_measurement="c/kWh",
        value_fn=lambda data: data.real_price_cents,
    ),
    TeslaChargingSensorDescription(
        key="solar_surplus_w",
        name="Solar surplus",
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda data: data.solar_surplus_w,
    ),
    TeslaChargingSensorDescription(
        key="target_battery",
        name="Target battery",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.target_battery,
    ),
    TeslaChargingSensorDescription(
        key="recommendation",
        name="Recommendation",
        value_fn=lambda data: data.recommendation,
    ),
    TeslaChargingSensorDescription(
        key="reason",
        name="Reason",
        value_fn=lambda data: data.reason,
    ),
    TeslaChargingSensorDescription(
        key="next_deadline",
        name="Next deadline",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.next_deadline,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(TeslaChargingSensor(coordinator, description) for description in SENSORS)


class TeslaChargingSensor(TeslaSmartChargingEntity):
    entity_description: TeslaChargingSensorDescription

    def __init__(
        self,
        coordinator,
        description: TeslaChargingSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self):
        return self.coordinator.attrs()
