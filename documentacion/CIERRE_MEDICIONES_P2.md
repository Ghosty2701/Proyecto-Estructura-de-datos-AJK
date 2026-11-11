# Cierre de mediciones conjuntas y documentación independiente de K

Fecha de revisión: 2026-11-11. Los dos apartados solicitados por Juan están
completados: ejecución conjunta con evidencia nueva y documentación que no
depende de elegir K. Esto no declara terminado el proyecto ni cumplidos sus
presupuestos de tiempo.

## Ejecución y evidencia

```powershell
python main.py --bench --bench-linea-tiempo --repeticiones 1
python -m pytest -q
```

La corrida conjunta terminó con código 0. Incluye 120 consultas repartidas
en diez escenarios, diez escenarios de memoria, cuatro de persistencia y nueve
comparaciones de reconstrucción/agenda/retroceso. Consultas, memoria y
persistencia usan 5 000 acciones vigentes; cada bloque declara su alcance.
Semilla 2026, una ronda general, Python 3.13.2, Windows. La ronda de memoria
usa trazado y la de tiempos se ejecuta separadamente sin él. No hay red ni vista
en estas cargas sintéticas. La regresión posterior aprobó **663 pruebas**.

- [Datos completos de esta corrida](evidencia/mediciones_linea_tiempo.json).
- [Salida de la línea de tiempo](evidencia/bench_linea_tiempo.txt).
- [Salida de la invocación completa](evidencia/bench_conjunto_completo_juan.txt).
- [Entorno y SHA-256 del código y evidencia](evidencia/entorno_cierre_juan.json).
- [Regresión completa](evidencia/pruebas_linea_tiempo.txt).

Se verificaron cantidades de escenarios, equivalencia, estado intacto, ausencia
de HTTP, separación de memoria/tiempos y publicación completa del JSON sin
archivo temporal pendiente. El código 0 indica que la medición terminó; no
significa que se cumplan 20/50 ms. Una ronda no caracteriza el peor caso ni
justifica K por sí sola. Las corridas históricas se conservan con sus fechas.

## Lectura de resultados

La tabla siguiente reúne datos de esta misma corrida con 32 cazadores,
200 salas y K constante. Consulta máxima: 12 destinos. Memoria retenida:
asignaciones Python tras GC, no RSS. Los ciclos incluyen acción y registro,
con copia cuando corresponde; son 5 001 acciones ejecutadas, incluida una
revertida con pergamino. No se atribuyen todos los picos únicamente a la copia.

| K | Consulta máxima ms | Consultas ≥50 ms | Memoria MiB | Copia máxima ms | Ciclos ≥20 ms |
| --- | --- | --- | --- | --- | --- |
| 10 | 104,241 | 6/12 | 338,90 | 657,169 | 503/5001 |
| 25 | 50,181 | 1/12 | 136,83 | 265,829 | 200/5001 |
| 50 | 65,830 | 6/12 | 69,45 | 253,405 | 101/5001 |
| 100 | 151,917 | 8/12 | 35,75 | 146,990 | 52/5001 |

**Los presupuestos siguen incumplidos en las muestras indicadas.** No se ajusta
el umbral ni se cambia K. La alternativa con solo el punto inicial ahorra
memoria pero requiere hasta 4 999 acciones re-simuladas; sus datos se conservan
en el JSON, junto a los escenarios sin cazadores.

## Documentación cerrada sin depender de K

Se revisaron README, contrato, especificación, plan, modelo de datos,
investigación, Documento de Decisiones, guía de validación y bitácora de prompts.
Se agregó una [matriz de trazabilidad](../specs/004-linea-tiempo/trazabilidad.md)
para los 16 FR y 7 PR, sincronizando los escenarios con la especificación.
Los archivos de código/pruebas citados existen y se revisaron los enlaces
locales. Los estados documentales ya distinguen implementación funcional,
medición y aceptación pendiente.

La revisión de §5.6 compara agenda/retroceso de P1 con las cargas nuevas,
incluidos límites y diferencias de equipo/carga; §5.5 conserva el diseño,
alternativas y evidencia. El prototipo compartido sigue aislado y no cambia
el formato 6 ni la partida normal. No se adoptó una estructura nueva ni se
eligió K. Las secciones antiguas del Documento de Decisiones son históricas;
este cierre y los datos conjuntos representan la corrida actual.

## Trabajo reservado para la siguiente etapa

Optimizar y volver a verificar consultas de 50 ms y ciclos de 20 ms, elegir K
con aprobación explícita y actualizar su justificación final. K sigue en 25
provisional. T035–T037 conservan pendientes dependientes de esa decisión y
de la aceptación de rendimiento, aunque la documentación independiente y la
regresión estén completas. El historial Git debe revisarse en el repositorio
original. El trabajo se inició en una copia sin `.git` y después se trasladó
sobre `4c34c88`; los nuevos commits registran ese traslado, no recrean el
historial previo de los ensayos.
