# Modelo de datos: Presentación y observaciones gráficas

**Fecha**: 2026-11-13. **Estado**: diseño de planificación, no implementado.
**Decisiones aprobadas**: D-IG-05/06/07 en [research.md](research.md).
**Reglas**: [spec.md](spec.md). Ninguna entidad gráfica se añade al esquema del motor v6.

## Propiedad y límites

El trabajador de sesión es el único propietario del motor, cargador, controlador
y memoria de observaciones. La ventana recibe valores inmutables, sin referencias
a salas, actores, inventario ni fuente de datos. Usa su propia cámara y controles.
Pygame no se importa en las entidades, proyección o persistencia descritas aquí.

## Sesión y presentación

| Entidad | Campos principales | Invariantes |
|---|---|---|
| `SesionGrafica` | generación, fase, sesión de juego, revisión, finalización procesada y error de puntaje si ocurrió | Una sola sesión activa; generación nueva al iniciar o sustituir la partida; cierre/finalización una sola vez |
| `PresentacionGrafica` | generación, revisión, estado del jugador, salas conocidas, objetivos actuales, inventario, mensajes, panel abierto | Copia profunda de valores; ninguna referencia al modelo; publicar solo al terminar una operación |
| `IntencionGrafica` | generación, revisión de origen, operación, argumento y objetivo | Se valida al recibir y antes de ejecutar; una operación aceptada a la vez |
| `ResultadoOperacion` | clase de resultado, aceptada, órdenes canónicas emitidas, mensajes, presentación y finalización | Distingue acción, retroceso, navegación, consulta, rechazo, carga y salida; no se infiere el resultado analizando mensajes |
| `ObjetivoActual` | clase, identificador lógico, posición real cuando proceda, nombre, comportamiento, datos visibles | Enemigos solo de la sala actual; posiciones de inventario/suelo válidas solo para esa revisión |

Los actores se identifican por `actor_id` junto con la generación/revisión.
Objetos sin identificador único se seleccionan por su posición real dentro de
una presentación vigente. La vista ordenada transporta esa posición original;
no reutiliza un índice antiguo ni cambia el orden real del inventario.

### Fases de aplicación

`INICIO` → `PREPARANDO` → `JUGANDO`; preparación fallida vuelve a `INICIO`
o conserva la sesión previa. Desde `JUGANDO` se pueden abrir inventario,
historia o ayuda, sin crear otra sesión. Victoria/derrota lleva a `RESULTADO`.
Volver al inicio finaliza los recursos de la sesión; cerrar lleva a `CERRANDO`
y luego a `CERRADA`. No se aceptan acciones en `RESULTADO` o `CERRANDO`.

El estado ocupado del trabajador es independiente del panel mostrado. La
ventana sigue procesando eventos y dibujando la última presentación confirmada.

## Conocimiento y distribución del mapa

| Entidad | Campos principales | Invariantes |
|---|---|---|
| `SalaVisual` | ID, conocimiento, nombre permitido, sala actual, conexiones conocidas, observación o falta de ella | Solo existe para salas incluidas en `Partida.mapa()` |
| `ConexionVisual` | origen, destino, dirección, costo permitido, recuerdo de puerta | No refleja el estado físico remoto; proximidad de casillas no implica conexión |
| `CasillaMapa` | ID de sala, columna, fila | Posición de presentación, sin influencia sobre el motor |
| `EnlaceCroquis` | conexión conocida y marca de ajuste geométrico | Señala conexiones que no encajan cardinalmente, sin ocultarlas ni inventar pasos |
| `CamaraMapa` | desplazamiento, escala, área visible | Sus límites se calculan solo con salas conocidas; no consume tiempo virtual |

### Estructuras elegidas

- Vectores de casillas, conexiones, controles y observaciones. Consultas por ID
  mediante `IndiceSalas`, implementado en el proyecto. No usar el ID como índice.
- Para el croquis se crea un índice a partir de los IDs de la proyección conocida,
  separado de cualquier índice del mundo completo. Ocupación: recorrido del
  vector de casillas colocadas; no índice espacial adicional.
- La memoria del trabajador puede usar las posiciones densas del conocimiento
  existente. Ni esa reserva interna ni el número de salas ocultas se transmiten
  como geometría, tamaño del mapa o contador visible.
- Los recorridos auxiliares del croquis usan un vector y cursor de lectura,
  sin cola de biblioteca. La colección de sprites es un vector pequeño por tipo.

### Construcción determinista del croquis

1. Tomar exclusivamente la proyección conocida. Elegir como ancla la sala inicial
   de la sesión visual si sigue conocida; en otro caso, la sala actual. Colocarla
   en `(0, 0)`. No conservar posiciones de salas que dejaron de ser conocidas.
2. Recorrer conexiones conocidas desde el ancla en orden fijo N, S, E, O; resolver
   los empates por ID con el ordenamiento propio existente.
3. Proponer una casilla vecina según la dirección. Si está libre, colocar allí
   el destino. Si ya estaba colocado, conservar su posición y marcar el enlace
   cuando la relación cardinal no coincida.
4. Si una sala nueva ocuparía una casilla ya usada, colocarla en la primera
   columna del carril de conflictos, dos columnas a la derecha del máximo
   actualmente ocupado, fila cero. Actualizar el máximo y marcar ese enlace
   como esquemático. Esta regla garantiza un destino libre sin búsqueda infinita.
5. Si quedan componentes conocidas desconectadas, iniciar cada una por su menor
   ID en un carril libre y continuar. Nunca recorrer salidas físicas ocultas.
6. Reconstruir al cambiar el conocimiento o cargar/retroceder; al mover o ampliar
   la cámara se reutiliza el croquis y no se consulta el modelo.

El croquis prioriza corrección, distinción de conexiones y ausencia de solapes.
No promete una incrustación espacial perfecta ni un algoritmo automático de
compactación de grafos. Su ancla es de presentación y se valida al cargar.

## Observaciones y cinco cambios reversibles

| Entidad | Campos principales | Invariantes |
|---|---|---|
| `ObservacionEnemigos` | ID de sala, instante observado, grupos de comportamiento/nombre/cantidad | Valores inmutables; solo enemigos vivos observados presencialmente; sin salud remota ni referencias a actores |
| `MemoriaVisual` | índice de salas, vector de observaciones opcionales, origen, hasta cinco deltas | `None` significa «sin observación»; una observación con grupos vacíos significa «observada vacía» |
| `DeltaVisual` | posición de la acción en el registro, contadores/relojes antes y después, valores anteriores de observaciones modificadas | Asociado a una acción aceptada realmente reversible; máximo cinco; no se crea por redibujar, consultar o rechazar |
| `OrigenVisual` | posición de registro y contador al inicializar/reiniciar memoria | Identifica la frontera anterior a la que no hay recuerdos verificables |

La observación inicial se toma una vez al abrir la sesión gráfica válida. Tras
una acción aceptada, registrar el valor anterior de la sala actual resultante
y sustituirlo por la observación nueva. Al cambiar de sala, el recuerdo de la
anterior sigue siendo el último estado que se mostró presencialmente allí.
No se inspeccionan enemigos de las demás salas, aunque estén cargados en memoria.

Cada delta se identifica por la posición de su `AccionVigente` en el registro
de órdenes, además de los contadores. No basta el instante ni el número de
acción: ambos pueden reutilizarse después de un pergamino. `sig`/`ant` se registran
para replay, pero no crean deltas de observación ni consumen turno.

`usar` un pergamino y la orden `retroceder` producen la misma clase de resultado
de retroceso aceptado. El contador disminuye en uno y se restaura un delta;
no se añade una observación como si se hubiera ejecutado una acción nueva.

### Transiciones de memoria

| Suceso | Resultado visual |
|---|---|
| Inicio gráfico válido | Memoria sin observación remota; observar solo sala actual |
| Acción aceptada | Un delta y una observación de la sala actual; retirar el delta más antiguo si supera cinco |
| Acción rechazada o consulta | Memoria y deltas intactos |
| Paso de viaje aceptado | La misma transición que un movimiento ordinario |
| Pergamino aceptado con delta coincidente | Restaurar sus valores anteriores, retirar el delta y observar solo la sala actual restaurada |
| Pergamino rechazado | No cambiar memoria, selecciones ni historial |
| Retroceso más allá del origen visual o delta no verificable | Descartar recuerdos inciertos, fijar nuevo origen y observar solo la sala actual |
| Revelación por antorcha o cambio remoto | No producir observación de enemigos |
| Consulta histórica | Mostrar enemigos y mapa de su `ResumenHistorico`, sin superponer memoria actual |
| Carga válida | Importar memoria validada o reiniciarla si falta/no corresponde; invalidar selección anterior |
| Carga de juego fallida | Mantener la sesión y la memoria anteriores |

Al importar deltas, sus posiciones deben corresponder a un sufijo de acciones
vigentes y no exceder las cinco acciones disponibles en el historial real.
El delta que se deshace debe coincidir con la acción vigente antes del pergamino.
La reobservación posterior al retroceso no crea un turno ni un delta adicional.

## Persistencia y complejidad

La carga visual opcional usa exclusivamente tipos básicos del codec v6 y tiene
versión propia. Sus campos y validaciones se definen en
[recuerdos-v6.md](contracts/recuerdos-v6.md). No se guardan superficies,
rectángulos, hilos, controles, cámara ni referencias a entidades vivas.

Sean V las salas, S las salas conocidas, E sus conexiones y T los grupos de
enemigos recordados. Memoria de observaciones O(V + T), más hasta cinco deltas
de los grupos modificados. Consulta por ID O(1) esperada con el índice propio;
sus colisiones conservan el comportamiento de sondeo existente. Croquis:
O(S² + E) esperado al construir, por búsqueda lineal de ocupación y consulta
indexada de destinos; memoria O(S + E). No se reconstruye por cada cuadro.
Estas cotas no son mediciones de latencia ni garantías de EX-01.
