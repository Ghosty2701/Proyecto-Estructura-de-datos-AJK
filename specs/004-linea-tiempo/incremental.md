# Investigación y piloto incremental — 2026-11-13

Ruta elegida; el usuario eligió la opción A el 2026-11-13. Amplía 004,
sin otra funcionalidad de usuario ni cambio del K provisional.

## Auditoría de mutaciones

| Frontera revisada | Hallazgo y cobertura necesaria |
|---|---|
| `modelo/retroceso.py` | `iniciar_accion` conserva solo cinco acciones. K=10/25 requiere seguimiento independiente; undo restaura por `setattr` y operaciones de listas/agenda fuera de `_cambiar`. |
| `modelo/motor_eventos.py` y `efectos.py` | `_cambiar` cubre atributos, no todas las escrituras. Observar también nuevos eventos/efectos, enlaces dobles, reloj, secuencias, cancelación y azar. |
| `modelo/agenda_eventos.py` | Inserción/extracción modifican posiciones de `heap` y secuencia directamente; cancelar modifica el evento. Conservar orden real y siguiente evento. |
| `modelo/inventario.py` y `inventario_reversible.py` | Enlaces, equipo, cursor y operaciones inversas tienen escrituras directas; navegación también cambia estado sin acción numerada. |
| `controlador/partida.py` | Registrar orden no equivale a registrar todas las mutaciones. Suelo, botín y pergamino fuera de undo necesitan cobertura explícita. |
| `modelo/conocimiento.py` | Observaciones usan callback, pero crean/reemplazan salidas. Separar estado persistible de índices de viaje derivados. |
| `controlador/cargar_partida.py` | `preparar_sala` publica listas, extiende enemigos y activa contenido fuera del motor; carga restaura campos y debe reiniciar seguimiento. |

Esto es un inventario inicial, no una prueba de cobertura de todas las escrituras.
Cada fila requiere oráculo de estado completo, continuación y pruebas negativas.
List/dict/tuple no soportan weakref como las clases ordinarias: resolver su ciclo
de vida y alias antes del piloto. No adoptar un registro permanente de referencias
fuertes a todo lo visto ni direcciones reutilizables sin control.

## Índices: alternativas para elegir

En ambas opciones se propone hash propio para identidad/cambios pendientes;
su política de IDs/retirada se especifica antes de conectarlo al juego.

| Opción | Versión publicada | Ventaja | Costo/riesgo |
|---|---|---|---|
| A. Hash propio + vector inmutable de casillas | Serializar lo cambiado y copiar superficialmente las referencias del índice | Acceso esperado constante; menor complejidad y sin recorrer atributos inalterados | O(C + D) esperado, no O(D); vector, crecimiento/borrado y memoria de cada versión deben medirse |
| B. Hash para cambios + AVL persistente por ID | Compartir ramas y copiar caminos modificados | Evita copiar todo el vector y permite claves dispersas | O(D log N), más nodos/rotaciones y asignaciones; el AVL mutable del catálogo no sirve sin adaptación |

C = capacidad, D = registros cambiados, N = registros indexados. No incluyen
serializar datos, detectar cambios, retirar registros o materializar consultas.

**Recomendación de primer piloto: A**, por simplicidad y porque copiar referencias
evita la lectura de atributos que domina hoy. No se presupone barato el vector:
se mide completo. B queda descartada para el primer piloto. A está elegida.

### Contrato del índice aislado elegido

Claves: IDs enteros no negativos (bool no es ID). Valores: registros codificados
como tuplas de tipos escalares/tuplas inmutables; no modelos ni contenedores
mutables. Casillas vacías None y tumbas (); entradas (ID, registro).
Doble hashing propio, capacidad potencia de dos (mínimo 8), salto impar,
carga activa máxima 70 %. Actualizar no aumenta ocupación. Borrado usa tumbas;
al insertar se recompone si la ocupación incluyendo tumbas exige limpiar,
y se duplica si la carga activa lo exige. No crece por el valor máximo de ID.

Una actualización por lote copia el vector y publica una nueva tupla; versiones
anteriores y registros no cambiados se conservan. Si el lote falla, la versión
original no cambia. No se omite una actualización por igualdad numérica: True,
1 y 1.0, y los ceros con signo, conservan su tipo/bits. Costos O(C + D) esperados
sin rehash, más validación de registros nuevos; crecimiento/rehash se miden.

Este índice no define aún identidad de modelos vivos ni seguimiento de
mutaciones. Su integración permanece bloqueada técnicamente hasta resolver
ciclo de vida de contenedores/IDs y probar la cobertura exigida; no se conecta
al motor solo por aprobar sus pruebas aisladas.

## Piloto acotado y criterios de salida

1. Elegir índices y definir IDs, altas/bajas, contenedores, direcciones reutilizadas
   y publicación atómica. No conectar el capturador antes de resolver estos puntos.
2. Estructuras aisladas: colisiones, borrado, crecimiento y versiones anteriores
   inalteradas. Todavía sin conexión al capturador del juego.
3. Capturador experimental: comparar con captura completa después de cada orden
   en trazas pequeñas (navegación, inventario, eventos, efectos, puertas, azar y
   carga diferida). Detectar deliberadamente una mutación omitida.
4. K=5/10/25, cinco undo, más de K órdenes, alias/ciclos, altas/bajas y fallo de
   publicación. Contar visitas a entidades inalteradas; evitar escaneo oculto.
5. Guardar/cargar v6, conservar puntos y continuar. Revisar bytes normalizados,
   límites de replay y memoria retirada; nunca confundir resumen con estado completo.
6. Historias completas y consultas/RSS oficiales contra `0160d94`, incluyendo
   mantenimiento, registro, GC y todos los picos. No basta mejorar la mediana.

Salida: equivalencia completa, memoria controlada y reducción real de trabajo/costo.
Si no demuestra ventaja, no se activa. Hasta entonces producción y K se conservan;
no se cierra ningún presupuesto por escribir el plan.

## Primer resultado: estructura aislada

Índice elegido implementado en `modelo/indice_versionado.py`. Diez casos nuevos
y regresión completa de 709 pruebas. Medición de 200 versiones/6 000 registros,
96 cambios por lote: publicación mediana 0,484 ms, máxima 3,351 ms; memoria
trazada retenida 29 827 032 bytes. No incluye detectar/serializar cambios ni
reconstruir modelos. Inicio con crecimiento 39,630 ms y limpieza separada de
9 000 tumbas 4,098 ms. No implica cumplimiento de ciclos/consultas.
Detalles en `documentacion/INDICE_VERSIONADO_JUAN.md`. CI-005 sigue abierto;
completada únicamente la subfase de estructura de CI-006, sin conexión al motor.

## Contrato del capturador experimental y ciclo de vida

Se desarrollará con los hashes y vectores ya elegidos, sin sustituir contenedores
del modelo ni instalar interceptores globales. Un registro por sesión conserva
fuertemente cada objeto y compara identidad, asignando IDs monótonos que no se
reciclan tras una publicación. Esto evita ABA también para list/dict/tuple.
Las marcas pendientes se deduplican en las entradas del mismo hash, fuera de undo.

La primera captura descubre todo el grafo. En las siguientes se leen atributos
solo de objetos marcados y nuevos; referenciar un objeto conocido no lo visita.
El llamador debe marcar el contenedor al cambiar sus elementos, el objeto al
escribir/borrar atributos y Random al consumir/restaurar azar. Una referencia
nueva descubre recursivamente sus registros, conservando alias y ciclos.

Cada publicación traza alcanzabilidad **sobre registros inmutables**, no sobre
atributos vivos. Retira registros y referencias fuertes inalcanzables, incluso
ciclos aislados, y recompone el hash de identidades al tamaño del grafo actual.
Este mantenimiento O(C + E) no es O(D): se contabilizará y puede descartar el
piloto si resulta caro. Entre puntos se retienen el último grafo y los objetos
marcados; cerrar libera todo el registro, sin invalidar puntos anteriores.

La captura prepara índices y registros temporales. Solo tras codificar, retirar
y verificar publica la versión y limpia marcas. Un fallo conserva la versión
previa y todas las marcas para reintentar. Los puntos contienen escalares/tuplas,
sin capturador, objetos vivos ni cadena de antecesores. Materializar convierte
IDs dispersos a ordinales locales y reutiliza el reconstructor ya probado.

El oráculo completo estará habilitado por defecto en el piloto: captura el
estado vivo y el reconstruido, compara tipos/bits y grafo completo antes de
publicar y rechaza marcas omitidas. Deshabilitarlo explícitamente solo permite
medir cargas controladas con marcas conocidas; no demuestra cobertura del juego.
La cobertura por fronteras de la auditoría seguirá abierta hasta instrumentar
y verificar cada escritura, navegación y undo. No se conecta este componente
a la línea de tiempo productiva por pasar pruebas de marcas manuales.

### Piloto de observación por frontera de orden

Antes de modificar las clases productivas se probará un envoltorio explícito
por orden. Conservará las referencias a deltas de las cinco acciones antes y
después de ejecutar, incluidas listas que undo vacía. Marcará sus destinatarios,
los vecinos de cambios de inventario y las fronteras fuera de undo: partida,
jugador, motor/azar, agenda/heap/secuencia, historial, inventario y nodos,
sala actual/suelo y publicación de enemigos. Solo marca objetos ya registrados;
los nuevos se descubren desde enlaces cambiados al capturar.

Las marcas se acumulan en el registro independiente hasta publicar, aunque los
deltas originales salgan de la ventana de cinco acciones. El envoltorio cubre
también navegación y errores mediante finally. No intercepta escrituras
arbitrarias ni precargas externas: su contrato exige ejecutar la operación
entera dentro de la frontera; el oráculo sigue obligatorio durante validación.
Recorrer inventario y deltas tiene costo explícito, incluido al medir órdenes.
No se usará marcar todo el modelo como sustituto de este seguimiento.

## Resultado del bloque completo

Registro, capturador y envoltorio implementados; 733 pruebas. Seis historias
de 5 000 acciones, equivalencia de todos los puntos K25 mediante bytes v6 y
consultas equivalentes. La captura incremental del juego cuesta 50,5–53,8 ms
de mediana frente a 13,6–13,7 ms de producción. No supera el criterio de costo:
**no activar esta variante**, aunque pase equivalencia. El envoltorio cubre su
contrato explícito; no se presenta como interceptación universal.

El perfil identifica reconstrucción del registro fuerte, alcanzabilidad y
publicación/validación. Se propone comparar un índice inverso hash ID → entrada
viva más borrado con tumbas contra conservar el barrido y reducir marcas.
La propuesta todavía no está elegida ni implementada. Incluye otro índice O(N)
y solo puede ahorrar parte del costo; se necesita decisión explícita antes
de añadirlo (AGENTS.md). Contrato, tablas, límites y recomendación detallados
en [el informe](../../documentacion/CAPTURA_INCREMENTAL_JUAN.md).

## Índice inverso elegido: contrato del siguiente ensayo

El usuario eligió explícitamente índice inverso hash por ID y bajas con tumbas.
Es privado de la sesión: ID monótono → la misma entrada del hash por identidad.
No se incluye en puntos, no retiene versiones anteriores y no cambia v6 ni K.
Ambos hashes usan direccionamiento abierto/doble hashing y carga activa ≤70 %.
Los borrados dejan tumbas; buscar atraviesa tumbas antes de decidir ausencia o
inserción. Las altas limpian ocupación activa+tumbas antes del 70 % o crecen;
al bajar del 17,5 % se reduce capacidad a la potencia de dos suficiente para
70 %. Así no se dimensiona el índice por el ID máximo ni se retienen modelos
retirados dentro de tumbas. No se recompone el índice en cada publicación.

El trazador devuelve los IDs retirados, además de la versión sin ellos. Cada
ID localiza su entrada y elimina la referencia fuerte de ambos hashes, O(R)
esperado para R bajas, salvo limpieza/reducción. Continúan el barrido O(C+E),
las copias transaccionales de vectores y el costo de altas en el índice nuevo.
No se describe como captura O(D) ni se promete cerrar 20 ms.

Preparar altas/bajas copia los dos vectores; errores no cambian índices, IDs
publicados, versión previa ni marcas. Se limpian solo las marcas procesadas
tras verificar, sin volver a recorrer todas las entradas para ese propósito.
Pruebas: colisiones con tumbas en ambos hashes, crecer/limpiar/reducir, IDs
dispersos, dos índices sincronizados, retirada de ciclos, liberación, fallos
en mitad de bajas y comparación de todos los puntos v6. Medir ABBA con la
variante anterior en procesos/trazas controlados, incluyendo mantenimiento.
