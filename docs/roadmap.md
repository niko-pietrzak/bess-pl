# Roadmap

Stages 0–10 are the core, ordered by dependency, not by month. Stage 10 is the guaranteed goal. Target: publication #1 in January 2027.

| # | Stage | Scope | Done when | Status |
|---|---|---|---|---|
| 0 | Market: how a battery earns | market primer + 3 ADRs | `docs/market-primer.md` and ADR 0001–0003 in repo | done |
| 1 | Repo skeleton and working rules | layout, uv, ruff, pytest, short README, STATUS.md, ADR template, CLI with empty commands | `bess --help` works, lint and tests pass | next |
| 2 | Source inventory | per source: coverage, resolution, history, publication time, licence, pitfalls; WDB rules; competitor landscape | `docs/data-sources.md` complete; open questions resolved or recorded | todo |
| 3 | Ingest and raw snapshots | ENTSO-E, PSE, Open-Meteo Single Runs; immutable raw with download time; backfill from 06.2024; daily 10:30 snapshot | one command downloads full history; rerun adds no duplicates | todo |
| 4 | Data layer (dbt-duckdb) | UTC, 15-min grid, units; one optimiser input table; tests for gaps, duplicates and DST | complete grid from 06.2024, tests pass | todo |
| 5 | Optimiser v1: day-ahead | LP: SoC, efficiency, cycle limit; day by day with SoC carry-over and end-of-day energy value; MILP only if needed | tests on hand-computed cases; results make sense by eye | todo |
| 6 | Optimiser v2: FCR and aFRR | joint optimisation; operating-point rule; energy headroom; activations in 3 variants (A typical level as Modo, B proportional, C none); CEN not as revenue | revenue split by market; order of magnitude matches benchmarks or is explained | todo |
| 7 | Index and methodology | ceiling, realistic variant (v1: naive forecasts), capture rate; versioned methodology; data breakpoints flagged | methodology v1.0 and series from 06.2024 for 2h and 4h | todo |
| 8 | Report and publication #1 | charts and post draft in one command, validations, EN post, public repo | post with methodology link published | todo |
| 9 | Forecast log | next-month index forecast (P50 with interval), settle the previous one, commit before the fact | first forecast published | todo |
| 10 | Price forecast on forecast weather | day-ahead price per 15 min, cutoff 11:00 D-1; ECMWF 00 UTC run, price lags, calendar, load forecast; one GBM + 2 baselines; walk-forward; scored in PLN/MW | feeds the realistic variant; backtest published; live forecast at 11:00. Time box ~25 h; a negative result is published too | todo |

Later, no promises:
- 11: intraday (RDB), once the TGE data licence is clear.
- 12: capacity market obligation.
- 13: price scenarios (11 GW of storage, offshore wind, nuclear, flexible demand).
- 14: P10/P50/P90 and a finance layer (CFADS, DSCR, debt sizing).

Architecture from day one: the asset is a swappable module (battery, PV + battery, heat storage); the market is configuration (Poland, other CEE countries).

## Open questions for stage 2
- Times of the balancing capacity auctions (basic and supplementary mode): gate closures for ADR-0003.
- Products: 15-min periods or blocks (FCR hourly per Modo)?
- Minutes of full power to hold in reserve for each product.
- Operating-point rule and reserve in both directions at once: confirm in WDB.
- How to model aFRR activation for a single battery (variants A, B, C).
- Actual publication times of PSE and ENTSO-E forecasts (10:45 snapshots for one week).
- Exact date of the day-ahead switch to 15 min; DST handling.
- Is a public index non-commercial use under Open-Meteo terms?
- PolBESS methodology: perfect foresight or not; efficiency and cycle assumptions.
