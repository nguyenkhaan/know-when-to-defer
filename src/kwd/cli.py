"""Command-line entry point: every pipeline step becomes a `kwd <command>` (spec 04 §2)."""

import typer

from kwd import __version__

app = typer.Typer(help="Know When to Defer: pipeline commands.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Pipeline commands are added phase by phase (see docs/plans/)."""


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)
