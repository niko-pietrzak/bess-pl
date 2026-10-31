# Roadmap

Stages 0–10 are the core, ordered by dependency, not by month. Stage 10 is the guaranteed goal. Target: publication #1 in January 2027.

| # | Stage | Scope | Done when | Status |
|---|---|---|---|---|
| 0 | Market: how a battery earns | market primer + 3 ADRs | `docs/market-primer.md` and ADR 0001–0003 in repo | done |
| 1 | Repo skeleton and working rules | layout, uv, ruff, pytest, short README, STATUS.md, ADR template, CLI with empty commands | `bess --help` works, lint and tests pass | done |
| 2 | Source inventory | per source: coverage, resolution, history, publication time, licence, pitfalls; WDB rules; competitor landscape | `docs/data-sources.md` complete; open questions resolved or recorded | done |
| 3 | Ingest and raw snapshots | ENTSO-E, PSE, Open-Meteo Single Runs; immutable raw with download time; daily snapshots before the 08:30 and 11:00 cutoffs with RFC 3161 time stamps; backfill from 06.2024; measured publication times | snapshots run in the cloud 7 days in a row without intervention, alert tested; backfill idempotent with a gap report; `bess status` shows last, late and missing snapshots | in progress |
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
- ~~Times of the balancing capacity auctions (basic and supplementary mode)~~: ADR-0006.
- ~~Products: 15-min periods or blocks~~: ADR-0006 (reserves hourly in basic mode, 15 min elsewhere).
- Minutes of full power to hold in reserve for each product.
- ~~Operating-point rule~~: moved to stage 6 (O5 in ADR-0006).
- How to model aFRR activation for a single battery (variants A, B, C).
- ~~Actual publication times of PSE and ENTSO-E forecasts~~: moved to stage 3.
- ~~Exact date of the day-ahead switch to 15 min~~: delivery day 1.10.2025 (ADR-0006). DST handling: WDB 8.1(25)–(26).
- Is a public index non-commercial use under Open-Meteo terms?
- PolBESS methodology: perfect foresight or not; efficiency and cycle assumptions.

## Open questions for stage 3
- Actual publication times of PSE and ENTSO-E data (O6 in ADR-0006).
- Does the PSE API return a publication time per record? Needed to apply cutoffs to history without snapshots. Partly answered: `publication_ts` exists but is the last revision time (`docs/data-sources.md`).
- Does PSE publish volumes and prices of supplementary-mode capacity? Endpoints exist (`cmbu-tu`, `mbu-tu`); check content and coverage.
- Do sources overwrite data after publication (forecast and price revisions), and does the API expose versions? If not, history may contain information from after the cutoff.
- Where do the snapshots run without a laptop switched on? ADR-0007. Evidence: RFC 3161 tokens on each slot manifest, stored with the data; a public evidence repo waits for stage 9.
- After 28.03.2027: a short repeat of the publication-time measurement in summer time. Sources on UTC schedules (ECMWF, Open-Meteo) then appear one hour later in local time; PSE works in local time.

## Open questions for stage 6
- Realistic variant: bids at opportunity cost or fixed volumes? Confirm in WDB (balancing rules) that the RMB marginal price is set per hour, product and direction.
- Operating-point rule for storage units (JGM1 states, WDB 8.6.5; O5 in ADR-0006).
- Under marginal pricing a small player's best capacity bid is its opportunity cost (forgone day-ahead arbitrage). The realistic variant then depends mainly on a day-ahead price forecast, not a reserve price forecast.

## Open questions for stage 7
- Naive forecast = day-ahead prices of the last known day. ADR: after weekends and holidays, take the same weekday one week earlier instead?
- Capture rate split by market.
- The methodology states the simplifications of v1: no intraday, no supplementary mode, a fixed plan.
- PSE settlement data is revised long after the fact (`crb-rozl` for 14.06.2024 revised on 16.09.2025), so the index for recent months can change. The methodology must state the data vintage of every publication and the rule for recalculation.

## Open questions for stage 10
- The price model takes the cutoff as a parameter: 11:00 D-1 for day-ahead, 08:30 D-1 for reserve bids. Data availability is checked separately for each cutoff.
- Foreign features: weather in DE, CZ and LT; ENTSO-E transfer capacities and flows (11.1.A, 11.1.B, 12.1.G).
- Is the 00 UTC ECMWF run available before 08:30 local in summer (06:30 UTC)? 08:30 is our conservative convention; bids are accepted until 09:00. If not, the reserve cutoff uses the 18 UTC run of D-2. Snapshots and the publication-time measurement (stage 3) answer this.
- PSE `pk5l-wp` and PKD (`pdgopkd`, `pdgobpkd`): wind, PV and demand forecasts of the TSO. `pk5l-wp` is available before both cutoffs; PKD for D appears around 16:00 on D-1, after them.
