# nodum-assets

Datasets y algoritmos del laboratorio de [Nodum](https://nodum.rekodes.com), el dataspace de la tesis
(compute-to-data con Ocean Protocol). Se publican, se confían y se ejecutan desde Nodum (web o API `/v1`).

## Organización

Por temáticas, como contextos de DDD: cada una lleva sus datasets y los algoritmos que solo tienen
sentido con ellos.

| Carpeta | Qué es | Qué hay |
|---|---|---|
| [`agro/`](agro/) | Temática: maíz | Fincas con estrés hídrico, entradas en el silo, estaciones agroclimáticas · 3 algoritmos |
| [`marine/`](marine/) | Temática: mar | Boyas con hipoxia, capturas pesqueras, estaciones costeras · 2 algoritmos |
| [`generic/`](generic/) | Algoritmos para cualquier dataset | line-count, data-quality, env-audit |
| [`shared/`](shared/) | Núcleo compartido | El contrato con ocean-node, la regresión logística, el mecanismo de Laplace y el Dockerfile |

Una temática no importa nada de otra; todas pueden usar `shared/`. Una temática nueva es una carpeta
con `datasets/` (generadores, `sinteticos/` y `SHA256SUMS`), `algorithms/` y su README.

## Algoritmos

Python 3.12, solo la biblioteca estándar. Una imagen por algoritmo:
`docker.io/rekodes/nodum-<algoritmo>:0.2.0`, con `shared/*.py` y el algoritmo como `/app/main.py`.

```python
from ocean_app import Algorithm, Job, Parameter, main


class MyAlgorithm(Algorithm):
    parameters = (Parameter("limit", "number", "Límite", "…", default=10),)

    def run(self, job: Job) -> None:
        limit = job.parameters.number("limit")
        job.outputs.write_json("result.json", {...})


if __name__ == "__main__":
    main(MyAlgorithm())
```

- `OceanApp` ([`shared/ocean_app.py`](shared/ocean_app.py)) cumple el contrato con el nodo: entradas en
  `/data/inputs`, parámetros en `algoCustomData.json` y salidas en `/data/outputs`.
- Un error que deba ver el usuario se lanza como `AlgorithmError` (código 1) o `InvalidParametersError`
  (código 2).
- Se publica en Nodum como tipo **imagen**, con entrypoint `python /app/main.py` y la imagen fijada por
  su digest (`make push`).

En local, sin Docker:

```bash
PYTHONPATH=shared OCEAN_INPUTS=/tmp/in OCEAN_OUTPUTS=/tmp/out python3 generic/algorithms/line_count.py
```

## Datasets

Sintéticos, con semilla fija y sin red: los bytes salen iguales en cada ejecución. Se sirven sin clave
desde `https://datos.rekodes.com/`, con la ruta que va desde `sinteticos/`. Lo publicado no cambia: un
cambio es una versión nueva (`v2`), y `SHA256SUMS` guarda la huella de cada fichero.

## Comandos

```bash
make data     # regenera los datasets de cada temática y comprueba que no cambian
make lint     # ruff y mypy
make build    # construye las imágenes
make run a=water_stress_model in="agro/datasets/sinteticos/maiz-estres-hidrico/v1/todas.json"
make push     # sube las imágenes a Docker Hub y da sus digests
```

## Licencia

Código: MIT ([`LICENSE`](LICENSE)). Datasets: CC BY 4.0 ([`LICENSE-DATA`](LICENSE-DATA)).
