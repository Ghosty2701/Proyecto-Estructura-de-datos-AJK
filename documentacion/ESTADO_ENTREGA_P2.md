# Estado de entrega de Cripta Parte II

## Cierre vigente de alcance ? 2026-11-13

Por instruccion de Juan, se termina el intento de optimizar estrictamente las
latencias: **EX-01** deja fuera del cierre solicitado lograr todos los ciclos
<20 ms y todas las consultas <50 ms. Se conservan funciones, K=10, v6 y mediciones.
Esto no altera el PDF ni acredita cumplimiento academico de esos presupuestos.

Verificacion nueva del codigo conservado: **759 pruebas pasan**. Cripta-06,
5 000 acciones, 32 cazadores iniciales, 36 consultas: **255 ciclos >=20 ms**
(maximo 92,0115 ms) y **2 consultas >=50 ms** (maximo 63,5862 ms). Partida intacta,
cero HTTP en consultas, maximo nueve acciones reaplicadas, pico 396,63 MiB.
[JSON nuevo](evidencia/revision_sesion_k10_2026-11-13.json),
[regresion nueva](evidencia/revision_sesion_pruebas_2026-11-13.txt).

Confirmación previa a los commits: **759 pruebas pasan en 29,32 s**;
[salida completa](evidencia/revision_sesion_pruebas_completas_2026-11-13.txt).
Revisión de las cuatro listas de tareas y de los enlaces de entrega completada.
Los pendientes CI-005/007/008 son antecedentes del experimento rechazado.

T037 se cierra funcional y documentalmente con EX-01; los requisitos temporales
PR-LT-001/007 y PR-TC-001 permanecen identificados como incumplidos en esta carga.
**Avance estimado original: ~95 %**; alcance funcional cerrado con excepcion,
sin mas optimizaciones pendientes en este encargo.
[Diagnostico y decisiones](REVISION_SESION_BLOQUEADA.md).

## Registro anterior, conservado como historial

Las secciones siguientes describen la revision previa; sus pendientes de
optimizacion y cifras no sustituyen el cierre vigente de arriba.


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
- Captura optimizada de producción: comparte tuplas planas de escalares exactos,
  reutiliza registros vacíos y reserva el índice fijo de esquemas existente.
  No cambia K, estructuras elegidas ni formato de guardado v6.
- Ciclos oficiales corregidos: incluyen ejecutar y registrar la orden, creando
  puntos dentro del cronómetro. Se descarta la cifra anterior sin registro
  como aceptación de 20 ms; el punto inicial refleja la preparación del ensayo.
- **759 pruebas pasan**. Incluyen los 23 casos del apéndice B, configuración,
  guardado/replay y la integración real del benchmark en escala pequeña.

## Validación con K elegido

Cripta-06, versión `f9ed9afa683d`, catálogo `4b9e75a42be5`, 300 salas,
32 cazadores activos iniciales, semilla 2026, 5 000 acciones y 36 consultas.
Producción sin capturadores experimentales; GC habilitado, sin trazado de tiempos.

| Comprobación | Resultado |
|---|---|
| Consulta oficial | Máxima **31,9232 ms**, **0/36** consultas ≥50 ms |
| Memoria de proceso observada externamente | Pico **397,66 MiB**, incluye todo el proceso |
| Consulta sin efectos | Partida intacta; cero HTTP durante consultas |
| Ciclos oficiales completos con registro | **31/5 000 ≥20 ms**; máximo **39,8973 ms** |
| Ciclos sin crear punto | 0/4 500 excedidos; máximo **17,6771 ms** |
| Ciclos creando punto | 31/500 excedidos; mediana de ciclo **14,5394 ms** |

[Consulta y ciclos oficiales finales](evidencia/validacion_k10_captura_final.json),
[regresión](evidencia/pruebas_captura_final.txt).
La vida del jugador se amplía en la carga experimental para completar acciones;
los cazadores conservan sus datos. No se garantiza otra ejecución o secuencia.
Resolubilidad y viaje conservan evidencia oficial previa conforme a 200/5 ms;
no se presenta como medición nueva.

## Lo que falta para cerrar

1. Terminar de reducir los picos de creación de puntos en **producción**, conservando estado,
   v6, alias, azar e independencia. No hay evidencia para reemplazar el motor
   con ninguno de los prototipos ensayados.
2. Validar el ciclo completo <20 ms en la referencia y repetir consultas K10
   sobre la corrección final. No mover el costo fuera del cronómetro.
3. Cerrar T037/aceptación y actualizar las cifras de la entrega final.

K ya no es una decisión pendiente. No hacen falta nuevas capacidades ni terminar
los contratos CI del experimento rechazado. Aprobar pruebas funcionales y cumplir
consultas no certifica 20 ms. **Estimación global orientativa: ~95 %, no nota.**

## Equivalencia y mejora de captura

[ABBA final](evidencia/captura_final_abba.json): cuatro historias independientes
de 5 000 acciones, K10, 300 salas, 32 cazadores; control `4d61ebd`, reconstrucción
vigente en ambas variantes y GC automático habilitado. Los 501 puntos por
historia (2 004 en total) producen el mismo SHA256 de bytes v6. Consultas sin
efectos y sin HTTP; ninguno de los cuatro bloques excedió 50 ms.

| Captura | Mediana copia (ms) | Ciclos ≥20 ms |
|---|---|---|
| Control A | 13,7544 | 27 |
| Actual B | 13,3155 | 18 |
| Actual B | 11,8274 | 9 |
| Control A | 13,4027 | 24 |

La mediana promedio baja 7,4 %. Se conservan todos los máximos en el JSON;
la mejora no certifica el límite. [Regresión final](evidencia/pruebas_captura_final.txt).
El intento de mantenimiento GC manual se retiró: no mejoró el límite y añadió
costo a ciclos sin punto. Su [resultado descartado](evidencia/validacion_k10_gc_descartado.json)
se distingue de producción. No se modifica el GC del juego.

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
