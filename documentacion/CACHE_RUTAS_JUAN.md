# Caché compartida de rutas (2026-11-12)

Elección explícita del usuario: tabla hash propia acotada frente a conservar
únicamente la caché individual y medir K menores. D-TC-09 amplía las capacidades
001/004; no requiere otro spec. Se conserva Dijkstra, rango y desempate.

La tabla de 256 casillas usa doble hashing y salto impar, sin crecimiento.
Retiene máximo 179 resultados; antes de superar el 70 % se vacía. La clave
compara identidad de origen/objetivo, rango y revisión de conexiones. Comparte
también resultados sin ruta. El último resultado por actor sigue disponible.
Cambiar puertas/costos o retroceder vacía la tabla. Copia y carga crean una
vacía; no se persiste ni modifica el formato v6, azar, reloj o deltas.

## Verificación

**684 pruebas aprobadas**. Casos nuevos: colisiones forzadas, actualización,
límite y liberación, identidad/rango/revisión, dos cazadores equivalentes,
costos y retroceso, 250 consultas contra cálculo desde cero y caché vacía en
copia manual, punto por ID y guardado/carga.
[Salida](evidencia/pruebas_cache_compartida_juan.txt).

## Consultas oficiales, misma partida y mismos puntos

Cripta-06 `f9ed9afa683d`, catálogo `4b9e75a42be5`, 300 salas, 32 cazadores
activos iniciales, K=25, 5 000 acciones, semilla 2026. ABBA de cuatro bloques
de 36 consultas, GC habilitado, sin red ni vista; resultados equivalentes y
partida intacta. Incluye copia/replay/resumen/liberación y contadores auxiliares.

| Bloque | Caché | Mediana (ms) | Máximo (ms) | ≥50 ms | Dijkstra |
|---|---|---:|---:|---:|---:|
| A1 | individual | 40,518 | 136,479 | 16/36 | 5 613 |
| B1 | compartida | 40,169 | 68,750 | 9/36 | 3 195 |
| B2 | compartida | 36,125 | 47,421 | 0/36 | 3 195 |
| A2 | individual | 36,704 | 98,233 | 16/36 | 5 613 |

Cada bloque compartido evita 2 418 búsquedas (**43,1 %**). Es una reducción de
trabajo reproducible en ambos bloques. Los tiempos fluctúan: no se declara
cumplimiento de 50 ms porque el primer bloque compartido tiene nueve excedidos.
[Resumen](evidencia/cache_compartida_oficial_juan.json).
Reproducir: `python -X utf8 -u -m modelo.bench_cache_rutas --salida-json resultado.json`.

## Ciclos y consultas sintéticas

300 salas, 32 cazadores, 5 000 acciones vigentes; 5 001 ciclos ejecutados por
el retroceso y 36 consultas por K, GC habilitado, registro/puntos incluidos.

| K | Ciclo máximo (ms) | Ciclos ≥20 ms | Consulta máxima (ms) | Consultas ≥50 ms |
|---|---:|---:|---:|---:|
| 5 | 64,581 | 710 | 12,701 | 0/36 |
| 10 | 76,411 | 278 | 20,629 | 0/36 |
| 25 | 43,190 | 166 | 19,541 | 0/36 |

Los ciclos todavía incumplen. Corridas previas son secuenciales y varía el
entorno; no se atribuye toda diferencia de tiempo a esta caché.
[Resumen](evidencia/presupuestos_cache_compartida_juan.json).
Reproducir: `python -X utf8 -u -m modelo.bench_presupuestos --salida-json resultado.json`.

Avance global estimado: **93 %**. Pendientes: estabilizar consultas oficiales,
reducir creación de puntos y seleccionar K con tiempos y memoria. Se comparan
capacidades de caché antes de cambiar su parámetro inicial; capacidad y K son
parámetros distintos. No se certifican PR-LT-001/007 ni aceptación final.

## Capacidad: 256 frente a 1 024

Otro ensayo ABBA sobre los mismos puntos produjo **3 195 búsquedas y 2 418
aciertos por bloque en ambas capacidades**. Máximos 63,247/82,924 ms con 256
y 53,086/60,840 ms con 1 024; hubo excedidos en todos los bloques. No hay ahorro
de búsquedas por aumentar la tabla, y los tiempos varían entre repeticiones.
Se conserva **256**, que usa menos casillas; no se cambia K.
[Resumen](evidencia/capacidades_cache_rutas_juan.json).
Reproducir: `python -X utf8 -u -m modelo.bench_cache_rutas --capacidades 256 1024 --salida-json resultado.json`.
