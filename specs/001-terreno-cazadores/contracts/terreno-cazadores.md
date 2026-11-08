# Contratos — Terreno y cazadores

**Fecha**: 2026-11-08. Contratos previstos; las interfaces nuevas aún no están implementadas.
Referencias: [especificación](../spec.md), [modelo de datos](../data-model.md).

## Datos de entrada y versiones

| Dato | Procedencia | Interpretación |
| --- | --- | --- |
| costo de salida | Esqueleto versionado de la cripta | Entero ≥ 1; ausente equivale a 100; simétrico |
| comportamiento cazador y rango | Catálogo con versión global | Rango entero explícito; no inventar un valor si falta |
| puertas actuales | Estado vivo de la partida | Aperturas y cierres vigentes, incluidos los automáticos |

El cargador normaliza costo ausente y rechaza datos que no cumplan el dominio de costos.
Comprueba coherencia de sentidos sin introducir reglas particulares por ID de cripta.
El contrato HTTP exacto sigue siendo el del servicio; esta capacidad no añade un endpoint.
La búsqueda no abre solicitudes de contenido ni consume presupuesto para calcular rutas.

## Frontera de búsqueda del modelo

Interfaz lógica prevista: `buscar_ruta(origen, objetivo, rango)` devuelve ResultadoRuta.
Los nombres se concretan en tareas; las propiedades del contrato son obligatorias.

- Entrada: salas del esqueleto del modelo con sus listas de salidas, costos y puertas actuales.
- Salida: primer paso y costo mínimo dentro del rango, o ausencia de ruta dentro del rango.
- Desempate: menor ID del primer vecino entre rutas mínimas, independiente de enumeración.
- Límite: no explorar costos superiores al rango ni preparar todos los registros del mapa.
- Efectos: no mueve actores, modifica puertas, ejecuta eventos, descarga contenido, consume
  azar o avanza el reloj. Las métricas opcionales de benchmark no cambian el resultado.
- Corrección: una búsqueda de referencia desde cero y una consulta reutilizada dan la
  misma decisión sobre el mismo estado. No se confunde el mapa del jugador con el real.

## Fronteras de las estructuras auxiliares

| Estructura | Operaciones lógicas | Garantías |
| --- | --- | --- |
| TablaDistancias | Buscar ID, insertar registro, actualizar registro existente | Igualdad por clave; crecimiento aprobado; referencias estables al redistribuir |
| HeapRutas | Insertar, extraer mínimo, mejorar etiqueta | Una entrada por sala; índice del registro correcto; orden determinista |
| Último resultado del actor | Consultar validez y reemplazar resultado | Un solo resultado; no retiene el heap/tabla; invalida en contexto incompatible |

Son estructuras propias; no se resuelven mediante dict/set, heapq o equivalentes. Los
contratos no exigen borrado individual de registros de la hash para esta capacidad.

## Ejecución del turno de cazador

1. Aplicar las condiciones heredadas de actor vivo y turno válido.
2. Si comparte sala con el jugador, atacar conforme a P1.
3. En otro caso, validar el último resultado o buscar desde su sala hasta la del jugador.
4. Sin ruta dentro del rango, esperar con costo base 100.
5. Con ruta, ejecutar un paso abierto y programar el intervalo con su costo de tránsito.

Las decisiones corresponden al instante del turno, después de procesar los eventos que
le preceden según la agenda existente. No se ejecuta una ruta entera ni se abren puertas.
Errantes y rastreadores mantienen su elección de destino; su movimiento usa el costo de
la salida. Atacar, esperar y otras acciones conservan sus costos de P1.

## Invalidez, reversión y persistencia

La consulta reutilizada comprueba origen, objetivo, rango y revisión de conexiones/costos.
Invalidar no añade acciones al log ni consume tiempo. Una puerta abierta fuera de la ruta
anterior puede crear un camino mejor y debe invalidar igual que una puerta de esa ruta.

Guardar/cargar conserva costo, rango, reloj, eventos y azar mediante esquema versionado.
La lectura selectiva muestra costo y rango sin restaurar toda la partida. Un guardado
antiguo incompatible se rechaza explícitamente, sin borrado manual ni carga silenciosa.
Los resultados derivados se descartan al cargar o retroceder y pueden recalcularse.

## Interfaz de usuario y modos existentes

- La sala actual muestra el costo de cada salida y distingue cazadores por comportamiento.
  No revela datos que correspondan a salas desconocidas cuando se integre la niebla.
- Los movimientos y órdenes de P1 siguen usando su ejecutor común; no se añade otro formato
  de comando para mover por terreno ni un generador de azar independiente.
- `--replay` reproduce sin instanciar vista y conserva las mismas decisiones y tiempos.
- `--bench` mide sin vista ni HTTP dentro del cronómetro y añade las cargas del plan.
- No se crean en esta capacidad `--verificar`, «ir a» o «historia»; pertenecen a otras specs.

## Evidencia y fallos

Los escenarios AC-TC-001 a AC-TC-019 se vinculan a pruebas o logs que citan los FR-TC.
Se comprueban errores de contrato antes de introducir parcialmente un estado inválido.
No se inventa una semántica nueva para todo posible dato malformado del servicio.
Un benchmark sin la referencia oficial se identifica como sintético; no certifica 20 ms
para una cripta aún no identificada. Cambiar las estructuras acordadas requiere al usuario.
