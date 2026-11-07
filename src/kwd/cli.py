"""Command-line entry point: every pipeline step becomes a `kwd <command>` (spec 04 §2)."""

from pathlib import Path
from typing import Annotated

import typer

from kwd import __version__
from kwd.data.config import load_data_config
from kwd.data.pipeline import (
    RESERVE_FILE,
    SNAPSHOTS_FILE,
    format_stats,
    load_snapshots,
    run_snapshot,
    snapshot_stats,
)

app = typer.Typer(help="Know When to Defer: pipeline commands.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Pipeline commands are added phase by phase (see docs/plans/)."""


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)


@app.command()
def snapshot(
    config: Annotated[Path, typer.Option(help="Data config, e.g. configs/data.yaml.")],
) -> None:
    """Select the pilot routes, build their snapshots and print the stats of spec 05, section 7."""
    cfg = load_data_config(config)
    meta = run_snapshot(cfg)
    pilot = load_snapshots(cfg.interim_dir / SNAPSHOTS_FILE)
    reserve = load_snapshots(cfg.interim_dir / RESERVE_FILE)
    typer.echo(format_stats(snapshot_stats(pilot, reserve, cfg), meta))
