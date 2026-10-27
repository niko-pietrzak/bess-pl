# ADR-0001: Reference asset

Status: accepted · 2026-10-25

## Context
The index needs one fixed, transparent asset, so that months are comparable with each other and with Modo, Clean Horizon and PolBESS.

## Decision
- Two assets: 1 MW / 2 MWh and 1 MW / 4 MWh. MWh are usable energy (SoC 0–100% of usable).
- Round-trip efficiency 86%, split evenly: √0.86 ≈ 92.7% on charge and on discharge.
- Cycle limit 1.5 full cycles per day; one cycle = discharged energy equal to usable capacity, from day-ahead trading and aFRR activations. v1 enforces it per day; a rolling budget is a stage 5 refinement.
- No degradation cost in the base case, because the cycle limit already prices wear. Degradation cost appears only as a sensitivity.
- The asset is always new (no capacity fade) and a price taker (1 MW does not move prices).
- Parameters live in `config/assets.yaml`; all of them are subject to sensitivity analysis.

## Consequences
- The series from 06.2024 reflects the market, not battery ageing or cell prices.
- Results are per MW, so 2h and 4h are directly comparable.
