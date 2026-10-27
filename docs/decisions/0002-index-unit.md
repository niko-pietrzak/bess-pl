# ADR-0002: Index unit

Status: accepted · 2026-10-25

## Context
Modo publishes annualised PLN/MW/year, PolBESS monthly PLN/MW, Clean Horizon EUR/MW/year. Without a stated unit and revenue boundary, comparisons between indices are meaningless.

## Decision
- Headline: PLN/MW/year, annualised as monthly revenue × 365 / days in month.
- Also published: monthly PLN/MW (not annualised) and EUR at the monthly average of NBP (Narodowy Bank Polski) mid rates.
- Gross market revenue: before grid fees, optimiser fee, opex and taxes.
- Ceiling, realistic variant and capture rate are reported in the same unit.

## Consequences
- One number compares directly with Modo (annualised) and PolBESS (monthly), and EUR with Clean Horizon.
- Net revenue for an investor is a separate, later layer (stage 14).
