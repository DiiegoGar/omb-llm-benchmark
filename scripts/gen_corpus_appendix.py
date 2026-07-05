"""Genera la tabla-anexo del corpus completo en LaTeX a partir de los YAML.

Emite filas para una longtable con: numero, id, dominio, tipo de fallo esperado
y salvaguardas relevantes. La columna de estado de validacion se anade en la
plantilla del anexo (no en cada fila) para no desincronizar.

Uso:
    python scripts/gen_corpus_appendix.py            # imprime por stdout
    python scripts/gen_corpus_appendix.py > out.tex  # vuelca a fichero
"""

from __future__ import annotations

import glob
import os

import yaml

BS = chr(92)  # backslash, para evitar ambiguedades de escapado
EOL = " " + BS * 2 + " " + BS + "hline"  # ' \\ \hline'

SG = {
    "minimization": "Min",
    "proportionality": "Prop",
    "authorization": "Aut",
    "human_oversight": "Sup",
    "traceability": "Traz",
}
FF = {
    "blind_obedience": "Ob. ciega",
    "normative_collapse": "Col. norm.",
    "internal_contradiction": "Contr. int.",
    "none": "---",
}


def tt(s: str) -> str:
    return BS + "texttt{" + s.replace("_", BS + "_") + "}"


def main() -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rows = []
    for f in sorted(glob.glob(os.path.join(root, "corpus", "full", "*.yaml"))):
        d = yaml.safe_load(open(f, encoding="utf-8"))
        num = os.path.basename(f).split("_")[0]
        sgs = ", ".join(SG.get(s, s) for s in d.get("relevant_safeguards", []))
        failure = FF.get(d["expected_failure"], d["expected_failure"])
        estado = "Sint." + BS + "," + "+" + BS + "," + "RC"  # Sint.\,+\,RC
        rows.append(
            f"{num} & {tt(d['id'])} & {tt(d['domain'])} & {failure} & {sgs} & {estado}{EOL}"
        )
    print("\n".join(rows))


if __name__ == "__main__":
    main()
