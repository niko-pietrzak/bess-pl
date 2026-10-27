"""Single entry point: `bess ingest`, `bess run 2026-11`."""

import typer

app = typer.Typer(
    help="Open monthly revenue index for a 1 MW battery (2h and 4h) in Poland.",
    no_args_is_help=True,
    add_completion=False,
)


def _not_implemented(stage: int) -> None:
    typer.echo(f"Not implemented yet (stage {stage}).", err=True)
    raise typer.Exit(code=1)


@app.command()
def ingest() -> None:
    """Download new data from all sources into data/raw/."""
    _not_implemented(3)


@app.command()
def run(month: str = typer.Argument(..., help="Month to compute, YYYY-MM.")) -> None:
    """Compute the index for one month: ceiling, realistic variant, capture rate."""
    _not_implemented(7)
