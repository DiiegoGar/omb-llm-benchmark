# OMB — Piloto técnico

Implementación del **Operational Misalignment Benchmark (OMB)** descrito en el TFM
*Operational Misalignment Benchmark (OMB)* (UNIR, Máster en IA).

Este piloto valida, sobre un corpus reducido (3 escenarios como pruebas principales) y un único modelo
evaluado, que el marco LLM-as-a-Judge mide lo que pretende medir antes de
escalar el experimento completo.

## Estructura

```
omb/                Código del benchmark
  models.py         Esquemas Pydantic (Scenario, JudgeVerdict, RunRecord)
  safeguards.py     Las 5 salvaguardas operativas (RGPD / NIS2 / AI Act)
  taxonomy.py       Los 3 tipos de fallo (obediencia ciega, colapso, contradicción)
  prompts.py        Las 3 condiciones experimentales + prompt del juez
  providers.py      Cliente LLM (Anthropic por defecto, extensible)
  metrics.py        UHR y métricas complementarias
  pipeline.py       Orquestador de la corrida

corpus/
  _template.yaml    Plantilla con los 5 campos obligatorios
  pilot/            Escenarios piloto en YAML (uno por archivo)

scripts/
  run_pilot.py      Ejecuta la corrida y guarda results/<timestamp>/
  validate_corpus.py  Valida los YAML contra el esquema

results/            Salidas de cada corrida (JSONL + resumen)
```

## Puesta en marcha

```powershell
# 1. Crear entorno virtual

.\.venv\Scripts\Activate.ps1 dentro de la terminal abierta en el proyecto

# 2. Instalar dependencias
pip install -e .

# 3. Configurar claves
Copy-Item .env.example .env
# editar .env con la key de Chagpt o Claude

# 4. Validar el corpus piloto
python scripts/validate_corpus.py

# 5. Ejecutar el piloto
python scripts/run_pilot.py --models claude-sonnet-4-6 --corpus corpus/pilot
```

## Trazabilidad con el TFM

| Artefacto del TFM         | Implementación                |
|---------------------------|-------------------------------|
| Catálogo de salvaguardas  | `omb/safeguards.py`           |
| Taxonomía de fallos       | `omb/taxonomy.py`             |
| Plantilla de escenario    | `corpus/_template.yaml`       |
| Rúbrica (UHR + comp.)     | `omb/metrics.py`              |
| Condiciones de prompt     | `omb/prompts.py`              |
| LLM-as-a-Judge            | `omb/prompts.py` + `providers.py` |
| Protocolo experimental    | `omb/pipeline.py`             |
