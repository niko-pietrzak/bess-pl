# ADR-0005: Data sources for v1

Status: accepted · 2026-10-27

## Context
The index needs day-ahead prices, reserve capacity and aFRR energy prices, imbalance prices, weather forecasts and EUR/PLN rates from 06.2024, from sources whose terms allow a public index. Details per source live in `docs/data-sources.md`.

## Decision
- Day-ahead prices for PL (15 min, SDAC): ENTSO-E Transparency Platform API, for technical reasons (documented API, same format as the load forecast). ENTSO-E does not settle the licence: Day-ahead Prices (12.1.D) are not on the ENTSO-E open data list (version 18.10.2023), so the policy of the primary data owner (TGE or PSE, to be established) governs reuse.
- Reserve capacity, aFRR energy and imbalance prices (CEN): PSE, the primary source. ENTSO-E datasets on the CC-BY 4.0 open data list (17.1.b/c/f/g/h, EB 12.3.f) serve as a cross-check or a licence-clean alternative where PL publishes them from 06.2024.
- Weather: Open-Meteo Single Runs (rule in CLAUDE.md). EUR/PLN: NBP (Narodowy Bank Polski) API, table A mid rates (ADR-0002).
- TGE (Polish Power Exchange): not used in v1. The same SDAC price for PL is available from ENTSO-E. TGE market data policy v2.0 (12.11.2024), points 2.4–2.6: delayed data (≥15 min) is free, but becomes payable when used in a value-added product (e.g. historical series, aggregation) sold to third parties. Intraday (RDB) is deferred to stage 11.

## Consequences
- We publish only derived results (index, split by market, capture rate), never day-ahead price series, and always name the sources.
- CC-BY 4.0 data requires attribution and a note on changes; the methodology (stage 7) carries this.
- Before publication #1: identify the primary owner of PL day-ahead prices on ENTSO-E and ask TGE about free use under points 2.4–2.6 of its policy.
