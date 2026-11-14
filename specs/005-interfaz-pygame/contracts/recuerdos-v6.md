# Contrato: Recuerdos opcionales en el guardado v6

**Estado**: diseño aprobado en cuanto a ubicación; implementación y pruebas pendientes.
**Decisión**: D-IG-06, elección explícita del usuario del 2026-11-13.
**Ubicación**: clave `interfaz_grafica` dentro de `datos_extra` del `.bin` existente.
**Formato de juego**: `VERSION_MODELO = 6` permanece sin cambios.

## Representación de intercambio

La clave opcional contiene una tupla de cinco componentes, todos admitidos
por el codec actual: `(version_visual, marca_sesion, origen, observaciones, deltas)`.
Los registros usan valores básicos y tuplas/listas; no clases nuevas del esquema.
El diccionario contenedor `datos_extra` es transporte, no un índice de recuerdos.

| Componente | Contenido y validación |
|---|---|
| `version_visual` | Entero exacto 1; bool no es un entero válido para este campo |
| `marca_sesion` | ID/versiones de cripta y catálogo, semilla, reloj, contador de acciones, sala actual y huella del registro de órdenes |
| `origen` | Posición del registro y contador al inicializar/reiniciar la memoria; dentro de los límites de la sesión |
| `observaciones` | Tuplas de sala, instante y grupos de comportamiento/nombre/cantidad; IDs únicos, existentes y explorados; instante no futuro |
| `deltas` | Hasta cinco cambios de acciones vigentes; ancla de orden, contadores/relojes y observaciones anteriores de salas modificadas |

La ausencia de una sala en `observaciones` significa «sin observación»; una tupla
con grupos vacíos significa «observada vacía». Cantidades enteras no negativas,
IDs y relojes del tipo esperado y nombres de texto. No almacenar vida remota
ni referencias a enemigos. Limitar el número de salas al tamaño real de la
sesión validada, rechazar IDs repetidos y no aceptar más de cinco deltas.

La huella usa SHA-256 de las órdenes completas existentes, incluidas navegación
y pergaminos. Cada orden se representa por `(texto, tipo, reloj)` con JSON UTF-8
compacto, sin escapes ASCII innecesarios, precedido por la longitud del registro
en ocho bytes little-endian. Procesar registros secuencialmente; no copiar todo
el log en otra estructura ni incluir `interfaz_grafica` en su propia huella.
Es una comprobación de correspondencia, no una promesa de autenticidad del archivo.

La marca se compara con el juego ya decodificado, no con datos introducidos por
la interfaz. La huella y las posiciones de acciones evitan aceptar recuerdos de
otra rama temporal solo porque coincidan el reloj y el contador.

## Escritura

1. Ejecutar `guardar` por la ruta compartida, dentro de la misma operación
   serializada que administra la sesión. No observar salas ni avanzar el juego.
2. Exportar memoria a tipos básicos y añadir la clave opcional a los datos extra
   preparados por el cargador. No sobrescribir `partida`, `contenido`, `fichas`
   o `linea`; el resto del guardado se produce como en la versión actual.
3. Publicar un único archivo mediante el reemplazo atómico existente. No escribir
   un `.gui.json` ni mantener dos archivos sincronizados.

La extensión del cargador es opcional y sin referencias a Pygame. El coordinador
gráfico proporciona/recibe los datos auxiliares mediante un adaptador de
persistencia. El cargador sin ese adaptador sigue generando los mismos campos
de juego y no conoce las reglas de representación de enemigos.

## Lectura y degradación

1. Validar primero el guardado de juego: identidad, versiones, raíces, contenido,
   fichas e historia, usando el cargador existente. Una carga de juego fallida
   no toca la sesión ni la memoria activas.
2. Si existe la clave opcional, validar sus tipos, versión, límites, marca y
   anclas sin modificar la partida. Los deltas deben corresponder a un sufijo de
   acciones vigentes y al límite del historial reversible real.
   Para un sufijo de `m` deltas, contrastar cada ancla con
   `linea.acciones[-m+i].posicion` y su reloj anterior con
   `linea.acciones[-m+i].reloj` y
   `motor.historial.acciones[-m+i].reloj_anterior`. Exigir contadores consecutivos
   cuyo último valor sea `acciones_ejecutadas`. Si no hay línea/historial
   suficiente o no coinciden, descartar la carga visual, sin tocar el juego.
3. Si es válida, preparar una memoria candidata; si falta, es de versión visual
   desconocida o no corresponde, descartar la carga visual y avisar sin rechazar
   una partida de juego válida. No intentar migraciones ni leer enemigos remotos.
4. Después de confirmar la carga de juego, aplicar la memoria candidata o una
   memoria vacía y observar solo la sala actual. Invalidar selecciones anteriores.

La degradación cubre **datos visuales semánticamente inválidos que el codec
puede decodificar**. Un archivo truncado, una raíz inválida o tipos binarios
desconocidos siguen siendo un error de guardado. No se promete recuperar
arbitrariamente un binario corrupto.

## Retroceso después de cargar

La memoria conserva únicamente los últimos cinco deltas verificables, no una
copia paralela de la historia. Antes de un pergamino se identifica la última
acción vigente; solo después de que el motor acepte el retroceso se retira su
delta coincidente. Reobservar la sala actual restaurada no agrega otro delta.

Si la memoria empezó en una carga antigua o no tiene el delta de esa acción,
un retroceso que cruce su origen descarta las observaciones inciertas. Se fija
un origen nuevo y se observa únicamente la sala actual. No reconstruir recuerdos
de salas remotas a partir del mundo físico restaurado.

## Compatibilidad cruzada obligatoria

| Recorrido | Resultado esperado |
|---|---|
| Guardado v6 anterior → gráficos | Mismo estado de juego; recuerdos ausentes y observación actual nueva |
| Gráficos → gráficos | Mismo juego, observaciones válidas y hasta cinco deltas |
| Gráficos → lector de consola de `main` | Carga válida, misma continuación; clave visual ignorada |
| Gráficos → consola antigua → nuevo guardado → gráficos | Carga de juego válida; se acepta pérdida de recuerdos porque la consola antigua reconstruye sus datos extra |
| Carga visual semánticamente inválida → gráficos | Advertencia y reinicio visual, sin perder el guardado válido |
| Carga de juego fallida en una sesión abierta | Partida y memoria anteriores conservadas |

La compatibilidad básica de una clave primitiva se exploró en una sonda temporal;
esta matriz completa se verificará con el payload implementado y el lector
congelado de `main` en `6107b98`. La re-guardada de consola no está obligada a
conservar extensiones de una versión que desconoce.
