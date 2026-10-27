# bess-pl

Open monthly revenue index for a 1 MW battery (2h and 4h) in Poland. Two numbers per month: a perfect-foresight ceiling and a realistic variant that uses only information known before each market's gate closure; capture rate = realistic / ceiling. Later: a public forecast log and a day-ahead price forecast on forecast weather (stage 10).

## Start of every session
1. Read `docs/STATUS.md` (where we are, next step) and the current stage in `docs/roadmap.md`.
2. Read the ADRs in `docs/decisions/` that touch the task. `docs/market-primer.md` explains how a battery earns money in Poland and has the glossary.

## How we work
- Talk to me in Polish. Code, docs, ADRs and commit messages in English (public repo).
- Act as a co-founder: correct and criticise when it matters, not for its own sake. Be concise: the point first, depth on request.
- Every stage starts with "what and why" as an ADR (5–10 lines: context, decision, consequences). Code only after I accept the plan. Understanding matters more than speed.
- Expand every abbreviation on first use.
- I have 5–7 h a week. Prefer the smallest solution that meets the stage's "done when".

## Repo rules
1. One job per document. README never exceeds one screen and is not a changelog.
2. One decision = one ADR in `docs/decisions/NNNN-short-name.md`.
3. No versions in file names (`_v2`, `_final`); that is what git is for.
4. `experiments/` is a scratchpad: the pipeline never imports from it. Code moves to `src/` together with a test, or gets deleted.
5. Every session ends with a commit and an updated `docs/STATUS.md` (max 15 lines).
6. Every stage is one CLI command; the monthly release is one command run by hand.

## Data rules (never break)
- `data/` and `.env` never go to git. Secrets (e.g. the ENTSO-E token) only as environment variables from `.env`.
- `data/raw/` is immutable: every download is stored with its download time and never overwritten.
- No look-ahead: the realistic variant and every forecast use only data published before the gate closure of the market being decided (day-ahead: 11:00 D-1).
- Weather: Open-Meteo Single Runs, ECMWF IFS run from 00 UTC on D-1. Never the Previous Runs API, never observed weather as a forecast input.
- Time: store in UTC on a 15-minute grid; Europe/Warsaw only for display. Test DST days.

## Stack
Python + uv, ruff, pytest, Parquet + DuckDB, dbt-duckdb, CLI `bess`. Local first; cloud only when needed.

## Commands
Added in stage 1.

## Layout
```
bess-pl/
├── CLAUDE.md            # this file
├── README.md            # what it is and how to run it, max one screen
├── pyproject.toml       # uv, ruff, pytest
├── config/assets.yaml   # 2h and 4h battery parameters (ADR-0001)
├── src/bess/
│   ├── ingest/          # one file per source (entsoe.py, pse.py, weather.py)
│   ├── optimize/        # LP model
│   ├── index/           # index, ceiling and realistic variant
│   ├── publish/         # charts and post draft
│   └── cli.py           # single entry point: bess ingest, bess run 2026-11
├── transform/           # dbt-duckdb: raw → staging → marts
├── tests/
├── experiments/         # scratchpad, never imported by the pipeline
├── data/                # not in git: raw/ (immutable) + warehouse.duckdb
└── docs/
    ├── STATUS.md        # where we are and the next step, max 15 lines
    ├── roadmap.md
    ├── market-primer.md
    ├── methodology.md   # public, versioned index methodology
    ├── data-sources.md  # source, licence, publication time, pitfalls
    └── decisions/       # one decision = one short ADR
```
