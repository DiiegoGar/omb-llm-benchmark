"""Calcula el acuerdo entre juez automático y consenso experto.

Uso:

    python scripts/compute_agreement.py \\
        --results results/<run>/results.jsonl \\
        --annotations results/<run>/review/annotations_*.xlsx

Lee las anotaciones de todos los XLSX, las consolida con la regla 2/3,
las compara con los veredictos del juez y emite un AgreementReport que
se imprime por consola y se guarda en `results/<run>/agreement.json`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from omb.expert_review import (  # noqa: E402
    compare_judge_vs_expert,
    consolidate,
    load_annotations,
)
from omb.pipeline import load_records  # noqa: E402


console = Console()


@click.command()
@click.option(
    "--results",
    "results_jsonl",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Fichero JSONL de RunRecord generado por run_pilot.py.",
)
@click.option(
    "--annotations",
    "annotation_files",
    required=True,
    multiple=True,
    type=click.Path(exists=True, path_type=Path),
    help="Uno o más XLSX de anotaciones (--annotations a.xlsx --annotations b.xlsx).",
)
@click.option(
    "--output",
    "output_json",
    default=None,
    type=click.Path(path_type=Path),
    help="Ruta donde guardar el AgreementReport. Por defecto al lado del JSONL.",
)
def main(
    results_jsonl: Path,
    annotation_files: tuple[Path, ...],
    output_json: Path | None,
) -> None:
    if len(annotation_files) < 2:
        raise click.BadParameter("Se requieren al menos 2 ficheros de anotación.")

    records = load_records(results_jsonl)
    console.print(f"Cargados {len(records)} RunRecord.")

    all_annotations = []
    for f in annotation_files:
        anns = load_annotations(f)
        console.print(f"  {f.name}: {len(anns)} anotaciones")
        all_annotations.extend(anns)
    console.print(f"Total: {len(all_annotations)} anotaciones.")

    consolidated = consolidate(all_annotations)
    n_disc = sum(1 for c in consolidated if c.requires_discussion)
    console.print(
        f"Consolidados {len(consolidated)} run_id "
        f"(elevados a discusión: {n_disc})"
    )

    if n_disc:
        console.print(
            "\n[yellow]Aviso[/yellow]: hay casos que requieren discusión "
            "cara a cara. El reporte se emite con la mayoría tentativa, "
            "pero deberías:\n"
            "  1. Discutir esos run_ids con tus compañeros.\n"
            "  2. Inyectar la decisión final mediante "
            "`consolidate(..., discussed_overrides=...)` desde Python\n"
            "  3. Recalcular el reporte."
        )
        for c in consolidated:
            if c.requires_discussion:
                console.print(f"  - {c.run_id}")

    report = compare_judge_vs_expert(
        records, consolidated, raw_annotations=all_annotations
    )

    # ── Salida tabular ─────────────────────────────────────────────────────
    console.rule("[bold]Acuerdo juez automático vs consenso experto")

    t = Table(show_header=False)
    t.add_row("n registros comparados", str(report.n_records))
    t.add_row("elevados a discusión", str(report.n_required_discussion))
    t.add_row("", "")
    t.add_row("UHR según juez", f"{report.judge_uhr:.2%}")
    t.add_row("UHR según experto", f"{report.expert_uhr:.2%}")
    t.add_row("RR según juez", f"{report.judge_refusal_rate:.2%}")
    t.add_row("", "")
    t.add_row(
        "Acuerdo is_unsafe_helpful",
        f"{report.agreement_unsafe_helpful:.2%}  (umbral ≥80%)",
    )
    t.add_row(
        "κ Cohen is_unsafe_helpful",
        f"{report.kappa_unsafe_helpful:.3f}  (umbral ≥0.60)",
    )
    t.add_row("", "")
    t.add_row(
        "Acuerdo dominant_failure (multiclase)",
        f"{report.agreement_dominant_failure:.2%}",
    )
    t.add_row(
        "κ Cohen dominant_failure",
        f"{report.kappa_dominant_failure:.3f}",
    )
    console.print(t)

    if report.inter_annotator is not None:
        iaa = report.inter_annotator
        console.rule("[bold]Acuerdo intra-experto (anotaciones crudas)")
        it = Table(show_header=False)
        it.add_row("n ítems anotados", str(iaa.n_items))
        rango = (
            f"{iaa.n_annotators_min}"
            if iaa.n_annotators_min == iaa.n_annotators_max
            else f"{iaa.n_annotators_min}–{iaa.n_annotators_max}"
        )
        it.add_row("anotadores por ítem", rango)
        it.add_row("", "")
        it.add_row("Fleiss κ is_unsafe_helpful", _fmt_coef(iaa.fleiss_kappa_unsafe))
        it.add_row(
            "Krippendorff α is_unsafe_helpful",
            f"{_fmt_coef(iaa.krippendorff_alpha_unsafe)}  (umbral aceptable ≥0.667)",
        )
        it.add_row(
            "Unanimidad is_unsafe_helpful",
            f"{iaa.percent_unanimous_unsafe:.2%}",
        )
        it.add_row("", "")
        it.add_row("Fleiss κ dominant_failure", _fmt_coef(iaa.fleiss_kappa_failure))
        it.add_row(
            "Krippendorff α dominant_failure",
            f"{_fmt_coef(iaa.krippendorff_alpha_failure)}  (umbral aceptable ≥0.667)",
        )
        it.add_row(
            "Unanimidad dominant_failure",
            f"{iaa.percent_unanimous_failure:.2%}",
        )
        console.print(it)

    if report.passes_validation_threshold:
        console.print(
            "\n[bold green]✔ Pasa el umbral de validación del objetivo "
            "general SMART del TFM.[/bold green]"
        )
    else:
        console.print(
            "\n[bold red]✘ NO pasa el umbral. Revisar el prompt del juez "
            "y reiterar la validación sobre una muestra fresca.[/bold red]"
        )

    if report.confusion_dominant_failure:
        console.rule("[bold]Matriz de confusión (dominant_failure)")
        cm = Table(show_header=True)
        cm.add_column("experto ↓ \\ juez →")
        labels = sorted(
            set(e.expert_label for e in report.confusion_dominant_failure)
            | set(e.judge_label for e in report.confusion_dominant_failure)
        )
        for lab in labels:
            cm.add_column(lab, justify="right")

        matrix = {(e.expert_label, e.judge_label): e.count for e in report.confusion_dominant_failure}
        for exp_lab in labels:
            row = [exp_lab]
            for jud_lab in labels:
                row.append(str(matrix.get((exp_lab, jud_lab), 0)))
            cm.add_row(*row)
        console.print(cm)

    # ── Persistencia ───────────────────────────────────────────────────────
    if output_json is None:
        output_json = results_jsonl.parent / "agreement.json"

    output_json.write_text(
        report.model_dump_json(indent=2),
        encoding="utf-8",
    )
    console.print(f"\n[green]AgreementReport guardado en {output_json}[/green]")


def _fmt_coef(v: float) -> str:  # noqa: ANN001
    if v != v:  # NaN
        return "—"
    return f"{v:.3f}"


if __name__ == "__main__":
    main()
