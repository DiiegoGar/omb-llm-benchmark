"""Valida los YAML del corpus contra el esquema Pydantic.

Útil antes de cualquier corrida: detecta campos mal escritos, salvaguardas
inválidas o tipos de fallo inexistentes sin gastar llamadas a la API.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

# Forzar UTF-8 en stdout/stderr para Windows (consola por defecto cp1252).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from omb.pipeline import load_corpus  # noqa: E402


console = Console()


@click.command()
@click.option(
    "--corpus",
    "corpus_dir",
    default="corpus/pilot",
    show_default=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
def main(corpus_dir: Path) -> None:
    try:
        scenarios = load_corpus(corpus_dir)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        sys.exit(1)

    console.print(f"[green]OK - {len(scenarios)} escenarios validos en {corpus_dir}.[/green]")
    for s in scenarios:
        console.print(
            f"  - {s.id} [{s.domain.value}] -> expected_failure={s.expected_failure.value}, "
            f"safeguards={[x.value for x in s.relevant_safeguards]}"
        )


if __name__ == "__main__":
    main()
