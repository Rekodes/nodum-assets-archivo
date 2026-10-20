# nodum-assets

Datasets y algoritmos del laboratorio de [Nodum](https://nodum.rekodes.com), el dataspace de la tesis
(compute-to-data con Ocean Protocol). Se publican, se confían y se ejecutan desde Nodum (web o API `/v1`).

## Organización

Primero, qué tipo de cosa es: `datasets/` (lo que se publica para que otros lo computen) y `algorithms/`
(lo que se ejecuta sobre ellos). Dentro, por temáticas, como contextos de DDD: cada una lleva sus datasets
y los algoritmos que solo tienen sentido con ellos.

| Carpeta | Qué es | Qué hay |
|---|---|---|
| [`datasets/agro/`](datasets/agro/) | Temática: maíz | Fincas con estrés hídrico, entradas en el silo, estaciones agroclimáticas |
| [`datasets/marine/`](datasets/marine/) | Temática: mar | Boyas con hipoxia, capturas pesqueras, estaciones costeras |
| [`algorithms/agro/`](algorithms/agro/) | Algoritmos de maíz | 3 algoritmos |
| [`algorithms/marine/`](algorithms/marine/) | Algoritmos de mar | 2 algoritmos |
| [`algorithms/generic/`](algorithms/generic/) | Algoritmos para cualquier dataset | line-count, data-quality, env-audit |
| [`shared/`](shared/) | Núcleo compartido | El contrato con ocean-node, la regresión logística, el mecanismo de Laplace y el Dockerfile |
| [`scripts/`](scripts/) | Herramientas del repositorio | `push_images.py`, que sube los algoritmos a Docker Hub |

Una temática no importa nada de otra; todas pueden usar `shared/`. Una temática nueva es una carpeta
con el mismo nombre en `datasets/` (generadores, `sinteticos/`, `SHA256SUMS` y su README) y en `algorithms/`.

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
- Se publica en Nodum como tipo **imagen**, con entrypoint `python /app/main.py`. Nodum fija la imagen
  por su digest.

En local, sin Docker:

```bash
PYTHONPATH=shared OCEAN_INPUTS=/tmp/in OCEAN_OUTPUTS=/tmp/out python3 algorithms/generic/line_count.py
```

## Subir a Docker Hub

Cada uno sube a su espacio de Docker Hub (su usuario o una organización suya) con su `docker login`;
el script no guarda credenciales. Un algoritmo, una carpeta o todos:

```bash
make push a=water_stress_model           # uno
make push a=agro                         # una carpeta
make push a=all                          # todos
make push                                # pregunta
make push a=agro ns=mi-org VERSION=0.3.0 # otro espacio u otra versión
```

Construye para linux/amd64, sube `<espacio>/nodum-<algoritmo>:<versión>`, comprueba que se ve sin
credenciales (el nodo la descarga así) e imprime lo que pide Nodum: imagen, entrypoint y parámetros.
Una etiqueta que ya está no se vuelve a subir: para un cambio, versión nueva (`force=1` solo si nadie
la usa). Sin terminal, con `DOCKERHUB_USERNAME` y `DOCKERHUB_TOKEN` (un token de acceso).

## Datasets

Sintéticos, con semilla fija y sin red: los bytes salen iguales en cada ejecución. Se sirven sin clave
desde `https://datos.rekodes.com/`, con la ruta que va desde `sinteticos/`. Lo publicado no cambia: un
cambio es una versión nueva (`v2`), y `SHA256SUMS` guarda la huella de cada fichero.

## Comandos

```bash
make data     # regenera los datasets de cada temática y comprueba que no cambian
make lint     # ruff y mypy
make build    # construye las imágenes
make run a=water_stress_model in="datasets/agro/sinteticos/maiz-estres-hidrico/v1/todas.json"
make push     # sube a tu Docker Hub un algoritmo, una carpeta o todos
```

## Licencia

Código: MIT ([`LICENSE`](LICENSE)). Datasets: CC BY 4.0 ([`LICENSE-DATA`](LICENSE-DATA)).
