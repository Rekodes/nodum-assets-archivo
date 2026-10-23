# Publicar en Nodum

Una ficha por asset, en el orden del formulario de **Publicar**. Lo que va en `código` se pega tal cual.

- **Nodo:** el de la ficha. Un dataset vale en cualquier nodo si el algoritmo tiene servicio allí.
- **Cabeceras de la petición:** ninguna; los datos se sirven sin clave.
- **Copia para auditar otro nodo:** la misma ficha con otro **Nodo** y « · nodo 2» al final del **Nombre**.
- **Etiquetas:** la línea entera se pega de una vez; cada coma separa una etiqueta.

## Índice

**Agro: maíz**

- Datasets: [Finca A · llanura manchega (estrés hídrico)](#finca-a--llanura-manchega-estrés-hídrico) · [Finca B · meseta del Duero (estrés hídrico)](#finca-b--meseta-del-duero-estrés-hídrico) · [Finca C · vega del Ebro (estrés hídrico)](#finca-c--vega-del-ebro-estrés-hídrico) · [Fincas A, B y C · juntas (estrés hídrico)](#fincas-a-b-y-c--juntas-estrés-hídrico) · [Silo · entradas limpias](#silo--entradas-limpias) · [Silo · entradas con defectos](#silo--entradas-con-defectos) · [Silo · entradas cortadas (JSON roto)](#silo--entradas-cortadas-json-roto) · [Estaciones agroclimáticas (XML)](#estaciones-agroclimáticas-xml)
- Algoritmos: [Modelo de estrés hídrico del maíz](#modelo-de-estrés-hídrico-del-maíz) · [Balance de riego (FAO-56)](#balance-de-riego-fao-56) · [Informe del silo con privacidad diferencial](#informe-del-silo-con-privacidad-diferencial)

**Mar**

- Datasets: [Boya A · laguna costera (hipoxia)](#boya-a--laguna-costera-hipoxia) · [Boya B · bahía abierta (hipoxia)](#boya-b--bahía-abierta-hipoxia) · [Boya C · mar abierto (hipoxia)](#boya-c--mar-abierto-hipoxia) · [Boyas A, B y C · juntas (hipoxia)](#boyas-a-b-y-c--juntas-hipoxia) · [Capturas · limpias](#capturas--limpias) · [Capturas · con defectos](#capturas--con-defectos) · [Capturas · cortadas (JSON roto)](#capturas--cortadas-json-roto) · [Estaciones costeras (XML)](#estaciones-costeras-xml)
- Algoritmos: [Histograma con privacidad diferencial](#histograma-con-privacidad-diferencial) · [Modelo de hipoxia](#modelo-de-hipoxia)

**Genéricos**

- Algoritmos: [Contar líneas](#contar-líneas) · [Calidad de los datos (JSON y XML)](#calidad-de-los-datos-json-y-xml) · [Auditoría del entorno del nodo](#auditoría-del-entorno-del-nodo) · [Muestra de salidas](#muestra-de-salidas) · [Resumen de entradas](#resumen-de-entradas) · [Carga de CPU y memoria](#carga-de-cpu-y-memoria)

## Datasets · Agro: maíz

### Finca A · llanura manchega (estrés hídrico)

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/maiz-estres-hidrico/v1/finca-a.json` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Finca A · llanura manchega (estrés hídrico)` |
| | Descripción | 720 lecturas horarias de una finca de maíz en julio de 2026: llanura manchega, pozo con cupo y suelo arenoso. 26 % de horas con estrés hídrico. Ola de calor del 12 al 17 y una tormenta. Sintético, para el modelo de estrés y el balance de riego. |
| | Etiquetas | `maiz, finca, estres-hidrico, json` |

### Finca B · meseta del Duero (estrés hídrico)

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/maiz-estres-hidrico/v1/finca-b.json` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Finca B · meseta del Duero (estrés hídrico)` |
| | Descripción | 720 lecturas horarias de una finca de maíz en julio de 2026: meseta del Duero, riego a manta cada 11 días. 13 % de horas con estrés hídrico. Ola de calor del 12 al 17 y una tormenta. Sintético, para el modelo de estrés y el balance de riego. |
| | Etiquetas | `maiz, finca, estres-hidrico, json` |

### Finca C · vega del Ebro (estrés hídrico)

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/maiz-estres-hidrico/v1/finca-c.json` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Finca C · vega del Ebro (estrés hídrico)` |
| | Descripción | 720 lecturas horarias de una finca de maíz en julio de 2026: vega del Ebro, pivote cada noche con tope. 9 % de horas con estrés hídrico. Ola de calor del 12 al 17 y una tormenta. Sintético, para el modelo de estrés y el balance de riego. |
| | Etiquetas | `maiz, finca, estres-hidrico, json` |

### Fincas A, B y C · juntas (estrés hídrico)

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/maiz-estres-hidrico/v1/todas.json` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Fincas A, B y C · juntas (estrés hídrico)` |
| | Descripción | Las tres fincas de maíz juntas: 2160 lecturas horarias de julio de 2026. Sirve para comparar el modelo centralizado con el federado. Sintético. |
| | Etiquetas | `maiz, finca, estres-hidrico, centralizado, json` |

### Silo · entradas limpias

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/silo-entradas/v1/limpias.json` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Silo · entradas limpias` |
| | Descripción | 240 entregas de maíz en el silo de una cooperativa (campaña de octubre de 2026, 24 socios), sin defectos. Sintético, para el informe del silo con privacidad diferencial y como referencia de calidad. |
| | Etiquetas | `maiz, silo, calidad, json` |

### Silo · entradas con defectos

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/silo-entradas/v1/sucias.json` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Silo · entradas con defectos` |
| | Descripción | 260 entregas de maíz en el silo de una cooperativa (campaña de octubre de 2026, 24 socios) con defectos conocidos: 10 % sin parcela, pesos como texto, humedad con coma decimal, híbridos nulos, camiones vacíos y 20 duplicados. Sintético, para probar la calidad de los datos. |
| | Etiquetas | `maiz, silo, calidad, json` |

### Silo · entradas cortadas (JSON roto)

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/silo-entradas/v1/cortadas.json` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Silo · entradas cortadas (JSON roto)` |
| | Descripción | Las entregas limpias del silo cortadas a 5000 bytes: un JSON mal formado a propósito. Sintético, para ver cómo responde el banco de calidad a un fichero que no se puede leer. |
| | Etiquetas | `maiz, silo, calidad, json` |

### Estaciones agroclimáticas (XML)

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/estaciones-agro/v1/estaciones.xml` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Estaciones agroclimáticas (XML)` |
| | Descripción | 120 estaciones agroclimáticas en XML, con huecos a propósito: 12 % sin el atributo province, 8 % con altitude_m vacío y 20 % sin operator. Sintético, para probar la calidad de los datos en XML. |
| | Etiquetas | `maiz, estaciones, calidad, xml` |

## Datasets · Mar

### Boya A · laguna costera (hipoxia)

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/boyas-hipoxia/v1/site-a.json` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Boya A · laguna costera (hipoxia)` |
| | Descripción | 720 lecturas horarias de una boya en una laguna costera en julio de 2026: temperatura, salinidad, clorofila, viento, oleaje y oxígeno disuelto. 23 % de horas con hipoxia. Sintético, para el modelo de hipoxia y el histograma con privacidad diferencial. |
| | Etiquetas | `mar, boya, hipoxia, json` |

### Boya B · bahía abierta (hipoxia)

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/boyas-hipoxia/v1/site-b.json` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Boya B · bahía abierta (hipoxia)` |
| | Descripción | 720 lecturas horarias de una boya en una bahía abierta en julio de 2026: temperatura, salinidad, clorofila, viento, oleaje y oxígeno disuelto. 11 % de horas con hipoxia. Sintético, para el modelo de hipoxia y el histograma con privacidad diferencial. |
| | Etiquetas | `mar, boya, hipoxia, json` |

### Boya C · mar abierto (hipoxia)

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/boyas-hipoxia/v1/site-c.json` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Boya C · mar abierto (hipoxia)` |
| | Descripción | 720 lecturas horarias de una boya en mar abierto en julio de 2026: temperatura, salinidad, clorofila, viento, oleaje y oxígeno disuelto. 5 % de horas con hipoxia. Sintético, para el modelo de hipoxia y el histograma con privacidad diferencial. |
| | Etiquetas | `mar, boya, hipoxia, json` |

### Boyas A, B y C · juntas (hipoxia)

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/boyas-hipoxia/v1/todas.json` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Boyas A, B y C · juntas (hipoxia)` |
| | Descripción | Las tres boyas juntas: 2160 lecturas horarias de julio de 2026. Sirve para comparar el modelo centralizado con el federado. Sintético. |
| | Etiquetas | `mar, boya, hipoxia, centralizado, json` |

### Capturas · limpias

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/capturas/v1/limpias.json` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Capturas · limpias` |
| | Descripción | 240 desembarcos pesqueros sin defectos. Sintético, como referencia para el banco de calidad de los datos. |
| | Etiquetas | `mar, sintetico, json` |

### Capturas · con defectos

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/capturas/v1/sucias.json` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Capturas · con defectos` |
| | Descripción | Capturas con defectos: 260 desembarcos con huecos a propósito: sin puerto, pesos como texto, especies nulas y duplicados. |
| | Etiquetas | `mar, sintetico, json` |

### Capturas · cortadas (JSON roto)

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/capturas/v1/cortadas.json` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Capturas · cortadas (JSON roto)` |
| | Descripción | Los desembarcos limpios cortados a 5000 bytes: un JSON mal formado a propósito. Sintético, para ver cómo responde el banco de calidad a un fichero que no se puede leer. |
| | Etiquetas | `mar, sintetico, json` |

### Estaciones costeras (XML)

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un dataset |
| Origen | Nodo | Nodo 1 |
| | URL del fichero | `https://datos.rekodes.com/sinteticos/estaciones/v1/estaciones.xml` |
| | Cabeceras de la petición | Ninguna |
| Datos | Nombre | `Estaciones costeras (XML)` |
| | Descripción | 120 estaciones costeras en XML, con huecos a propósito: 12 % sin el atributo region, 8 % con depth_m vacío y 20 % sin operator. Sintético, para probar la calidad de los datos en XML. |
| | Etiquetas | `mar, estaciones, calidad, xml` |

## Algoritmos · Genéricos

### Contar líneas

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un algoritmo |
| | Tipo de algoritmo | Solo una imagen |
| Origen | Imagen con etiqueta | `docker.io/rekodes/nodum-line-count:0.2.0` |
| | Entrypoint | `python /app/main.py` |
| Datos | Nombre | `Contar líneas` |
| | Descripción | Cuenta las líneas y los bytes de cada dataset de entrada y devuelve el total en line-count.json. Vale para cualquier fichero de texto: sirve para comprobar el ciclo completo. |
| | Etiquetas | `generico, prueba, line-count` |
| | Lenguaje | `python` |
| | Versión | `0.2.0` |
| Nodos | Dónde podrá ejecutarse | Nodo 1, Nodo 2 y Nodo 3 |
| | Necesita internet al ejecutarse | No |
| Se prueba con | | Cualquiera |

**Parámetros**

| Nombre | Etiqueta | Tipo | Valor por defecto | Descripción | Obligatorio |
|---|---|---|---|---|---|
| `skip_header` | Saltar la cabecera | Sí o no | `No` | No cuenta la primera línea de cada fichero. | No |

### Calidad de los datos (JSON y XML)

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un algoritmo |
| | Tipo de algoritmo | Solo una imagen |
| Origen | Imagen con etiqueta | `docker.io/rekodes/nodum-data-quality:0.2.0` |
| | Entrypoint | `python /app/main.py` |
| Datos | Nombre | `Calidad de los datos (JSON y XML)` |
| | Descripción | Nota de calidad de 0 a 100 de ficheros JSON y XML: validez, completitud, consistencia y unicidad, medidas por registro. Salen quality-report.json y quality-report.html. |
| | Etiquetas | `generico, calidad, json, xml` |
| | Lenguaje | `python` |
| | Versión | `0.2.0` |
| Nodos | Dónde podrá ejecutarse | Nodo 1, Nodo 2 y Nodo 3 |
| | Necesita internet al ejecutarse | No |
| Se prueba con | | Silo y capturas (limpias, con defectos, cortadas) y estaciones |

**Parámetros**

| Nombre | Etiqueta | Tipo | Valor por defecto | Descripción | Obligatorio |
|---|---|---|---|---|---|
| `required_fields` | Campos obligatorios | Texto | `` | Separados por comas; se suman a los que aparecen en la mayoría de registros. | No |

### Auditoría del entorno del nodo

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un algoritmo |
| | Tipo de algoritmo | Solo una imagen |
| Origen | Imagen con etiqueta | `docker.io/rekodes/nodum-env-audit:0.2.0` |
| | Entrypoint | `python /app/main.py` |
| Datos | Nombre | `Auditoría del entorno del nodo` |
| | Descripción | Audita el entorno en el que el nodo ejecuta el algoritmo, sin tocar los datos: usuario, límites de CPU y memoria, si hay red, sha256 de las entradas y nombres de las variables de entorno. Sale env-audit.json. |
| | Etiquetas | `generico, auditoria, seguridad` |
| | Lenguaje | `python` |
| | Versión | `0.2.0` |
| Nodos | Dónde podrá ejecutarse | Nodo 1, Nodo 2 y Nodo 3 |
| | Necesita internet al ejecutarse | No |
| Se prueba con | | Cualquiera |

**Parámetros**

| Nombre | Etiqueta | Tipo | Valor por defecto | Descripción | Obligatorio |
|---|---|---|---|---|---|
| `probe_host` | Dirección de prueba de red | Texto | `1.1.1.1` | A qué dirección intenta conectar para comprobar que no hay red. | No |

## Algoritmos · Agro: maíz

### Modelo de estrés hídrico del maíz

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un algoritmo |
| | Tipo de algoritmo | Solo una imagen |
| Origen | Imagen con etiqueta | `docker.io/rekodes/nodum-water-stress-model:0.2.0` |
| | Entrypoint | `python /app/main.py` |
| Datos | Nombre | `Modelo de estrés hídrico del maíz` |
| | Descripción | Regresión logística que predice el estrés hídrico del maíz con el tiempo y la temperatura de la cubierta, sin la sonda. Entrenamiento local del aprendizaje federado: salen los pesos y las métricas, no las lecturas. |
| | Etiquetas | `maiz, estres-hidrico, regresion-logistica, fl` |
| | Lenguaje | `python` |
| | Versión | `0.2.0` |
| Nodos | Dónde podrá ejecutarse | Nodo 1 |
| | Necesita internet al ejecutarse | No |
| Se prueba con | | Fincas A, B, C y juntas |

**Parámetros**

| Nombre | Etiqueta | Tipo | Valor por defecto | Descripción | Obligatorio |
|---|---|---|---|---|---|
| `epochs` | Épocas | Número | `300` | Pasadas del descenso de gradiente. | No |
| `learning_rate` | Tasa de aprendizaje | Número | `0.5` | Tamaño del paso. | No |
| `l2` | Regularización L2 | Número | `0.001` | Penaliza los pesos grandes. | No |
| `min_radiation` | Radiación mínima (W/m²) | Número | `300` | Solo entran las horas con al menos esta radiación; 0 para usarlas todas. | No |

### Balance de riego (FAO-56)

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un algoritmo |
| | Tipo de algoritmo | Solo una imagen |
| Origen | Imagen con etiqueta | `docker.io/rekodes/nodum-irrigation-balance:0.2.0` |
| | Entrypoint | `python /app/main.py` |
| Datos | Nombre | `Balance de riego (FAO-56)` |
| | Descripción | Balance de agua diario de cada finca de maíz (FAO-56): días de estrés, cuánto regar y en cuántos días coincide con la sonda. Salen totales diarios por finca, no las lecturas horarias. |
| | Etiquetas | `maiz, riego, fao-56` |
| | Lenguaje | `python` |
| | Versión | `0.2.0` |
| Nodos | Dónde podrá ejecutarse | Nodo 1 |
| | Necesita internet al ejecutarse | No |
| Se prueba con | | Fincas A, B, C y juntas |

**Parámetros**

| Nombre | Etiqueta | Tipo | Valor por defecto | Descripción | Obligatorio |
|---|---|---|---|---|---|
| `kc` | Kc del cultivo | Número | `1.2` | Maíz a mitad de ciclo: 1,2 (FAO-56). | No |
| `taw_mm` | Agua útil (mm) | Número | `130` | Agua que el suelo guarda para las raíces. | No |
| `p` | Fracción p | Número | `0.55` | Parte del agua útil que el maíz gasta sin estrés. | No |
| `efficiency` | Eficiencia del riego | Número | `0.85` | Goteo 0,9; pivote 0,85; manta 0,6. | No |
| `initial_depletion_mm` | Agotamiento inicial (mm) | Número | `20` | Lo que le falta al suelo el primer día. | No |

### Informe del silo con privacidad diferencial

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un algoritmo |
| | Tipo de algoritmo | Solo una imagen |
| Origen | Imagen con etiqueta | `docker.io/rekodes/nodum-dp-silo-report:0.2.0` |
| | Entrypoint | `python /app/main.py` |
| Datos | Nombre | `Informe del silo con privacidad diferencial` |
| | Descripción | Entregas, toneladas, humedad media e histograma de humedad del silo con privacidad diferencial por socio. Solo salen los agregados con ruido; el log no da ninguna cifra real. |
| | Etiquetas | `maiz, silo, privacidad-diferencial` |
| | Lenguaje | `python` |
| | Versión | `0.2.0` |
| Nodos | Dónde podrá ejecutarse | Nodo 1 |
| | Necesita internet al ejecutarse | No |
| Se prueba con | | Silo · entradas limpias y con defectos |

**Parámetros**

| Nombre | Etiqueta | Tipo | Valor por defecto | Descripción | Obligatorio |
|---|---|---|---|---|---|
| `epsilon` | ε (privacidad) | Número | `5` | Para todo el informe de cada dataset. Más pequeño, más ruido. | Sí |
| `max_deliveries` | Entregas por socio | Número | `5` | Cuántas entregas de cada socio cuentan como mucho. Más, menos sesgo y más ruido. | No |

## Algoritmos · Mar

### Histograma con privacidad diferencial

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un algoritmo |
| | Tipo de algoritmo | Solo una imagen |
| Origen | Imagen con etiqueta | `docker.io/rekodes/nodum-dp-histogram:0.2.0` |
| | Entrypoint | `python /app/main.py` |
| Datos | Nombre | `Histograma con privacidad diferencial` |
| | Descripción | Histograma y media de una variable de las boyas con privacidad diferencial (mecanismo de Laplace). Solo sale el agregado con ruido, nunca una lectura. |
| | Etiquetas | `mar, boya, privacidad-diferencial` |
| | Lenguaje | `python` |
| | Versión | `0.2.0` |
| Nodos | Dónde podrá ejecutarse | Nodo 1 |
| | Necesita internet al ejecutarse | No |
| Se prueba con | | Boyas A, B, C y juntas |

**Parámetros**

| Nombre | Etiqueta | Tipo | Valor por defecto | Descripción | Obligatorio |
|---|---|---|---|---|---|
| `column` | Variable | Lista | `sea_surface_temp_c` | Qué variable de las boyas se resume. | Sí |
| `epsilon` | ε (privacidad) | Número | `1` | Más pequeño, más ruido y más privacidad. | Sí |
| `bins` | Intervalos | Número | `16` | Cuántas barras tiene el histograma. | No |
| `lower` | Mínimo | Número | `15` | Los valores por debajo se recortan a este. | No |
| `upper` | Máximo | Número | `35` | Los valores por encima se recortan a este. | No |

Opciones de `column`:

```text
sea_surface_temp_c=Temperatura del agua (°C)
salinity_psu=Salinidad (PSU)
chlorophyll_mg_m3=Clorofila (mg/m³)
dissolved_oxygen_mg_l=Oxígeno disuelto (mg/l)
wind_speed_m_s=Viento (m/s)
wave_height_m=Oleaje (m)
```

### Modelo de hipoxia

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un algoritmo |
| | Tipo de algoritmo | Solo una imagen |
| Origen | Imagen con etiqueta | `docker.io/rekodes/nodum-hypoxia-model:0.2.0` |
| | Entrypoint | `python /app/main.py` |
| Datos | Nombre | `Modelo de hipoxia` |
| | Descripción | Regresión logística que predice la hipoxia con los datos de las boyas, sin que salgan del nodo. Entrenamiento local del aprendizaje federado: salen los pesos y las métricas, no las lecturas. |
| | Etiquetas | `mar, boya, hipoxia, regresion-logistica, fl` |
| | Lenguaje | `python` |
| | Versión | `0.2.0` |
| Nodos | Dónde podrá ejecutarse | Nodo 1 |
| | Necesita internet al ejecutarse | No |
| Se prueba con | | Boyas A, B, C y juntas |

**Parámetros**

| Nombre | Etiqueta | Tipo | Valor por defecto | Descripción | Obligatorio |
|---|---|---|---|---|---|
| `epochs` | Épocas | Número | `300` | Pasadas del descenso de gradiente. | No |
| `learning_rate` | Tasa de aprendizaje | Número | `0.5` | Tamaño del paso. | No |
| `l2` | Regularización L2 | Número | `0.001` | Penaliza los pesos grandes. | No |

### Muestra de salidas

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un algoritmo |
| | Tipo de algoritmo | Un script |
| Origen | Entorno | Python 3.11 |
| | De dónde sale | Subir un fichero |
| | Fichero | `algorithms/generic/output_samples.py` |
| Datos | Nombre | `Muestra de salidas` |
| | Descripción | Escribe un fichero de cada tipo que la ficha de una ejecución sabe enseñar (SVG, PNG, JPG, CSV, TSV, JSON, Markdown, HTML, texto y log) y los casos límite: una tabla de 500 filas, un texto de más de 256 KiB, un HTML con script y ficheros sin vista. |
| | Etiquetas | `generico, prueba, salidas` |
| | Lenguaje | `python` |
| | Versión | `3.11` |
| Parámetros | | Ninguno |
| Nodos | Dónde podrá ejecutarse | Nodo 1, Nodo 2 y Nodo 3 |
| | Necesita internet al ejecutarse | No |
| Se prueba con | | Cualquiera: no lee los datos |

### Resumen de entradas

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un algoritmo |
| | Tipo de algoritmo | Un script |
| Origen | Entorno | Python 3.11 |
| | De dónde sale | Un fichero de GitHub |
| | Fichero de GitHub | `github.com/Rekodes/nodum-assets/blob/main/algorithms/generic/resumen_entradas.py` |
| Datos | Nombre | `Resumen de entradas` |
| | Descripción | Cuenta bytes y líneas de cada fichero de entrada y deja una muestra en JSON, CSV y Markdown. |
| | Etiquetas | `generico, prueba` |
| | Lenguaje | — |
| | Versión | — |
| Nodos | Dónde podrá ejecutarse | Nodo 1, Nodo 2 y Nodo 3 |
| | Necesita internet al ejecutarse | No |
| | Formatos que lee | CSV, TSV, JSON, JSON Lines, XML y Texto |
| | Genérico | Sí |
| Se prueba con | | Cualquiera; con `fallar` = Sí termina con código 3 |

**Parámetros**

| Nombre | Etiqueta | Tipo | Valor por defecto | Descripción | Obligatorio |
|---|---|---|---|---|---|
| `muestra` | Líneas de muestra | Número | `3` | Cuántas líneas de cada fichero se enseñan. | No |
| `fallar` | Terminar con error | Sí o no | `No` | Para probar un fallo: sale con código 3. | No |

### Carga de CPU y memoria

| Paso | Campo | Valor |
|---|---|---|
| Tipo | Qué publicas | Un algoritmo |
| | Tipo de algoritmo | Un script |
| Origen | Entorno | Python 3.11 |
| | De dónde sale | Un fichero de GitHub |
| | Fichero de GitHub | `github.com/Rekodes/nodum-assets/blob/main/algorithms/generic/carga_cpu_memoria.py` |
| Datos | Nombre | `Carga de CPU y memoria` |
| | Descripción | Trabaja a toda CPU durante los segundos que le digas y va ocupando memoria poco a poco, para ver las métricas del nodo. No lee los datos. |
| | Etiquetas | `generico, prueba, metricas` |
| | Lenguaje | — |
| | Versión | — |
| Nodos | Dónde podrá ejecutarse | Nodo 1, Nodo 2 y Nodo 3 |
| | Necesita internet al ejecutarse | No |
| | Formatos que lee | Ninguno marcado: no lee los datos |
| | Genérico | Sí |
| Se prueba con | | Cualquiera. Con «Una serie, cada 10 s» al ejecutar se ve la memoria subir; con `sin_memoria` = Sí falla por memoria |

**Parámetros**

| Nombre | Etiqueta | Tipo | Valor por defecto | Descripción | Obligatorio |
|---|---|---|---|---|---|
| `segundos` | Segundos de trabajo | Número | `60` | Cuánto trabaja. El entorno gratuito corta a los 120 s, bajada de la imagen incluida. | No |
| `memoria_mb` | Memoria al final (MB) | Número | `400` | La memoria que alcanza al acabar, subiendo cada segundo. | No |
| `sin_memoria` | Quedarse sin memoria | Sí o no | `No` | Pide memoria sin parar hasta que el nodo lo para por el límite. | No |
