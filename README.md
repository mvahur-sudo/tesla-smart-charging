# Tesla Smart Charging

Home Assistant custom integration for Tesla EV charging planning.

This integration is designed for cost-aware, solar-aware Tesla charging, with weekday/event minimum battery targets and Home Assistant dashboard-friendly entities.

## Current scope, v0.1.0

The first version provides a planner layer that exposes:

- `sensor.real_price`
- `sensor.solar_surplus`
- `sensor.target_battery`
- `sensor.next_deadline`
- `sensor.recommendation`
- `sensor.reason`
- `binary_sensor.charge_allowed`
- `binary_sensor.car_home`
- `binary_sensor.plugged_in`
- `binary_sensor.sauna_active`
- `binary_sensor.tesla_limit_too_low`

It does not yet write Tesla target SOC. It only computes recommendations.

## Supported logic

- Charge only when the Tesla is at home and plugged in
- Add network fees and extra fees on top of spot price
- Monday minimum battery target
- Thursday event target
- Default weekday and weekend targets
- Sauna block
- Manual mode entity support:
  - `automatic`
  - `charge_now`
  - `dont_charge_today`
  - `cheap_only`
  - `ensure_ready`

## HACS installation

1. Open HACS
2. Integrations
3. Custom repositories
4. Add repository URL for this repo
5. Category: Integration
6. Install `Tesla Smart Charging`
7. Restart Home Assistant
8. Add integration from Settings → Devices & Services

## Required source entities

You select these during setup:

- current price entity
- Tesla battery entity
- Tesla location entity
- Tesla plugged-in entity
- solar production entity
- grid power entity

Optional:

- wall connector power entity
- sauna power entity
- sauna boolean entity
- Tesla charge limit entity
- manual mode entity
- Thursday event entity

## Notes on price units

The integration auto-detects these common units:

- `c/kWh`
- `senti/kWh`
- `EUR/kWh`
- `EUR/MWh`

## Roadmap

- cheapest-hours planner for today/tomorrow
- solar-preferred windows
- fallback charge windows
- per-session cost accounting
- monthly EV charging cost sensor
- notifications and service actions
- Lovelace example dashboard

## Development

This repository is intentionally structured for HACS custom integration distribution.
