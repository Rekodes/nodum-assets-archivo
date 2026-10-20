# Datasets

Sintéticos. Se sirven sin clave desde `https://datos.rekodes.com/sinteticos/`, con la misma ruta que
aquí. Lo publicado no cambia: un cambio es una versión nueva (`v2`). `SHA256SUMS` guarda la huella de
cada fichero.

## Catálogo

| Fichero | Registros | Qué es |
|---|---|---|
| `boyas-hipoxia/v1/site-a.json` | 720 h | Boya en una laguna costera. 23 % de horas con hipoxia |
| `boyas-hipoxia/v1/site-b.json` | 720 h | Boya en una bahía abierta. 11 % |
| `boyas-hipoxia/v1/site-c.json` | 720 h | Boya en mar abierto. 5 % |
| `boyas-hipoxia/v1/todas.json` | 2160 h | Las tres juntas, para comparar con un modelo centralizado |
| `capturas/v1/limpias.json` | 240 | Desembarcos pesqueros sin defectos |
| `capturas/v1/sucias.json` | 260 | Los mismos, con defectos conocidos |
| `capturas/v1/cortadas.json` | — | Los limpios cortados a 5000 bytes: JSON roto |
| `estaciones/v1/estaciones.xml` | 120 | Estaciones costeras, con atributos y elementos que faltan |

### Boyas

- Julio de 2026, una lectura por hora.
- Campos: `timestamp`, `site_id`, `sea_surface_temp_c`, `salinity_psu`, `chlorophyll_mg_m3`,
  `wind_speed_m_s`, `wave_height_m`, `dissolved_oxygen_mg_l`, `hypoxia`.
- `hypoxia` es `dissolved_oxygen_mg_l < 4`.
- Cada sitio tiene su propio clima: los datos no son IID.

### Defectos conocidos

| Fichero | Defectos |
|---|---|
| `sucias.json` | 10 % sin `port` · 6 % con `weight_kg` como texto · 5 % con `species` nulo · 4 % con `vessel` vacío · 20 duplicados |
| `cortadas.json` | JSON mal formado |
| `estaciones.xml` | 12 % sin el atributo `region` · 8 % con `depth_m` vacío · 20 % sin `operator` |

## En Nodum

| Dataset | Fichero | Nodo | Algoritmos de confianza |
|---|---|---|---|
| Boya A · laguna costera (hipoxia) | `site-a.json` | nodeds1 | line-count, dp-histogram, hypoxia-model, env-audit |
| Boya B · bahía abierta (hipoxia) | `site-b.json` | nodeds1 | ídem |
| Boya C · mar abierto (hipoxia) | `site-c.json` | nodeds1 | ídem |
| Capturas pesqueras limpias (JSON) | `limpias.json` | nodeds1 | line-count, data-quality, env-audit |
| Capturas pesqueras con defectos (JSON) | `sucias.json` | nodeds1 | ídem |
| Capturas pesqueras cortadas (JSON roto) | `cortadas.json` | nodeds1 | ídem |
| Estaciones costeras (XML) | `estaciones.xml` | nodeds1 | ídem |
| Estaciones costeras (XML) · nodo 2 | `estaciones.xml` | nodeds2 | ídem |
| Capturas pesqueras limpias (JSON) · nodo 3 | `limpias.json` | nodeds3 | ídem |

Las copias en nodeds2 y nodeds3 sirven para auditar cada nodo.

## Generar

```bash
make data
```

| Generador | Ficheros |
|---|---|
| [`generadores/boyas_hipoxia.py`](generadores/boyas_hipoxia.py) | `boyas-hipoxia/v1/*` |
| [`generadores/calidad_json_xml.py`](generadores/calidad_json_xml.py) | `capturas/v1/*`, `estaciones/v1/*` |

Semilla fija y sin red: los bytes salen iguales en cada ejecución.
