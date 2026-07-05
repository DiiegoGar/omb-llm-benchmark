"""Extrae TODAS las cifras del Capítulo 5 desde un results.jsonl.

Uso:
    python scripts/cap5_report.py [carpeta_run]
    (por defecto: el run más reciente)

Robusto ante ficheros en escritura (salta líneas no parseables).
"""
from __future__ import annotations
import json, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from omb.pipeline import load_records  # noqa: E402
from omb import metrics  # noqa: E402


def pct(x):
    return f"{x*100:.2f}" if isinstance(x, float) else str(x)


def main():
    if len(sys.argv) > 1:
        run = Path(sys.argv[1])
        if not run.is_absolute():
            run = ROOT / run
    else:
        runs = sorted((ROOT / "results").glob("*/results.jsonl"), key=lambda p: p.stat().st_mtime)
        run = runs[-1].parent
    jsonl = run / "results.jsonl"

    # Carga robusta (salta líneas incompletas)
    recs = []
    for line in jsonl.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    R = load_records  # noqa
    # Reusar pydantic via load_records sobre fichero temporal no hace falta;
    # metrics.compute espera RunRecord. Cargamos con el loader oficial:
    records = load_records(jsonl) if True else None

    print(f"== RUN {run.name} ==  N={len(records)} unidades")
    models = sorted(set(r.evaluated_model for r in records))
    conds = ["normal", "explicit_regulation", "policy_card"]
    scens = sorted(set(r.scenario_id for r in records))
    domains = sorted(set(r.domain.value for r in records))
    print(f"modelos={models}")
    print(f"escenarios={len(scens)}  dominios cubiertos={domains}")
    print(f"registros/modelo={dict(Counter(r.evaluated_model for r in records))}")

    g = metrics.compute(records)
    print("\n== GLOBAL ==")
    for k, v in g.as_dict().items():
        print(f"  {k}: {pct(v) if isinstance(v,float) else v}")

    print("\n== POR MODELO ==")
    for m in models:
        sub = [r for r in records if r.evaluated_model == m]
        gm = metrics.compute(sub)
        print(f"  {m:20} n={gm.n:3}  UHR={pct(gm.uhr)}  SC={pct(gm.safeguard_completeness)}  RR={pct(gm.refusal_rate)}")

    print("\n== MODELO x CONDICION ==")
    bymc = metrics.by_model_and_condition(records)
    for key, m in bymc.by_key.items():
        print(f"  {key:42} n={m.n:3} UHR={pct(m.uhr)} BOR={pct(m.blind_obedience_rate)} "
              f"NCR={pct(m.normative_collapse_rate)} ICR={pct(m.internal_contradiction_rate)} "
              f"SC={pct(m.safeguard_completeness)} RR={pct(m.refusal_rate)} "
              f"EID={pct(m.expected_in_detected_rate)} DMR={pct(m.dominant_match_rate)}")

    print("\n== POR CONDICION (agregado los 3 modelos) ==")
    for c in conds:
        sub = [r for r in records if r.condition.value == c]
        if not sub:
            continue
        gc = metrics.compute(sub)
        print(f"  {c:22} n={gc.n:3} UHR={pct(gc.uhr)} SC={pct(gc.safeguard_completeness)} RR={pct(gc.refusal_rate)}")

    print("\n== POR DOMINIO (agregado) ==")
    for dom in domains:
        sub = [r for r in records if r.domain.value == dom]
        gd = metrics.compute(sub)
        print(f"  {dom:22} n={gd.n:3} UHR={pct(gd.uhr)} SC={pct(gd.safeguard_completeness)}")

    print("\n== EFECTO policy_card vs normal (por modelo) ==")
    for m in models:
        base = metrics.compute([r for r in records if r.evaluated_model == m and r.condition.value == "normal"])
        pc = metrics.compute([r for r in records if r.evaluated_model == m and r.condition.value == "policy_card"])
        er = metrics.compute([r for r in records if r.evaluated_model == m and r.condition.value == "explicit_regulation"])
        print(f"  {m:20} UHR normal={pct(base.uhr)} -> explicit={pct(er.uhr)} -> policy={pct(pc.uhr)} | "
              f"SC normal={pct(base.safeguard_completeness)} -> policy={pct(pc.safeguard_completeness)}")

    print("\n== DISTRIBUCION dominant_failure entre UNSAFE ==")
    unsafe = [r for r in records if r.verdict.is_unsafe_helpful]
    print(f"  total unsafe={len(unsafe)}  ", dict(Counter(r.verdict.dominant_failure.value for r in unsafe)))


if __name__ == "__main__":
    main()
