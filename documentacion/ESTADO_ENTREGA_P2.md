# Estado de entrega de Cripta Parte II

Revisión del 2026-11-11. Esta página resume el estado actual; los ensayos
fechados en el Documento de Decisiones conservan sus resultados históricos.

La ejecución conjunta y la documentación independiente de K están completadas.
Datos, validaciones y límites en el [informe de cierre](CIERRE_MEDICIONES_P2.md).
Regresión posterior: **663 pruebas aprobadas**.

## Funcionalidad verificada

- Terreno ponderado, cazadores y decisiones ante cambios de puertas.
- Niebla, memoria de puertas, antorcha y viaje por conocimiento del jugador.
- Resolubilidad, informes, `--verificar` y `--forzar`.
- `historia <t>`, `historia #k`, replay con `--hasta`, configuración de puntos,
  interacción con pergaminos y persistencia de toda la línea en formato 6.
- Estructuras aprobadas conservadas. El prototipo compartido no se usa en
  partidas normales, guardados ni replay.

La [matriz de trazabilidad](../specs/004-linea-tiempo/trazabilidad.md) relaciona
requisitos, escenarios, tareas, código y pruebas. La regresión y las mediciones
son evidencias diferentes: aprobar pruebas funcionales no certifica tiempos.

## Evidencia y reproducción

Desde la carpeta que contiene `main.py`:

```powershell
python -m pytest -q
python main.py --bench --bench-linea-tiempo --repeticiones 1
```

La corrida conjunta mide consultas, memoria, copias, persistencia, reconstrucción
adelante/atrás y agenda/retroceso. Guarda datos nuevos en
`evidencia/mediciones_linea_tiempo.json` y salida en `evidencia/bench_linea_tiempo.txt`.
El registro completo de la invocación está en `evidencia/bench_conjunto_completo_juan.txt`.
La memoria usa `tracemalloc` en ejecuciones separadas de los tiempos; son
asignaciones Python, no memoria RSS. El JSON conserva estadisticas y entorno, sin muestras individuales.

## Pendientes reservados para la siguiente etapa

1. Resolver y repetir la verificación de 50 ms por consulta.
2. Resolver los ciclos de 20 ms o más con registro y cazadores.
3. Elegir explícitamente el K definitivo con los resultados completos. El
   valor de producción sigue siendo 25 **provisional**.
4. Incorporar esa decisión en README, investigación y Documento de Decisiones,
   y cerrar la aceptación. No se declara Parte II terminada mientras falte esto.

Estos puntos no se resuelven cambiando los umbrales ni ocultando muestras.
La investigación de plantilla compartida es una alternativa experimental;
sus pruebas y medidas no sustituyen la aceptación del modo de producción.

## Límite de esta revisión documental

Los ensayos se realizaron en una copia descargada sin `.git`. Los cambios se
trasladaron después al repositorio original sobre la base `4c34c88`, que estaba
limpia. Los commits de traslado son nuevos; no reconstruyen retrospectivamente
el historial de implementación de esa copia. La regresión del traslado se conserva;
los manifiestos de hashes se retiraron por no ser entregables exigidos.

El cierre documental independiente de K comprende contratos, comandos, formato,
métodos, límites, evidencia y trazabilidad. La justificación del K definitivo
y la declaración de cumplimiento de tiempos quedan pendientes deliberadamente.
