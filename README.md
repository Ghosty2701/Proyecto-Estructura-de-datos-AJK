# Cripta

Primera partida de consola conectada al motor y al servicio oficial. El contenido,
las conexiones y las estadisticas se leen del servicio; no hay un mapa escrito
dentro del programa.

## Ejecutar en PowerShell

Desde la raiz del proyecto, con Python y las dependencias instaladas:

```powershell
python -m pip install requests pytest
python main.py --listar
python main.py --cripta cripta-01 --semilla 2026
```

Con el paquete local del curso, sin solicitudes HTTP:

```powershell
python main.py --offline --listar
python main.py --offline --cripta cripta-01 --semilla 2026
```

`--offline` usa `datos_offline`; para otra carpeta, usa `--offline ruta_del_paquete`.
Tambien se puede combinar con `--cargar` o `--replay`. Requiere los archivos del paquete local.

`python main.py --bench` ejecuta las mediciones de estructuras sin HTTP ni informes
persistentes. Usa `--repeticiones 1` para una revision rapida. Al terminar una sesion
de juego se muestran solicitudes, presupuesto y aciertos/fallos de cache en consola.

Para medir ciclos completos con datos reales: `python main.py --bench --cripta cripta-01`.
Se precarga la cripta fuera del cronometro y se informa el maximo de todos los ciclos
entre decisiones, sin red ni renderizado. Un ciclo de 20 ms o mas devuelve codigo 1.

Para registrar y reproducir los comandos con la misma semilla y versiones:

```powershell
python main.py --cripta cripta-01 --semilla 2026 --bitacora partida.log
python main.py --replay partida.log
```

Durante la partida, `guardar` y `cargar` usan `partida.bin` sin consumir tiempo.
Puedes elegir la ruta con `--archivo-guardado mi_partida.bin` y reanudar despues con
`python main.py --cargar mi_partida.bin`. Se permite guardar mientras se registra
una bitacora; cargar requiere otra ejecucion sin grabacion activa.

La bitacora no sobrescribe archivos existentes. Replay no crea una vista ni pide
entrada; muestra solo el resumen final. No registra otro puntaje y
requiere acceso a los datos de las versiones originales.

Escoge un ID de la lista del servicio. `cripta-01` estuvo disponible durante la
verificacion del 17 de octubre de 2026; la disponibilidad posterior depende del
servicio. La semilla es configurable y su valor predeterminado es 2026.

Tambien puedes ajustar la cache:

```powershell
python main.py --cripta cripta-01 --semilla 2026 --cache-size 25 --cache-dir .cache_cripta
```

Cada ejecucion usa un solo cliente HTTP y conserva su identificador entre
solicitudes. Se reutilizan la precarga, cache persistente, manejo de errores y
presupuesto de solicitudes de los adaptadores existentes. La carpeta de cache se
crea al utilizarla y esta excluida de Git. No contiene un guardado de la partida.

## Que puedes probar

| Comando | Accion |
| --- | --- |
| `w`, `a`, `s`, `d` o `ir n` | Moverse al norte, oeste, sur o este. |
| `atacar` o `atacar 2` | Atacar al enemigo indicado en la lista de la sala. |
| `recoger` o `recoger 2` | Recoger un objeto del suelo; coste 25 ajustado por velocidad. |
| `equipar` | Equipar el arma o armadura seleccionada con `sig`/`ant`; coste 50 ajustado por velocidad. |
| `usar` | Consumir la pocion, antidoto o antorcha seleccionada; coste 50 ajustado por velocidad. |
| `soltar` | Dejar en el suelo el objeto seleccionado; coste 25 ajustado por velocidad. |
| `retroceder` | Consumir un pergamino y deshacer el ultimo intervalo, sin tiempo adicional; hasta cinco acciones disponibles. |
| `guardar`, `cargar` | Guardar o restaurar el estado completo y los cinco intervalos disponibles. |
| `abrir n` | Abrir la puerta hacia el norte con la llave correspondiente; coste 50 ajustado por velocidad. |
| `esperar` | Dejar pasar el intervalo de una accion. |
| `inv`, `sig`, `ant`, `orden peso` | Consultar o recorrer el inventario, sin tiempo virtual. |
| `ayuda` | Consultar todos los comandos reconocidos por el controlador. |
| `salir` | Cerrar esta prueba, sin guardar. |

El motor existente determina tiempos, desempates, azar, movimientos enemigos,
combate, regeneracion y trampas. La vida y el reloj mostrados son los del modelo.
Los enemigos muertos desaparecen de la lista de objetivos y dejan su botin en el
suelo. Al morir el jugador, la consola muestra la derrota y termina.

Las salidas muestran direccion, nombre e ID de destino; las puertas cerradas se
presentan aparte con la llave requerida. El contador de red muestra solicitudes
consumidas y presupuesto. La bitacora conserva los ultimos 20 mensajes e incluye
tiempo virtual, daño de trampas, resultado de ataques y movimientos enemigos
visibles, ademas de regeneracion y avisos de efectos y entorno.

El inventario empieza vacio y permite recoger objetos y consultar sus vistas.

La victoria ocurre al entrar por la puerta de salida abierta con su llave.
Al ganar o morir se registra el resultado en `puntajes.json`; puedes indicar
`--nombre Kendall` y `--puntajes otra_ruta.json`. Salir voluntariamente no registra resultado.
El guardado usa el esquema binario 3, con inventario reversible, contadores, efectos y referencias compartidas a fichas.
Los archivos del esquema anterior se rechazan. No se presenta esta prueba como el
proyecto completo ni como evidencia del limite de 20 ms.

## Organizacion de esta integracion

- `main.py`: argumentos, composicion de componentes y mensajes de errores.
- `controlador/cargar_partida.py`: construye las salas con el AVL existente,
  resuelve sus conexiones y convierte contenido/catalogo en instancias.
- `controlador/partida.py`: expone el contrato que ya esperaba el controlador.
- `modelo/inventario_reversible.py`: extension de Kendall, pendiente de conectar
  al historial y al formato de guardado; vease su
  [contrato](modelo/CONTRATO_INVENTARIO_REVERSIBLE.md).

El cargador conserva los IDs y las fichas compartidas, convierte `guardian`
desde el valor `guardián` del servicio y utiliza `vida_max` cuando la vida de una
instancia llega como `null`. Los IDs de salas se buscan en O(log n). Las conexiones
se construyen una vez; convertir o precargar contenido no activa enemigos.

Antes de confirmar un movimiento se prepara su destino. Si ya esta cargado no se
recrean sus instancias. Las respuestas anticipadas permanecen a cargo de
`ServicioCripta`. La interfaz localiza enemigos por su sala actual, incluso si se
movieron desde otra sala. Esa consulta recorre las instancias cargadas; no se ha
medido todavia su comportamiento con criptas grandes.

Por defecto, el contenido se solicita para la sala necesaria y sus vecinas
inmediatas abiertas, en orden N, S, E, O. Si la estimacion indica que esa politica
no cabe en el presupuesto normal, se activa la excepcion de agrupacion amplia:
completa lotes de hasta diez pendientes, manteniendo la prioridad de la vecindad.
Si el contenido de la sala ya esta disponible,
no se abre otra consulta solo para ampliar su vecindad. El limite HTTP sigue siendo
diez salas, aunque esta politica normalmente solicita menos. El esqueleto completo
se conserva como requiere el proyecto. Anticipar contenido no activa enemigos.

El catalogo usa precarga adaptativa: resuelve las fichas necesarias de la sala
actual y aprovecha espacio en esas mismas consultas para las vecinas abiertas.
El botin se resuelve cuando corresponde incorporar sus enemigos. No abre otra
consulta exclusivamente para precarga. Solo con la excepcion activada aprovecha
espacio del mismo lote para otras fichas conocidas. Las fichas validas en disco
se reutilizan. Todo esto sigue siendo
sincrono, sin hilos. Limitar la anticipacion no libera automaticamente salas que
ya fueron visitadas; ese desalojo requiere otra integracion con el estado reversible.

`main.py` habilita una reserva inicial `ceil(presupuesto / 5)`: las solicitudes
normales tienen como limite el presupuesto menos esa reserva. Los reintentos de
HTTP 429 pueden usarla, pero el total nunca supera el presupuesto del servidor.
La consola muestra ambos contadores. Por ejemplo, para presupuesto 9 se permiten
7 solicitudes normales y se reservan 2. Cada reintento consume una solicitud real;
la reserva no se repone automaticamente tras un fallo. Otras clases de error se
informan sin agregar reintentos automaticos. Los consumidores anteriores de
`ClienteHTTP` mantienen su comportamiento salvo que habiliten
`reservar_imprevistos=True`, como hace la aplicacion.

La vecindad estricta no alcanzo para completar `cripta-01` y `cripta-02` con la
reserva. Kendall eligio permitir la excepcion por presupuesto. Antes de una carga
necesaria se estima el contenido restante segun las salas recibidas por consulta;
para el primer lote se usa el tamaño de la vecindad. Se suman lotes de fichas ya
conocidas que faltan, la validacion de version si corresponde y, mientras queden
salas desconocidas, una consulta prevista de tipos nuevos y otra de botin.

Si esa suma supera las solicitudes normales disponibles, se activa la agrupacion.
Se mantiene hasta cargar otra cripta para evitar cambios continuos de politica.
Es una
estimacion preventiva: no demuestra una necesidad matematica ni conoce todo el
catalogo futuro. Nunca eleva limites ni usa solicitudes normales de la reserva.

El OpenAPI actual describe salidas dirigidas: cada salida conserva su propia
puerta. Para trampas se convierte el contrato HTTP actual de daño directo; no se
inventa una interpretacion de pociones de velocidad ni de otros tipos de trampa.
Referencia del contrato HTTP: [documentacion oficial](https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/docs).
Las reglas del enunciado original mantienen prioridad.

Un error de red, presupuesto o datos durante la carga de un destino se informa
con contexto y devuelve el control a la consola. El movimiento no se confirma:
posicion, reloj e historial quedan como antes de intentarlo. Las solicitudes ya
realizadas y la cache no se deshacen. Se puede seguir actuando en salas disponibles
o salir; un presupuesto agotado no se reinicia ni se ignora. Si el fallo ocurre
antes de crear la partida, se informa y termina el arranque.
Los errores de programacion no se ocultan con una captura general.
El botin normal se retira al deshacer una muerte. Los pergaminos recogidos conservan
su estado fuera del historial y no se duplican al volver a derrotar al mismo enemigo.

## Pruebas

```powershell
python -m pytest -q
python -m pytest Pruebas/prueba_partida.py -v
```

Las pruebas automaticas de esta integracion usan el motor, la consola, el AVL,
la cache y el servicio existentes con respuestas sinteticas locales. No necesitan
red y no usan una partida simulada. La prueba manual contra el servicio es evidencia
separada: se inicio `cripta-01`, se entro al pasillo, se ataco y se proceso la derrota
con semilla 2026. No equivale a haber probado todas las criptas o todos los comandos.

Despues de corregir los lotes se repitio el recorrido `N, N` en `cripta-01` con
semilla 2026 y una cache temporal vacia: se descargaron las seis salas en un lote,
se usaron 6 de 9 solicitudes en total y se llego a la sala 3 en tiempo 200 sin
nuevas solicitudes al moverse. Esa es evidencia de la version consultada el
17 de octubre de 2026, no un presupuesto universal ni una prueba de victoria.

Para benchmarks y detalles de guardado, consulta
[adaptadores/LEEME.md](adaptadores/LEEME.md). El archivo [LEEME.md](LEEME.md)
conserva las notas historicas de la fase de efectos del motor.
