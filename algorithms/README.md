# Algoritmos

Python 3.12, solo la biblioteca estándar. Una imagen por algoritmo:
`docker.io/rekodes/nodum-<algoritmo>:0.2.0`.

| Algoritmo | Código | Qué hace | Datasets | Salidas |
|---|---|---|---|---|
| line-count | [`line_count.py`](line_count.py) | Cuenta líneas y bytes | Cualquiera | `line-count.json` |
| data-quality | [`data_quality.py`](data_quality.py) | Nota de calidad 0–100: validez, completitud, consistencia y unicidad | JSON y XML | `quality-report.json`, `quality-report.html` |
| dp-histogram | [`dp_histogram.py`](dp_histogram.py) | Histograma y media con privacidad diferencial (Laplace) | Boyas | `dp-histogram.json`, `dp-histogram.svg` |
| hypoxia-model | [`hypoxia_model.py`](hypoxia_model.py) | Regresión logística que predice la hipoxia; salen pesos y métricas | Boyas | `model.json`, `metrics.json`, `coefficients.svg` |
| env-audit | [`env_audit.py`](env_audit.py) | Audita el entorno del nodo: usuario, límites, red, sha256 de las entradas | Cualquiera | `env-audit.json` |

## Parámetros

| Algoritmo | Parámetro | Tipo | Por defecto | Qué hace |
|---|---|---|---|---|
| line-count | `skip_header` | boolean | `false` | No cuenta la primera línea de cada fichero |
| data-quality | `required_fields` | text | — | Campos obligatorios, separados por comas |
| dp-histogram | `column` | select | `sea_surface_temp_c` | Variable de las boyas |
| | `epsilon` | number | `1` | Más pequeño, más ruido |
| | `bins` | number | `16` | Intervalos |
| | `lower`, `upper` | number | `15`, `35` | Recorte de los valores |
| hypoxia-model | `epochs` | number | `300` | Pasadas del descenso de gradiente |
| | `learning_rate` | number | `0.5` | Tamaño del paso |
| | `l2` | number | `0.001` | Regularización |
| env-audit | `probe_host` | text | `1.1.1.1` | Dirección con la que se prueba la red |

`column` admite `sea_surface_temp_c`, `salinity_psu`, `chlorophyll_mg_m3`, `dissolved_oxygen_mg_l`,
`wind_speed_m_s` y `wave_height_m`.

## Estructura

- [`ocean_app.py`](ocean_app.py)
  - `OceanApp`: el contrato con ocean-node. Entradas en `/data/inputs`, parámetros en
    `algoCustomData.json` y salidas en `/data/outputs`.
  - `Algorithm`: la base de cada algoritmo.
- `<algoritmo>.py`: una clase que hereda de `Algorithm`, declara sus `parameters` e implementa
  `run(job)`.
- [`Dockerfile`](Dockerfile): copia `ocean_app.py` y el algoritmo como `/app/main.py`.

```python
class MyAlgorithm(Algorithm):
    parameters = (Parameter("limit", "number", "Límite", "…", default=10),)

    def run(self, job: Job) -> None:
        limit = job.parameters.number("limit")
        job.outputs.write_json("result.json", {...})


if __name__ == "__main__":
    main(MyAlgorithm())
```

Un error que deba ver el usuario se lanza como `AlgorithmError` (código 1) o `InvalidParametersError`
(código 2).

En local, sin Docker:

```bash
OCEAN_INPUTS=/tmp/in OCEAN_OUTPUTS=/tmp/out python3 line_count.py
```

## Publicar en Nodum

Tipo **imagen**, entrypoint `python /app/main.py` y la imagen fijada por su digest (`make push`).

| Imagen | Digest |
|---|---|
| `nodum-line-count:0.2.0` | pendiente |
| `nodum-data-quality:0.2.0` | pendiente |
| `nodum-dp-histogram:0.2.0` | pendiente |
| `nodum-hypoxia-model:0.2.0` | pendiente |
| `nodum-env-audit:0.2.0` | pendiente |
