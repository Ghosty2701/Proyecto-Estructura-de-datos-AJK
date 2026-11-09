# Modelo de datos: Niebla y viaje

**Fecha**: 2026-11-09. Diseño implementado y verificado; evidencia en tasks.md.
**Referencias**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md).
Las entidades implementadas están en modelo/conocimiento.py.

## ConocimientoMapa

Pertenece al modelo de una partida y contiene el arreglo de SalaConocida de
longitud S aprobado en D-NV-01 y el índice estático ID → posición de D-NV-02.
Las posiciones se asignan una vez a las salas del esqueleto y se conservan durante
la partida. Guardar el orden ID/posición y validarlo al cargar: cada ID aparece
una vez y la posición coincide con su entrada. No usar el mayor ID como tamaño.
Una referencia de sala con su posición permite acceso directo sin hash.

El índice estático propio usa doble hashing, capacidad mínima potencia de dos
C ≥ 2 tal que 10·S ≤ 7·C, salto impar entre 1 y C−1 y como máximo C sondeos.
Construirlo con los IDs ya recibidos; rechazar duplicados/inconsistencias.
No insertar ni quitar IDs por exploración, retroceso o búsqueda.
Los parámetros aprobados no son evidencia de cumplimiento de 5 ms.

## SalaConocida (registro de conocimiento de sala)

Campos: sala, sala_id, posicion, estado, nombre y salidas. Los dos últimos
contienen exclusivamente información revelada; sala es referencia interna física.
Estado: DESCONOCIDA, AVISTADA o EXPLORADA. Una desconocida no contiene nombre
revelado ni salidas publicadas; una avistada solo permite mostrar su existencia.
La inicial comienza explorada en t=0 sin crear una acción ni un delta reversible.
La observación inicial recuerda sus puertas y avista los destinos correspondientes.

Explorar publica nombre y lista de SalidaConocida y avista sus destinos no
explorados. En reobservaciones no recorrer el mapa completo. La transición
normal aumenta conocimiento; el pergamino restaura el valor previo, que puede
ser desconocido, avistado o explorado. El ID interno no autoriza mostrar nombre.

## SalidaConocida y RecuerdoPuerta

SalidaConocida contiene dirección, posición/ID del destino, costo y referencia
al RecuerdoPuerta de esa conexión. Se crea/publica al revelar la sala. La lista
publicada no se modifica después: un cambio de referencia puede guardar la lista
previa mediante los deltas existentes, sin copiar el mapa completo.

RecuerdoPuerta tiene observada: inicialmente None (sin observar), luego
abierto o cerrado. Cada Puerta física tiene referencia a un recuerdo reservado
al construir la partida (D-NV-07). Ambos sentidos conocidos enlazan el mismo
recuerdo. Reservarlo no lee/publica su estado real. Los registros de partidas
independientes no se comparten.

Observar copia el valor real a observada únicamente en una observación
autorizada: desde un extremo donde está el jugador o al revelar con antorcha,
según la interpretación explícita del equipo. Un cambio físico remoto no
actualiza el recuerdo. Una puerta sin observación no se trata como abierta.
La búsqueda lee el recuerdo; no una propiedad que delegue en la Puerta física.

## Actualización y retroceso

Operaciones de modelo previstas: inicializar conocimiento, observar sala actual,
revelar vecinas por entrada con antorcha y consultar proyecciones sin mutación.
La antorcha revela solo las vecinas de la sala de entrada, por salidas abiertas
o cerradas; sus destinos pueden quedar avistados, sin exploración recursiva.
No cargar contenido ni activar enemigos/trampas de vecinas por esta revelación.

Dentro de una acción, registrar cada cambio de estado, nombre, lista o recuerdo
con registrar_atributo antes de modificarlo (D-NV-05). El orden inverso existente
restaura incluso varias modificaciones del mismo atributo. Cierres y aperturas
locales se observan en el evento/acción correspondiente; no al dibujar pantalla.
No registrar como mutación una consulta que solo presenta el mapa.

Para D cambios y R salidas nuevas, registrar/invertir atiende a O(D + R), no al
mapa completo. Las listas anteriores y los recuerdos referenciados por deltas
permanecen vivos hasta que el historial ya no los necesite. Aplicar pergamino
conserva excepciones de P1, revierte el último paso y cancela el viaje.

## Registros derivados de búsqueda

Arreglo separado por posiciones con registros: sala, distancia, primer_salto,
definitivo, posicion_heap y generacion. Un contador identifica la consulta nueva.
Solo inicializar registros alcanzados en su primer acceso de esa generación.
Reutilizar HeapRutas, con un heap separado por búsqueda y una entrada por
candidato. No permitir búsquedas concurrentes sobre esos mismos registros.

El núcleo Dijkstra compartido recibe operaciones para vecinos permitidos y
almacenamiento de registros; los wrappers de cazador y viaje mantienen fuentes
separadas. Cazador usa mapa físico y rango; viaje usa solo exploradas y recuerdos
abiertos, sin inventar rango ni calcular un límite recorriendo todo el esqueleto.
El primer salto de menor ID resuelve empates de costo total. Reiniciar campos
de prioridad y posición cuando cambia la generación.

No persistir auxiliares como conocimiento ni restaurar generaciones con el
pergamino. Al cargar, reconstruirlos desde posiciones consistentes. Cada paso
recalcula desde conocimiento vigente. Incluir inicialización por consulta y
liberación de H candidatos pendientes en el costo medido, no solo el bucle útil.

## Viaje: estado transitorio

Destino resuelto, en_curso, motivo_fin y observaciones del paso: hubo_dano y
habia_enemigos_al_entrar. Usar escalares/referencias, sin índices adicionales.
Resolver nombre una vez recorriendo el arreglo y comparando únicamente nombres
de exploradas, completo y sensible a mayúsculas. Dos coincidencias requieren ID.
No convertir el nombre completo a minúsculas ni descartar palabras.

Cada paso usa la misma acción ordinaria que el movimiento manual. Capturar
enemigos al entrar, antes de que los eventos posteriores los muevan o maten.
Capturar cada daño del intervalo aunque luego se cure. Comprobar esas causas,
terminación de partida, llegada y ruta conocida antes de otro paso.

El controlador deja cancelar entre acciones completas mediante entrada opcional
de consola. La vista detecta entrada pendiente sin exigir confirmación por paso;
si el jugador escribe, el viaje se cancela y se lee/procesa el comando. Preservar
la tecla detectada. No hilos ni colas adicionales. Replay no sondea teclado.

## Persistencia y aislamiento

Formato de modelo previsto: 5, con rechazo explícito de versiones anteriores.
Añadir esquemas y validaciones para conocimiento, recuerdos, salidas conocidas,
referencias físicas y deltas. Conservar ID/posición y el grafo de referencias
compartidas; no reconstruir recuerdos a partir del estado real de puertas.
Guardar historial reversible completo permitido por P1, incluidas listas anteriores.

El índice hash y los registros de búsqueda son derivados y se reconstruyen.
Guardar/cargar no observa todas las puertas ni amplía exploración. El viaje en
curso se detiene para devolver control antes de procesar guardar/cargar; no se
reanudan movimientos invisibles. La futura línea de tiempo reconstruirá
conocimiento independiente sin mutar el vivo; no se implementa ahora.
