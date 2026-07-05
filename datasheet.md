# Datasheet — Corpus del Operational Misalignment Benchmark (OMB)

Ficha de datos siguiendo el esquema de *Datasheets for Datasets* (Gebru et al., 2021).

## Motivación
- **¿Para qué se creó el conjunto?** Para medir la *utilidad insegura* (Unsafe Helpfulness) de modelos de lenguaje en tareas de ciberseguridad: respuestas técnicamente útiles pero normativamente inadmisibles bajo el marco europeo (RGPD, NIS2, AI Act). Cubre un vacío no atendido por los benchmarks de utilidad (CTIBench, AttackSeqBench) ni de robustez adversarial (CyberSecEval 2).
- **¿Quién lo creó?** Diego García Coloma, Gontzal Gómez Arteta y José María Cárceles Jiménez, en el marco de un Trabajo de Fin de Máster (Máster en Inteligencia Artificial, UNIR), dirigido por Igor Santos-Grueiro.

## Composición
- **Unidades:** 60 escenarios operativos en formato YAML, distribuidos en 7 dominios (SOC, respuesta a incidentes, análisis de logs, threat intelligence, monitorización de empleados, contención automática, gestión de vulnerabilidades).
- **Campos por escenario:** `id`, `domain`, `title`, `context`, `user_request`, `ideal_response`, `normative_risk`, `expected_failure`, `relevant_safeguards`, `notes`.
- **Etiquetas:** tipo de fallo esperado (obediencia ciega, colapso normativo, contradicción interna) y salvaguardas relevantes (minimización, proporcionalidad, autorización, supervisión humana, trazabilidad).
- **¿Contiene datos personales o sensibles?** No. Todos los escenarios son **sintéticos**; los nombres, organizaciones e incidentes son ficticios. No se derivan de personas ni de casos reales identificables.

## Proceso de creación
- Redactados por el equipo a partir de patrones documentados en la literatura y en los textos regulatorios, mediante una plantilla estructurada (`corpus/_template.yaml`).
- **Validación en tres pasos:** (1) validación sintáctica automatizada contra esquema Pydantic (`scripts/validate_corpus.py`); (2) revisión cruzada por un integrante distinto del redactor; (3) validación del director sobre una muestra.

## Usos
- **Uso previsto:** evaluación *defensiva* de la seguridad operacional normativa de LLMs antes de su despliegue en entornos regulados; investigación sobre mitigaciones ligeras (policy cards).
- **Usos no recomendados:** el corpus no debe emplearse para entrenar modelos a producir las respuestas inseguras que documenta, ni como sustituto de una evaluación jurídica profesional.

## Distribución y licencia
- **Corpus** (`corpus/`) y resultados (`results/`): licencia **Creative Commons Attribution 4.0 (CC BY 4.0)**.
- **Código** (`omb/`, `scripts/`): licencia **Apache 2.0**.
- Publicado en repositorio público con versión etiquetada y DOI en Zenodo (ver `CITATION.cff`).

## Mantenimiento
- Mantenido por los autores. Las incidencias y contribuciones se gestionan a través del repositorio público.
- Versionado semántico; cada corrida experimental queda trazada en `results/<timestamp>/`.
