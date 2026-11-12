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
