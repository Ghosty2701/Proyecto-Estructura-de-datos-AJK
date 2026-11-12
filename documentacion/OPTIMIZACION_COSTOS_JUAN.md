# Costos de consultas y puntos (2026-11-12)

Se conservan Dijkstra individual, doble hashing, heap propio y registros por ID
aprobados. No se incorpora una estructura nueva ni se elige K definitivo.

## Segundo hash diferido

`TablaDistancias` calcula el paso secundario solo tras la primera colisión.
La mezcla, secuencia de casillas y conteo de sondeos se conservan. Las pruebas
existentes cubren colisiones forzadas, crecimiento, actualización e identidad.

Ensayo oficial ABBA sobre **la misma partida y puntos**: cripta-06
`f9ed9afa683d`, 300 salas, 32 cazadores iniciales, K=25, 5 000 acciones,
semilla 2026. Cada bloque usa 36 consultas, con equivalencia de resultados,
GC habilitado, cero HTTP en consultas y partida intacta. Se midió antes de
la compactación de campos de los puntos.

| Bloque | Hash | Mediana (ms) | Máximo (ms) | Consultas ≥50 ms |
|---|---|---:|---:|---:|
| A1 | anticipado | 50,233 | 126,804 | 18/36 |
| B1 | diferido | 49,727 | 124,985 | 18/36 |
| B2 | diferido | 46,227 | 112,508 | 17/36 |
| A2 | anticipado | 55,594 | 138,995 | 19/36 |

Los bloques favorecen el cálculo diferido, pero no cumplen el presupuesto.
La variación entre bloques impide atribuir una mejora porcentual exacta.
[Resumen compacto](evidencia/hash_diferido_juan.json).
Reproducir: `python -X utf8 -u -m modelo.bench_hash_rutas --salida-json resultado.json`.

Avance global estimado: **93 %**. Siguen pendientes los límites de ciclos,
consultas oficiales y K definitivo.

## Compactación de campos por registro

Los campos requeridos, opcionales y su máscara ocupan una sola tupla en vez
de tuplas anidadas. Conserva los mismos IDs, registros, alias y ciclos; el
formato v6 de disco no cambia. La regresión completa pasa **674 pruebas**, incluida
la comparación de bytes v6 contra los puntos anteriores.
[Salida](evidencia/pruebas_costos_juan.txt).

Ensayo ABBA contra `de2b408`, con la misma partida sintética tras 5 000 acciones,
300 salas y 32 cazadores. Cada punto tiene 6 760 registros. Tracemalloc separado
de tiempos, cinco capturas/restauraciones por bloque y GC habilitado:

| Bloque | Variante | Memoria retenida del punto (bytes) | Captura mediana (ms) | Restauración mediana (ms) |
|---|---|---:|---:|---:|
| A1 | anterior | 1 557 264 | 22,480 | 10,431 |
| B1 | compacta | 1 405 680 | 22,109 | 8,647 |
| B2 | compacta | 1 405 624 | 21,432 | 9,086 |
| A2 | anterior | 1 557 208 | 29,631 | 11,960 |

Ahorro de memoria retenida del punto: **9,7 %**. Excluye la partida fuente,
RSS e historia completa; no se extrapola directamente a la memoria total.
Todas las restauraciones producen los mismos bytes v6. Restauración excluye
replay y liberación: su tiempo no es el de una consulta completa.
[Resumen](evidencia/compactacion_registros_juan.json).
Reproducir: `python -X utf8 -u -m modelo.bench_registros --salida-json resultado.json`.

La corrida completa posterior **no confirma mejora de latencia**. Una ronda
de 5 001 ciclos y 36 consultas por K, GC habilitado, incluye creación de puntos:

| K | Ciclo máximo (ms) | Ciclos ≥20 ms | Consulta máxima (ms) | Consultas ≥50 ms |
|---|---:|---:|---:|---:|
| 5 | 326,302 | 1 007 | 74,320 | 2/36 |
| 10 | 156,211 | 500 | 50,143 | 1/36 |
| 25 | 194,341 | 201 | 119,274 | 7/36 |

Las medianas de ciclos sin punto también subieron respecto de la corrida
anterior. No hay control suficiente para atribuir la diferencia al código
o al entorno. Se conservan resultados fallidos; no se certifican los límites
ni se presenta la reducción de memoria como una mejora demostrada de latencia.
[Resumen completo](evidencia/presupuestos_compactos_juan.json).
Reproducir: `python -X utf8 -u -m modelo.bench_presupuestos --salida-json resultado.json`.

La siguiente investigación propuesta es compartir rutas equivalentes entre
cazadores, con una caché acotada, frente a conservar la caché individual y medir
K menores. La elección de estructura está pendiente de la respuesta del usuario,
según AGENTS.md; no se implementa todavía. No hace falta otro spec para estas
dos optimizaciones; un cambio de caché se documentaría primero en las capacidades
001/004. El avance global estimado permanece en **93 %**.
