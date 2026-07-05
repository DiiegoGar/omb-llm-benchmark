# Operational Misalignment Benchmark (OMB)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21210236.svg)](https://doi.org/10.5281/zenodo.21210236)
[![Código: Apache-2.0](https://img.shields.io/badge/c%C3%B3digo-Apache--2.0-blue.svg)](LICENSE)
[![Corpus: CC BY 4.0](https://img.shields.io/badge/corpus-CC%20BY%204.0-lightgrey.svg)](LICENSE-CORPUS.md)

Banco de pruebas para medir la **utilidad insegura** (*Unsafe Helpfulness*) de los
modelos de lenguaje en tareas de ciberseguridad: respuestas técnicamente útiles
pero **normativamente inadmisibles** bajo el marco europeo (RGPD, NIS2, AI Act).
Cubre un vacío que no atienden ni los benchmarks de utilidad (CTIBench,
AttackSeqBench) ni los de robustez adversarial (CyberSecEval 2).

Desarrollado como Trabajo de Fin de Máster (Máster en Inteligencia Artificial,
Universidad Internacional de La Rioja — UNIR).

## Qué mide

Ante un dilema operativo planteado por un analista legítimo, el OMB clasifica la
respuesta del modelo y calcula el **Unsafe Helpfulness Rate (UHR)** junto a
métricas complementarias (obediencia ciega, colapso normativo, contradicción
interna, completitud de salvaguardas y tasa de negativas). La evaluación es
automática mediante un **LLM-as-a-Judge** validado frente a criterio experto.

## Resultados principales (corpus completo, 60 escenarios × 3 modelos × 3 condiciones = 540 unidades)

- **UHR global: 22,6 %** de respuestas útiles pero normativamente inseguras.
- Fuerte contraste entre modelos: del **1,7 %** al **48,3 %** según el modelo.
- La **policy card** (tarjeta de salvaguardas en el prompt) reduce el UHR
  agregado del **36,7 %** al **7,8 %** — mitigación ligera y de coste casi nulo.
- Juez validado frente a criterio experto: **acuerdo 93,3 %, κ de Cohen 0,801**.

## Estructura

```
omb/                Marco del benchmark (Python)
  safeguards.py     Las 5 salvaguardas operativas (RGPD / NIS2 / AI Act)
  taxonomy.py       Los 3 tipos de fallo + regla de desempate
  prompts.py        Las 3 condiciones de prompt + prompt del juez
  providers.py      Proveedores LLM: Anthropic, OpenAI y Ollama (local)
  metrics.py        UHR y métricas complementarias
  pipeline.py       Orquestador de la corrida
  models.py         Esquemas Pydantic
  expert_review.py  Muestreo, exportación a Excel, consolidación 2/3, kappa/Fleiss/Krippendorff

corpus/
  full/             Los 60 escenarios en YAML
  pilot/            Subconjunto de 3 escenarios (prueba rápida)
  coverage_matrix.md  Matriz de cobertura (dominio × tipo de fallo × sector)

scripts/            CLI: validate_corpus, run_pilot, export_for_review, compute_agreement, ...
results/entrega_final/  Resultados de la corrida completa (JSONL) + informe de acuerdo
```

## Instalación

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1  |  Linux/Mac: source .venv/bin/activate
pip install -e .
cp .env.example .env   # y rellenar OPENAI_API_KEY / ANTHROPIC_API_KEY
```

El modelo abierto (`ollama:llama3.2:3b`) se ejecuta en local con [Ollama](https://ollama.com)
(`ollama pull llama3.2:3b`), sin coste de API.

## Reproducir la evaluación

```bash
# 1. Validar el corpus
python scripts/validate_corpus.py --corpus corpus/full

# 2. Correr el benchmark completo (3 modelos x 3 condiciones x 60 escenarios)
python scripts/run_pilot.py \
    --models gpt-4o-mini --models claude-sonnet-4-6 --models ollama:llama3.2:3b \
    --judge gpt-4o --corpus corpus/full

# 3. Validación del juez frente a criterio experto
python scripts/export_for_review.py results/<run>/results.jsonl --annotators a,b,c --ratio 0.25
python scripts/compute_agreement.py --results results/<run>/results.jsonl \
    --annotations results/<run>/review/annotations_*.xlsx
```

## Licencias

- **Código** (`omb/`, `scripts/`): [Apache-2.0](LICENSE).
- **Corpus y resultados** (`corpus/`, `results/`): [CC BY 4.0](LICENSE-CORPUS.md).

## Cómo citar

Si utiliza el OMB, cítelo mediante el DOI de Zenodo (véase `CITATION.cff`):

> García Coloma, D., Cárceles Jiménez, J. M., y Gómez Arteta, G. (2026).
> *Operational Misalignment Benchmark (OMB)* (v1.0.0). Zenodo.
> https://doi.org/10.5281/zenodo.21210236

## Autoría y contribuciones

Trabajo grupal (UNIR). Reparto de contribuciones (CRediT):

- **Diego García Coloma** (autor principal) — conceptualización, metodología,
  software (marco de evaluación e implementación), diseño experimental, curación
  del corpus, análisis, redacción y coordinación del proyecto.
- **José María Cárceles Jiménez** — marco normativo y diseño del corpus; validación (anotación experta).
- **Gontzal Gómez Arteta** — definición de métricas y taxonomía de fallos; validación (anotación experta).

Dirección del TFM: Igor Santos-Grueiro.
