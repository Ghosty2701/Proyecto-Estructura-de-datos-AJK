# Modelo de datos: Línea de tiempo y puntos de control

**Estado**: diseño implementado; estructuras aprobadas en [research.md](research.md).
Los registros no amplían reglas de [spec.md](spec.md). El prototipo compartido sigue fuera del formato de producción.

## Registros

| Registro | Campos | Validación e invariantes |
| --- | --- | --- |
| Orden ejecutada | texto normalizado como en `partida.log`; tipo (acción, pergamino, navegación); instante de decisión al ejecutarla | Solo órdenes aceptadas y reproducibles. El arreglo solo crece; su posición es estable. |
| Acción vigente | instante de decisión; posición de su orden | La posición k − 1 es la acción k. Instantes estrictamente crecientes. El pergamino trunca el final. |
| Punto de control | posición de orden (la siguiente por re-ejecutar); número de acciones vigentes; instante; copia completa del estado; K del tramo | Arreglo creciente en posición de orden; reloj y acciones vigentes pueden retroceder tras un pergamino. El punto 0 está en posición 0 e instante 0. Dentro de un tramo de K constante se crea cada K acciones ejecutadas, incluidas las revertidas después; el pergamino no cuenta. Los puntos anteriores se conservan al cambiar K. |
| Tramo de K | K vigente; posición donde empieza | Un tramo nuevo empieza solo al cargar con un `--checkpoint-cada` distinto. |
| Línea de tiempo | arreglo de órdenes, arreglo de acciones, arreglo de puntos, tramos, acciones del tramo en curso, instante pendiente | Pertenece a la partida y se persiste con ella. No usa `dict`/`set` como índice. |
| Objetivo de consulta | posición final; límite de tiempo opcional | Lo calculan `#k` o t; nunca está más allá de la última orden. |
| Resumen histórico | reloj; sala (ID y nombre); vida/máxima, ataque y defensa; inventario en orden real con equipados y cursor; efectos activos; enemigos vivos de la sala con vida/máxima, dormido o activo y marca de cazador; mapa conocido | Mismo contenido para `historia` y `--replay --hasta`; se deriva solo del estado de la copia. |

## Copia completa del estado

| Elemento | Diseño |
| --- | --- |
| Raíces | La partida (con motor, jugador, enemigos, inventario y conocimiento) y la lista de salas, igual que en el guardado. |
| Campos por tipo | Campos obligatorios y opcionales del esquema explícito del guardado, compartido para no divergir. |
| Tabla de identidades | Direccionamiento abierto propio; clave = identidad del objeto original, valor = copia; capacidad potencia de dos con crecimiento al 70 %; una tabla por copia, descartada al terminar. |
| Recorrido | Pila propia (iterativo, sin recursión) para grafos con ciclos, como el anillo de salas. |
| Valores especiales | Enteros, textos, booleanos y `None` se comparten; las tuplas se reconstruyen; `random.Random` se copia por estado; los `dict` de fichas y contenido se copian como datos. |
| Excluidos | Funciones de enlace (preparar sala, fuente, gestor de guardado), mensajes de vista e índices derivados, que se reconstruyen como al cargar. |

## Transiciones

| Evento | Efecto en la línea |
| --- | --- |
| Inicio de partida nueva | Punto 0, tramo con K de la ejecución, instante pendiente 0. |
| Acción aceptada | Orden más acción vigente; tramo + 1; punto si el tramo llega a K. |
| Pergamino aceptado | Orden; acciones vigentes truncadas al contador restaurado; el tramo no cambia (el pergamino no es una acción); instante pendiente igual al reloj restaurado. |
| Navegación de inventario | Solo orden. |
| Orden rechazada, consulta, guardar | Sin cambios. |
| Guardar | Se persiste la línea completa (formato 6). |
| Cargar | Se restaura la línea; si `--checkpoint-cada` difiere, empieza un tramo nuevo. |
| Cargar formato anterior | Rechazo explícito; la línea actual no cambia. |
| Fin de la partida | La sesión interactiva termina; la línea queda en el log para `--replay --hasta`. |
