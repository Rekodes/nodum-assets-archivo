# Algoritmos genéricos

Valen para los datasets de cualquier temática.

| Algoritmo | Qué hace | Datasets | Salidas |
|---|---|---|---|
| [line-count](algorithms/line_count.py) | Cuenta líneas y bytes | Cualquiera | `line-count.json` |
| [data-quality](algorithms/data_quality.py) | Nota de calidad 0–100: validez, completitud, consistencia y unicidad | JSON y XML | `quality-report.json`, `quality-report.html` |
| [env-audit](algorithms/env_audit.py) | Audita el entorno del nodo: usuario, límites, red, sha256 de las entradas | Cualquiera | `env-audit.json` |

| Algoritmo | Parámetro | Tipo | Por defecto | Qué hace |
|---|---|---|---|---|
| line-count | `skip_header` | boolean | `false` | No cuenta la primera línea de cada fichero |
| data-quality | `required_fields` | text | — | Campos obligatorios, separados por comas |
| env-audit | `probe_host` | text | `1.1.1.1` | Dirección con la que se prueba la red |
