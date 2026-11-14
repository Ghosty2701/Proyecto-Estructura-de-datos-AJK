# Contrato de escena, recursos y animaciones

## Flujo y propiedad

El trabajador ejecuta la orden vigente con un callback opcional para efectos.
`RespuestaGrafica` lleva una tupla de `EfectoVisual`, vacía por defecto. El nuevo
parámetro de Controlador y de las operaciones de Partida es opcional y conserva
las llamadas actuales de consola/replay, incluidas las de pruebas con dobles.
No se cambian reglas, orden de eventos, azar, conteo ni órdenes registradas.

La vista solo recibe valores y envía `IntencionGrafica` con `ObjetivoActual`.
Cada efecto identifica generación/revisión mediante la respuesta que lo contiene.
Derrota requiere hecho de vida cero observable; ausencia por movimiento solo
permite salida. Daño+curación neta cero puede incluir dos hechos separados.
No se interpretan mensajes para fabricar efectos.

## Recursos originales

- `sala.png`: fondo opaco, habitación pétrea cenital, cuatro paredes completas,
  sin puertas, actores, objetos utilizables, texto, interfaz o luces que oculten suelo.
- `actores.png`: transparencia real; atlas de 3 columnas × 2 filas iguales, orden
  por fila: jugador, guardián, errante; rastreador, cazador, enemigo genérico.
- `elementos.png`: transparencia real; atlas de 4 columnas × 3 filas iguales, orden
  por fila: puerta cerrada, puerta abierta, arma, armadura; llave, pergamino,
  poción, antídoto; antorcha, amuleto, objeto genérico, contenedor genérico.
- Arte ilustrado de fantasía oscura, coherente, márgenes dentro de cada celda.
  Pygame recorta por fracciones de dimensiones y ajusta por alfa al cargar.
- Fondos, puertas y actores siempre separados. No usar el mockup como fondo jugable.
- Prompts y procedencia en `assets/README.md`; archivos incluidos al clonar.

## Interacciones y tiempo

Seleccionar sprite revela nombre y objetivo, sin turno. Puertas muestran costo
y controles mover/abrir. Se mantienen botones/listas para todas las operaciones.
El minimapa abre mapa completo, con cámara y viaje conocidos.

Una animación usa tiempo real inyectable; controles normales no acumulan acciones.
Espacio o botón Saltar finaliza el efecto y no ejecuta esperar. Cambiar a efectos
reducidos/sin efectos solo cambia presentación. Carga, retroceso, foco y cierre
invalidan inmediatamente la animación; si una acción ya está aceptada se conserva
su resultado seguro. El viaje no programa el siguiente paso antes del ciclo de eventos.

## Validación de contrato

AC-EV-001–004: habitación, puertas, sprites de suelo y costos.
AC-EV-005–008: objetivos individuales, efectos confirmados y misma sala de combate.
AC-EV-009–012: minimapa, privacidad, viaje, carga y retroceso.
AC-EV-013–015: consistencia de recursos, paginación, tamaños mínimos y continuidad.
SC-EV-003: comparar exactamente reloj, azar, estado y registro con consola para
normal/reducida/sin efectos; inactividad 60 s inyectados y 300 cuadros.
SC-EV-005: revisión visual nativa independiente de vídeo dummy; no marcarla por tests.

## Contrato vigente de presentación 16 bits

La petición posterior del usuario sustituye el arte ilustrado por pixel art.
Se conservan arte original, alfa, distribución local y composición independiente
del estado. Nuevos atlas con sufijo `_16bits`; puertas en atlas 4 × 2, columnas
N/S/E/O, fila superior cerrada e inferior abierta. Se usan directamente, sin giros.

La pantalla normal muestra hasta seis comandos. Selección de enemigo/objeto/puerta
no consume turno y determina el único comando principal. Inventario y pausa
son paneles; Escape vuelve a la habitación. Persistencia e historia conservan
sus intenciones y validaciones. El mapa y las páginas siguen alcanzables.
Las pruebas anteriores que exigían todos los botones simultáneamente se adaptan
a recorrer estos paneles; no se eliminan sus comprobaciones de juego.

## Claridad y especies

El sprite recibe nombre observable, además del comportamiento; los casos sin
arte usan símbolo neutral. No se añaden campos persistidos ni consultas remotas.
Inicio ofrece panel de nueva partida y panel de carga distintos. Selección de
cripta se confirma con fila resaltada y resumen persistente. Buscar archivo es
opcional, cancelar conserva ruta y cargar requiere confirmación explícita.
Ordenar explica ascendente (nombre A–Z, peso menor primero, valor menor primero).
El resultado sigue llegando del trabajador. Indicador de actividad animado sin
porcentaje se superpone durante toda operación pendiente, atendiendo cierre.
