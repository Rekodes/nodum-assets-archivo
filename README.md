# nodum-assets

Datasets y algoritmos del laboratorio de [Nodum](https://nodum.rekodes.com), el dataspace de la tesis
(compute-to-data con Ocean Protocol).

| Carpeta | Qué hay |
|---|---|
| [`datasets/`](datasets/) | Catálogo de datasets sintéticos y sus generadores |
| [`algorithms/`](algorithms/) | Los algoritmos; una imagen Docker por algoritmo |

Se publican, se confían y se ejecutan desde Nodum (web o API `/v1`).

## Comandos

```bash
make data     # regenera los datasets y comprueba que no cambian
make lint     # ruff y mypy
make build    # construye las imágenes
make run a=line_count in="datasets/sinteticos/estaciones/v1/estaciones.xml"
make push     # sube las imágenes a Docker Hub y da sus digests
```

## Licencia

Código: MIT. Datasets: CC BY 4.0.
