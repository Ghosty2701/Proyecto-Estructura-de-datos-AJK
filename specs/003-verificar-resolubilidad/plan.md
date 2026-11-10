# Plan: Verificación de resolubilidad

**Fecha**: 2026-11-09. **Rama real**: `main`.
**Capacidad activa de spec-kit**: `003-verificar-resolubilidad`.
**Entrada**: [spec.md](spec.md). **Estado**: planificación completada, sin implementación.
**Decisiones**: D-RS-01 a D-RS-07, todas A, aprobadas por el usuario; certificado
de grupo y emparejamiento único de recíprocas también aprobados. Alternativas,
pruebas de razonamiento y descartes: [research.md](research.md).

## Resumen

Verificar si puede obtenerse la llave de salida y alcanzarse la salida mediante
una puerta que la requiere. Se procesa el esqueleto y ubicaciones sin contenido,
actores, motor ni vista. Un cierre incremental obtiene llaves y reactiva solo
sus puertas pendientes. El resultado negativo incluye llaves no obtenibles,
frontera y certificados de grupos circulares con alternativas y ciclo concreto.
Las reglas están en spec.md; este plan concreta la implementación futura.

## Contexto técnico

| Aspecto | Diseño |
| --- | --- |
| Lenguaje y entorno | Python 3.11+, CLI/MVC existentes; Windows local de referencia. |
| Dependencias | Ninguna nueva en producción; HTTP existente; pytest como herramienta de pruebas. |
| Topología | Arreglo de salas compactas y listas de salidas; registro compartido por puerta física identificable, D-RS-01A. |
| Índices | Hash propio de enteros y texto a posiciones, doble hashing, reserva inicial potencia de dos a carga máxima 70 %, paso impar y sondeo acotado, D-RS-02/03A. |
| Trabajo pendiente | FIFO propia con lista/cursor; listas de llaves por sala y puertas pendientes por llave, D-RS-04/05A. |
| Diagnóstico | Registros de reglas/procedencia, incidencias directas/inversas, marcas y pilas propias, D-RS-06A. |
| Ubicaciones | En memoria durante la ejecución, sin nueva persistencia, D-RS-07A. |
| Objetivo | PR-RS-001: <200 ms locales, sin red/renderizado, en la mayor cripta publicada al medir. |
| Escala | S salas, E salidas, K IDs de llave, U ubicaciones, L longitud total de identificadores procesados. |

## Algoritmo y determinismo

1. Obtener generales, páginas del esqueleto y ubicaciones por FuenteDatos;
   comprobar versión y presupuesto. Preparar listas e índices directamente,
   sin construir el AVL ni las entidades de partida para verificar.
2. Normalizar salidas y puertas una sola vez con la regla del equipo. Compartir
   una puerta entre recíprocas compatibles de emparejamiento único; conservar
   arcos independientes y advertir si la correspondencia es ambigua. Compartir
   la misma normalización con el cargador, no jugar otra topología.
3. Marcar/encolar la sala inicial. Al procesar una sala, obtener sus llaves antes
   de revisar salidas. Cada primera obtención activa solo los pendientes de esa
   llave. Cada sala se descubre una vez. Completar el cierre para el informe.
4. Comprobar la condición completa de victoria, no solo la sala alcanzada.
   Una salida desde región alcanzada hacia la sala de salida, habilitada y que
   requiere la llave de salida obtenida, aporta el acceso requerido.
5. Para negativo, construir frontera sobre el cierre real, sin duplicar puertas
   identificadas. Imprimir tablas compartidas de ubicaciones y alternativas
   con referencias, evitando repetir U ubicaciones por cada puerta.
6. Diagnóstico circular: recorrido físico ignorando solo cierres con llave
   válida, cierre hipotético con llaves físicamente aisladas disponibles y grafo
   negativo residual con TODAS las alternativas. Kosaraju iterativo propio
   obtiene componentes sin enlaces salientes. Por cada componente pertinente,
   elegir una llave k, ubicación r y camino r → k dentro de ella; k → r completa
   el ciclo concreto. El informe incluye el grupo cerrado y sus reglas/puertas,
   sin presentar cada flecha entre llaves como individualmente inevitable.

El diagnóstico usa arreglos privados; nunca concede llaves reales, acciones,
tiempo, exploración o azar. La conectividad de una llave es existencial entre
ubicaciones, pero el certificado conserva todas sus ubicaciones posibles.
Orígenes/ubicaciones físicamente aislados y barreras cerradas sin llave figuran
como imposibilidades estructurales, no como ciclos. La demostración y los
contraejemplos descartados están en research.md.

Orden: salas según páginas y orden de respuesta estable; salidas N/S/E/O;
ubicaciones según respuesta; FIFO de descubrimiento y registros asignados en
ese orden. Recorridos iterativos y selección de testigos siguen esos índices.
No ordenar con sorted/list.sort, recorrer casillas hash para decidir el informe
ni consumir random del juego. Misma entrada/versiones produce mismo informe.

## Complejidad prevista y límites

Con posiciones resueltas, preparación de incidencias, cierres, componentes y
testigos cuestan O(S+E+K+U). Hay un número constante de recorridos globales,
no uno por llave. Restringir cada extracción a su componente disjunta;
inicializar marcas una vez, no un arreglo global por componente. La salida
también debe ser lineal mediante tablas compartidas, sin enumerar todos los
ciclos simples posibles.

Los índices aportan coste esperado aproximadamente lineal, más L y sondeos;
no se promete peor caso lineal con colisiones. Memoria O(S+E+K+U+L). Si cada
llave tiene una ubicación, U=K; no asumirlo por el esquema HTTP.
La inicialización de la partida puede construir el AVL heredado con los mismos
datos, sin repetir HTTP; ese coste no pertenece al verificador puro y se
informará aparte si se mide. Medir toda la preparación local del verificador,
sin esconderla detrás del temporizador del cierre.

Las decisiones son teóricas hasta ejecutar --bench. No se acreditan 200 ms,
crecimiento ni ventajas con las mediciones anteriores de terreno/niebla.

## Integración y estructura del proyecto

| Archivo o área prevista | Responsabilidad | Requisitos |
| --- | --- | --- |
| `modelo/verificacion.py` | Entrada normalizada, cierre y resultado puro; certificados, componentes y procedencia. | FR-RS-001 a 009, 013, 015; PR-RS-002 |
| `modelo/indice_llaves.py` | Índice propio de texto; reutilizar IndiceSalas sin convertir la tabla especializada de distancias en caché genérica. | FR-RS-005/009/015; PR-RS-002 |
| `adaptadores/fuente_datos.py`, `cliente_http.py`, `modo_offline.py` | Operación ubicacion_llaves; presupuesto y errores; archivo offline equivalente. | FR-RS-001/014/015 |
| `adaptadores/servicio_cripta.py` | Carga de datos de verificación en listas, validación de versión y entrega reutilizable al iniciar. | FR-RS-001/014/015 |
| `controlador/cargar_partida.py` y normalización compartida | Construir partida desde datos validados, mismas puertas, sin repetir solicitudes ni alterar niebla inicial. | FR-RS-007/010/011/013/014 |
| `main.py` | --verificar, --forzar, exclusión de modos, salida textual y bloqueo previo. | FR-RS-010/011/012 |
| `modelo/bench_resolubilidad.py`, integración con bench existente | Incremental frente a referencia repetida; preparación/cierre/diagnóstico/total; cargas sintéticas y oficial. | PR-RS-001/002/003 |
| `Pruebas/` | Nuevos archivos de aceptación/modelo/CLI/HTTP/offline y regresión necesaria. | AC-RS-001 a 020 |

La normalización puede permanecer en un módulo propio del modelo dentro de
`verificacion.py`; no incorporar otra estructura ni regla de juego. Mantener
la validación vigente de simetría de costes de FR-TC-001, P2 §3.1: el coste no
identifica una puerta, pero una pareja física identificada debe conservar las
reglas ya aprobadas de terreno. Los cambios necesarios se expresarán en tareas.

## Comprobación de la constitución antes y después del diseño

| Principio | Comprobación de diseño final |
| --- | --- |
| I. Estructuras manuales | D-RS-01 a 07 aprobadas; sin dict/set como índice, heapq, bisect, collections ni bibliotecas de grafos. |
| II. Determinismo | Orden explícito de páginas/direcciones/registros y selección de testigos; sin azar de partida. |
| III. MVC y modos sin vista | Verificador puro; HTTP en adaptadores; CLI imprime sin VistaConsola, actores o motor. |
| IV. Datos externos | Datos de fuente HTTP/offline; ninguna respuesta por ID concreto. |
| V. Presupuesto/versiones | _get cuenta intentos; validación de versión y carga compartida; no nueva caché persistida. |
| VI. Rendimiento | Complejidad y límites descritos; comparaciones y evidencia previstas, ejecución pendiente. |
| VII. Especificación anterior | Spec y aclaraciones se confirman antes del código; no hay implementación de esta capacidad. |
| VIII. Trazabilidad | Matriz de cobertura documental abajo; tareas y enlaces de código/pruebas serán la fase siguiente. |
| IX. Prompts | Elecciones y aclaraciones registradas por bloque con respuesta literal. |

**Resultado**: controles de diseño satisfechos; investigación e interpretaciones
cerradas. No se solicita ninguna excepción. Esto no sustituye pruebas de
ejecución ni mediciones finales. No existe extensions.yml con hooks aplicables.

## Cobertura para la descomposición en tareas

| Trabajo | Requisitos | Escenarios |
| --- | --- | --- |
| Preparación, índices, datos y ubicaciones | FR-RS-001/014/015 | AC-RS-007/017/018/019/020 |
| Cierre, orden y victoria | FR-RS-002/003/004/005/009 | AC-RS-001 a 007, 011, 016 |
| Frontera, aislamiento y certificado circular | FR-RS-006/007/008/009 | AC-RS-003/004/008/009/010/011/012 |
| Modos, forzar y no mutación | FR-RS-010/011/012/013 | AC-RS-013/014/015/016 |
| Mediciones y comparación de referencia | PR-RS-001/002/003 | SC-RS-005 y cargas de quickstart |

No se marca ningún escenario como ejecutado. tasks.md deberá enlazar cada
escenario con tareas verificables y posteriormente código y prueba/log.

## Validación y mediciones previstas

Cubrir los 20 escenarios y variantes de rutas alternativas, llaves en varias
ubicaciones, recíprocas únicas, paralelas ambiguas y ausencia de llave. Validar
el certificado completo, no solo que aparezca la palabra ciclo. Comprobar que
el cargador y el verificador normalizan la misma puerta y no modifican niebla.

Comparar con cierre por recorridos repetidos en casos pequeños y cargas con
llaves encadenadas. La referencia lenta pertenece a pruebas/bench, no producción.
Medir preparación, cierre, diagnóstico, informe y total; excluir red y vista.
Identificar la mayor cripta publicada al medir y registrar versiones, entorno,
repeticiones, solicitudes y huellas. Añadir casos con muchas llaves, alternativas
y grupos independientes para detectar coste por llave/componente oculto.
Tras implementar, ejecutar regresión de partida, niebla, replay, presupuesto,
persistencia y comandos afectados.

## Artefactos y siguiente paso

Diseño: [data-model.md](data-model.md). Interfaces: [contrato](contracts/verificacion.md).
Validación prevista: [quickstart.md](quickstart.md). El plan termina aquí.
Sigue `$speckit-tasks`, después `$speckit-analyze` y luego implementación.
La fase de planificación no generó código. La descomposición posterior está en
[tasks.md](tasks.md), todavía sin tareas ejecutadas.
