"""Orquestador del OMB.

Flujo de una corrida:

    corpus YAML ──► Scenario
            │
            ▼  para cada condición × modelo evaluado
    render_condition_prompt ──► provider.complete ──► ModelResponse
                                                       │
                                                       ▼
                              render_judge_prompt ──► provider.complete (juez)
                                                       │
                                                       ▼
                                                JudgeVerdict (JSON)
                                                       │
                                                       ▼
                                                  RunRecord ──► JSONL
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import yaml
from pydantic import ValidationError

from omb.models import (
    JudgeVerdict,
    PromptCondition,
    RunRecord,
    Scenario,
)
from omb.prompts import render_condition_prompt, render_judge_prompt
from omb.providers import LLMProvider, build_provider
from omb.taxonomy import FailureType, dominant_failure


# ---------------------------------------------------------------------------
# Carga del corpus
# ---------------------------------------------------------------------------

def load_corpus(corpus_dir: Path) -> list[Scenario]:
    """Lee todos los YAML del directorio y los valida con Pydantic."""
    files = sorted(corpus_dir.glob("*.yaml"))
    scenarios: list[Scenario] = []
    errors: list[str] = []
    for path in files:
        if path.name.startswith("_"):
            continue
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            scenarios.append(Scenario.model_validate(raw))
        except (yaml.YAMLError, ValidationError) as exc:
            errors.append(f"{path.name}: {exc}")
    if errors:
        joined = "\n  - ".join(errors)
        raise ValueError(f"Errores en el corpus:\n  - {joined}")
    return scenarios


# ---------------------------------------------------------------------------
# Parseo del veredicto del juez
# ---------------------------------------------------------------------------

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


def parse_judge_verdict(raw_text: str) -> JudgeVerdict:
    """Extrae y valida el JSON del modelo juez, tolerando texto colateral."""
    match = _JSON_BLOCK_RE.search(raw_text)
    if not match:
        raise ValueError(f"El juez no devolvió JSON parseable. Salida cruda:\n{raw_text}")
    data = json.loads(match.group(0))

    # Si el juez olvida calcular dominant_failure, lo derivamos del listado.
    if "dominant_failure" not in data or not data["dominant_failure"]:
        failures = [FailureType(f) for f in data.get("failure_types", [])]
        data["dominant_failure"] = dominant_failure(failures).value

    return JudgeVerdict.model_validate(data)


# ---------------------------------------------------------------------------
# Ejecución
# ---------------------------------------------------------------------------

def run_single(
    *,
    scenario: Scenario,
    condition: PromptCondition,
    model_provider: LLMProvider,
    judge_provider: LLMProvider,
    temperature: float,
    max_tokens: int,
) -> RunRecord:
    """Ejecuta una unidad experimental escenario × condición × modelo."""
    # 1. Respuesta del modelo evaluado
    eval_prompt = render_condition_prompt(scenario, condition)
    response = model_provider.complete(
        eval_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # 2. Veredicto del juez
    sys_prompt, judge_user = render_judge_prompt(scenario, response.text)
    judge_raw = judge_provider.complete(
        judge_user,
        system=sys_prompt,
        temperature=0.0,
        max_tokens=max_tokens,
    )
    verdict = parse_judge_verdict(judge_raw.text)

    return RunRecord(
        run_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        scenario_id=scenario.id,
        domain=scenario.domain,
        condition=condition,
        evaluated_model=model_provider.name,
        judge_model=judge_provider.name,
        response=response,
        verdict=verdict,
        expected_failure=scenario.expected_failure,
    )


def run_pilot(
    *,
    scenarios: Iterable[Scenario],
    models: list[str],
    conditions: list[PromptCondition],
    judge_model: str,
    output_dir: Path,
    temperature: float = 0.2,
    max_tokens: int = 2000,
) -> Path:
    """Ejecuta la corrida completa y persiste a `output_dir/results.jsonl`.

    Devuelve la ruta al fichero JSONL generado.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "results.jsonl"

    judge_provider = build_provider(judge_model)
    providers = {m: build_provider(m) for m in models}

    scenarios = list(scenarios)
    total = len(scenarios) * len(models) * len(conditions)
    done = 0

    with out_path.open("w", encoding="utf-8") as fh:
        for scenario in scenarios:
            for model_name in models:
                for condition in conditions:
                    done += 1
                    print(
                        f"[{done}/{total}] {scenario.id} | {model_name} | {condition.value}"
                    )
                    try:
                        record = run_single(
                            scenario=scenario,
                            condition=condition,
                            model_provider=providers[model_name],
                            judge_provider=judge_provider,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        )
                    except Exception as exc:  # noqa: BLE001 — el piloto debe seguir
                        print(f"   ERROR: {exc}")
                        continue
                    fh.write(record.model_dump_json() + "\n")
                    fh.flush()

    return out_path


def load_records(jsonl_path: Path) -> list[RunRecord]:
    """Carga registros guardados por `run_pilot`."""
    records: list[RunRecord] = []
    with jsonl_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            records.append(RunRecord.model_validate_json(line))
    return records
