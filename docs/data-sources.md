# Data sources

One card per source: what we take, coverage, licence, publication time, pitfalls. Why each source was chosen: ADR-0005. Market gate closures: ADR-0006. Publication times are measured in stage 3, not taken from documentation.

Each dataset has a role: **decision** (input to a bid before gate closure), **revenue** (prices that settle what the battery earns), **forecast** (feature of a forecast model), or **check** (cross-check only). Revisions are a look-ahead problem only for decision and forecast inputs; for revenue we take the latest version.

## PSE (Polskie Sieci Elektroenergetyczne)
- **What:** balancing capacity prices and volumes, capacity demand, imbalance and balancing energy prices (incl. aFRR), load forecast, SDAC price in PLN.
- **Access:** `https://api.raporty.pse.pl/api/<endpoint>`, no key. OData-style `$filter` (e.g. `business_date eq '2024-06-14'`), `$first`, paging via `nextLink`. Endpoint list: PSE "Mapowanie endpointów API" (`api.raporty.pse.pl/EndpointsMap.pdf`).
- **Licence:** PSE reuse page (pse.pl/bip, "Ponowne wykorzystywanie informacji sektora publicznego"): free, commercial and non-commercial, with source and download date; remove the PSE logo. The page covers pse.pl and BIP and does not name raporty.pse.pl (open question Q4).

| Endpoint | Content | Resolution | Role | Checked |
|---|---|---|---|---|
| `cmbp-tp` | basic-mode (RMB) capacity prices: FCR, aFRR, mFRRd, RR, up/down | hour (ONMBP) | revenue; decision (naive forecast from last known auction, ADR-0003) | data from 14.06.2024 |
| `mbp-tp` | basic-mode capacity volumes, same products | hour | forecast | endpoint map |
| `zmb` | RMB capacity demand (ZMB), published by 07:30 D-1 | hour | decision | endpoint map |
| `cmbu-tu`, `mbu-tu` | supplementary-mode (ZPG) capacity prices and volumes | 15 min (OREB) | none in v1 (ADR-0006) | endpoint map |
| `crb-rozl` | settlement prices: CEN, CEB, CEB for aFRR up/down | 15 min | revenue (aFRR energy); forecast (lagged values) | data from 14.06.2024 |
| `crb-prog` | forecast prices (CEN, CEB) | 15 min | forecast | endpoint map |
| `csdac-pln` | SDAC price in PLN | 15 min | revenue (alternative to ENTSO-E); forecast (lags) | data from 14.06.2024 |
| `prog-obc` | load forecast (KSE) | – | forecast | endpoint map |

- **Pitfalls:**
  - Every record has `publication_ts` (local) and `publication_ts_utc`. It is the time of the **last revision**, not the first publication: `crb-rozl` for 14.06.2024 shows `publication_ts` 16.09.2025. Raw history therefore contains data published after the cutoff: a problem for decision and forecast inputs, not for revenue.
  - `dtime` is the **end** of the period (`onmb` "00 - 01" → `dtime` 01:00; period "00:00 - 00:15" → `dtime` 00:15). UTC fields exist (`dtime_utc`, `period_utc`).
  - `csdac-pln` is on a 15-min grid already on 14.06.2024, before the SDAC 15-min switch (1.10.2025): probably hourly prices repeated. Verify in stage 3.
  - CEB aFRR fields are null on 14.06.2024; expected before PICASSO accession (11.07.2025). Verify.
  - API v1 (`v1.api.raporty.pse.pl`) was announced to shut down at the end of 2025 (secondary: CIRE). Use v2 only.
  - Units of capacity prices are not stated in the endpoint map (PLN/MW/h expected). Verify.

## ENTSO-E Transparency Platform
- **What:** day-ahead prices for PL (technical choice, ADR-0005), day-ahead load forecast; reserve datasets as a cross-check of PSE.
- **Access:** REST API with a personal security token (environment variable, `.env`).
- **Licence:** ENTSO-E open data list, version 18.10.2023. Datasets on the list are CC-BY 4.0 (free reuse, also commercial, with attribution and a note on changes). Datasets off the list need the consent of the primary data owner.

| Dataset (Transparency Regulation article) | On CC-BY list | Role |
|---|---|---|
| Day-ahead prices (12.1.D) | no | revenue; forecast (lags); ADR-0005 |
| Day-ahead total load forecast (6.1.B) | yes | forecast (stage 10) |
| Wind and solar forecast (14.1.D) | no | forecast (stage 10), licence open |
| Actual generation per type (16.1) | no | not planned |
| Volumes of contracted reserves (17.1.B) | yes | check of `mbp-tp` |
| Prices of contracted reserves (17.1.C) | yes | check of `cmbp-tp` |
| Procured balancing capacity (EB 12.3.F) | yes | check |
| Prices of activated balancing energy (17.1.F) | yes | check of `crb-rozl` |
| Imbalance prices and volumes (17.1.G/H) | yes | check of `crb-rozl` |

- **Pitfalls:** whether PL publishes 17.1.B/C from 06.2024, and at what resolution, is not yet checked: it needs an API token (Q5). Primary owner of PL day-ahead prices on ENTSO-E is unknown (O2a in ADR-0006).

## Open-Meteo Single Runs
- **What:** ECMWF IFS run from 00 UTC on D-1 (rule in CLAUDE.md). Role: forecast (stage 10).
- **Coverage:** ECMWF IFS runs archived from 14.03.2024 (Open-Meteo docs, Single Runs API); covers 06.2024. Runs selected with `run=` (initialisation time, not publication time).
- **Licence:** data CC-BY 4.0. Free API only for non-commercial use (definition: Creative Commons); commercial includes sites with subscriptions or ads. Limits: <10,000 calls/day, 5,000/hour, 600/minute.
- **Pitfalls:** whether a public, free index counts as non-commercial (Q6). An Open-Meteo reply states full-resolution IFS (9 km) needs an ECMWF licence; check which resolution Single Runs serves (Q7). IFS cycle upgrade from 12.05.2026 06 UTC: possible break in forecast quality.

## NBP (Narodowy Bank Polski)
- **What:** EUR/PLN mid rate, table A, for the EUR series (ADR-0002). Role: revenue (currency conversion only).
- **Access:** `https://api.nbp.pl/api/exchangerates/tables/a/{start}/{end}/`, HTTPS only, max 93 days per query, data from 2.01.2002.
- **Licence:** no explicit terms on the API page ("All rights reserved"). Low risk: we publish monthly averages, not the series (Q8).
- **Pitfalls:** no rates on weekends and holidays; monthly average over published days only.

## TGE (Towarowa Giełda Energii): not used in v1
- **Why not:** the SDAC price for PL is available from ENTSO-E and PSE. TGE market data policy v2.0 (12.11.2024), points 2.4–2.6: delayed data (≥15 min) is free, but payable when used in a value-added product (historical series, aggregation) sold to third parties. Intraday (RDB) deferred to stage 11.
- **Before publication #1:** a question to TGE about free use under points 2.4–2.6 (ADR-0005).

## Competitor landscape
Figures and sources: `docs/market-primer.md` (benchmarks).

| Index | Asset | Markets | Unit | Foresight |
|---|---|---|---|---|
| Modo Energy, ME BESS PL | simulated 50 MW, 2h and 4h | day-ahead, FCR, aFRR | PLN/MW/year, annualised | flat 80% calibration, public data only |
| Clean Horizon Storage Index | Poland 2h | not checked | EUR/MW/year | not checked |
| Envalis, PolBESS | 1 MW, 2h and 4h | day-ahead, FCR, aFRR | PLN/MW per month | open (Q9) |

All three are secondary sources (press and company pages); none publishes a realistic variant next to a ceiling.

## Open questions
- Q1: publication times of each dataset (stage 3).
- Q2: do PSE revisions keep earlier versions anywhere? If not, history needs our own snapshots (stage 3).
- Q3: content of `cmbu-tu`/`mbu-tu` (supplementary mode) and whether it is complete from 06.2024 (stage 3).
- Q4: terms of use of the PSE API and raporty.pse.pl; does the pse.pl reuse page apply?
- Q5: does PL publish 17.1.B/C on ENTSO-E from 06.2024, at what resolution?
- Q6: is a free public index non-commercial under Open-Meteo terms?
- Q7: which IFS resolution Single Runs serves, and does it need an ECMWF licence?
- Q8: NBP terms of reuse.
- Q9: PolBESS method: perfect foresight or not; efficiency and cycle assumptions.
- O2a (ADR-0006): primary owner of PL day-ahead prices. PSE publishes the same price (`csdac-pln`) under its free reuse terms; if those terms cover it, PSE may be the cleaner source.
