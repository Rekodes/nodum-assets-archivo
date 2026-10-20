# Nodum · datasets y algoritmos del laboratorio

Los datasets sintéticos y los algoritmos que se ejecutan en **Nodum**, el dataspace de la tesis
doctoral de Antonio López Muzas sobre compute-to-data y aprendizaje federado con
[Ocean Protocol](https://oceanprotocol.com) (`ocean-node` 4.2.0). Están aquí para que cualquiera pueda
**reproducir cada ejecución**:

- los mismos bytes de cada dataset;
- la misma imagen de cada algoritmo, por su digest;
- los mismos resultados, salvo el ruido aleatorio del histograma con privacidad diferencial.

En compute-to-data los datos no salen del nodo de su dueño: el algoritmo viaja hasta ellos, corre en
un contenedor sin red y solo devuelve sus salidas. Lo de este repositorio sirve para comprobar que
ese ciclo funciona de punta a punta:

1. publicar un dataset y un algoritmo;
2. que el dueño del dataset confíe en el algoritmo;
3. lanzar el trabajo y leer su log y su salida.

## Qué hay

```
datasets/
  generadores/      el código que produce cada dataset (semilla fija, sin red)
  sinteticos/       los ficheros generados, idénticos a los publicados
  SHA256SUMS        el sha256 de cada fichero publicado
algorithms/
  Dockerfile        una imagen por algoritmo (python:3.12-slim fijada por digest, solo stdlib)
  common.py         entradas, parámetros y salidas como los deja el nodo
  <algoritmo>/      el código de cada uno
  DIGESTS           el digest de cada imagen publicada
tests/              cada algoritmo con los datasets, como lo ejecutaría el nodo
catalog/            lab.json: qué se publica en Nodum; published.json: lo ya publicado
tools/              free_compute.py (un trabajo en un ocean-node sin Nodum) y publish_lab.py (publica el catálogo)
runs/               las ejecuciones de prueba: estado, logs y salidas tal como las dio el nodo
CATALOGO.md         lo publicado en Nodum (DIDs, nodos, huellas) y las ejecuciones de prueba
```

## Datasets

Todos son sintéticos y se sirven sin clave desde `https://datos.rekodes.com`. Cada versión publicada
no cambia nunca: el nodo guarda el sha256 de cada fichero, y un cambio en los datos es una versión
nueva (`v2`).

| Dataset | URL | Qué es |
|---|---|---|
| Boyas con hipoxia, sitio A | `https://datos.rekodes.com/sinteticos/boyas-hipoxia/v1/site-a.json` | Laguna costera: 720 horas (julio de 2026), 23 % de horas con hipoxia |
| Boyas con hipoxia, sitio B | `…/boyas-hipoxia/v1/site-b.json` | Bahía abierta: 11 % |
| Boyas con hipoxia, sitio C | `…/boyas-hipoxia/v1/site-c.json` | Mar abierto: 5 % |
| Boyas con hipoxia, las tres | `…/boyas-hipoxia/v1/todas.json` | Las tres juntas (2160 horas), para comparar con un modelo centralizado |
| Capturas limpias | `https://datos.rekodes.com/sinteticos/capturas/v1/limpias.json` | 240 desembarcos pesqueros (JSON) sin defectos |
| Capturas sucias | `…/capturas/v1/sucias.json` | Los mismos, con defectos conocidos: campos que faltan, tipos mezclados, nulos y 20 duplicados |
| Capturas cortadas | `…/capturas/v1/cortadas.json` | Las limpias cortadas a 5000 bytes: JSON mal formado |
| Estaciones costeras | `https://datos.rekodes.com/sinteticos/estaciones/v1/estaciones.xml` | 120 estaciones (XML) con atributos y elementos que faltan |

**Boyas:**
- Cada sitio tiene su propio clima: los datos no son IID, como en un aprendizaje federado real.
- La etiqueta `hypoxia` (oxígeno disuelto < 4 mg/L) sale de una relación conocida con la
  temperatura, la salinidad, la clorofila y el viento, más ruido. Así se sabe qué tendría que
  aprender un modelo.

**Capturas y estaciones:** los defectos están descritos en su generador, para que se sepa qué
tiene que encontrar el banco de calidad.

```bash
make data    # regenera los ficheros y comprueba que coinciden byte a byte con SHA256SUMS
```

## Algoritmos

Imágenes públicas en Docker Hub (`docker.io/rekodes/nodum-<algoritmo>:0.1.0`), fijadas por digest
en `algorithms/DIGESTS`. Leen los datasets de `/data/inputs/` y los parámetros de
`/data/inputs/algoCustomData.json`, y escriben en `/data/outputs/`.

| Algoritmo | Qué hace | Datasets | Parámetros | Salidas |
|---|---|---|---|---|
| `line-count` | Cuenta las líneas y los bytes de cada dataset. El más simple: comprueba el ciclo completo | Cualquiera, uno o varios | `skip_header` (boolean) | `line-count.json` |
| `data-quality` | Banco de calidad de JSON y XML: validez, completitud, consistencia y unicidad por registro, con una nota de 0 a 100 | Capturas y estaciones | `required_fields` (text) | `quality-report.json`, `quality-report.html` |
| `dp-histogram` | Histograma con **privacidad diferencial** (mecanismo de Laplace) sobre varias boyas: solo sale el agregado con ruido | Boyas A, B y C juntas | `column`, `epsilon`, `bins`, `lower`, `upper` | `dp-histogram.json`, `dp-histogram.svg` |
| `hypoxia-model` | Regresión logística que predice la hipoxia. Es el entrenamiento local que repetirá cada nodo en el aprendizaje federado: salen los pesos y las métricas, no las lecturas | Una boya (o varias) | `epochs`, `learning_rate`, `l2` | `model.json`, `metrics.json`, `coefficients.svg` |
| `env-audit` | Audita el entorno de ejecución del nodo: usuario, capacidades, límites de CPU y memoria, red, entradas con su sha256 y carpetas | Cualquiera | `probe_host` (text) | `env-audit.json` |

## Reproducir en local

Hace falta Docker (y Python 3.11 o posterior para los tests). Las imágenes se ejecutan como en el
nodo: sin red, como el usuario 1000:1000, sin capacidades de Linux y con las entradas de solo
lectura.

```bash
make test                                  # los tests de los cinco algoritmos
make build                                 # construye las cinco imágenes para linux/amd64
make run a=data-quality in="datasets/sinteticos/capturas/v1/*.json"
make run a=dp-histogram in="datasets/sinteticos/boyas-hipoxia/v1/site-?.json" params='{"epsilon":0.5}'
```

Para usar las imágenes publicadas en vez de construirlas, `docker pull` con el digest de
`algorithms/DIGESTS`.

## Reproducir contra un ocean-node

Cualquier nodo con entorno gratuito sirve. Uno de los de la tesis es `https://nodeds1.ibatec.es`.
`tools/free_compute.py`:
1. firma la petición con una dirección de usar y tirar (la ruta gratuita no pide saldo);
2. espera a que el trabajo termine;
3. baja los logs y las salidas.

```bash
uv run --no-project --with eth-account --with httpx python tools/free_compute.py \
  https://nodeds1.ibatec.es \
  "rekodes/nodum-dp-histogram:0.1.0@sha256:15b43f80475599c8a461af35aa8b37fb229021c1f6c758cbac0cab862115725e" \
  "python /app/main.py" \
  https://datos.rekodes.com/sinteticos/boyas-hipoxia/v1/site-a.json \
  https://datos.rekodes.com/sinteticos/boyas-hipoxia/v1/site-b.json \
  https://datos.rekodes.com/sinteticos/boyas-hipoxia/v1/site-c.json \
  --params '{"epsilon": 0.5}'
```

## En Nodum

En Nodum cada algoritmo se publica como **imagen** (ADR-0051 de Nodum):

- **El digest:** decide qué bytes se ejecutan; el nodo arranca `imagen@digest`.
- **El entrypoint.**
- **Un descriptor canónico:** fija las dos huellas de la lista de confianza, `filesChecksum` y
  `containerSectionChecksum`.

El dueño de un dataset confía en un algoritmo concreto, por esas dos huellas, y solo ese puede
ejecutarse sobre sus datos.

[`catalog/lab.json`](catalog/lab.json) describe lo que se publica en Nodum:
- **Datasets:** cada uno con su nodo; las boyas y los de calidad en `nodeds1`, y una copia en
  `nodeds2` y `nodeds3` para auditar cada nodo.
- **Algoritmos:** los cinco, en los tres nodos y con sus parámetros.
- **Confianza:** qué algoritmos admite cada dataset.
- **Ejecuciones de prueba:** las que se lanzan para comprobarlo.

[`tools/publish_lab.py`](tools/publish_lab.py) lo publica con una clave de API de Nodum (Cuenta →
Claves de API) y apunta lo publicado en `catalog/published.json`, para no repetir nada:

```bash
NODUM_API_KEY=ak_… uv run --with certifi python tools/publish_lab.py --dry-run   # qué haría
NODUM_API_KEY=ak_… uv run --with certifi python tools/publish_lab.py
``` Lo publicado, con sus DIDs y las ejecuciones de prueba, está en
[`CATALOGO.md`](CATALOGO.md).

## Licencia

El código, MIT ([`LICENSE`](LICENSE)). Los datasets, CC BY 4.0 ([`datasets/LICENSE`](datasets/LICENSE)).
