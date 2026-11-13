# Estado de entrega de Cripta Parte II

Revisión vigente: **2026-11-13**. La fuente de prioridades es el
[reanálisis del enunciado y los specs](REANALISIS_ENTREGA_P2.md).
Las corridas anteriores se conservan como históricas, sin reemplazar este estado.

## Implementado y verificado

- Las cuatro capacidades: terreno/cazadores, niebla/viaje, resolubilidad e historia.
- **K predeterminado 10**, elegido por Juan y aplicado a nuevas partidas/replay.
  Cargar sin opción conserva el K guardado; v6 mantiene la historia completa.
- `--bench` incluye historia por defecto; alias anterior compatible, salida
  configurable, entorno en JSON y errores de medición/exportación informados.
- Entradas raíz `DECISIONES.md` y `PROMPTS_LLM.md`, README y trazabilidad actualizados.
- **751 pruebas pasan**. Incluyen los 23 casos del apéndice B, configuración,
  guardado/replay y la integración real del benchmark en escala pequeña.

## Validación con K elegido

Cripta-06, versión `f9ed9afa683d`, catálogo `4b9e75a42be5`, 300 salas,
32 cazadores activos iniciales, semilla 2026, 5 000 acciones y 36 consultas.
Producción sin capturadores experimentales; GC habilitado, sin trazado de tiempos.

| Comprobación | Resultado |
|---|---|
| Consulta oficial | Máxima **35,9904 ms**, **0/36** consultas ≥50 ms |
| Memoria de proceso observada externamente | Pico **400,14 MiB**, incluye todo el proceso |
| Consulta sin efectos | Partida intacta; cero HTTP durante consultas |
| Ciclos sintéticos con registro, misma escala/K | **14/5 001 ≥20 ms**; máximo **40,3269 ms** |
| Ciclos sin crear punto | 0/4 501 excedidos; máximo **1,1315 ms** |
| Ciclos creando punto | 14/500 excedidos; captura máxima **39,9700 ms** |

[Consulta oficial](evidencia/validacion_k10_entrega.json),
[ciclos](evidencia/ciclos_k10_entrega.json),
[regresión](evidencia/pruebas_entrega_p2.txt).
La vida del jugador se amplía en la carga experimental para completar acciones;
los cazadores conservan sus datos. No se garantiza otra ejecución o secuencia.
Resolubilidad y viaje conservan evidencia oficial previa conforme a 200/5 ms;
no se presenta como medición nueva.

## Lo que falta para cerrar

1. Corregir los picos de creación de puntos en **producción**, conservando estado,
   v6, alias, azar e independencia. No hay evidencia para reemplazar el motor
   con ninguno de los prototipos ensayados.
2. Validar el ciclo completo <20 ms en la referencia y repetir consultas K10
   sobre la corrección final. No mover el costo fuera del cronómetro.
3. Cerrar T037/aceptación y actualizar las cifras de la entrega final.

K ya no es una decisión pendiente. No hacen falta nuevas capacidades ni terminar
los contratos CI del experimento rechazado. Aprobar pruebas funcionales y cumplir
consultas no certifica 20 ms. **Estimación global orientativa: ~95 %, no nota.**

## Reproducir

```powershell
python -m pytest -q
python main.py --bench --repeticiones 1
python main.py --bench --repeticiones 1 --salida-bench resultados/defensa
python -m modelo.bench_k_oficial --valores-k 10 --salida-json resultados/k10.json
```

El benchmark completo puede tardar varios minutos. El comando estándar deja
resultados nuevos en `resultados/bench`, ignorado en Git. Las pruebas de CLI
usan cargas pequeñas para comprobar integración; no sustituyen los ensayos
largos. La evidencia de arriba sí corresponde a 5 000 acciones.

El traslado desde una copia sin Git está declarado en las tareas. No se
reconstruye ese historial ni se afirma aceptación del proyecto mientras falte 20 ms.
