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
