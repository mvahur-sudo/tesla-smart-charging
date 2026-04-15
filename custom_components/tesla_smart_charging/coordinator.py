from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_CAR_HOME,
    ATTR_MODE,
    ATTR_NEXT_DEADLINE,
    ATTR_PLUGGED_IN,
    ATTR_REASON,
    ATTR_REAL_PRICE_CENTS,
    ATTR_SAUNA_ACTIVE,
    ATTR_SOLAR_SURPLUS_W,
    ATTR_TARGET_BATTERY,
    ATTR_TESLA_LIMIT_TOO_LOW,
    CONF_BATTERY_MIN_DEFAULT,
    CONF_BATTERY_MIN_MONDAY,
    CONF_BATTERY_MIN_THURSDAY,
    CONF_BATTERY_MIN_WEEKEND,
    CONF_GRID_POWER_ENTITY,
    CONF_HOME_STATE,
    CONF_MAX_PRICE_CENTS,
    CONF_MODE_ENTITY,
    CONF_NETWORK_FEE_CENTS,
    CONF_OTHER_FEES_CENTS,
    CONF_PRICE_ENTITY,
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
    DEFAULT_HOME_STATE,
    DEFAULT_THURSDAY_EVENT_TIME,
    DEFAULT_WORKDAY_CUTOFF,
    UPDATE_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class PlannerResult:
    real_price_cents: float | None
    solar_surplus_w: float | None
    target_battery: int
    next_deadline: datetime
    recommendation: str
    reason: str
    car_home: bool
    plugged_in: bool
    sauna_active: bool
    mode: str
    tesla_limit_too_low: bool


class TeslaSmartChargingCoordinator(DataUpdateCoordinator[PlannerResult]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        super().__init__(
            hass,
            _LOGGER,
            name=entry.title,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )

    @property
    def cfg(self) -> dict[str, Any]:
        return {**self.entry.data, **self.entry.options}

    async def _async_update_data(self) -> PlannerResult:
        cfg = self.cfg

        car_home = self._get_state(cfg[CONF_TESLA_LOCATION_ENTITY]) == cfg.get(
            CONF_HOME_STATE, DEFAULT_HOME_STATE
        )
        plugged_in = self._is_on(cfg[CONF_TESLA_PLUGGED_ENTITY])
        mode = self._get_state(cfg.get(CONF_MODE_ENTITY)) or "automatic"
        sauna_active = self._compute_sauna_active()
        real_price = self._compute_real_price()
        solar_surplus = self._compute_solar_surplus()
        next_deadline, target_battery = self._compute_deadline_and_target()
        battery = self._get_float(cfg[CONF_TESLA_BATTERY_ENTITY])
        tesla_limit = self._get_float(cfg.get(CONF_TESLA_CHARGE_LIMIT_ENTITY))
        tesla_limit_too_low = tesla_limit is not None and tesla_limit < target_battery

        recommendation, reason = self._compute_recommendation(
            car_home=car_home,
            plugged_in=plugged_in,
            sauna_active=sauna_active,
            mode=mode,
            battery=battery,
            target_battery=target_battery,
            real_price=real_price,
        )

        return PlannerResult(
            real_price_cents=real_price,
            solar_surplus_w=solar_surplus,
            target_battery=target_battery,
            next_deadline=next_deadline,
            recommendation=recommendation,
            reason=reason,
            car_home=car_home,
            plugged_in=plugged_in,
            sauna_active=sauna_active,
            mode=mode,
            tesla_limit_too_low=tesla_limit_too_low,
        )

    def _compute_recommendation(
        self,
        *,
        car_home: bool,
        plugged_in: bool,
        sauna_active: bool,
        mode: str,
        battery: float | None,
        target_battery: int,
        real_price: float | None,
    ) -> tuple[str, str]:
        max_price = float(self.cfg.get(CONF_MAX_PRICE_CENTS, 15.0))

        if mode == "charge_now":
            return "charge_now", "manual_override_charge_now"
        if mode == "dont_charge_today":
            return "blocked", "manual_override_do_not_charge"
        if not car_home:
            return "wait", "car_not_home"
        if not plugged_in:
            return "wait", "car_not_plugged_in"
        if sauna_active:
            return "blocked", "sauna_active"
        if battery is not None and battery >= target_battery:
            return "wait", "battery_already_above_target"
        if mode == "ensure_ready":
            return "charge", "ensure_ready_mode"
        if real_price is None:
            return "wait", "price_unavailable_safe_hold"
        if mode == "cheap_only":
            if real_price <= max_price:
                return "charge", "cheap_only_window"
            return "wait", "cheap_only_price_too_high"
        if real_price <= max_price:
            return "charge", "price_below_threshold"
        return "wait", "waiting_for_cheaper_window"

    def _compute_deadline_and_target(self) -> tuple[datetime, int]:
        now = dt_util.now()
        weekday = now.weekday()
        thursday_event = self._is_on(self.cfg.get(CONF_THURSDAY_EVENT_ENTITY))

        if weekday == 0:
            target = int(self.cfg.get(CONF_BATTERY_MIN_MONDAY, 80))
            deadline_time = self.cfg.get(CONF_WORKDAY_CUTOFF, DEFAULT_WORKDAY_CUTOFF)
        elif weekday == 3 and thursday_event:
            target = int(self.cfg.get(CONF_BATTERY_MIN_THURSDAY, 40))
            deadline_time = self.cfg.get(
                CONF_THURSDAY_EVENT_TIME, DEFAULT_THURSDAY_EVENT_TIME
            )
        elif weekday >= 5:
            target = int(self.cfg.get(CONF_BATTERY_MIN_WEEKEND, 30))
            deadline_time = "10:00"
        else:
            target = int(self.cfg.get(CONF_BATTERY_MIN_DEFAULT, 30))
            deadline_time = self.cfg.get(CONF_WORKDAY_CUTOFF, DEFAULT_WORKDAY_CUTOFF)

        hours, minutes = [int(part) for part in deadline_time.split(":", 1)]
        deadline = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        if deadline <= now:
            deadline += timedelta(days=1)
        return deadline, target

    def _compute_real_price(self) -> float | None:
        price_entity = self.cfg[CONF_PRICE_ENTITY]
        raw = self._get_float(price_entity)
        if raw is None:
            return None

        unit = (self.hass.states.get(price_entity).attributes.get("unit_of_measurement") or "").lower()
        if "eur/mwh" in unit or "€/mwh" in unit:
            spot_cents = raw * 0.1
        elif "eur/kwh" in unit or "€/kwh" in unit:
            spot_cents = raw * 100
        else:
            spot_cents = raw

        return round(
            spot_cents
            + float(self.cfg.get(CONF_NETWORK_FEE_CENTS, 0))
            + float(self.cfg.get(CONF_OTHER_FEES_CENTS, 0)),
            3,
        )

    def _compute_solar_surplus(self) -> float | None:
        solar = self._get_float(self.cfg[CONF_SOLAR_POWER_ENTITY])
        grid = self._get_float(self.cfg[CONF_GRID_POWER_ENTITY])
        if solar is None or grid is None:
            return None
        wall = self._get_float(self.cfg.get(CONF_WALL_POWER_ENTITY)) or 0.0
        surplus = max(0.0, solar + min(0.0, grid * -1) - wall)
        return round(surplus, 1)

    def _compute_sauna_active(self) -> bool:
        sauna_bool = self._is_on(self.cfg.get(CONF_SAUNA_BOOLEAN_ENTITY))
        sauna_power = self._get_float(self.cfg.get(CONF_SAUNA_POWER_ENTITY)) or 0.0
        threshold = float(self.cfg.get(CONF_SAUNA_POWER_THRESHOLD_W, 500.0))
        return sauna_bool or sauna_power >= threshold

    def _get_state(self, entity_id: str | None) -> str | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        if state.state in {"unknown", "unavailable"}:
            return None
        return state.state

    def _get_float(self, entity_id: str | None) -> float | None:
        state = self._get_state(entity_id)
        if state is None:
            return None
        try:
            return float(state)
        except (TypeError, ValueError):
            return None

    def _is_on(self, entity_id: str | None) -> bool:
        state = self._get_state(entity_id)
        return state in {"on", "home", "true", "charging"}

    def attrs(self) -> dict[str, Any]:
        if not self.data:
            return {}
        return {
            ATTR_REASON: self.data.reason,
            ATTR_TARGET_BATTERY: self.data.target_battery,
            ATTR_NEXT_DEADLINE: self.data.next_deadline.isoformat(),
            ATTR_REAL_PRICE_CENTS: self.data.real_price_cents,
            ATTR_SOLAR_SURPLUS_W: self.data.solar_surplus_w,
            ATTR_CAR_HOME: self.data.car_home,
            ATTR_PLUGGED_IN: self.data.plugged_in,
            ATTR_SAUNA_ACTIVE: self.data.sauna_active,
            ATTR_MODE: self.data.mode,
            ATTR_TESLA_LIMIT_TOO_LOW: self.data.tesla_limit_too_low,
        }
