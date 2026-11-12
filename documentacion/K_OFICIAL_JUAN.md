# K oficial: consultas y memoria (2026-11-12)

Se añadió `--checkpoint-cada` al benchmark oficial para elegir un **K
experimental**; el juego conserva 25 provisional. No es una elección de K
definitivo ni cambia las reglas del motor.

`modelo/bench_k_oficial.py` ejecuta cada K en un proceso nuevo. Así, al terminar
un caso el sistema libera su memoria antes de iniciar el siguiente. Un
observador externo con psutil mide el pico residente observado cada 100 ms.
psutil ya estaba instalado en el entorno; solo lo requiere este ejecutor
optativo, no el juego ni el benchmark básico. No se añadió una dependencia
de producción. Se conserva la versión del observador en el JSON.

La memoria incluye Python, red/caché, partida, puntos e historia del proceso;
no es memoria exclusiva de puntos, memoria virtual ni asignaciones trazadas.
En Windows se lee `peak_wset`; en otros sistemas se muestrea RSS. Los tiempos
de consulta se miden en el proceso hijo sin tracemalloc ni perfilador.

Comandos reproducibles:

```powershell
python -X utf8 -u -m modelo.bench_k_oficial --valores-k 10 5 25 --salida-json resultado.json
python -X utf8 -u -m adaptadores.bench_adaptadores --solo consultas --cripta cripta-06 --acciones 5000 --rondas 3 --muestras 12 --semilla 2026 --checkpoint-cada 10 --salida-json resultado.json
```

La segunda ruta no requiere psutil y mide consultas, sin observar memoria.
Cada caso conserva identidad/versiones, carga, semilla, máximo, excedidos y
comprobaciones de partida intacta/cero HTTP. La regresión completa de este
cambio pasa **686 pruebas**, incluyendo K explícitos en el ejecutor real con
datos offline. [Salida](evidencia/pruebas_k_oficial_juan.txt).

## Resultado

Misma cripta `cripta-06`, versión `f9ed9afa683d`, catálogo `4b9e75a42be5`,
300 salas, 32 cazadores activos iniciales, semilla 2026 y 5 000 acciones.
Caché compartida de 256 casillas y puntos por ID con campos compactos. Cada K
tuvo una preparación y tres rondas de 12 consultas. Orden de procesos: 10, 5, 25.

| K | Consulta mediana (ms) | Máxima (ms) | Consultas ≥50 ms | Pico residente observado (MiB) |
|---|---:|---:|---:|---:|
| 5 | 14,649 | 55,533 | 1/36 | 1 833,22 |
| 10 | 31,812 | 79,727 | 9/36 | 941,14 |
| 25 | 46,302 | 65,366 | 16/36 | 407,10 |

Se conservó la partida y no hubo HTTP durante las consultas. Cada proceso
completó sus 5 000 acciones; máximo de acciones reaplicadas 5/9/23 para K=5/10/25.
[Resumen y condiciones](evidencia/k_oficial_cache_memoria_juan.json).

K=5 tiene menos consultas excedidas, con un pico residente aproximadamente
4,5 veces el observado para K=25 y más ciclos de creación de puntos. Los
ensayos son secuenciales, con una preparación por K; carga del equipo y picos
del recolector pueden influir. No demuestran que K=10 sea siempre más lento
que K=25 ni permiten garantizar el máximo en otra ejecución. RSS no sustituye
el análisis de memoria exclusiva de puntos ni el de asignaciones Python.

Ningún candidato satisface todos los límites observados. **K definitivo sigue
pendiente; 25 conserva su condición provisional**. No se propone cerrar
PR-LT-001/007 ni aceptación. Antes de fijar K debe reducirse el costo de los
puntos y repetirse la comparación de consultas/ciclos/memoria.

El usuario eligió conservar las tuplas y optimizar su captura frente a la
propuesta de empaquetar en bytes. No se implementa empaquetado. Resultados
posteriores en [captura de tuplas](CAPTURA_TUPLAS_JUAN.md).
Avance global estimado: **93 %**.
