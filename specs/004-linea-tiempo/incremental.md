# Investigación y piloto incremental — 2026-11-13

Ruta elegida; índices propuestos **sin elegir ni implementar**. Amplía 004,
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
se mide completo. B es alternativa si el vector domina. Ninguna está elegida.

## Piloto acotado y criterios de salida

1. Elegir índices y definir IDs, altas/bajas, contenedores, direcciones reutilizadas
   y publicación atómica. No codificar antes de resolver estos puntos.
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
