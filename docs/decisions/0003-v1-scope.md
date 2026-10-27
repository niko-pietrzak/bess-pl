# ADR-0003: Scope of v1 and the realistic variant

Status: accepted · 2026-10-25

## Context
Modo models day-ahead, FCR and aFRR. Reserve capacity is sold in the D-1 morning auction, before the day-ahead market, and reserves give ~75–80% of revenue in 2026 (Modo).

## Decision
- In v1: day-ahead (15-min), FCR capacity, aFRR capacity (both directions), aFRR energy.
- Out of v1: mFRR/RR, intraday, capacity market, imbalance (CEN) as revenue.
- Ceiling: perfect knowledge of all prices.
- Realistic variant: each decision uses only information available before that market's gate closure. Day-ahead cutoff stays 11:00 D-1. Reserve capacity prices in v1 use a naive forecast: the same period from the last known auction.
- aFRR energy: headline uses variant A (activation capped at the typical level for the time of day, as Modo). Variants B (proportional) and C (none) are sensitivities.

## Consequences
- Same market scope as Modo, so comparisons are like-for-like.
- In 2026 the capture rate will mostly reflect reserve-price forecasting, not day-ahead. Stage 10 gains weight as reserves saturate towards 2030.
- Gate closure time of each market is an open question for stage 2.
