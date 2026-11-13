# Trazabilidad de línea de tiempo — estado revisado

Fuente: [spec.md](spec.md); tareas: [tasks.md](tasks.md). Revisión 2026-11-13.
K=10 elegido, 759 pruebas pasan en la regresión nueva. Cierre funcional con
EX-01 autorizada por el usuario; los límites 20/50 ms no cumplen en esta corrida.
Evidencia actual en [Estado de entrega](../../documentacion/ESTADO_ENTREGA_P2.md).
Las rutas de código parten de la raíz; las pruebas de `Pruebas/`. Los rangos
de tareas son números T. Los escenarios son AC-LT. Las filas no sustituyen
la lectura de sus aserciones ni reconstruyen Git: los ensayos se hicieron en
una copia sin `.git` y posteriormente se trasladaron al repositorio original.
Se separa comportamiento probado de mediciones con límites incumplidos.

| Requisito | AC-LT | Tareas T | Código | Pruebas | Estado |
| --- | --- | --- | --- | --- | --- |
| FR-LT-001 | 001/002/014 | 012-016 | controlador/partida.py; controlador/controlador.py | prueba_historia_partida.py | Verificado |
| FR-LT-002 | 001/002/003/006/015 | 014-016 | controlador/partida.py; vista/vista_consola.py | prueba_historia_partida.py | Verificado |
| FR-LT-003 | 001/003/004/005 | 006-007/011/016 | modelo/motor_eventos.py; controlador/partida.py | prueba_limite_tiempo.py; prueba_historia_partida.py | Verificado |
| FR-LT-004 | 002/012 | 004-005/019 | modelo/linea_tiempo.py | prueba_linea_tiempo.py; prueba_historia_partida.py | Verificado |
| FR-LT-005 | 006 | 014/016 | modelo/conocimiento.py; controlador/partida.py | prueba_historia_partida.py | Verificado |
| FR-LT-006 | 007/008/009/010 | 017-018 | controlador/controlador.py; controlador/cargar_partida.py | prueba_historia_partida.py; prueba_niebla_partida.py | Verificado |
| FR-LT-007 | 008/009/011 | 012/019 | controlador/comandos.py; modelo/linea_tiempo.py | prueba_comandos.py; prueba_historia_partida.py | Verificado |
| FR-LT-008 | 011/012/013/017 | 019-020/022 | modelo/linea_tiempo.py; adaptadores/bitacora_partida.py | prueba_historia_partida.py; prueba_bitacora_partida.py | Verificado |
| FR-LT-009 | 014 | 019-020 | modelo/retroceso.py; controlador/partida.py | prueba_historia_partida.py; prueba_motor_retroceso.py | Verificado |
| FR-LT-010 | 015/016/017 | 021-023 | main.py; adaptadores/bitacora_partida.py | prueba_partida.py; prueba_bitacora_partida.py | Verificado |
| FR-LT-011 | 018 | 021/023 | main.py | prueba_partida.py | Verificado |
| FR-LT-012 | 019/022/025 | 024-025/034 | main.py; modelo/linea_tiempo.py | prueba_historia_partida.py; prueba_estado_binario.py | Verificado, K=10 elegido |
| FR-LT-013 | 019/020 | 004-005/009 | adaptadores/copia_estado.py; modelo/linea_tiempo.py | prueba_copia_estado.py; prueba_linea_tiempo.py | Verificado |
| FR-LT-014 | 021/023 | 011/026 | controlador/partida.py; controlador/cargar_partida.py | prueba_historia_partida.py; prueba_estado_binario.py | Verificado |
| FR-LT-015 | 023/025 | 026-028 | adaptadores/estado_binario.py; controlador/cargar_partida.py | prueba_estado_binario.py | Verificado |
| FR-LT-016 | 024 | 026-027 | adaptadores/estado_binario.py | prueba_estado_binario.py | Verificado |

| Rendimiento | Tareas | Código/evidencia | Estado |
| --- | --- | --- | --- |
| PR-LT-001 | T029/T033 | bench_linea_tiempo.py; revision_sesion_k10_2026-11-13.json | EX-01: incumplido en corrida nueva, 2/36 ≥50 ms; máximo 63,5862 ms |
| PR-LT-002 | T004/T005/T029 | prueba_linea_tiempo.py; prueba_bench_linea_tiempo.py | Cota K y búsqueda verificadas |
| PR-LT-003 | T029 | bench_memoria.py; mediciones_memoria_juan.json | Medido; asignaciones Python, no RSS |
| PR-LT-004 | T020 | prueba_historia_partida.py::test_pr004_recorte_trabaja_solo_sobre_lo_revertido | Verificado |
| PR-LT-005 | T029/T032/T034 | main.py; bench_cierre.py; comparación de K en research.md | Comando estándar completo, K10 elegido |
| PR-LT-006 | T030 | bench_decisiones.py; mediciones_decisiones_juan.json | Comparaciones medidas; memoria de contenedores explícitamente parcial |
| PR-LT-007 | T029/T031 | bench_linea_tiempo.py; revision_sesion_k10_2026-11-13.json | EX-01: incumplido, 255/5 000 ≥20 ms; máximo 92,0115 ms |
| PR-LT-008 | ENT-001 | main.py; bench_cierre.py; prueba_bench_entrega.py | Integración real pequeña, salida configurable, entorno y fallos verificados |

Las evidencias JSON están en `documentacion/evidencia/`. El prototipo compartido
sigue aislado y no sustituye el contrato ni el formato 6 de producción. T037
queda cerrada con EX-01 funcional/documental; no certifica los presupuestos
20/50 ms. K no cambia. Ver [la decisión de cierre](../../documentacion/REVISION_SESION_BLOQUEADA.md).
