# Tesla Smart Charging

Home Assistant custom integration for Tesla EV charging planning.

This integration is designed for cost-aware, solar-aware Tesla charging, with weekday and event minimum battery targets, planner windows for today and tomorrow, and Lovelace-friendly entities for dashboards.

## What it does today

Version `v0.2.x` focuses on the planner layer.

It exposes:

- current real charging price
- current solar surplus
- target battery for the next deadline
- next deadline timestamp
- recommendation and reason
- today planner summary
- tomorrow planner summary
- binary sensors for charge allowed, cheap time, car home, plugged in, sauna active, Tesla limit too low
- rich attributes containing:
  - today cheap windows
  - tomorrow cheap windows
  - today recommended windows
  - tomorrow recommended windows
  - today solar windows
  - tomorrow solar windows
  - today fallback windows
  - tomorrow fallback windows

It does **not** modify Tesla target SOC. It does **not** yet automatically start or stop charging. It is planner-first and HACS-ready.

## Current planning logic

- charge logic only becomes relevant when the Tesla is at home and plugged in
- price = spot price + network fee + other fees
- weekday rules:
  - Monday minimum battery target
  - Thursday event target
  - default weekday target
  - weekend target
- sauna lockout
- manual modes supported through an optional Home Assistant entity:
  - `automatic`
  - `charge_now`
  - `dont_charge_today`
  - `cheap_only`
  - `ensure_ready`
- today and tomorrow cheapest-window extraction from price list entities
- solar window marking when current solar surplus exceeds configured minimum threshold
- fallback windows by selecting cheapest overall windows from today and tomorrow when battery target is not yet met

## HACS installation

1. Open HACS
2. Integrations
3. Custom repositories
4. Add repository URL:
   - `https://github.com/mvahur-sudo/tesla-smart-charging`
5. Category: **Integration**
6. Install `Tesla Smart Charging`
7. Restart Home Assistant
8. Go to **Settings → Devices & Services → Add Integration**
9. Add `Tesla Smart Charging`

## Setup fields

During setup, select:

### Required
- current price entity
- Tesla battery entity
- Tesla location entity
- Tesla plugged-in entity
- solar production entity
- grid power entity

### Strongly recommended
- today price list entity
- tomorrow price list entity

### Optional
- wall connector power entity
- sauna power entity
- sauna boolean entity
- Tesla charge limit entity
- manual mode entity
- Thursday event entity

## Exact entity mapping for your current Home Assistant

These are the entities currently present in your HA and are the recommended mapping for the integration setup dialog.

### Recommended mapping

| Setup field | Recommended entity |
|---|---|
| Current price entity | `sensor.nord_pool_ee_current_price` |
| Today price list entity | `sensor.ee_today_price_list` |
| Tomorrow price list entity | `sensor.ee_tomorrow_price_list` |
| Tesla battery entity | `sensor.tesla_battery_level` |
| Tesla location entity | `device_tracker.tesla_location` |
| Tesla plugged-in entity | `binary_sensor.tesla_wall_connector_vehicle_connected` |
| Tesla charge limit entity | `number.tesla_charge_limit` |
| Solar production entity | `sensor.solarnet_power_photovoltaics` |
| Grid power entity | `sensor.smart_meter_ts_65a_3_real_power` |
| Wall connector power entity | `sensor.tesla_wall_connector_power` |
| Sauna power entity | `sensor.dusssaun_switch_0_power` |
| Sauna boolean entity | `input_boolean.saun_sisse` |

### Optional future manual mode helper
If you later create an HA helper for manual mode, map it as:
- `input_select.ev_charging_mode`

### Optional future Thursday event helper
If you later create an HA helper for the Thursday special event, map it as:
- `input_boolean.ev_thursday_event_active`

## Entity model exposed by this integration

Assuming the integration title is `Tesla Smart Charging`, Home Assistant will create entities similar to:

### Sensors
- `sensor.tesla_smart_charging_real_price`
- `sensor.tesla_smart_charging_solar_surplus`
- `sensor.tesla_smart_charging_target_battery`
- `sensor.tesla_smart_charging_next_deadline`
- `sensor.tesla_smart_charging_recommendation`
- `sensor.tesla_smart_charging_reason`
- `sensor.tesla_smart_charging_today_planner`
- `sensor.tesla_smart_charging_tomorrow_planner`

### Binary sensors
- `binary_sensor.tesla_smart_charging_charge_allowed`
- `binary_sensor.tesla_smart_charging_cheap_time`
- `binary_sensor.tesla_smart_charging_car_home`
- `binary_sensor.tesla_smart_charging_plugged_in`
- `binary_sensor.tesla_smart_charging_sauna_active`
- `binary_sensor.tesla_smart_charging_tesla_limit_too_low`

## Planner attributes

The planner sensors expose window arrays as attributes. These are intended for dashboards and future automation logic.

Important attributes:
- `today_cheap_windows`
- `tomorrow_cheap_windows`
- `today_recommended_windows`
- `tomorrow_recommended_windows`
- `today_solar_windows`
- `tomorrow_solar_windows`
- `today_fallback_windows`
- `tomorrow_fallback_windows`

Each window item is structured like:

```json
{
  "start": "2026-04-15T09:00:00+00:00",
  "end": "2026-04-15T09:15:00+00:00",
  "price_cents": 9.24
}
```

## Price unit handling

The integration auto-detects these common units:

- `EUR/MWh`
- `EUR/kWh`
- `c/kWh`
- `senti/kWh`

For list entities that label values as `senti/kWh` but provide decimal euro values, the integration applies a defensive normalization heuristic so planner windows still work.

## Example Lovelace dashboard

An example dashboard file is included here:

- `examples/lovelace-dashboard.yaml`

It is intentionally simple and safe. It does not touch Overview or Lovelace mode.

## Roadmap

Next planned steps:

- better deadline-aware selection of required window count
- solar-preferred windows using forecast data, not only current surplus
- fallback charging window scoring by deadline urgency
- per-session cost accounting
- monthly EV charging cost sensor
- notifications
- service calls for `charge_now`, `stop`, and override reset
- optional automations package

## Development notes

This repository is intentionally structured for HACS custom integration distribution.
