Guardado del modelo: esquema explícito y binario propio
=====================================================

Decisión elegida por Juan: campos explícitos por entidad, referencias por ID,
resolución mediante el AVL existente y binario propio por campos. El codec está en
`adaptadores/estado_binario.py`; el contenedor indexado sigue en
`adaptadores/guardado_binario.py`. El modelo, inventario, heap y retroceso no cambian.

El esquema actual es la version 2: incluye inventario reversible, deltas de suelo,
marcas de pergaminos, apertura con llave y estado de la sesion. Rechaza la version 1.

Uso desde la capa que ya dispone del modelo y las versiones:

```python
from adaptadores.estado_binario import (
    guardar_partida, cargar_partida, leer_identidad_guardada, leer_sala_guardada,
)

guardar_partida(
    "partida.bin", motor, jugador, salas,
    id_cripta=datos_cripta["id"],
    version_cripta=datos_cripta["version"],
    version_catalogo=version_catalogo,
    datos_extra={"acciones": acciones_jugador, "enemigos_derrotados": derrotados},
)

cargada = cargar_partida(
    "partida.bin",
    id_cripta=datos_cripta["id"],
    version_cripta=datos_cripta["version"],
    version_catalogo=version_catalogo,
)
motor, jugador, salas = cargada.motor, cargada.jugador, cargada.salas
datos_extra = cargada.datos_extra
```

`datos_extra` es opcional y admite registros de datos o listas de los tipos
contemplados por el esquema. Permite guardar contadores/indicadores de la capa de
partida; el codec no inventa ni actualiza esos contadores. Las versiones se pasan
explícitamente: guardar/cargar no efectúa HTTP. Si se omiten las versiones esperadas
al cargar, se reconstruye el estado autocontenido del archivo y su identidad queda
disponible en `cargada.identidad`; no se está validando contra un servidor externo.

`leer_identidad_guardada(ruta)` recupera la identidad desde el bloque global.
`leer_sala_guardada(ruta, id_sala)` recupera una vista de disco autocontenida, o
`None` si la sala no existe, mediante búsqueda binaria en el índice. No carga el
bloque global ni las otras salas. La vista contiene nombre, rastro, estado de carga,
salidas, actores con estadísticas, identificadores de objetos y trampas. No es una
sala del motor con referencias externas parcialmente reconstruidas. Los registros
completos de entidades se almacenan en los bloques y se reconstruyen al cargar la
partida completa.

Representación y reconstrucción
-------------------------------

1. Ordenar salas con la función pública de ordenamiento existente.
2. Asignar IDs de archivo a las entidades alcanzables siguiendo solo los campos
   enumerados en `_ESQUEMAS`. Un AVL relaciona la identidad en memoria con el ID.
   `id(objeto)` solo es una clave temporal del AVL: nunca se escribe como ID de
   archivo. Las referencias compartidas reutilizan el mismo ID.
3. Guardar entidades y sus contenedores en bloques por sala. Reloj, agenda,
   historial, azar y datos sin sala se guardan en el bloque global. Cada bloque de
   sala incluye además su vista autocontenida para la recuperación selectiva.
4. Al cargar, crear primero todas las entidades de los tipos conocidos.
5. Resolver todas las referencias mediante un AVL de ID a entidad. Así se recuperan
   las puertas compartidas, enlaces de eventos y nodos del inventario sin duplicarlos.
6. Validar estructura, heap, secuencias activas, enlaces, inventario, deltas y raíces
   antes de publicar el modelo cargado. Una carga no modifica una partida viva.

Los campos requeridos y opcionales de cada tipo son una lista explícita en el código.
Se conservan listas mutables y registros de fichas JSON con su identidad. Los
`dict` de fichas/datos extra son registros de datos; los índices de entidades y
referencias usan AVL, no `dict`. Las tuplas del historial y del estado aleatorio se
guardan como valores de tupla, manteniendo las referencias a entidades que contienen.

Se contemplan los tipos actuales de motor, agenda, eventos, actores, salas, puertas,
salidas, efectos, trampas, inventario, nodos y deltas. `ObjetoPartida` proporciona un
registro explícito para objetos del inventario; los registros `SimpleNamespace` de
las pruebas actuales se admiten solo con los campos enumerados en el esquema.
Tipos nuevos o atributos fuera del esquema producen `ErrorGuardado` en lugar de
perderse silenciosamente. Incorporarlos requiere extender el esquema y revisar la
versión del formato con el equipo. No se usa `pickle`, carga dinámica de clases ni
serialización automática de `__dict__`.

Formato binario, versión 1
-------------------------

El contenedor exterior conserva `CRPT`, su versión y el índice por sala. Su
disposición exacta está en las constantes `FORMATO_*` de `guardado_binario.py`.
Offsets, longitudes e IDs de sala son enteros sin signo de 32 bits; este contenedor
no está diseñado para archivos de más de 4 GiB.

El bloque global comienza por `MDLO` y una versión `<H`. Continúa con tres textos
(id de cripta y versiones), los IDs `<I` del motor, jugador y datos extra (0 indica
ausencia de extra), cantidad de salas y pares `(id_sala, id_entidad_sala)`, seguidos
de los registros globales.

Cada bloque de sala comienza por `SALA`, versión `<H`, ID de su entidad `<I`, vista
de la sala y sus registros. Una lista de registros contiene cantidad `<I` y, por
cada registro, longitud `<I` seguida de sus bytes. Cada registro comienza con ID de
entidad `<I` e ID de tipo `<B`. Los IDs de tipo y orden de campos son los de
`_ESQUEMAS`. Los campos opcionales tienen una marca 0/1 previa al valor.

Cada valor usa una etiqueta `<B`:

| Etiqueta | Valor y contenido |
|---|---|
| 0 | `None`, sin contenido adicional |
| 1 / 2 | `False` / `True`, sin contenido adicional |
| 3 | Entero: longitud `<I` y bytes little-endian con signo; admite semillas grandes |
| 4 | Número finito de doble precisión `<d` |
| 5 | Texto: longitud `<I` y bytes UTF-8 |
| 6 | Bytes: longitud `<I` y contenido |
| 7 | Referencia a ID de entidad `<I` |
| 8 | Tupla: cantidad `<I` seguida de sus valores |

Listas, registros de fichas y el generador aleatorio tienen tipos propios en el
esquema. El generador se restaura con su estado actual; los intervalos conservan
sus estados de azar anteriores. Los eventos cancelados alcanzables se conservan:
algunos son necesarios para volver a activar eventos al deshacer.

El historial sigue conteniendo como máximo cinco registros de deltas. Guardar el
estado actual en disco no convierte el retroceso en snapshots por acción. El
pergamino consumido sigue fuera del historial, incluso después de cargar.

Escritura y costos
-----------------

La captura y validación se completan antes de abrir el destino. La escritura usa un
archivo temporal en su mismo directorio y `os.replace`; si falla la publicación, el
guardado anterior se conserva. No se fuerza `fsync`, por lo que esto no constituye
una garantía contra un corte de energía.

Con N entidades/contenedores, E campos y referencias y B bytes, registro y carga
usan aproximadamente O(B + (N + E) log N), más el ordenamiento existente de salas al
guardar. El agrupamiento por sala y las comprobaciones de pertenencia usan AVL;
no requieren recorrer todas las salas por cada actor. La memoria es O(B + N + E).
La lectura selectiva cuesta O(log S + B_s), para S salas y B_s bytes del bloque.

Verificación y medición
----------------------

```powershell
python -m pytest Pruebas/prueba_estado_binario.py -v
python -m pytest -q
python -m adaptadores.bench_adaptadores --solo guardado
```

Las pruebas incluyen continuación determinista y cinco retrocesos después de cargar,
equipo/cursor/orden del inventario, referencias compartidas, muertes, eventos
cancelados, efectos, pergaminos, archivos incompatibles y escritura fallida.
La lectura selectiva se verifica contando bytes leídos del archivo real.

El benchmark conserva la comparación del contenedor original y agrega el codec por
campos con el modelo real. Compara los mismos campos completos contra JSON en
tamaño y lectura/decodificación a registros; mide por separado la escritura de
representaciones preparadas y el guardado/restauración completos del modelo. No
confunde parsear JSON con reconstruir entidades, ni estos tiempos de persistencia
con la validación de 20 ms de un ciclo de juego.

Queda integrar estas funciones con el objeto de partida y las banderas de la
aplicación. La persistencia no implementa las acciones de inventario, victoria o
puntaje pendientes del modelo ni cambia los archivos de los otros integrantes.
