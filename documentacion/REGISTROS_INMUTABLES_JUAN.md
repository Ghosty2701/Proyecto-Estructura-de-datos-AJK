# Puntos por ID: implementación y límites (2026-11-12)

Juan eligió «Extender el prototipo a registros inmutables por ID». D-LT-08
pertenece a la capacidad 004; no requiere otro spec. K=25 sigue provisional.

Cada punto contiene valores inmutables y referencias numéricas locales, sin
retener objetos del modelo original. Captura y restauración reutilizan el
esquema explícito y la tabla propia de identidades con doble hashing. Se
preservan alias y ciclos. El guardado sigue en formato v6: materializa cada
punto temporalmente para el codec existente y lo compacta de nuevo al cargar.

También se corrigió la retención por la función recursiva del copiador y se
liberan los objetos temporales de `historia` al terminar, incluso ante error.
La liberación solo vacía objetos creados por la copia, sin alterar datos
prestados de la caché viva.

Regresión final: **674 pruebas aprobadas**, `python -m pytest -q`. Incluye consultas,
retroceso, replay y guardado/carga. Casos nuevos comprueban independencia,
alias, ciclos, azar y liberación sin depender de la recolección de ciclos.

## Sintético

Python 3.13.2/Windows; semilla 2026, 300 salas, 32 cazadores y 5 000 acciones
vigentes. Una ronda de ciclos (5 001 acciones ejecutadas por el retroceso) y
36 consultas por K. GC habilitado; sin tracemalloc, red ni renderizado.
El ciclo incluye registro y punto. Se conservan todos los picos.

| K | Consulta mediana / máxima (ms) | Consultas ≥50 ms | Punto mediano (ms) | Ciclos ≥20 ms |
|---|---:|---:|---:|---:|
| 5 | 8,118 / 10,596 | 0/36 | 19,303 | 493/5 001 |
| 10 | 8,929 / 13,920 | 0/36 | 19,050 | 230/5 001 |
| 25 | 16,435 / 48,918 | 0/36 | 21,682 | 158/5 001 |

K=25: todos los excedidos crearon punto; máximo con punto 76,886 ms y sin
punto 16,163 ms. K=10 tuvo también un pico sin punto de 101,098 ms.
[Resumen](evidencia/presupuestos_registros_id_juan.json).
Reproducir: `python -X utf8 -u -m modelo.bench_presupuestos --salida-json resultado.json`.

## Referencia oficial

Cripta-06 `f9ed9afa683d`, catálogo `4b9e75a42be5`, 300 salas, 32 cazadores
activos iniciales, K=25, 5 000 acciones, semilla 2026 y 36 consultas:
mediana **93,171 ms**, máximo **763,224 ms**, **23/36 ≥50 ms**. Partida intacta
y cero HTTP en consultas. Enemigos originales; vida experimental del jugador.
[Resumen oficial](evidencia/consultas_referencia_registros_id_juan.json).
Reproducir: `python -X utf8 -u -m adaptadores.bench_adaptadores --solo consultas --cripta cripta-06 --acciones 5000 --rondas 3 --semilla 2026 --muestras 12 --salida-json resultado.json`.

La copia previa también tuvo 23/36 excedidos, mediana 75,178 ms y máximo
200,821 ms. Corridas secuenciales; los máximos dependen del entorno. El nuevo
ensayo **no demuestra mejora oficial** ni cierra PR-LT-001/007.

Repetición diagnóstica: 12 consultas, máximo 167,886 ms, 7 excedidos. Una
consulta adicional con cProfile tardó 797 ms bajo instrumentación: 739 ms
acumulados en las 23 acciones de replay y 649 ms en 380 búsquedas de rutas.
El perfil identifica dónde trabajar; su tiempo no se compara con el presupuesto
de 50 ms por la sobrecarga del perfilador. El último punto tenía 7 689 registros.
El replay de cazadores domina esa muestra, además del costo de crear puntos.

Se añadió una prueba explícita que compara los bytes v6 de cada punto
con la representación anterior y comprueba su recarga a registros por ID.
[Salida de regresión](evidencia/pruebas_registros_id_juan.txt).

Pendiente: perfilar reconstrucción/replay oficial, reducir creación de puntos
y medir memoria de esta representación antes de fijar K. La memoria medida
anteriormente corresponde al copiador de grafos. Avance global estimado: **93 %**.
