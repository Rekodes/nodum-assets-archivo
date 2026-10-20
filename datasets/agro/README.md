# Agro: maíz

Tres fincas de maíz que no comparten sus datos y la cooperativa a la que entregan la cosecha. Para la
calidad de los datos se usan los algoritmos de [`generic/`](../../algorithms/generic/).

## Datasets

En `https://datos.rekodes.com/sinteticos/`, con la misma ruta que en `sinteticos/`.

| Fichero | Registros | Qué es |
|---|---|---|
| `maiz-estres-hidrico/v1/finca-a.json` | 720 h | Llanura manchega, pozo con cupo y suelo arenoso. 26 % de horas con estrés |
| `maiz-estres-hidrico/v1/finca-b.json` | 720 h | Meseta del Duero, riego a manta cada 11 días. 13 % |
| `maiz-estres-hidrico/v1/finca-c.json` | 720 h | Vega del Ebro, pivote cada noche con tope. 9 % |
| `maiz-estres-hidrico/v1/todas.json` | 2160 h | Las tres juntas, para comparar con un modelo centralizado |
| `silo-entradas/v1/limpias.json` | 240 | Entradas de maíz en el silo de la cooperativa, sin defectos |
| `silo-entradas/v1/sucias.json` | 260 | Las mismas, con defectos conocidos |
| `silo-entradas/v1/cortadas.json` | — | Las limpias cortadas a 5000 bytes: JSON roto |
| `estaciones-agro/v1/estaciones.xml` | 120 | Estaciones agroclimáticas, con atributos y elementos que faltan |

### Fincas

- Julio de 2026, en plena floración, una lectura por hora. Ola de calor del 12 al 17 (+4 °C) y una
  tormenta en cada finca.
- Campos: `timestamp`, `farm_id`, `air_temp_c`, `relative_humidity_pct`, `solar_radiation_w_m2`,
  `wind_speed_m_s`, `rain_mm`, `irrigation_mm`, `et0_mm`, `canopy_temp_c`, `soil_moisture_pct`,
  `water_stress`.
- El agua del suelo sigue el balance de la FAO-56 (Kc 1,2; p 0,55). `water_stress` es que el
  agotamiento pase de p · TAW, lo que diría la sonda de humedad.
- La señal que hay que aprender: con sed, la cubierta cierra estomas y se calienta respecto al aire
  (línea base de Idso para el maíz).
- Cada finca tiene su clima, su suelo y su riego: los datos no son IID. El documento de cada fichero
  trae el suelo (`taw_mm`, `raw_mm`).

### Silo

- Octubre de 2026, campaña de maíz. 24 socios con un número de entregas muy distinto (de 2 a 42).
- Campos: `ticket_id`, `member`, `parcel` (referencia SIGPAC), `crop`, `hybrid`, `net_weight_kg`,
  `moisture_pct`, `test_weight_kg_hl`, `impurities_pct`, `received_at`, `truck` (`plate`, `axles`).

### Defectos conocidos

| Fichero | Defectos |
|---|---|
| `sucias.json` | 10 % sin `parcel` · 6 % con `net_weight_kg` como texto · 4 % con `moisture_pct` con coma decimal · 5 % con `hybrid` nulo · 4 % con `truck` vacío · 20 duplicados |
| `cortadas.json` | JSON mal formado |
| `estaciones.xml` | 12 % sin el atributo `province` · 8 % con `altitude_m` vacío · 20 % sin `operator` |

### Generadores

| Generador | Ficheros |
|---|---|
| [`maiz_estres_hidrico.py`](generadores/maiz_estres_hidrico.py) | `maiz-estres-hidrico/v1/*` |
| [`silo_estaciones.py`](generadores/silo_estaciones.py) | `silo-entradas/v1/*`, `estaciones-agro/v1/*` |

## Algoritmos

| Algoritmo | Qué hace | Datasets | Salidas |
|---|---|---|---|
| [water-stress-model](../../algorithms/agro/water_stress_model.py) | Regresión logística que predice el estrés hídrico con el tiempo y la cubierta, sin la sonda; salen pesos y métricas | Fincas | `model.json`, `metrics.json`, `coefficients.svg` |
| [irrigation-balance](../../algorithms/agro/irrigation_balance.py) | Balance de agua diario (FAO-56), días de estrés, cuánto regar y cuánto coincide con la sonda | Fincas | `irrigation-balance.json`, `irrigation-balance.svg` |
| [dp-silo-report](../../algorithms/agro/dp_silo_report.py) | Entregas, toneladas, humedad media e histograma de humedad con privacidad diferencial **por socio** | Silo | `dp-silo-report.json`, `dp-silo-report.svg` |

| Algoritmo | Parámetro | Tipo | Por defecto | Qué hace |
|---|---|---|---|---|
| water-stress-model | `epochs` | number | `300` | Pasadas del descenso de gradiente |
| | `learning_rate` | number | `0.5` | Tamaño del paso |
| | `l2` | number | `0.001` | Regularización |
| | `min_radiation` | number | `300` | Solo horas con al menos esta radiación (W/m²); `0`, todas |
| irrigation-balance | `kc` | number | `1.2` | Coeficiente del cultivo |
| | `taw_mm` | number | `130` | Agua útil del suelo |
| | `p` | number | `0.55` | Fracción que el maíz gasta sin estrés |
| | `efficiency` | number | `0.85` | Eficiencia del riego |
| | `initial_depletion_mm` | number | `20` | Agotamiento el primer día |
| dp-silo-report | `epsilon` | number | `5` | Para todo el informe; más pequeño, más ruido |
| | `max_deliveries` | number | `5` | Entregas de cada socio que cuentan como mucho |

### Lo que sale con los valores por defecto

- **water-stress-model** con `todas.json`: AUC 0,93 y F1 0,67. De noche la cubierta no delata la sed,
  por eso entrena solo con horas de sol; con `min_radiation=0` el AUC baja a 0,77.
- **irrigation-balance** con el suelo de cada finca (`taw_mm` 117 · 135 · 144): coincide con la sonda
  entre el 77 % y el 87 % de los días.
- **dp-silo-report** con `limpias.json`: unas 106 entregas, 1775 t y 23,6 % de humedad reales (con el
  tope de 5 por socio) salen con un ruido del orden del 5–10 %.
