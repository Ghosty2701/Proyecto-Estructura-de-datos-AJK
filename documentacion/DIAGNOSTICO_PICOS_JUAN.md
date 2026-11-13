# Diagnóstico de ciclos lentos (2026-11-13)

Este tramo identifica causas antes de otra optimización. Cambia únicamente
el diagnóstico, sus pruebas y evidencia; conserva el motor y K=25 provisional.

## Método

300 salas sintéticas, 32 cazadores, semilla 2026, 5 000 acciones vigentes y
5 001 ciclos ejecutados por el retroceso. K=10/25. El reloj abarca orden,
registro y captura. GC permanece habilitado, con sus umbrales originales.
Un callback registra tiempo y cantidad de colecciones por generación; se
retira al terminar, incluso ante error. Se conservan resúmenes de todos los
excedidos y detalle de solo los diez peores por K, sin exportar 5 000 muestras.

El observador añade sobrecarga: **no certifica los límites**. El tiempo de CPU
del hilo mostró cuantización de 15,625 ms; restarlo del tiempo de pared no
permite atribuir cada diferencia al sistema operativo. GC está incluido en la
captura y en el ciclo: esas columnas no se suman como fases independientes.

```powershell
python -X utf8 -u -m modelo.bench_picos --salida-json resultado.json
```

## Hallazgos

| K | Ciclos lentos | Con punto | Con GC | Con generación 2 | Tiempo lento total (ms) | En captura (ms) | En GC (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 | 52 | 52 | 52 | 10 | 1 407,626 | 1 379,326 | 207,164 |
| 25 | 19 | 19 | 19 | 4 | 454,355 | 443,387 | 75,484 |

- La captura explica **98,0 % / 97,6 %** del tiempo acumulado de los ciclos
  lentos. El resto de orden/eventos/registro promedia 0,54/0,58 ms en esos ciclos.
- GC coincide con todos los excedidos, pero representa **14,7 % / 16,6 %** de
  su tiempo acumulado. Coincidencia no significa que explique todo el retraso.
- Las pausas de generación 2 en los ejemplos lentos duran unos 13–16 ms y se
  suman al trabajo de captura. Hay también picos grandes sin generación 2.
- El peor K=10 duró 77,123 ms, con 76,222 ms de captura, unos 5,364 ms de GC
  y 31,25 ms de CPU del hilo. El dato sugiere factores adicionales al trabajo
  del recolector; no demuestra por sí solo cuál fue el retraso externo.

[Datos y diez ejemplos por K](evidencia/diagnostico_picos_juan.json).
No se modifica el recolector, no se desplaza su costo fuera del ciclo y no se
declara que los eventos o las rutas sean el cuello de botella de esta carga.

## Revisión de la plantilla heredada

Se midió el prototipo existente `estado_compartido.py` contra la captura actual
en el mismo estado tras 5 000 acciones. ABBA aislado de 20 capturas por variante,
GC habilitado y recolección entre muestras fuera del cronómetro; resumen y azar
reconstruidos comprobados. Preparación con solo punto inicial (K=10 000).

| Captura | Mediana (ms) | p95 (ms) | Máxima (ms) |
|---|---:|---:|---:|
| actual | 18,245 | 22,776 | 23,858 |
| plantilla heredada | 25,236 | 28,981 | 29,258 |

Una exploración preliminar también favoreció la actual (16,80 frente a 21,15
ms); el archivo conserva la ejecución reproducida por el nuevo comando.
El prototipo mantiene grafos mutables y este ensayo no valida historia completa,
guardado, memoria ni consulta oficial. **No se integra ni se presenta como solución.**
[Resumen](evidencia/exploracion_plantilla_actual_juan.json).

```powershell
python -X utf8 -u -m modelo.bench_picos --comparar-plantilla --salida-json resultado.json
```

## Siguiente decisión

La captura actual sigue visitando el estado completo aun si reutiliza la mayor
parte de su salida. Optimizar únicamente la ruta de eventos o responsabilizar
solo a GC no atiende ese costo. No hay evidencia para seguir acumulando ajustes
pequeños sin cambiar la cantidad de trabajo.

Se presentan dos rutas **pendientes de elección**:

1. Captura incremental versionada: IDs estables y seguimiento de cambios para
   evitar recorrer todo el estado en cada punto. Requiere especificar registro
   de mutaciones, listas, altas/bajas, undo, carga y reconstrucción sin superar K.
2. Separación estático/mutable con registros especializados: definir y proteger
   lo inmutable, distinto del prototipo heredado, para capturar menos campos.

La primera es la recomendación de investigación, no una mejora demostrada ni
una estructura ya aprobada. Antes de implementarla se ampliará la capacidad
004 y se concretarán sus estructuras con el usuario conforme a AGENTS.md.
Se exigirá una prueba acotada con equivalencia y ciclos completos antes de
integrarla; no basta otra mejora de mediana.

**699 pruebas pasan**, incluidas restauración de callbacks/umbrales y salida
ante error. [Regresión](evidencia/pruebas_diagnostico_picos_juan.txt).
Funcionalidad del juego: implementada y verificada; presupuestos de ciclos,
K definitivo y aceptación final: pendientes. Avance global estimado: **93 %**.
