# Modelo de datos: escena y efectos de presentación

**Estado**: Diseño aprobado por D-EV-04 e implementado; validación nativa pendiente.

## Registros transitorios

| Entidad | Campos | Invariantes |
|---|---|---|
| EfectoVisual | tipo, actor_id, sala_id, reloj, cantidad, nombre, comportamiento | Congelado; valores simples; solo hechos observables |
| RegionEscena | clase, objetivo/dirección, rectángulo | Vector de la página; objetivo incluye revisión/generación |
| Recurso | clave de clase/tipo, superficie fuente, superficie escalada | Vector pequeño; carga local una vez, escala por área activa |
| AnimacionActiva | generación, revisión, inicio real, duración, efectos, foto anterior | Una sola activa; no almacena Partida ni usa reloj virtual como temporizador |

Tipos de efecto: ataque, daño, curación, derrota, entrada, salida y movimiento
del jugador. Actor del jugador se identifica como `jugador`; cantidad es una
variación confirmada no negativa. Los efectos no contienen objetos vivos.

## Colocación y selección

Vector con hasta 12 enemigos y 8 objetos por página; jugador en zona central
inferior, enemigos en tres columnas por cuatro filas, objetos en banda separada.
Puertas N/S/E/O ocupan centros de pared y solo existen si la proyección las da.
La posición es escénica; ni colisión ni alcance forman parte de esta entidad.

Los clics recorren regiones visibles y devuelven el objetivo exacto. Cambiar
generación o revisión invalida selección caducada. Páginas exponen siempre total
y controles anterior/siguiente; no agregan varios enemigos atacables en un sprite.

## Ciclo de efectos

INACTIVA → ACTIVA solo por una acción aceptada que tenga efectos confirmados.
ACTIVA → INACTIVA por tiempo cumplido, salto, pérdida de foco, carga, retroceso o
cierre. En normal dura hasta 500 ms, en reducida hasta 180 ms y sin efectos 0 ms.
Redibujar no reinicia el inicio. No se programa una acción al terminar una animación,
salvo la solicitud explícita de siguiente paso de viaje ya activo de 005.

El trabajador construye un vector nuevo por operación. Lo publica como tupla
solo tras completar y confirmar esa operación. Rechazo/consulta/carga/retroceso
no se convierten en efectos de combate; se descartan efectos de revisiones previas.

## Persistencia

Ninguno de estos registros se agrega a Partida, MotorEventos, checkpoints o
payload visual v6. Cargar o retroceder reconstruye escena y vuelve a INACTIVA.
El recuerdo remoto conserva exclusivamente la representación aprobada en 005.

## Metadatos de claridad de la presentación

`ObjetivoActual` de inventario expone peso y valor simples, y `PresentacionGrafica`
el criterio de orden aplicado por su dueño. Son ampliaciones de los mismos
registros congelados, no de Partida, MotorEventos, guardados o checkpoints.
El catálogo vectorial añade especies por nombre observable. El selector de panel
se reutiliza para nueva partida/carga, y dos escalares visuales describen la
operación pendiente y el inicio del indicador. No hay nuevas estructuras.
