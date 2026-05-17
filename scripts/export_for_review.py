"""Exporta una muestra estratificada de RunRecord a hojas Excel para
anotación experta independiente.

Uso:

    python scripts/export_for_review.py results/<run>/results.jsonl \\
        --annotators diego,gontzal,jose \\
        --ratio 0.25 \\
        --corpus corpus/pilot \\
        --output results/<run>/review/

Genera un .xlsx por anotador con la misma muestra (mismos run_id) para
que las anotaciones sean comparables registro a registro.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
import yaml
from rich.console import Console

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from omb.expert_review import export_for_annotation, sample_records  # noqa: E402
from omb.models import Scenario  # noqa: E402
from omb.pipeline import load_corpus, load_records  # noqa: E402


console = Console()


@click.command()
@click.argument("results_jsonl", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--annotators",
    required=True,
    help="Lista separada por comas de identificadores de los anotadores (p.ej. 'diego,gontzal,jose').",
)
@click.option(
    "--corpus",
    "corpus_dir",
    default="corpus/pilot",
    show_default=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--ratio",
    default=None,
    type=float,
    help="Fracción a muestrear (0, 1]. Mutuamente excluyente con --n.",
)
@click.option(
    "--n",
    "n_records",
    default=None,
    type=int,
    help="Número absoluto a muestrear. Mutuamente excluyente con --ratio.",
)
@click.option(
    "--output",
    "output_dir",
    default=None,
    type=click.Path(file_okay=False, path_type=Path),
    help="Carpeta de salida. Por defecto al lado del JSONL (subcarpeta review/).",
)
@click.option("--seed", default=42, type=int, show_default=True)
def main(
    results_jsonl: Path,
    annotators: str,
    corpus_dir: Path,
    ratio: float | None,
    n_records: int | None,
    output_dir: Path | None,
    seed: int,
) -> None:
    if ratio is None and n_records is None:
        ratio = 0.25
        console.print(
            f"[yellow]No se ha pasado --ratio ni --n. Usando --ratio={ratio} por defecto.[/yellow]"
        )

    annotator_ids = [a.strip() for a in annotators.split(",") if a.strip()]
    if len(annotator_ids) < 2:
        raise click.BadParameter("Se requieren al menos 2 anotadores.")

    records = load_records(results_jsonl)
    console.print(f"Cargados {len(records)} RunRecord desde {results_jsonl}.")

    scenarios: list[Scenario] = load_corpus(corpus_dir)
    scenarios_by_id = {s.id: s for s in scenarios}

    sample = sample_records(records, ratio=ratio, n=n_records, seed=seed)
    console.print(f"Muestra estratificada: {len(sample)} registros.")

    if output_dir is None:
        output_dir = results_jsonl.parent / "review"
    output_dir.mkdir(parents=True, exist_ok=True)

    for aid in annotator_ids:
        out = output_dir / f"annotations_{aid}.xlsx"
        export_for_annotation(
            sample,
            scenarios_by_id=scenarios_by_id,
            output_path=out,
            annotator_id=aid,
        )
        console.print(f"  [green]ok[/green]  {out}")

    # Persistir también la muestra (run_ids) para reproducibilidad.
    sample_path = output_dir / "_sample_run_ids.yaml"
    with sample_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(
            {
                "seed": seed,
                "ratio": ratio,
                "n": n_records,
                "run_ids": [r.run_id for r in sample],
            },
            fh,
            allow_unicode=True,
            sort_keys=False,
        )
    console.print(f"\n[blue]Lista de run_ids muestreados: {sample_path}[/blue]")
    console.print(
        "[bold]Siguiente paso[/bold]: cada anotador rellena su Excel "
        "(columnas H, I, J) y luego ejecutar `scripts/compute_agreement.py`."
    )


if __name__ == "__main__":
    main()
