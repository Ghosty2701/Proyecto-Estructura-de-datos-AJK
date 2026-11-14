# Decisiones de diseño de Cripta

**Cierre vigente (EX-01, 2026-11-13):** por instruccion del usuario se termina
la optimizacion estricta de 20/50 ms tras descartar los intentos sin mejora.
Las funciones permanecen implementadas; los presupuestos incumplidos se declaran
en [la revision y evidencia nuevas](documentacion/REVISION_SESION_BLOQUEADA.md).
Las alusiones inferiores a optimizacion pendiente corresponden al estado anterior.


Entrada de entrega de P2 §7.1/7.2. El desarrollo completo de alternativas,
complejidades y evidencia está en el [Documento de Decisiones](documentacion/DOCUMENTO_DECISIONES.md).
El [estado vigente](documentacion/ESTADO_ENTREGA_P2.md) separa implementación,
mediciones y requisitos aún pendientes. Los ensayos históricos no son resultados nuevos.

| Problema de P2 | Decisión implementada | Especificación y plan | Evidencia y límites |
|---|---|---|---|
| §5.1 Ruta barata del cazador | Dijkstra con heap y tabla hash propios; región limitada por rango; empate por primer vecino de menor ID | [001 spec](specs/001-terreno-cazadores/spec.md), [plan](specs/001-terreno-cazadores/plan.md) | [Terreno/cazadores](documentacion/DOCUMENTO_DECISIONES.md#parte-ii--terreno-y-cazadores-2026-11-09); costos, empates y región comprobados |
| §5.2 Invalidación | Revisión de conexiones y caché propia acotada; misma decisión que recalcular, sin persistir resultados derivados | [001 spec](specs/001-terreno-cazadores/spec.md), [plan](specs/001-terreno-cazadores/plan.md) | [Caché compartida](documentacion/CACHE_RUTAS_JUAN.md); equivalencia y trabajo ahorrado, sin garantía universal de tiempo |
| §5.3 Mapa conocido | Salas por posición e índice propio; recuerdo compartido por puerta; rutas solo sobre conocimiento | [002 spec](specs/002-niebla-viaje/spec.md), [plan](specs/002-niebla-viaje/plan.md) | [Niebla/viaje](documentacion/DOCUMENTO_DECISIONES.md#parte-ii--niebla-de-guerra-y-viaje-ir-a-2026-11-09); antorcha/undo/guardado/replay comprobados |
| §5.4 Resolubilidad | Cierre incremental con FIFO propia y puertas pendientes por llave; diagnóstico determinista con componentes propias | [003 spec](specs/003-verificar-resolubilidad/spec.md), [plan](specs/003-verificar-resolubilidad/plan.md) | [Resultado](documentacion/DOCUMENTO_DECISIONES.md#parte-ii--resolubilidad-implementada-y-verificada-2026-11-09); referencia medida <200 ms |
| §5.5 Historia | Reconstrucción hacia adelante desde puntos cada K=10 acciones, en registros inmutables por ID; búsqueda binaria propia; formato v6 con todos los puntos | [004 spec](specs/004-linea-tiempo/spec.md), [plan](specs/004-linea-tiempo/plan.md) | [Consolidado §5.5](documentacion/DOCUMENTO_DECISIONES.md#parte-ii--55-línea-de-tiempo-y-puntos-de-control-consolidado): alternativas, cambios frente al plan (D-LT-08, K) y evidencia; 20/50 ms no se cumplen (EX-01) |
| §5.6 Revisión de P1 | Se mantienen agenda (heap) y retroceso por deltas, con datos de la carga nueva; se modifica el guardado (v3 → v6) y se añade el copiador de puntos | [004 plan](specs/004-linea-tiempo/plan.md) | [Consolidado §5.6](documentacion/DOCUMENTO_DECISIONES.md#parte-ii--56-revisión-de-las-decisiones-de-la-primera-parte-consolidado): tabla antes/después de cada decisión de P1 |

K=10 fue elegido por Juan tras comparar consultas y memoria. Cargar sin
`--checkpoint-cada` conserva el K de la sesión guardada; no se reescribe su historia.
Los resultados que motivaron esta elección están en
[la comparación de producción](documentacion/REGISTROS_IGUALES_JUAN.md).

Los prototipos incremental/versionado/índice inverso quedaron rechazados para
producción. Sus informes se conservan como antecedentes, no como funcionalidades
faltantes ni condiciones de entrega. No se activan en juego, replay ni guardado.

Completar una medición no equivale a cumplir su límite: la aceptación de 20 ms
se mantiene abierta. La [revisión de pendientes](documentacion/REANALISIS_ENTREGA_P2.md)
identifica qué queda por implementar o verificar.
