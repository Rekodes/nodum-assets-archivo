# Catálogo de lo publicado en Nodum

Se rellena al publicar en producción (`https://nodum.rekodes.com`, cadena 8996 de pruebas, nodos
`nodeds1..3` con `ocean-node` 4.2.0). Cada fila dice qué se publicó, dónde, y con qué huellas, para
poder comprobarlo contra el DDO de cualquier nodo (`/api/aquarius/assets/ddo/<did>`).

## Datasets

| Dataset | Nodo | DID | Fichero (sha256) |
|---|---|---|---|

## Algoritmos

| Algoritmo | Imagen@digest | DID | Nodos | filesChecksum | containerSectionChecksum |
|---|---|---|---|---|---|

## Ejecuciones de prueba

### Contra el nodo, sin Nodum (2026-10-20)

Con [`tools/free_compute.py`](tools/free_compute.py):
- **Algoritmo:** imagen por digest en `meta`.
- **Datasets:** por URL de `datos.rekodes.com`.
- **Firma:** una dirección de usar y tirar.

No pasan por la cadena: prueban que el nodo descarga la imagen exacta y los datos, que ejecuta con
las restricciones que promete y que devuelve el log y las salidas. En cada carpeta están:
- el estado que dio el nodo (`status.json`);
- los logs de imagen, configuración y algoritmo;
- las salidas.

| Fecha | Algoritmo | Datasets | Nodo · entorno | Job | Resultado |
|---|---|---|---|---|---|
| 2026-10-19 23:13 UTC | `line-count` | 2 (estaciones.xml, capturas limpias) | `nodeds1` · gratuito | `…75e9d9e00ae52c93` (13 s) | 3345 líneas · [`runs/2026-10-20-nodeds1/line-count/`](runs/2026-10-20-nodeds1/line-count/) |
| 2026-10-19 23:15 UTC | `env-audit` | 1 (capturas limpias) | `nodeds1` · gratuito | `…2e7f4c7a32e1ce61` (10 s) | 1000:1000, 1 CPU, 1 GiB, sin red ni DNS; sha256 de la entrada igual al publicado · [`runs/2026-10-20-nodeds1/env-audit/`](runs/2026-10-20-nodeds1/env-audit/) |
| 2026-10-19 23:18 UTC | `data-quality` | 4 (capturas limpias, sucias y cortadas, estaciones.xml) | `nodeds1` · gratuito | `…74c803ad71bb6471` (12 s) | limpias 100 · estaciones 92,1 · sucias 91,5 · cortadas 0 · [`runs/2026-10-20-nodeds1/data-quality/`](runs/2026-10-20-nodeds1/data-quality/) |
| 2026-10-19 23:14 UTC | `dp-histogram` | 3 (boyas A, B y C), ε = 0,5 | `nodeds1` · gratuito | `…be6b49f7f88d35e6` (12 s) | histograma y media con ruido de Laplace · [`runs/2026-10-20-nodeds1/dp-histogram/`](runs/2026-10-20-nodeds1/dp-histogram/) |
| 2026-10-19 23:14 UTC | `hypoxia-model` | 1 (boya A) | `nodeds1` · gratuito | `…f5e424ca9a7bb390` (12 s) | exactitud 0,826 · F1 0,576 · AUC 0,923 · [`runs/2026-10-20-nodeds1/hypoxia-model/`](runs/2026-10-20-nodeds1/hypoxia-model/) |

### Desde Nodum

| Fecha | Algoritmo | Datasets | Nodo · entorno | Job | Resultado |
|---|---|---|---|---|---|
