# Market primer: how a battery earns money in Poland

Stage 0 knowledge, as of 10.2026. Figures are dated; check the source before reusing one.

## In short
- Today a Polish battery earns mostly for being available (aFRR reserve capacity), not from arbitrage.
- That window is closing. Modo expects reserves to drop from ~80% of revenue in 2026 to below 10% in 2030, when the fleet passes 8 GW.
- After 2030 the money moves to day-ahead spreads, longer durations and better forecasts.

## Basics
- MW is power (how fast it charges and discharges), MWh is energy (how much it holds). 1 MW / 4 MWh = 4 h at full power.
- Round-trip efficiency ~86%: 4 MWh in, ~3.4 MWh out.
- Availability payment: PLN/MW/h for holding MW in reserve, even without activation. Arbitrage: buy low, sell high, in PLN/MWh.
- A MW sold as reserve cannot do arbitrage. Upward reserve needs stored energy, downward reserve needs free room, so a reserve-heavy battery stays near mid state of charge.
- Activations are usually partial and short, so activation energy is a small share of revenue.
- Energy can be carried over, but is usually cycled within the day, and cells dislike sitting at 100%. The optimiser therefore needs a value for energy left at the end of the day.

## Revenue streams

| Stream | Paid for | Notes |
|---|---|---|
| aFRR capacity | availability | D-1 auction, marginal pricing; ~400–500 MW per direction; average 181 PLN/MW/h in 2025 |
| aFRR energy | activated MWh (PICASSO) | usually close to the day-ahead price, spikes in ~1% of periods; activation only within the reserved band |
| FCR | availability | ~197 MW; hourly blocks |
| Day-ahead (RDN) | spread | 15-min products; solar trough at noon, peak in the evening |
| mFRR / RR | capacity and energy | slower; per LCP, mFRR is converging towards aFRR; not modelled by Modo |
| Intraday (RDB) | position adjustments | deferred to stage 11; TGE data terms in ADR-0005 |
| Capacity market | multi-year contract | derating for storage falls fast, see below |
| Imbalance (CEN) | settlement of deviations | a risk, not revenue; PSE penalises deliberate imbalance |

Modo benchmark, 4h: July 2026 1.67 m PLN/MW/year (aFRR 67%, day-ahead 24%, FCR 8%); August 1.89 m. 2h in August: 1.71 m, 60% from aFRR.

## How reserves work
- FCR: the battery measures frequency itself and responds proportionally; full power at a 200 mHz deviation within 30 s.
- aFRR: a setpoint from the PSE controller every few seconds; full activation within 5 min. mFRR takes ~12–15 min, RR ~30 min.
- Nothing happens on its own after grid connection. A battery needs an EMS, a link to PSE, a balancing service provider (DUB) and PSE prequalification per product and direction, which takes months.
- Operating-point rule: reserve is counted from current operation, and an idle battery must pick one direction. Only one direction of operation per 15-min period. WDB 8.6.5 defines storage unit states; to be confirmed in stage 6.
- First battery prequalified by PSE: Nowe Czarnowo I. First independent DUB after the reform: Ekovoltis.

## Order of decisions (optimiser skeleton)
1. D-1 08:30–09:00: balancing capacity auction (RMB), basic mode, hourly; results by 10:00.
2. D-1 12:00: day-ahead market (SDAC) in 15-min products.
3. D-1 10:00–14:30 and later: supplementary mode in ZPG (not in v1); intraday until 1 h before delivery.
Times and sources: ADR-0006.
4. Day D: aFRR activations via PICASSO; imbalance settled at CEN every 15 min.

## Data breakpoints
- 14.06.2024: balancing market reform; PSE reports available in the API from this day.
- 11.07.2025: PSE joins PICASSO.
- 1.10.2025 (delivery day): day-ahead moves to 15-min products (ADR-0006).
- 1.02.2027: unit schedules in 15 min.

## Saturation, 2h vs 4h, after 2030
- Modo forecast: the aFRR capacity price falls from 46 to 14 EUR/MW/h by 2030.
- 4h battery: 366 k EUR/MW in 2027, trough of 146 k EUR in 2030, recovery to ~170 k EUR by the late 2030s.
- A 2h battery earns ~90% of a 4h one today, because reserves need power, not energy; ~60% estimated for 2030. Each additional hour of capacity is worth less than the previous one.
- After 2030 spreads likely widen (more solar, coal exit, demand growth; offshore wind creates day-to-day differences). They narrow with more storage, flexible demand and interconnection. The market rewards longer durations and better forecasts.

## Capacity market
Revenue depends on the auction year of the project.

| Auction (delivery year) | Storage derating (KWD) | Clearing price | Revenue per 1 MW |
|---|---|---|---|
| Dec 2023 (2028) | ~95% | n/a | almost full capacity contracted |
| Dec 2024 (2029) | 61.3% | 264.90 PLN/kW/year | ~160 k PLN/year |
| Dec 2025 (2030) | 13.39% | ~465–512 PLN/kW/year (preliminary) | ~60–70 k PLN/year |
| 2026 and 2027 | no main auction | additional auctions for 2028 in Q1 2027 | – |

New units get contracts of up to 17 years. Older cohorts have a solid floor, new ones do not. NFOŚiGW grants reduce capacity market payments.

## Benchmarks to check against
| Who | What | Note |
|---|---|---|
| Modo Energy | ME BESS PL index, simulated 50 MW battery, 2h and 4h | standard for banks; day-ahead + FCR + aFRR, flat 80% calibration, public data only |
| Clean Horizon | free Storage Index; Poland 2h: >800 k EUR/MW/year in May 2026, 581.8 k EUR in July | up to ~1.5× apart from Modo |
| Envalis (PolBESS) | monthly benchmark for 1 MW 2h and 4h (day-ahead, FCR, aFRR) | June 2026, 4h: 193.3 k PLN/MW; 12 months: 2.15 m PLN/MW |

June 2026 annualised: PolBESS ~2.3 m PLN/MW, Modo 1.84 m PLN/MW.

Optimisers active in Poland: Entrix (>1.5 GW, the largest), Axpo (≥510 MW), Capalo AI, Ekovoltis with enspired, Respect Energy, Suena, Tesla Autobidder.

## Glossary
Polish balancing terms follow WDB sections 2.2–2.3 (abbreviations and definitions).

| Term | Meaning |
|---|---|
| ADR | Architecture Decision Record, one short file per decision |
| aFRR | automatic frequency restoration reserve |
| CEE | Central and Eastern Europe |
| CEN | imbalance price (cena energii niezbilansowania) |
| CFADS / DSCR | cash flow available for debt service / debt service coverage ratio |
| D-1 | the day before delivery |
| DST | daylight saving time change |
| DUB / BSP | balancing service provider (dostawca usług bilansujących) |
| EMS | energy management system, the battery controller |
| FCR | frequency containment reserve |
| GBM | gradient boosting model (e.g. LightGBM) |
| GCT | gate closure time: the last moment to submit or change bids |
| JG / JGM1 | scheduling unit (jednostka grafikowa): set of delivery points through which a BSP provides balancing services; JGM1 = storage scheduling unit with ZAK = 1 (jednostka grafikowa magazynu), fully dispatchable by PSE |
| KWD | capacity market derating factor (korekcyjny współczynnik dyspozycyjności) |
| LP / MILP | linear programming / mixed-integer linear programming |
| mFRR / RR | manual frequency restoration reserve / replacement reserve |
| NFOŚiGW | National Fund for Environmental Protection and Water Management |
| OEB | balancing energy bid (oferta na energię bilansującą): price offer to deliver or take balancing energy, part of the ZPG bid |
| OMB | balancing capacity bid (oferta na moce bilansujące): price offer for balancing capacity, part of the ZPG bid, per scheduling unit |
| ONMBP / ONMBU | balancing capacity procurement period (okres nabywania mocy bilansujących) in basic / supplementary mode; hour / 15 min |
| OPMB | portfolio balancing capacity bid (oferta portfolio na moce bilansujące): submitted by a BSP without naming the scheduling units that will deliver |
| OREB | balancing energy settlement period (okres rozliczania energii bilansującej): 15 min |
| P10 / P50 / P90 | value exceeded in 90% / 50% / 10% of cases |
| PICASSO | European platform for aFRR balancing energy |
| PP | operating programme (program pracy): load schedule and reserve schedules submitted by a BSP for a scheduling unit |
| PSE | Polish transmission system operator |
| RBN / RBB | day-ahead / intraday balancing market (rynek bilansujący dnia następnego / bieżącego): PSE submission windows for PP, OEB, OMB |
| RDN / RDB | day-ahead / intraday market |
| RMB | balancing capacity market (rynek mocy bilansujących): PSE procurement of balancing capacity in basic mode, D-1 |
| SDAC | single day-ahead coupling: the EU day-ahead auction |
| SoC | state of charge |
| TGE | Polish Power Exchange |
| WDB | PSE balancing market rules (Warunki Dotyczące Bilansowania) |
| ZAK | activity flag (znacznik aktywności): how far PSE may dispatch a scheduling unit |
| ZPG | integrated scheduling process (zintegrowany proces grafikowania): iterative PSE process that selects units, balancing capacity (supplementary mode) and energy |

## Sources
TODO: add links.
- Modo: aFRR in Poland; Polish Dispatch Model; Polish BESS revenues, July and August 2026; Poland Forecast release, July 2026; Who are the Polish optimisers
- Gramwzielone: PolBESS (Envalis); Nowe Czarnowo I; KWD 13.39% and contracts from 12.2025
- ESS News and pv magazine: Clean Horizon, May and July 2026
- LCP: Poland's BESS boom
- PSE: main auction results for 2029; Globenergia: auction for 2030
- URE: balancing market reform
