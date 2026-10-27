# ADR-0006: Gate closures and information cutoffs

Status: accepted · 2026-10-27

## Context
The realistic variant (ADR-0003) may only use information published before each market's gate closure. Times below come from primary sources: PSE, Warunki Dotyczące Bilansowania (WDB, balancing rules), consolidated text including Amendments 1/2024 to 5/2026 (5/2026 dated 10.08.2026, approved in part by the URE President on 12.08.2026). Local time (Europe/Warsaw); D = delivery day. Abbreviations are expanded in the glossary of `docs/market-primer.md`.

| # | Market / decision | Window | Gate closure | Results | Resolution | Source |
|---|---|---|---|---|---|---|
| 1 | RMB: PSE publishes capacity demand (FCR, aFRR, mFRRd, RR; up/down) | – | – | by 07:30 D-1 | hour | WDB 10.2(4.1) |
| 2 | RMB basic mode: portfolio bids (OPMB) | 08:30–09:00 D-1 | 09:00 D-1 | by 10:00 D-1 | hour; 24 ONMBP per day (23/25 on DST days) | WDB 8.3.1(1), table 8.1, 10.2(4.4), 8.1(21)–(26) |
| 3 | Day-ahead, SDAC | – | 12:00 CET/CEST D-1 | – | 15 min from delivery day 1.10.2025 | Market Coupling Steering Committee, 12.09.2025; Nord Pool SDAC page (GCT) |
| 4 | RBN: PP, OEB, OMB (supplementary mode in ZPG) | 10:00–14:30 D-1 | 14:30 D-1 | first ZPG run by 16:30 D-1 | 15 min (ONMBU = OREB) | WDB 8.3.2(1), 10.3(3), 10.3(6.1) |
| 5 | RBB: PP, OEB, OMB updates | 16:30 D-1 to 22:05 D | for hour h: end of minute 5 of hour h-1 (h − 55 min) | ZPG hourly | 15 min | WDB 8.3.3(2), 8.3.3(4), 10.3(9) |
| 6 | aFRR energy (PICASSO) | no separate BSP bid | as #4/#5: PSE derives platform bids from accepted OEB | activation every 4 s | 15 min | WDB 10.4(3), 10.4(7), 10.4(9) |

## Decision
- Reserve capacity in v1 comes from basic mode (RMB) only. Ceiling and realistic variant cover the same markets; neither includes supplementary mode (ZPG), which is an algorithmic PSE selection without a public marginal price.
- Reserve cutoff: only data published before 08:30 D-1. The live 08:30 snapshot is evidence that the rule held, not its definition.
- Day-ahead cutoff stays 11:00 D-1; RMB results (10:00 D-1) are known by then, so day-ahead is optimised after reserves.
- aFRR energy bid price is fixed by h − 55 min (RBB gate).

## Consequences
- Stage 3 needs two daily snapshots (08:30 and 10:30).
- Stage 6: reserves are hourly, day-ahead is quarter-hourly, so an hourly commitment holds for 4 quarter-hours.
- O1: local time is inferred from WDB 8.1(21)–(26) (23/25-hour days); no explicit clause found.
- O2a: primary owner of PL day-ahead prices on ENTSO-E (ADR-0005). Due before publication #1.
- O3: whether these times hold unchanged since 14.06.2024 (backfill). Due before stage 7: ingest stores everything, cutoffs apply only when the index is computed.
- O4: which points of Amendments 5/2026 were approved.
- O5: operating-point rule for storage units (JGM1 states, WDB 8.6.5). Stage 6.
- O6: actual public publication times. Stage 3.
- Secondary, unverified: PSE elastic aFRR demand on PICASSO (03.2026) as a possible break in the aFRR energy price series; cap of 800 ONMBP per year with demand below the required volume (WDB 10.2(4.1)).
