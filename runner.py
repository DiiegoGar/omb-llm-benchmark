# evaluator/runner.py
# Orquestador principal del benchmark OMB

from __future__ import annotations
import json
import os
from datetime import datetime
from typing import List, Dict

from config import EvalConfig
from evaluator.judge import evaluate_response, get_model_response
from evaluator.metrics import EvaluationResult, compute_model_report, compute_oai


def load_corpus(path: str) -> List[dict]:
    """Carga el corpus de dilemas desde disco."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    dilemmas = data.get("dilemmas", [])
    print(f"[OMB] Corpus cargado: {len(dilemmas)} dilemas desde '{path}'")
    return dilemmas


def run_benchmark(config: EvalConfig) -> dict:
    """
    Ejecuta el benchmark completo para un modelo:
      1. Carga el corpus
      2. Obtiene la respuesta del modelo evaluado para cada dilema
      3. Envía la respuesta al modelo juez para su clasificación
      4. Calcula métricas agregadas (OAI)
      5. Guarda los resultados en disco

    Retorna el informe completo del modelo.
    """
    corpus = load_corpus(config.corpus_path)
    results: List[EvaluationResult] = []

    for i, dilemma in enumerate(corpus, 1):
        dilemma_id = dilemma["id"]
        scenario   = dilemma["scenario"]
        question   = dilemma["question"]

        print(f"[{i}/{len(corpus)}] {dilemma_id} — {dilemma['title']}")

        # Paso 1: obtener respuesta del modelo evaluado
        try:
            model_response = get_model_response(
                model_name = config.model_name,
                scenario   = scenario,
                question   = question,
                config     = config,
            )
        except Exception as exc:
            print(f"  ⚠️  Error al obtener respuesta del modelo: {exc}")
            continue

        if config.verbose:
            print(f"  → Respuesta modelo ({len(model_response)} chars)")

        # Paso 2: evaluar con el modelo juez
        try:
            result = evaluate_response(
                dilemma_id     = dilemma_id,
                model_name     = config.model_name,
                scenario       = scenario,
                question       = question,
                model_response = model_response,
                config         = config,
            )
        except Exception as exc:
            print(f"  ⚠️  Error en la evaluación del juez: {exc}")
            continue

        results.append(result)
        status = "✅ ALIGNED" if not result.is_misaligned else f"❌ {result.classification}"
        print(f"  → {status} (conf={result.confidence:.2f})")

    # Paso 3: métricas agregadas
    report = compute_model_report(results)
    report["run_timestamp"] = datetime.utcnow().isoformat()
    report["raw_results"]   = [r.to_dict() for r in results]

    # Paso 4: guardar en disco
    _save_results(report, config)

    return report


def _save_results(report: dict, config: EvalConfig) -> None:
    """Persiste los resultados en el directorio de salida."""
    os.makedirs(config.output_path, exist_ok=True)
    timestamp   = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    model_slug  = config.model_name.replace("/", "_").replace(":", "_")
    output_file = os.path.join(config.output_path, f"{model_slug}_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n[OMB] Resultados guardados en: {output_file}")
    print(f"[OMB] OAI Score: {report['oai_score']} | "
          f"Misalignment rate: {report['misalignment_rate']:.0%}")
