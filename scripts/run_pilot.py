"""Script CLI para ejecutar el piloto técnico.

Uso típico:

    python scripts/run_pilot.py \
        --models claude-sonnet-4-6 \
        --judge claude-opus-4-7 \
        --corpus corpus/pilot
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Permitir ejecutar el script sin instalar el paquete.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from omb import metrics  # noqa: E402
from omb.models import PromptCondition  # noqa: E402
from omb.pipeline import load_corpus, load_records, run_pilot  # noqa: E402


console = Console()


@click.command()
@click.option(
    "--models",
    multiple=True,
    default=("claude-sonnet-4-6",),
    show_default=True,
    help="Modelos evaluados (repetir la opción para varios).",
)
@click.option(
    "--judge",
    default=None,
    help="Modelo juez. Por defecto OMB_JUDGE_MODEL del .env.",
)
@click.option(
    "--corpus",
    "corpus_dir",
    default="corpus/pilot",
    show_default=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--output",
    "output_dir",
    default=None,
    type=click.Path(file_okay=False, path_type=Path),
    help="Carpeta de salida. Por defecto results/<timestamp>/.",
)
@click.option(
    "--conditions",
    multiple=True,
    type=click.Choice([c.value for c in PromptCondition]),
    default=tuple(c.value for c in PromptCondition),
    show_default=True,
)
@click.option("--temperature", default=None, type=float)
@click.option("--max-tokens", default=None, type=int)
def main(
    models: tuple[str, ...],
    judge: str | None,
    corpus_dir: Path,
    output_dir: Path | None,
    conditions: tuple[str, ...],
    temperature: float | None,
    max_tokens: int | None,
) -> None:
    load_dotenv()

    judge_model = judge or os.environ.get("OMB_JUDGE_MODEL", "claude-opus-4-7")
    temperature = (
        temperature
        if temperature is not None
        else float(os.environ.get("OMB_TEMPERATURE", "0.2"))
    )
    max_tokens = (
        max_tokens
        if max_tokens is not None
        else int(os.environ.get("OMB_MAX_TOKENS", "2000"))
    )

    if output_dir is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = ROOT / "results" / ts

    console.rule("[bold]OMB — Piloto técnico")
    console.print(f"  Corpus       : {corpus_dir}")
    console.print(f"  Modelos      : {', '.join(models)}")
    console.print(f"  Juez         : {judge_model}")
    console.print(f"  Condiciones  : {', '.join(conditions)}")
    console.print(f"  Salida       : {output_dir}")
    console.print(f"  Temperature  : {temperature}")
    console.rule()

    # Verificar claves según los modelos pedidos.
    all_models = list(models) + [judge_model]
    needs_anthropic = any(m.startswith("claude") for m in all_models)
    needs_openai = any(m.startswith(("gpt", "o1", "o3", "o4")) for m in all_models)
    missing = []
    if needs_anthropic and not os.environ.get("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if needs_openai and not os.environ.get("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")
    if missing:
        console.print(
            f"[red]Faltan variables: {', '.join(missing)}. Revisa tu .env.[/red]"
        )
        sys.exit(1)

    scenarios = load_corpus(corpus_dir)
    console.print(f"Cargados {len(scenarios)} escenarios.\n")

    out_path = run_pilot(
        scenarios=scenarios,
        models=list(models),
        conditions=[PromptCondition(c) for c in conditions],
        judge_model=judge_model,
        output_dir=output_dir,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    console.print(f"\n[green]Resultados crudos: {out_path}[/green]")

    records = load_records(out_path)
    if not records:
        console.print("[yellow]Sin registros: no se imprime resumen.[/yellow]")
        return

    _print_summary(records)


def _print_summary(records) -> None:  # noqa: ANN001
    console.rule("[bold]Resumen global")
    global_metrics = metrics.compute(records)
    table = Table(show_header=False)
    for k, v in global_metrics.as_dict().items():
        table.add_row(k, _fmt(v))
    console.print(table)

    console.rule("[bold]Por modelo × condición")
    by_mc = metrics.by_model_and_condition(records)
    breakdown = Table(show_lines=False)
    breakdown.add_column("modelo | condición")
    breakdown.add_column("n", justify="right")
    breakdown.add_column("UHR", justify="right")
    breakdown.add_column("BOR", justify="right")
    breakdown.add_column("NCR", justify="right")
    breakdown.add_column("ICR", justify="right")
    breakdown.add_column("SC", justify="right")
    breakdown.add_column("RR", justify="right")
    breakdown.add_column("EID", justify="right")
    breakdown.add_column("DMR", justify="right")
    for key, m in by_mc.by_key.items():
        breakdown.add_row(
            key,
            str(m.n),
            _fmt(m.uhr),
            _fmt(m.blind_obedience_rate),
            _fmt(m.normative_collapse_rate),
            _fmt(m.internal_contradiction_rate),
            _fmt(m.safeguard_completeness),
            _fmt(m.refusal_rate),
            _fmt(m.expected_in_detected_rate),
            _fmt(m.dominant_match_rate),
        )
    console.print(breakdown)


def _fmt(v) -> str:  # noqa: ANN001
    if isinstance(v, float):
        return f"{v:.2%}" if 0 <= v <= 1 else f"{v:.3f}"
    return str(v)


if __name__ == "__main__":
    main()
