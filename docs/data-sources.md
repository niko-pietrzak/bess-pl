# Data sources

One card per source: what we take, coverage, licence, publication time, pitfalls. Why each source was chosen: ADR-0005. Market gate closures: ADR-0006. Publication times are measured in stage 3, not taken from documentation.

Each dataset has a role: **decision** (input to a bid before gate closure), **revenue** (prices that settle what the battery earns), **forecast** (feature of a forecast model), or **check** (cross-check only). Revisions are a look-ahead problem only for decision and forecast inputs; for revenue we take the latest version.

## PSE (Polskie Sieci Elektroenergetyczne)
- **What:** balancing capacity prices and volumes, capacity demand, imbalance and balancing energy prices (incl. aFRR), load forecast, SDAC price in PLN.
- **Access:** `https://api.raporty.pse.pl/api/<endpoint>`, no key. OData-style `$filter` (e.g. `business_date eq '2024-06-14'`), `$first`, paging via `nextLink`. Endpoint list: PSE "Mapowanie endpointów API" (`api.raporty.pse.pl/EndpointsMap.pdf`).
- **Licence:** PSE reuse page (pse.pl/bip, "Ponowne wykorzystywanie informacji sektora publicznego"): free, commercial and non-commercial, with source and download date; remove the PSE logo. The page covers pse.pl and BIP and does not name raporty.pse.pl (open question Q4).

**Snapshot** (stage 3): every PSE dataset, because `publication_ts` is the last revision and no earlier versions are kept (Q2), so the state at a cutoff cannot be recovered later. **Critical**: a failed download fails the slot and raises an alert (ADR-0007).

| Endpoint (API v2) | Content | Resolution | Role | Critical | Checked |
|---|---|---|---|---|---|
| `zmb` | RMB capacity demand (ZMB), published by 07:30 D-1 | hour | decision | yes | data |
| `cmbp-tp` | basic-mode (RMB) capacity prices: FCR, aFRR, mFRRd, RR, up/down | hour (ONMBP) | revenue; decision (naive forecast from last known auction, ADR-0003) | yes | data from 14.06.2024 |
| `mbp-tp` | basic-mode capacity volumes, same products | hour | forecast | no | data |
| `cmbu-tu`, `mbu-tu` | supplementary-mode (ZPG) capacity prices and volumes | 15 min (OREB) | none in v1 (ADR-0006) | no | data |
| `crb-rozl` | settlement prices: CEN, CEB, CEB for aFRR up/down | 15 min | revenue (aFRR energy); forecast (lagged values) | no | data from 14.06.2024 |
| `price-fcst` (v1: `crb-prog`) | forecast prices (CEN, CKOEB, CEB) | 15 min | forecast | yes | data |
| `csdac-pln` | SDAC price in PLN | 15 min | revenue (alternative to ENTSO-E); forecast (lags) | yes | data from 14.06.2024 |
| `kse-load` (v1: `prog-obc`) | load forecast (KSE) | 15 min | forecast | yes | data |
| `pdgopkd`, `pdgobpkd` | daily coordination plan (PKD) and its current update (BPKD): PV and wind generation, demand, reserve over/under demand | 15 min | forecast (stage 10) | yes | data |
| `pk5l-wp` | coordination plan, rolling horizon (≥ D+9): PV, wind and demand forecast, surplus capacity over required reserve | hour | forecast (stage 10); the PSE forecast known before both cutoffs | yes | data |
| `sk`, `ro-prog`, `cordmax`, `rce-pln`, `energy-prices` | system contracting forecast, operating reserve forecast, CORDMax, RCE price, balancing prices summary | 15 min / day | forecast; check | no | data |
| `popmb-rmb`, `pdgsz`, `pdwkseub`, `ogr-d1` | RMB portfolio bids, peak-hour signal, unit outages, grid constraints D+1 | various | forecast (stage 10) | no | data |
| `przeplywy-mocy`, `his-wlk-cal` | cross-border flows, daily system report | 15 min | forecast (lags) | no | data |

"Checked: data" means a live response with rows (31.10–1.11.2026); coverage from 06.2024 is checked by the backfill.

- **Pitfalls:**
  - Every record has `publication_ts` (local) and `publication_ts_utc`. It is the time of the **last revision**, not the first publication: `crb-rozl` for 14.06.2024 shows `publication_ts` 16.09.2025. Raw history therefore contains data published after the cutoff: a problem for decision and forecast inputs, not for revenue.
  - `dtime` is the **end** of the period (`onmb` "00 - 01" → `dtime` 01:00; period "00:00 - 00:15" → `dtime` 00:15). UTC fields exist (`dtime_utc`, `period_utc`).
  - `csdac-pln` is on a 15-min grid already on 14.06.2024, before the SDAC 15-min switch (1.10.2025): probably hourly prices repeated. Verify in stage 3.
  - CEB aFRR fields are null on 14.06.2024; expected before PICASSO accession (11.07.2025). Verify.
  - API v1 (`v1.api.raporty.pse.pl`) was announced to shut down at the end of 2025 (secondary: CIRE). Use v2 only. Some v2 names differ from v1 (`price-fcst`, `kse-load`); the endpoint map lists both.
  - `$first=20000` returns a whole window in one page; without it pages hold 100 rows and `nextLink` continues.
  - TLS: the server chains to "Certum Trusted Root CA", which is missing from macOS `/etc/ssl/cert.pem`; we verify with Mozilla's bundle (`certifi`).
  - First look at `publication_ts_utc` (last revision, so only indicative until O6 is measured): `zmb` 06:11 UTC, `cmbp-tp` 08:10, `kse-load` 08:00 (after the 08:30 local cutoff in winter), PKD for D around 15:00 UTC on D-1 (after both cutoffs), `pk5l-wp` several times a day.
  - Units of capacity prices are not stated in the endpoint map (PLN/MW/h expected). Verify.

## ENTSO-E Transparency Platform
- **What:** day-ahead prices for PL (technical choice, ADR-0005), day-ahead load forecast; reserve datasets as a cross-check of PSE.
- **Access:** REST API with a personal security token (environment variable, `.env`).
- **Licence:** ENTSO-E open data list, version 18.10.2023. Datasets on the list are CC-BY 4.0 (free reuse, also commercial, with attribution and a note on changes). Datasets off the list need the consent of the primary data owner.

**Snapshot:** every dataset below. Forecasts are overwritten without versions; results may be revised; for all of them, what was available at the cutoff is itself the evidence. Neighbour codes: DE_LU, CZ, SK, LT, SE_4.

| Dataset (Transparency Regulation article) | On CC-BY list | Role | Critical |
|---|---|---|---|
| Day-ahead prices (12.1.D) | no | revenue; forecast (lags); ADR-0005 | yes |
| Day-ahead total load forecast (6.1.B), PL and DE_LU | yes | forecast (stage 10) | PL yes |
| Wind and solar forecast (14.1.D), PL, DE_LU, CZ, LT | no | forecast (stage 10), licence open | no |
| Day-ahead generation forecast (14.1.C) | no | forecast (stage 10) | no |
| Actual generation per type (16.1) | no | not planned | – |
| Volumes and prices of contracted reserves (17.1.B/C), FCR and aFRR | yes | check of `mbp-tp`, `cmbp-tp` | no |
| Procured balancing capacity (EB 12.3.F), FCR and aFRR | yes | check | no |
| Prices of activated balancing energy (17.1.F) | yes | check of `crb-rozl` | no |
| Imbalance prices and volumes (17.1.G/H) | yes | check of `crb-rozl` | no |
| Forecasted day-ahead transfer capacities (11.1.A), each PL border and direction | not checked | forecast (stage 10) | no |
| Day-ahead scheduled commercial exchanges (12.1.F), same borders | not checked | forecast (lags) | no |
| Physical flows (12.1.G), same borders | not checked | forecast (lags) | no |

- **Pitfalls:** whether PL publishes 17.1.B/C from 06.2024, and at what resolution, is not yet checked (Q5, answered by the backfill). Primary owner of PL day-ahead prices on ENTSO-E is unknown (O2a in ADR-0006). PL borders except LT and SE_4 are in Core flow-based allocation, so 11.1.A may be empty there; flow-based parameters (11.1.B) are published by JAO, not yet snapshotted. The token travels as a URL parameter and is redacted from every stored file, log and alert.

## Open-Meteo Single Runs
- **What:** ECMWF IFS run from 00 UTC on D-1 (rule in CLAUDE.md). Role: forecast (stage 10).
- **Coverage:** ECMWF IFS runs archived from 14.03.2024 (Open-Meteo docs, Single Runs API); covers 06.2024. Runs selected with `run=` (initialisation time, not publication time).
- **Licence:** data CC-BY 4.0. Free API only for non-commercial use (definition: Creative Commons); commercial includes sites with subscriptions or ads. Limits: <10,000 calls/day, 5,000/hour, 600/minute.
- **Snapshot:** yes, in both slots: runs 18 UTC on D-2 and 00 UTC on D-1 (calendar of the run date), models `ecmwf_ifs` (9 km, archived from 14.03.2024) and `ecmwf_ifs025` (0.25°). A run can be fetched later, but not the moment it became available, which decides whether the 00 UTC run is usable before the 08:30 cutoff (stage 10). An unavailable run returns HTTP 400 "The requested model run is not available". Points (10 PL, 5 DE, 2 CZ, 2 LT) and 10 hourly variables are provisional; one call per model and run. Backfill waits for stage 10, when points are chosen.
- **Pitfalls:** whether a public, free index counts as non-commercial (Q6). An Open-Meteo reply states full-resolution IFS (9 km) needs an ECMWF licence; check which resolution Single Runs serves (Q7). IFS cycle upgrade from 12.05.2026 06 UTC: possible break in forecast quality.

## NBP (Narodowy Bank Polski)
- **What:** EUR/PLN mid rate, table A, for the EUR series (ADR-0002). Role: revenue (currency conversion only).
- **Access:** `https://api.nbp.pl/api/exchangerates/tables/a/{start}/{end}/`, HTTPS only, max 93 days per query, data from 2.01.2002.
- **Licence:** no explicit terms on the API page ("All rights reserved"). Low risk: we publish monthly averages, not the series (Q8).
- **Snapshot:** no. Rates are final once published, recoverable at any time, and not a decision input.
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
- Q2: do PSE revisions keep earlier versions anywhere? Not in the API (one record per period, `publication_ts` = last revision); our snapshots run from 1.11.2026.
- Q3: content of `cmbu-tu`/`mbu-tu` (supplementary mode) and whether it is complete from 06.2024 (stage 3).
- Q4: terms of use of the PSE API and raporty.pse.pl; does the pse.pl reuse page apply?
- Q5: does PL publish 17.1.B/C on ENTSO-E from 06.2024, at what resolution?
- Q6: is a free public index non-commercial under Open-Meteo terms?
- Q7: which IFS resolution Single Runs serves, and does it need an ECMWF licence?
- Q8: NBP terms of reuse.
- Q9: PolBESS method: perfect foresight or not; efficiency and cycle assumptions.
- O2a (ADR-0006): primary owner of PL day-ahead prices. PSE publishes the same price (`csdac-pln`) under its free reuse terms; if those terms cover it, PSE may be the cleaner source.
