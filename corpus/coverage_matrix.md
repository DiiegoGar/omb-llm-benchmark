# Matriz de cobertura del corpus OMB

Objetivo: 60 escenarios distribuidos sobre 7 dominios operativos, balanceando los 3 tipos de fallo de la taxonomía y diversificando sectores y marcos regulatorios.

## Distribución por dominio × tipo de fallo

| Dominio                | Blind obedience | Normative collapse | Internal contradiction | Total |
|------------------------|-----------------|--------------------|------------------------|-------|
| soc                    | 3               | 3                  | 3                      | **9** |
| incident_response      | 3               | 3                  | 3                      | **9** |
| log_analysis           | 3               | 3                  | 2                      | **8** |
| threat_intelligence    | 3               | 2                  | 3                      | **8** |
| employee_monitoring    | 3               | 3                  | 3                      | **9** |
| auto_containment       | 3               | 3                  | 3                      | **9** |
| vuln_management        | 3               | 2                  | 3                      | **8** |
| **Total**              | **21**          | **19**             | **20**                 | **60** |

## Cobertura de sectores y marcos regulatorios

Se busca que cada bloque sectorial aparezca en al menos 3 dominios distintos.

- Sanidad — RGPD (categorías especiales) + NIS2 entidad esencial + MDR/IVDR
- Banca / financiero — RGPD + DORA + NIS2 entidad esencial + PSD2
- Energía / utilities — NIS2 entidad esencial + AI Act anexo III
- Administración pública — RGPD + ENS (Real Decreto 311/2022) + AI Act
- Educación — RGPD (menores, art. 8) + LOPDGDD
- Telecomunicaciones — RGPD + NIS2 + LSSI + ePrivacy
- Industria / OT — NIS2 entidad importante + IEC 62443
- Defensa / electoral — RGPD + AI Act anexo III + secreto oficial
- Retail / e-commerce — RGPD + LSSI + AI Act

## Reglas de calidad por escenario

1. La petición del analista debe sonar profesional, **sin malicia adversarial**.
2. Debe existir al menos una salvaguarda concreta que la respuesta tal cual vulnere.
3. El campo `normative_risk` debe citar **artículo o principio** concreto cuando proceda.
4. El campo `expected_failure` se elige para que un buen modelo pueda fallar de esa forma con probabilidad razonable, no garantizada.
5. Cada escenario es revisado al menos por un integrante distinto al redactor.

## Listado completo de IDs

| ID  | Dominio                | Tipo fallo               | Sector                  |
|-----|------------------------|--------------------------|-------------------------|
| 01  | employee_monitoring    | blind_obedience          | banca                   |
| 02  | auto_containment       | normative_collapse       | sanidad                 |
| 03  | threat_intelligence    | internal_contradiction   | energía                 |
| 04  | soc                    | blind_obedience          | banca                   |
| 05  | soc                    | normative_collapse       | telco                   |
| 06  | soc                    | internal_contradiction   | AAPP                    |
| 07  | soc                    | blind_obedience          | retail                  |
| 08  | soc                    | normative_collapse       | educación               |
| 09  | soc                    | internal_contradiction   | sanidad                 |
| 10  | soc                    | blind_obedience          | banca                   |
| 11  | soc                    | normative_collapse       | logística               |
| 12  | soc                    | internal_contradiction   | seguros                 |
| 13  | incident_response      | blind_obedience          | manufactura             |
| 14  | incident_response      | normative_collapse       | telco                   |
| 15  | incident_response      | internal_contradiction   | banca                   |
| 16  | incident_response      | blind_obedience          | AAPP                    |
| 17  | incident_response      | normative_collapse       | retail                  |
| 18  | incident_response      | internal_contradiction   | energía                 |
| 19  | incident_response      | blind_obedience          | e-commerce              |
| 20  | incident_response      | normative_collapse       | educación               |
| 21  | incident_response      | internal_contradiction   | sanidad                 |
| 22  | log_analysis           | blind_obedience          | sanidad                 |
| 23  | log_analysis           | normative_collapse       | banca                   |
| 24  | log_analysis           | internal_contradiction   | AAPP                    |
| 25  | log_analysis           | blind_obedience          | telco                   |
| 26  | log_analysis           | normative_collapse       | educación               |
| 27  | log_analysis           | internal_contradiction   | seguros                 |
| 28  | log_analysis           | blind_obedience          | manufactura             |
| 29  | log_analysis           | normative_collapse       | banca                   |
| 30  | threat_intelligence    | blind_obedience          | tecnología              |
| 31  | threat_intelligence    | normative_collapse       | banca                   |
| 32  | threat_intelligence    | internal_contradiction   | energía                 |
| 33  | threat_intelligence    | blind_obedience          | retail                  |
| 34  | threat_intelligence    | normative_collapse       | telco                   |
| 35  | threat_intelligence    | internal_contradiction   | banca                   |
| 36  | threat_intelligence    | blind_obedience          | defensa                 |
| 37  | employee_monitoring    | normative_collapse       | retail                  |
| 38  | employee_monitoring    | internal_contradiction   | call center             |
| 39  | employee_monitoring    | blind_obedience          | sanidad                 |
| 40  | employee_monitoring    | normative_collapse       | tecnología              |
| 41  | employee_monitoring    | internal_contradiction   | telco                   |
| 42  | employee_monitoring    | blind_obedience          | banca                   |
| 43  | employee_monitoring    | normative_collapse       | manufactura             |
| 44  | employee_monitoring    | internal_contradiction   | logística               |
| 45  | auto_containment       | blind_obedience          | banca                   |
| 46  | auto_containment       | normative_collapse       | e-commerce              |
| 47  | auto_containment       | internal_contradiction   | banca                   |
| 48  | auto_containment       | blind_obedience          | retail                  |
| 49  | auto_containment       | normative_collapse       | industrial              |
| 50  | auto_containment       | internal_contradiction   | AAPP                    |
| 51  | auto_containment       | blind_obedience          | electoral               |
| 52  | auto_containment       | normative_collapse       | sanidad                 |
| 53  | vuln_management        | blind_obedience          | banca                   |
| 54  | vuln_management        | normative_collapse       | tecnología              |
| 55  | vuln_management        | internal_contradiction   | sanidad                 |
| 56  | vuln_management        | blind_obedience          | sanidad                 |
| 57  | vuln_management        | normative_collapse       | retail                  |
| 58  | vuln_management        | internal_contradiction   | AAPP                    |
| 59  | vuln_management        | blind_obedience          | telco                   |
| 60  | vuln_management        | internal_contradiction   | energía                 |
