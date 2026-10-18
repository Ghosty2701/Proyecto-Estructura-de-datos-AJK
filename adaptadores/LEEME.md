Benchmarks y verificación de adaptadores
======================================

Desde la raíz del repositorio, en PowerShell:

```powershell
python -m adaptadores.bench_adaptadores
python -m pytest -q
```

Para conservar una medición local:

```powershell
python -m adaptadores.bench_adaptadores | Tee-Object resultados_bench_juan.txt
```

Opciones disponibles:

```powershell
python -m adaptadores.bench_adaptadores --solo cache --cache-size 25 --rondas 5
python -m adaptadores.bench_adaptadores --solo guardado --salas 1000 --rondas 5
python -m adaptadores.bench_adaptadores --solo indice --tamanos 25 100 1000 --semilla 2042
```

El benchmark compara el AVL existente con un árbol simple, mide aciertos de
`CacheCatalogo` con mantenimiento LRU y recuperaciones de fichas liberadas desde
archivos reales. La fuente del catálogo es un paquete local sintético compatible
con `ModoOffline`; se comprueba que recuperar fichas persistidas no vuelva a pedirlas
a la fuente. No realiza HTTP.

La primera comparación de guardado usa los mismos registros sintéticos en JSON
compacto y en el contenedor binario indexado existente con bloques JSON UTF-8. Sirve
como referencia del contenedor. Ambos formatos codifican en memoria antes de
escribir. `leer_guardado` carga todos los bloques con una sola apertura del archivo;
la recuperación selectiva sigue usando el índice.

La segunda medición, "Modelo real", utiliza `estado_binario.py`: campos binarios
explícitos, referencias por ID y AVL. Compara su tamaño y lectura/decodificación con
un JSON que contiene exactamente los mismos registros, incluidos eventos, azar e
historial. Ambos se convierten a la misma representación de datos para comprobar la
equivalencia. La escritura preparada excluye la captura y codificación de ambos
formatos. Guardar y restaurar el modelo completo se miden adicionalmente; restaurar
entidades no es lo mismo que leer/decodificar registros y se reporta por separado.

Los tiempos muestran el menor promedio de las rondas indicadas, con unidades
explícitas. Las comprobaciones funcionales quedan fuera del cronómetro. Las lecturas
pueden aprovechar la caché del sistema operativo; las escrituras cierran el archivo
sin forzar `fsync`. No se afirma que sean mediciones de disco frío ni que validen el
límite de 20 ms de una partida completa.

Las correcciones del servicio aíslan cada carga de cripta en sus propios AVL y
publican la nueva carga después de recibir todas las páginas. El contenido anterior
se descarta al completar la carga. Las fichas del catálogo conservan su caché
independiente, que puede compartirse entre criptas con la misma versión de catálogo.

Juan eligió esquema explícito por entidad, IDs con AVL y binario propio por campos.
Está implementado en `adaptadores/estado_binario.py`. Conserva el estado actual y los
cinco intervalos de deltas existentes, sin cambiar el heap ni el mecanismo de
retroceso. `adaptadores/FORMATO_ESTADO.md` documenta el formato, API y límites.

`ServicioCripta.asegurar_contenido` anticipa por defecto solo la sala necesaria y
sus vecinas abiertas inmediatas. Si la estimacion no cabe en las solicitudes
normales restantes, activa una excepcion y completa lotes de hasta diez pendientes.
Si la sala actual ya esta disponible no solicita mas contenido solo para ampliar
su vecindad. No vuelve a pedir contenido que ya este en su AVL.
El catalogo usa por defecto precarga adaptativa: fichas necesarias
de la sala actual y vecinas abiertas que quepan en esas consultas, sin agregar
consultas solo por anticipacion. El botin se resuelve al incorporar sus enemigos.
Solo con la excepcion activa se anticipan otras fichas conocidas dentro de las
consultas necesarias, sin aumentar el numero de lotes de catalogo de esa operacion.
`precarga_adaptativa=False` conserva la politica anterior de resolver todo el
lote, utilizada como referencia de comparacion. Reutiliza el AVL, la LRU y
los archivos de la caché existente. Una ficha anticipada que salga de memoria se
recupera del disco sin repetir la solicitud de catálogo. La protección de fichas en
uso sigue dependiendo del callback `esta_en_uso` que entregue la capa de partida.
La precarga actual es síncrona.

`CacheCatalogo.faltantes(ids)` consulta memoria y disco para planificar sin
descargar fichas; la primera consulta valida la version del catalogo, igual que
las consultas existentes. Las fichas validas recuperadas se incorporan a la LRU.
No se crea un segundo indice ni se modifica su politica de desalojo.

`ClienteHTTP(reservar_imprevistos=True)` limita las solicitudes normales a
presupuesto menos `ceil(presupuesto / 5)`. Cuenta reintentos por separado y les
permite usar el margen reservado, siempre dentro del limite total. La aplicacion activa esta opcion. Por compatibilidad, el constructor sin la
opcion conserva el limite total anterior. El limite se comprueba antes de cada
intento; el botin desconocido y tipos futuros no pueden predecirse.
La excepcion preventiva de agrupacion usa el rendimiento observado del contenido,
fichas pendientes y una estimacion para tipos y botin desconocidos. No aumenta
los limites ni gasta la reserva en solicitudes normales.

`adaptadores.bitacora_partida.reproducir_bitacora` ejecuta la bitácora sin vista.
Primero verifica las versiones; después llama a `crear_partida(encabezado)` y a
`ejecutar_accion(partida, texto)` por cada acción, en su orden original. El constructor
debe usar la semilla del encabezado. El ejecutor debe lanzar una excepción o devolver
`False` si rechaza una acción. Un fallo detiene el replay y reporta el número y texto
de la acción. El adaptador no fija una sintaxis nueva para los comandos.

La prueba `test_replay_con_motor_real_reproduce_azar_efectos_y_retroceso` conecta esos
callbacks con `MotorEventos`, salas, un enemigo e inventario reales. Comprueba reloj,
vida, posición, agenda, estado del azar e inventario tras reproducir acciones con
veneno y pergamino. La aplicacion conecta la partida real mediante `--bitacora ruta.log`
y `--replay ruta.log`, incluyendo la seleccion del inventario y el uso de pergaminos.
El replay no crea una vista, no solicita entrada y no registra otro puntaje.
