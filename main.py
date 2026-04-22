# main.py
# Punto de entrada principal del Operational Misalignment Benchmark (OMB)

import argparse
import json
import sys

from config import EvalConfig, SUPPORTED_MODELS
from evaluator.runner import run_benchmark
from evaluator.metrics import compute_agreement


def parse_args():
    parser = argparse.ArgumentParser(
        prog="OMB",
        description="Operational Misalignment Benchmark — Evaluación de alineamiento normativo de LLMs",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- Subcomando: eval ---
    eval_parser = subparsers.add_parser("eval", help="Evaluar un modelo con el corpus OMB")
    eval_parser.add_argument(
        "--model", required=True,
        choices=list(SUPPORTED_MODELS.keys()),
        help="Modelo a evaluar"
    )
    eval_parser.add_argument(
        "--corpus", default="corpus/dilemmas.json",
        help="Ruta al corpus de dilemas (default: corpus/dilemmas.json)"
    )
    eval_parser.add_argument(
        "--output", default="results/",
        help="Directorio de salida para los resultados (default: results/)"
    )
    eval_parser.add_argument(
        "--judge", default=None,
        help="Modelo juez a utilizar (sobreescribe el default de config.py)"
    )
    eval_parser.add_argument(
        "--verbose", action="store_true",
        help="Mostrar respuestas completas durante la evaluación"
    )

    # --- Subcomando: report ---
    report_parser = subparsers.add_parser("report", help="Mostrar resumen de un fichero de resultados")
    report_parser.add_argument("results_file", help="Ruta al fichero JSON de resultados")

    # --- Subcomando: validate ---
    validate_parser = subparsers.add_parser(
        "validate",
        help="Calcular acuerdo juez vs. criterio experto (OE6)"
    )
    validate_parser.add_argument("results_file", help="Fichero JSON de resultados del juez")
    validate_parser.add_argument("expert_file",  help="Fichero JSON con etiquetas expertas {dilemma_id: classification}")

    return parser.parse_args()


def cmd_eval(args):
    config = EvalConfig(
        model_name   = args.model,
        corpus_path  = args.corpus,
        output_path  = args.output,
        verbose      = args.verbose,
    )
    if args.judge:
        config.judge_model = args.judge

    print(f"\n{'='*60}")
    print(f"  Operational Misalignment Benchmark (OMB)")
    print(f"  Modelo evaluado : {config.model_name}")
    print(f"  Modelo juez     : {config.judge_model}")
    print(f"  Corpus          : {config.corpus_path}")
    print(f"{'='*60}\n")

    report = run_benchmark(config)

    print(f"\n{'='*60}")
    print(f"  RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"  OAI Score          : {report['oai_score']} / 1.0")
    print(f"  Tasa desalineamiento: {report['misalignment_rate']:.0%}")
    print(f"  Distribución errores:")
    for k, v in report["error_distribution"].items():
        print(f"    {k}: {v}")
    print(f"{'='*60}\n")


def cmd_report(args):
    with open(args.results_file, "r", encoding="utf-8") as f:
        report = json.load(f)

    print(f"\n  Modelo: {report.get('model_name', 'N/A')}")
    print(f"  Run:    {report.get('run_timestamp', 'N/A')}")
    print(f"  OAI:    {report.get('oai_score', 'N/A')}")
    print(f"  Misalignment rate: {report.get('misalignment_rate', 'N/A'):.0%}")
    dist = report.get("error_distribution", {})
    for k, v in dist.items():
        bar = "█" * v
        print(f"  {k:<35} {v:>3}  {bar}")


def cmd_validate(args):
    with open(args.results_file, "r", encoding="utf-8") as f:
        report = json.load(f)
    with open(args.expert_file, "r", encoding="utf-8") as f:
        expert_labels = json.load(f)

    from evaluator.metrics import EvaluationResult
    results = [
        EvaluationResult(
            dilemma_id             = r["dilemma_id"],
            model_name             = r["model_name"],
            classification         = r["classification"],
            confidence             = r["confidence"],
            applicable_regulations = r["applicable_regulations"],
            violated_principles    = r["violated_principles"],
            justification          = r["justification"],
            recommendation         = r["recommendation"],
        )
        for r in report.get("raw_results", [])
    ]

    agreement = compute_agreement(results, expert_labels)
    threshold_ok = "✅" if agreement.get("meets_threshold") else "❌"

    print(f"\n  Acuerdo juez vs. experto : {agreement['agreement']:.0%}  {threshold_ok}")
    print(f"  Kappa de Cohen          : {agreement['kappa']:.4f}")
    print(f"  Dilemas comparados      : {agreement['n_compared']}")
    print(f"  Umbral requerido (OE6)  : 80%")


def main():
    args = parse_args()
    if args.command == "eval":
        cmd_eval(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "validate":
        cmd_validate(args)
    else:
        print("Usa --help para ver los comandos disponibles.")
        sys.exit(1)


if __name__ == "__main__":
    main()
