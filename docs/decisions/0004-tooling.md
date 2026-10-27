# ADR-0004: Tooling

Status: accepted · 2026-10-27

## Context
A small, single-maintainer project needs a toolchain with few moving parts, a fast lint/test loop and one CLI entry point per stage (repo rule 6).

## Decision
- Python 3.12, pinned in `.python-version`; `requires-python = ">=3.12"`.
- uv for environments, locking (`uv.lock` committed) and builds (`uv_build` backend, src layout).
- ruff for lint and format: rules E, F, I, UP, B; line length 100.
- pytest for tests; ruff and pytest in the `dev` dependency group.
- Typer for the CLI `bess`: commands are typed functions, help is generated from signatures and docstrings, and `typer.testing.CliRunner` makes CLI tests one-liners. It sits on Click, so we can drop down if needed.

## Consequences
- One runtime dependency (Typer, which pulls in Click and Rich) instead of zero with argparse; accepted for less boilerplate as commands grow (ingest, transform, optimise, run, publish, forecast).
- No mypy or pre-commit for now; add when they would catch a real bug.
