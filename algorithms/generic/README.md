# Algoritmos genéricos

Valen para los datasets de cualquier temática.

| Algoritmo | Qué hace | Datasets | Salidas |
|---|---|---|---|
| [line-count](line_count.py) | Cuenta líneas y bytes | Cualquiera | `line-count.json` |
| [data-quality](data_quality.py) | Nota de calidad 0–100: validez, completitud, consistencia y unicidad | JSON y XML | `quality-report.json`, `quality-report.html` |
| [env-audit](env_audit.py) | Audita el entorno del nodo: usuario, límites, red, sha256 de las entradas | Cualquiera | `env-audit.json` |
| [output-samples](output_samples.py) | Un fichero de cada tipo que Nodum enseña, y los casos límite. Es un script: se sube a Nodum, sin imagen | Cualquiera | `imagenes/`, `tablas/`, `datos/`, `informe.md`, `informe.html`… |
| [resumen-entradas](resumen_entradas.py) | Bytes, líneas y una muestra de cada fichero de entrada. Es un script: se publica desde GitHub o se sube, sin imagen | Cualquiera | `resumen.json`, `resumen.csv`, `resumen.md` |

| Algoritmo | Parámetro | Tipo | Por defecto | Qué hace |
|---|---|---|---|---|
| line-count | `skip_header` | boolean | `false` | No cuenta la primera línea de cada fichero |
| data-quality | `required_fields` | text | — | Campos obligatorios, separados por comas |
| env-audit | `probe_host` | text | `1.1.1.1` | Dirección con la que se prueba la red |
| resumen-entradas | `muestra` | number | `3` | Líneas de muestra de cada fichero |
| resumen-entradas | `fallar` | boolean | `false` | Sale con código 3, para probar un fallo |
