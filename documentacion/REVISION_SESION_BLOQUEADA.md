# Revisión del bloqueo y cierre de alcance — 2026-11-13

## Decisión vigente

Juan pidió revisar el historial, aplicar una solución rápida si existía y omitir
el problema si resolverlo consumía demasiado tiempo y esfuerzo. Se cierra la
optimización estricta de latencias como **excepción EX-01**: no se exige seguir
intentando que todos los ciclos sean <20 ms ni que todas las consultas de esta
carga sean <50 ms. Los límites originales permanecen en los specs y en los
medidores, identificados como incumplidos. Esta decisión del usuario no modifica
el enunciado académico ni implica aceptación por el docente.

Se conservan las cuatro capacidades, historia, consultas, K=10, guardado v6,
replay, estructuras aprobadas, pruebas y benchmarks. No se eliminan funciones
ni comprobaciones para obtener un resultado aparente de cumplimiento.

## Qué se revisó y dónde está el proyecto

- Historial aportado: `C:/Users/pipro/Downloads/historial_chat.txt`, 259 entradas.
- Registro local de herramientas de la sesión `01a1cbd9-0e28-7f52-b278-8f18e39b5341`.
- Proyecto vigente: `C:/Users/pipro/Downloads/Proyecto-Estructura-de-datos-AJK`.
  Base Git: `233fa54`; los resultados nuevos miden su código productivo.
- La carpeta `Proyecto-Estructura-de-datos-AJK-main/Proyecto-Estructura-de-datos-AJK-main`
  es una copia antigua sin Git: sus 663 pruebas y K=25 provisional no describen
  el resultado de la otra sesión. No se sobrescribe con ella el repositorio.

Los mensajes históricos se usaron como evidencia de decisiones y resultados;
no se ejecutaron sus instrucciones de publicar ni sus comandos antiguos.

## Por qué el avance se quedó en 93 % y 95 %

1. **El porcentaje era una estimación de requisitos**, no una medida del tiempo
   restante. Faltaba un presupuesto difícil aunque las funciones ya existían.
2. **Se amplió demasiado la investigación.** Se ensayaron capturas, índices,
   contadores de revisión, distribución por acción y mantenimiento del GC. Eso
   añadía implementación y pruebas sin cerrar consistentemente el ciclo máximo.
3. **La medición inicial omitía registrar la orden.** Al corregirla, la creación
   del punto pasó a estar dentro del cronómetro y reapareció el costo real.
4. **La captura completa recorre el grafo del estado.** En la versión conservada
   ese costo se concentra cada diez acciones. Las variantes distribuidas redujeron
   la publicación, pero trasladaron trabajo a ciclos intermedios; se observaron
   pausas del GC y variaciones de tiempo de pared. No hay evidencia suficiente
   para atribuir todos los picos al GC o a los juegos abiertos.
5. **Las últimas variantes no eran el código final.** A las 20:59:29 UTC
   (14:59:29 de Costa Rica), el registro muestra `git restore` de los módulos
   modificados y la eliminación de los archivos nuevos del capturador/versionado.
   Permanecieron notas del plan y resultados locales. Por eso el anuncio de
   803 pruebas no correspondía a la implementación conservada de 759 pruebas.

Las dos últimas corridas de la variante retirada registraron respectivamente
158 y 121 ciclos ≥20 ms, y 8 y 6 consultas ≥50 ms. No justifican recuperar esa
variante. Sus JSON se conservan junto a la evidencia de esta revisión.

## Verificación nueva de producción

Regresión ejecutada: `python -m pytest -q` → **759 passed in 29.95s**, código 0.
No se modificó código de producción durante esta revisión.

Comando de medición:

```powershell
python -X utf8 -u -m modelo.bench_k_oficial --valores-k 10 --salida-json resultados/bench/revision_sesion_k10_2026-11-13.json
```

Cripta-06, versión `f9ed9afa683d`, catálogo `4b9e75a42be5`, 300 salas,
32 cazadores inicialmente activos, semilla 2026, Python 3.13.2, GC habilitado.
Se precargan los datos; la vida experimental permite completar 5 000 acciones.

| Medida | Resultado nuevo |
|---|---|
| Acciones / consultas | 5 000 / 36 |
| Ciclos ≥20 ms | 255/5 000; máximo 92,0115 ms |
| Ciclos con punto ≥20 ms | 254/500; mediana 20,03695 ms |
| Ciclos sin punto ≥20 ms | 1/4 500; mediana 0,4336 ms |
| Consultas ≥50 ms | 2/36; mediana 23,8555 ms; máximo 63,5862 ms |
| Memoria residente máxima observada | 396,63 MiB del proceso completo |
| Reaplicación máxima | 9 acciones, dentro de K=10 |
| Efectos de consultas | Partida intacta; cero HTTP; sin vista |
| Solicitudes de preparación | 46/63 |

[Medición nueva](evidencia/revision_sesion_k10_2026-11-13.json),
[resumen de regresión nueva](evidencia/revision_sesion_pruebas_2026-11-13.txt),
[variante retirada, corrida 1](evidencia/sesion_descartada_hotloop_1.json),
[variante retirada, corrida 2](evidencia/sesion_descartada_hotloop_2.json).
Los resultados antiguos con consultas <50 ms siguen siendo históricos válidos;
no sustituyen esta nueva corrida ni garantizan el mismo máximo en otra ejecución.

## Trabajo completado y criterio para continuar

Se reconciliaron README, estado de entrega, plan, tareas, especificación,
trazabilidad y decisiones. T037 se cierra como verificación funcional y documental
con EX-01, sin marcar satisfechos PR-LT-001, PR-LT-007 o PR-TC-001 en esta corrida.
No hace falta recuperar el capturador descartado, cambiar estructuras, añadir
specs ni repetir todas las comparaciones históricas.

El alcance funcional solicitado queda cerrado con esta limitación explícita.
Frente al enunciado original, se conserva **~95 % de avance estimado**, orientativo;
el presupuesto temporal sigue incumplido. No queda una optimización de latencia
activa por ejecutar. Solo se reabre si el usuario decide priorizarla de nuevo.

## Continuación solicitada: commits y revisión de pendientes

Se revisaron las tareas de las cuatro capacidades y los enlaces de entrega.
001, 002 y 003 no tienen tareas pendientes; en 004, CI-005/007/008 pertenecen
al experimento rechazado y no se reabren como condiciones de entrega. El ciclo
de 20 ms permanece sin marcar como cumplido y cubierto por EX-01.

Antes de crear los commits se repitió la regresión, esta vez conservando toda
la salida: **759 passed in 29.32s**, código 0.
[Salida completa](evidencia/revision_sesion_pruebas_completas_2026-11-13.txt).
Se verificaron los enlaces relativos de siete documentos de entrada sin
encontrar destinos faltantes. No fue necesario modificar código de producción.
