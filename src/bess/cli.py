"""Single entry point: `bess ingest`, `bess snapshot`, `bess run 2026-11`."""

import os
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(
    help="Open monthly revenue index for a 1 MW battery (2h and 4h) in Poland.",
    no_args_is_help=True,
    add_completion=False,
)


class Slot(StrEnum):
    reserves = "reserves"
    dayahead = "dayahead"
    poll = "poll"


def _not_implemented(stage: int) -> None:
    typer.echo(f"Not implemented yet (stage {stage}).", err=True)
    raise typer.Exit(code=1)


def load_env_file(path: Path) -> None:
    """Read KEY=VALUE lines into the environment; variables already set win."""
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


@app.command()
def ingest() -> None:
    """Download new data from all sources into data/raw/."""
    _not_implemented(3)


@app.command()
def snapshot(
    slot: Annotated[Slot, typer.Option(help="reserves (cutoff 08:30), dayahead (11:00) or poll.")],
    root: Annotated[Path, typer.Option(help="Raw data directory.")] = Path("data/raw"),
) -> None:
    """Store raw responses before a gate closure (ADR-0006) in data/raw/snapshots/."""
    from bess.ingest.snapshot import LocalStore, default_opener, ping, run_slot

    load_env_file(Path(".env"))
    token = os.environ.get("ENTSOE_TOKEN")
    report = run_slot(slot.value, LocalStore(root), token)
    ping(
        os.environ.get(f"BESS_HC_{slot.value.upper()}"),
        report,
        [token] if token else [],
        default_opener,
    )
    if not report.ok:
        raise typer.Exit(code=1)


@app.command()
def run(month: str = typer.Argument(..., help="Month to compute, YYYY-MM.")) -> None:
    """Compute the index for one month: ceiling, realistic variant, capture rate."""
    _not_implemented(7)
