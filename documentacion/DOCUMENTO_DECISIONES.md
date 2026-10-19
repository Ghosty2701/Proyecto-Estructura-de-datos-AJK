# Documento de Decisiones de Diseño

Andrey: motor, agenda, retroceso y rastro. Juan: red, precarga de salas, resolución del catálogo, caché persistente, guardado binario y bitácora/replay (decisiones 2, 3, 4, 10 y 11). Kendall: inventario, consola y ordenamiento. Las integraciones conectan las tres partes mediante el controlador; el motor no depende de la vista ni de HTTP.

Las secciones corresponden a §4.1–§4.11 del enunciado. Las cifras proceden de los [benchmarks actualizados](evidencia/bench_subsistemas.txt) y las [comparaciones adicionales](evidencia/mediciones.json), con Python 3.14.6 en Windows. El JSON distingue las comparaciones sintéticas previas de la verificación oficial actual y conserva sus huellas de código. Los benchmarks de estructuras informan mínimos de cinco repeticiones; el ciclo completo informa su máximo. Las frecuencias indicadas corresponden a cada carga experimental.

# Documento de Decisiones de Diseño — (ANDREY CHACÓN SÁNCHEZ)

Secciones: **Agenda de eventos**, **Retroceso** y **Rastro del jugador**.

## 1. Agenda de eventos

- **Problema:** seleccionar el siguiente evento y gestionar cancelaciones y cambios de velocidad; la carga medida realiza 2000 inserciones, 500 cancelaciones y 1500 extracciones activas.
- **Alternativas:** lista ordenada o heap binario. Se descarta la lista porque cada inserción desplaza hasta H posiciones; el benchmark compara ambas.
- **Decisión:** heap propio, desempate por secuencia y cancelación perezosa. El ascenso/descenso mueve un hueco para evitar intercambios y tuplas de comparación por nivel.
- **Complejidad:** insertar/extraer O(log H); marcar cancelación O(1). Descartar varios cancelados requiere varias extracciones.
- **Evidencia:** 2000 inserciones, 500 cancelaciones y 1500 eventos activos extraídos: heap 8.462 ms frente a lista 246.837 ms.
- **Límite:** los eventos cancelados permanecen hasta ser extraídos y pueden acumularse.

## 6. Retroceso

- **Problema:** deshacer intervalos completos sin copiar toda la partida; la carga medida revierte 2000 deltas de vida/rastro en un intervalo.
- **Alternativas:** snapshots completos —descartados por la prohibición y por copiar datos no modificados— o deltas de cambios.
- **Decisión:** hasta cinco intervalos de deltas, aplicados en orden inverso. Se restauran reloj, azar, eventos, vida, efectos, inventario y suelo; el pergamino consumido queda fuera.
- **Complejidad:** registrar un delta O(1) amortizado; deshacer depende de su cantidad y del costo de restaurar eventos, inventario y suelo.
- **Evidencia:** 2000 deltas de vida/rastro se deshicieron en 0.289 ms; contenedores del registro: 160528 bytes, sin contar entidades referenciadas.
- **Límite:** cinco intervalos no implica memoria constante en bytes ni acceso a cualquier punto del pasado.

## 7. Rastro del jugador

- **Problema:** escoger el vecino con rastro más reciente sin revisar toda la cripta; la carga mayor mide 10000 decisiones de 100 rastreadores, con cuatro salidas por decisión.
- **Alternativas:** recorrer el mapa o consultar directamente las salidas. Se descarta el recorrido global por trabajo O(S) por decisión frente al grado local y por la prohibición del enunciado.
- **Decisión:** marca temporal en cada sala, válida durante menos de 400 unidades; solo salidas abiertas y desempate por menor ID.
- **Complejidad:** actualizar O(1); decidir O(d), siendo d la cantidad de salidas.
- **Evidencia:** 100 decisiones en un mapa de 4000 salas: vecinos 0.1127 ms, recorrido global 25.1588 ms.
- **Límite:** no es búsqueda global de caminos; otros métodos de la partida sí recorren enemigos cargados.

# Documento de Decisiones de Diseño — (JUAN)

Secciones: **Precarga de salas**, **Resolución del catálogo**, **Caché persistente**, **Guardado binario** y **Bitácora y replay**.

## 2. Precarga de salas

- **Responsable de la decisión:** Juan.
- **Problema:** preparar destinos sin gastar solicitudes ni memoria innecesarias; se miden recorridos de tres y 200 salas para comparar consultas y anticipaciones.
- **Alternativas:** cargar al entrar, anticipar vecinas o completar lotes amplios. Cargar solo al entrar desaprovecha lotes; ampliar siempre descarga salas que quizá no se visiten.
- **Decisión:** vecindad abierta por defecto y agrupación hasta diez cuando la estimación de presupuesto lo requiere. El margen preventivo del 20 % redondeado hacia arriba orienta la precarga; las consultas necesarias pueden consumirlo sin superar el presupuesto total, incluidos reintentos.
- **Complejidad:** buscar una sala O(log S); seleccionar vecindad O((d + 1) log S). Ampliar lotes y estimar tipos puede recorrer contenido acumulado.
- **Evidencia:** corredor sintético de 200 salas: vecindad 100 llamadas de contenido; lotes amplios 20. Visitando solo tres salas, cargan cuatro y diez respectivamente.
- **Límite:** son llamadas locales de prueba, no HTTP real; la estimación no garantiza completar cualquier cripta.

## 3. Resolución del catálogo

- **Responsable de la decisión:** Juan.
- **Problema:** convertir IDs de tipos y botín en fichas compartidas, conservando estados independientes por instancia; se miden consultas por ficha en índices de 25, 100 y 1000 IDs.
- **Alternativas:** búsqueda lineal, árbol simple o AVL propio. Se descartan las dos primeras por su peor caso O(T) al resolver repetidamente tipos, especialmente con IDs ordenados.
- **Decisión:** AVL para localizar fichas y referencias ligeras compartidas por ID.
- **Complejidad:** localizar una referencia O(log T); resolver un lote añade IO y deduplicaciones que pueden costar O(m²).
- **Evidencia:** con 1000 IDs ordenados, altura AVL 10 frente a 1000 del árbol simple; búsquedas de 0.810 frente a 39.205 µs/ficha.
- **Límite:** el índice de referencias ligeras crece con los tipos conocidos, aunque se liberen sus datos completos.

## 4. Caché persistente

- **Responsable de la decisión:** Juan.
- **Problema:** reutilizar fichas y recuperar las liberadas sin repetir red; se miden accesos residentes y 500 recuperaciones desde disco.
- **Alternativas:** FIFO o LRU; memoria solamente o persistencia por versión. FIFO ignora los accesos recientes; sin disco, una ficha desalojada requiere otra solicitud.
- **Decisión:** AVL, lista doble LRU y JSON por ficha y versión. Desalojar vacía los datos de la referencia compartida; no elimina su identidad. El tope es estricto: la precarga opcional puede quedarse solo en disco; se comprueba la capacidad antes de preparar una acción.
- **Complejidad:** acierto O(log C), enlaces LRU O(1); seleccionar una ficha no protegida puede recorrer candidatos y entidades en uso.
- **Evidencia:** acierto 0.673 µs; recuperar desde disco, reinsertar y desalojar 169.558 µs. Se midieron 500 recuperaciones sin HTTP.
- **Límite:** si las fichas protegidas necesarias superan `--cache-size`, la acción se rechaza sin avanzar ni consumir pergaminos. Se informa el mínimo para reanudar con más capacidad: conservar todas y respetar un tope menor es imposible. El tope mide fichas residentes, no todos los bytes del proceso.

## 10. Guardado binario

- **Responsable de la decisión:** Juan.
- **Problema:** recuperar una sala sin cargar todo el archivo y restaurar las referencias compartidas del modelo; se miden guardado completo, restauración completa y lectura de una sala en un modelo de 200 salas con dos acciones de historial.
- **Alternativas:** JSON completo o formato binario indexado por bloques. Se descarta JSON como guardado principal porque recuperar una sala exige leer el documento completo; permanece como referencia de tamaño y tiempos.
- **Decisión:** contenedor `CRPT` versión 1, índice de ID/offset/longitud y esquema explícito de entidades versión 3. El AVL resuelve referencias al cargar. La lectura selectiva devuelve una vista de sala, no un motor parcialmente reconstruido.
- **Complejidad:** sala selectiva O(log S + B_s); captura/carga aproximada O(B + (N + E) log N), más ordenamiento de salas al guardar.
- **Evidencia:** modelo de 200 salas: binario 56789 bytes, JSON equivalente 132292. Restauración completa 22.893 ms; vista selectiva 0.17967 ms. JSON fue más rápido al decodificar a registros.
- **Límite:** offsets de 32 bits, rechazo de esquemas anteriores y ausencia de garantía ante corte eléctrico. Una restauración completa no es un ciclo normal de juego.

## 11. Bitácora y replay

- **Responsable de la decisión:** Juan.
- **Problema:** repetir acciones con la misma semilla y versiones, sin interacción; la comparación adicional registra y reproduce 100 acciones.
- **Alternativas:** comandos solos o comandos con encabezado de identidad y versiones. Se descartan comandos solos porque no permiten rechazar un catálogo o una cripta incompatibles ni reproducir el azar.
- **Decisión:** log de texto nuevo, encabezado `CRIPTA-LOG 1` y comandos añadidos tras acciones exitosas. Replay comparte el ejecutor del controlador sin crear vista.
- **Complejidad:** escribir O(L) por comando; leer O(B) y reproducir según el costo acumulado de las acciones. El lector mantiene las acciones en memoria.
- **Evidencia:** 100 acciones, log de 923 bytes y replay de 5.2759 ms, con igualdad de estado y azar.
- **Límite:** requiere datos compatibles. Se puede guardar mientras se graba, pero no cargar; el log no representa ese salto de historia.

# Documento de Decisiones de Diseño — (KENDALL PALACIOS AZOFEIFA)

Secciones: **Problema 4 (Inventario)**, **Problema 7 (Bitácora de pantalla)** y **Problema 8 (Ordenamiento)**, más la parte del inventario que se integra con el retroceso (§2.11).

> **Sobre las mediciones.** Salen de `modelo/bench_alternativas_rol_c.py` (se ejecuta con `python main.py --bench` una vez enganchado, o con `python -m modelo.bench_alternativas_rol_c`) y del `--bench` existente del repo. Se corrieron en Linux con Python 3.12.3, semilla 2026, y se reporta el **menor tiempo observado**. Los valores absolutos dependen del equipo: **antes de entregar, repitan la corrida en su máquina y reemplacen las cifras si difieren**. Los resultados completos están en `resultados_bench_rol_c_2026-10-17.txt`.

---

## 5. Inventario

- **Problema:** recorrer en ambos sentidos, equipar, soltar el objeto seleccionado y producir vistas ordenadas; la carga ejecuta 1000 inserciones, recorrido al centro, equipo y 1000 retiros.
- **Alternativas:** arreglo o lista doble. Se descarta el arreglo para el orden real porque retirar por cursor desplaza elementos; se mantiene como alternativa medida y para vistas temporales.
- **Decisión:** lista doble con cursor; enlaces adicionales para separar objetos reversibles de pergaminos. Las vistas se ordenan aparte.
- **Complejidad:** recoger, mover cursor y retirar el nodo actual O(1); buscar/listar O(I). Validar o restaurar un cambio reversible puede recorrer O(I).
- **Evidencia:** carga de 1000 inserciones y retiros: 1.825 ms. En la comparación adicional previa, solo retiros centrales: lista 0.3681 ms, arreglo 0.1771 ms.
- **Límite:** el arreglo de Python fue más rápido en esa muestra; se elige la lista por el retiro por referencia sin desplazamientos, no por ganar todos los tiempos.

## 8. Bitácora de pantalla

- **Problema:** conservar los últimos 20 mensajes sin desplazar los anteriores; la comparación adicional ejecuta 20000 inserciones y verifica los 20 retenidos.
- **Alternativas:** lista con eliminación al frente o búfer circular. Se descarta la eliminación al frente porque desplaza mensajes, operación expresamente restringida.
- **Decisión:** arreglo fijo con índice inicial y sobrescritura del mensaje más antiguo.
- **Complejidad:** agregar O(1); consultar todos O(K), con K = 20.
- **Evidencia:** 20000 inserciones: búfer 3.2291 ms, lista 2.3701 ms; ambos retuvieron los mismos 20 mensajes.
- **Límite:** se elige por evitar desplazamientos, aunque la lista fue más rápida en esta muestra. Los bytes dependen de la longitud de los textos.

## 9. Ordenamiento

- **Problema:** ordenar vistas sin modificar el inventario y elegir algoritmo según los datos; se miden listas de 16 y 256 elementos con orden aleatorio, casi ordenado y comparación costosa.
- **Alternativas:** insertion sort o merge sort. Insertion evita auxiliares en listas pequeñas; merge evita el peor caso cuadrático en listas grandes desordenadas. Se comparan ambos con las mismas entradas.
- **Decisión:** insertion para listas pequeñas o con pocos descensos; merge para las demás. Umbrales: 32 elementos, u ocho si la comparación se marca costosa; hasta 5 % de descensos para considerar casi ordenado. En listas grandes el intento de insertion se limita a `n * n.bit_length()` movimientos; al excederlo se usa merge sobre la entrada original.
- **Complejidad:** insertion independiente O(n) ordenado y O(n²) en peor caso; merge O(n log n), espacio auxiliar O(n). El selector acota el intento y garantiza O(n log n) para listas grandes, suponiendo claves de costo constante.
- **Evidencia:** 256 elementos mezclados: insertion 2.590 ms y merge 0.601 ms; casi ordenados: 0.046 y 0.456 ms. La regresión de dos bloques invertidos de 1024 elementos verifica el cambio a merge y una cota de comparaciones O(n log n).
- **Límite:** una clasificación inicial equivocada añade un intento acotado antes de merge. Los puntajes se guardan por orden de llegada y `--ver-puntajes` genera una vista estable mediante el selector propio, agrupada por cripta, versión y resultado.

## Problema 4 — Inventario (§4.5)

### 1. Problema
El jugador lleva un número acotado de objetos (`inventario_max`). Debe poder recorrerlos hacia adelante y hacia atrás, soltar **el objeto que está viendo, en cualquier posición, sin que el costo dependa de dónde esté**, equipar un objeto (que pasa al frente del orden real) y ver el inventario ordenado por peso, valor o nombre sin alterar el orden real.

Operaciones que el programa ejecuta y cuándo:
- `recoger`, `soltar_actual` y `equipar_actual`: a lo sumo una por acción del jugador.
- `avanzar` y `retroceder` (comandos `sig` y `ant`): una por comando, y no consumen tiempo virtual.
- `vista_ordenada`: solo cuando el jugador escribe `orden peso|valor|nombre`.
- `consumir_primero`: al usar un objeto consumible, por ejemplo el pergamino de retroceso.

*Frecuencia:* son operaciones por decisión del jugador, no por evento del reloj, así que el volumen es bajo. No se midió su frecuencia sobre una cripta real; puede extraerse reproduciendo una partida con `--replay`.

### 2. Alternativas consideradas
1. **Arreglo contiguo con desplazamiento escrito a mano.** Soltar o equipar en una posición `i` desplaza los elementos que siguen (o los que preceden).
2. **`list` nativa de Python con `pop(i)` e `insert(0, x)`.** El desplazamiento lo hace el intérprete en C (`memmove`).
3. **Lista doblemente enlazada con cursor** (la elegida).

Descartadas: la 1, por costo dependiente de la posición; la 2, porque su costo sigue dependiendo de la posición (ver evidencia) y por usar la lista como la estructura misma en vez de implementarla.

### 3. Decisión
**Lista doblemente enlazada** (`NodoInventario` con `anterior`/`siguiente`) y un **cursor** que referencia el nodo visto.
- Soltar el objeto visto es desconectar el nodo de sus vecinos: O(1), sin importar la posición.
- Equipar es un *splice*: desenganchar el nodo y reengancharlo al frente, O(1).
- Las ranuras de arma y armadura son **dos atributos**, no un diccionario (§7).
- El orden real y las vistas ordenadas están separados: `vista_ordenada(clave)` arma un arreglo aparte de referencias y lo ordena con `comun/ordenamiento.py`, sin tocar la lista.
- El inventario es genérico: no asume `.peso`, `.valor` ni `.clase`; recibe la función clave y el tipo de equipo desde quien lo llama.
- Con el inventario lleno, `recoger` devuelve `False` y no cambia nada (Apéndice B).

### 4. Análisis de complejidad

| Operación | Costo |
|---|---|
| `recoger`, `soltar_actual`, `equipar_actual`, `avanzar`, `retroceder` | O(1) |
| `consumir_primero` | O(n) buscar + O(1) retirar |
| `listar` | O(n) |
| `vista_ordenada` | O(n) para copiar + costo del ordenamiento (§Problema 8) |

La operación más frecuente es soltar o equipar el objeto visto, y es O(1). `consumir_primero` es O(n), pero n ≤ `inventario_max`.

### 5. Evidencia empírica
Soltar el objeto que se está viendo (µs, menor tiempo observado):

| n | posición | lista enlazada | arreglo manual | `list.pop` nativo |
|---|---|---|---|---|
| 10 | medio | 0.67 | 0.37 | 0.13 |
| 1000 | inicio | 0.46 | 32.27 | 0.25 |
| 1000 | medio | 0.59 | 18.87 | 0.20 |
| 1000 | final | 0.52 | 0.33 | 0.12 |
| 10 000 | inicio | 1.63 | 349.24 | 23.82 |
| 10 000 | medio | 1.66 | 186.20 | 12.19 |
| 10 000 | final | 1.77 | 1.73 | 0.38 |

Equipar un objeto del medio (µs):

| n | lista enlazada | arreglo manual |
|---|---|---|
| 10 | 0.79 | 0.41 |
| 1000 | 0.55 | 15.16 |
| 10 000 | 1.81 | 179.79 |

Lectura honesta de los datos:
- **El costo de la lista enlazada no depende de la posición** (a 10 000 elementos: 1.63, 1.66 y 1.77 µs en inicio, medio y final). Es el requisito del §4.5.
- **El arreglo manual sí depende de la posición**: a 10 000 elementos pasa de 1.73 µs al final a 349 µs al inicio (≈200 veces más).
- **`list.pop` nativo es más rápido que la lista enlazada hasta alrededor de 1000 elementos** (0.2 µs frente a 0.5 µs), porque el desplazamiento corre en C. Pero su costo también depende de la posición (12–24 µs en el inicio y el medio a 10 000 elementos, frente a 0.38 µs al final), y a 10 000 elementos pierde frente a la lista enlazada al soltar en el inicio o en el medio (solo gana al soltar al final).
- **Con n ≈ 10** (el `inventario_max` del ejemplo del enunciado) las tres opciones cuestan menos de 1 µs. No hay diferencia práctica de rendimiento.
- El `--bench` del repo mide el inventario con 1000 inserciones, recorrido al centro, equipar y 1000 retiros: ≈1.09 ms en total.

### 6. Límites conocidos
- Con `inventario_max` pequeño, la elección se sustenta en el **requisito** (costo independiente de la posición) y en que la lista enlazada escala sin degradarse, no en que sea más rápida hoy. Con n ≤ 1000, una `list` nativa sería igual o más rápida en CPython.
- Alcanzar un objeto por su posición es O(distancia) con el cursor. Es correcto para recorrer con `sig` y `ant`, pero un acceso aleatorio por índice no sería eficiente.
- Si se agregaran más ranuras de equipo, los dos atributos ya no bastarían.
- `consumir_primero` crece linealmente con el inventario.

### 4.b Inventario reversible (parte de §2.11 / §4.6 a cargo del Rol C)

**Problema.** Recoger, soltar, equipar y consumir deben poder deshacerse con el pergamino de retroceso, **sin guardar copias del inventario**. Además, el propio pergamino queda fuera de la reversión: ni su consumo ni los pergaminos recogidos o soltados durante el intervalo se deshacen.

**Alternativas.**
1. *Copiar el inventario antes de cada acción*: prohibido por el §2.11 y el §4.6.
2. *Registrar funciones inversas que reinsertan el nodo junto a los vecinos recordados*: se exploró y funcionaba. Pero si un pergamino vecino había desaparecido, el objeto volvía solo "cerca" de su posición, y la cantidad podía superar `inventario_max`. Se descartó por no restaurar el orden exacto.

**Decisión.** `InventarioReversible` extiende a `Inventario` y mantiene, además de la lista real, una **segunda cadena de enlaces que omite los pergaminos**. Cada operación reversible (`recoger_reversible`, `soltar_actual_reversible`, `equipar_actual_reversible`, `consumir_primero_reversible`) devuelve `(resultado, cambio)`. El `CambioInventario` guarda un número **constante** de referencias (nodo, vecinos reales y reversibles, cursor, equipo previo), y `deshacer_cambio(cambio)` lo restaura. Los pergaminos devuelven registro `None`: no se deshacen. Si al deshacer no hay espacio, se lanza `ErrorInventario` **antes** de modificar algo.

**Complejidad.** Registrar un cambio es O(1). **Deshacer es O(n)**, porque valida pertenencia y busca el hueco real.

**Evidencia (µs, soltar un objeto del medio):**

| n | soltar sin registro | soltar con registro | deshacer |
|---|---|---|---|
| 10 | 0.45 | 1.33 | 1.73 |
| 100 | 0.50 | 1.59 | 7.26 |
| 1000 | 1.14 | 2.20 | 60.80 |
| 10 000 | 3.73 | 6.68 | 585.58 |

Registrar cuesta pocas veces más que soltar sin registro, y deshacer crece aproximadamente de forma lineal (×10 de elementos ≈ ×10 de tiempo), lo que confirma el análisis.

**Límites.** Hay que deshacer en orden inverso (LIFO). No se deben mezclar cambios registrados con operaciones sin registro sobre objetos ordinarios. La clase del objeto no puede cambiar mientras está en la lista. A fecha de esta redacción, `controlador/partida.py` todavía usa el `Inventario` común y no las operaciones `*_reversible`, de modo que la integración con el historial de retroceso está **pendiente**.

---

## Problema 7 — Bitácora de pantalla (§4.8)

### 1. Problema
La interfaz muestra solo los **últimos 20 mensajes**. La memoria usada debe ser **constante** durante toda la partida y agregar un mensaje **no debe desplazar físicamente** los 19 anteriores.

Operaciones: `agregar` una vez por mensaje del juego (cuántos por acción lo decide la partida) y `mensajes()` una vez por cada pantalla dibujada, es decir, por decisión del jugador. *No se midió la cantidad de mensajes por acción en una cripta real.*

### 2. Alternativas consideradas
1. **Lista que crece sin límite** y se muestra `lista[-20:]`.
2. **Lista recortada**: `append` y, si pasa de 20, `del lista[0]`.
3. **Cola de la biblioteca estándar** (`collections.deque`).
4. **Búfer circular** sobre un arreglo fijo (el elegido).

Descartadas: la 1, por memoria no acotada; la 2, por desplazar físicamente los elementos, lo que el enunciado excluye de forma literal; la 3, porque el §7 pide implementar las estructuras y no usar equivalentes de biblioteca.

### 3. Decisión
**Búfer circular**: arreglo de tamaño fijo (20 por defecto, configurable), con `inicio` y `cantidad`. La posición de escritura es `(inicio + cantidad) % capacidad`. Cuando está lleno, se sobrescribe el mensaje más antiguo y solo avanza `inicio`. Un contador `total_generados` lleva la cuenta histórica sin gastar memoria.

### 4. Análisis de complejidad
`agregar`: O(1). `mensajes()`: O(capacidad), que es O(1) porque la capacidad es fija. Memoria: O(capacidad), independiente de la duración de la partida.

### 5. Evidencia empírica
Tiempo por mensaje agregado (µs):

| mensajes | búfer circular | lista recortada | lista sin límite |
|---|---|---|---|
| 1000 | 0.139 | 0.049 | 0.013 |
| 100 000 | 0.149 | 0.055 | 0.016 |

Memoria retenida tras N mensajes (KB, `tracemalloc`):

| mensajes | búfer circular | lista sin límite |
|---|---|---|
| 1000 | 1.6 | 66.1 |
| 10 000 | 1.6 | 668.0 |
| 100 000 | 1.6 | 6728.4 |

Lectura honesta:
- El búfer mantiene **1.6 KB constantes**; la lista sin límite crece de forma proporcional (6.7 MB a 100 000 mensajes).
- **El búfer circular es más lento por mensaje que la lista recortada** (≈0.15 µs frente a ≈0.05 µs) porque la aritmética de módulo corre en Python y `del lista[0]` en C. La diferencia es de décimas de microsegundo por mensaje y es irrelevante en la práctica: con 20 posiciones, desplazar 20 referencias es casi gratis.
- Por eso la decisión **no se apoya en la velocidad**: la lista recortada tiene memoria constante, pero incumple el requisito literal de no desplazar físicamente. El búfer lo cumple por construcción.

### 6. Límites conocidos
- La capacidad es fija. Mostrar un número variable de mensajes, o filtrar por tipo, exigiría rediseñar.
- Si el requisito de "no desplazar" no existiera, la lista recortada sería una alternativa más simple y más rápida con 20 elementos.

---

## Problema 8 — Ordenamiento dinámico (§4.9)

### 1. Problema
Se ordena en distintos contextos (vistas del inventario, tabla de puntajes, listas auxiliares) con datos de tamaños y grados de desorden muy distintos, a veces con comparaciones costosas. Hay que implementar **al menos dos algoritmos con características distintas** y que el programa **elija automáticamente** según propiedades medibles. No se permite `list.sort()` ni `sorted()`.

Frecuencia: ordenar es una operación puntual (comando `orden`, o al mostrar tablas), no ocurre en el bucle de eventos. *No se midió su frecuencia en una partida real.*

### 2. Alternativas consideradas
1. **Quick Sort con pivote fijo** (primer elemento).
2. **Heap Sort.**
3. **Insertion Sort + Merge Sort con selector** (la elegida).

Para poder medirlas directamente, las dos primeras se implementaron solo en el script de benchmark; el programa no las usa.

### 3. Decisión
- **Insertion Sort**: estable y adaptativo; cerca de O(n) si los datos están casi ordenados; sin recursión ni memoria extra; peor caso O(n²).
- **Merge Sort**: estable; O(n log n) garantizado sin importar el orden de entrada, a costa de listas auxiliares.
- **Selector `ordenar`**, con tres señales medibles:
  1. *Tamaño:* si n ≤ 32, Insertion Sort.
  2. *Desorden:* se cuentan los "descensos" (`dato[i] > dato[i+1]`) en una pasada O(n); si son ≤ 5 % de n, Insertion Sort.
  3. *Costo de comparación:* si el llamador la marca costosa, el umbral de "pequeño" baja a 8, para que casi siempre gane Merge Sort.
  
  En el resto de casos, Merge Sort.
- Todas las funciones son **no destructivas** (devuelven una lista nueva) y **estables**. Un `ContadorOperaciones` opcional cuenta comparaciones y movimientos.

### 4. Análisis de complejidad

| | Mejor | Promedio | Peor | Memoria extra |
|---|---|---|---|---|
| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) |
| Selector | O(n) para decidir, más el algoritmo elegido | | | |

### 5. Evidencia empírica
Tiempo (ms) / comparaciones. Selecciones de la tabla completa (16 casos en el archivo de resultados):

| n | datos | insertion | merge | eligió | más rápido |
|---|---|---|---|---|---|
| 16 | mezclado | 0.006 / 72 | 0.014 / 47 | insertion | insertion |
| 256 | casi ordenado | 0.025 / 256 | 0.250 / 1024 | insertion | insertion |
| 256 | mezclado | 1.108 / 15 624 | 0.346 / 1717 | merge | merge |
| 1024 | casi ordenado | 0.119 / 1024 | 1.194 / 5120 | insertion | insertion |
| 1024 | mezclado | 22.616 / 254 966 | 1.799 / 8948 | merge | merge |
| 1024 | invertido | 44.123 / 523 776 | 1.191 / 5120 | merge | merge |

- **El selector coincidió con el algoritmo más rápido en 15 de 16 casos.** El caso fallido (n = 64, mezclado) es un empate técnico: 0.070 ms frente a 0.071 ms. Indica que el punto de cruce medido está cerca de n = 64 en datos mezclados, así que el umbral de 32 es **conservador**.
- Con datos casi ordenados a n = 1024, Insertion Sort es ≈10 veces más rápido que Merge Sort. Con datos mezclados o invertidos a n = 1024, Merge Sort es entre ≈12 y ≈37 veces más rápido.
- **Clave costosa** (20 sumas por comparación): a n = 256, Insertion Sort hace 15 624 comparaciones y Merge Sort 1717 (≈9 veces menos). El `--bench` del repo lo confirma en tiempo: 9.9 ms contra 2.3 ms.

**Alternativas descartadas, n = 1024 (ms / comparaciones):**

| datos | merge (elegido) | quicksort pivote fijo | heapsort |
|---|---|---|---|
| ordenado | 1.183 / 5120 | 51.026 / 523 776 | 2.999 / 18 060 |
| mezclado | 1.816 / 8948 | 1.686 / 11 760 | 2.953 / 17 335 |
| invertido | 1.228 / 5120 | 64.477 / 523 776 | 2.744 / 16 407 |

**Estabilidad** (200 registros con claves repetidas): Insertion Sort y Merge Sort son estables; Quick Sort con pivote fijo y Heap Sort **no** lo son.

Lectura honesta: en datos mezclados, Quick Sort fue ligeramente más rápido que Merge Sort (1.69 ms frente a 1.82 ms). Se descarta por su peor caso (≈43–52 veces más lento que Merge Sort en datos ordenados o invertidos con pivote fijo, con 523 776 comparaciones) y por no ser estable. Heap Sort se descarta por inestable y porque, siendo O(n log n), hace más comparaciones que Merge Sort en todos los casos medidos.

### 6. Límites conocidos
- Los umbrales (32, 8 y 5 %) se eligieron y se **validaron con estas mediciones**, pero dependen del intérprete y del equipo; deben revisarse si cambia el entorno de ejecución.
- Los "descensos" son una señal aproximada de desorden: una lista con pocos descensos grandes y muchos elementos desplazados lejos puede parecer "casi ordenada" y no serlo en el sentido del costo de Insertion Sort.
- Merge Sort usa memoria O(n); con listas enormes en memoria limitada podría preferirse un algoritmo en sitio.
- Si el tamaño típico de los datos fuera siempre ≤ 32, el selector sería innecesario y bastaría Insertion Sort.

# Validación general

Las [437 pruebas](evidencia/pruebas.txt) pasaron. Se usaron temporales dentro del proyecto y se desactivó la caché de pytest para evitar errores de permisos del entorno. El [entorno y la huella del código](evidencia/entorno.json) identifican la versión medida. Las regresiones incluyen presupuesto de seis solicitudes con inicio en cinco, caché sin capacidad, conservación de sesión/pergamino ante errores y ordenamiento de puntajes.

En la comparación sintética previa de 20 salas y diez rastreadores se midieron 500 ciclos, con máximo **0.1701 ms**. Su perfil de 100 decisiones registró 47 movimientos, 53 ataques, 153 inserciones/extracciones de heap y diez cancelaciones; esas frecuencias describen aquella carga, no cualquier partida.

El 18 de octubre de 2026 se verificaron las cuatro criptas oficiales, semilla 2026, tope 25 y cinco repeticiones por modalidad. Se precargaron todas las salas antes de medir; cada ciclo comprueba que no cambie el contador HTTP. Hubo **800 ciclos**, ninguno de 20 ms o más, con máximo **3.6073 ms**. Los intervalos terminales se midieron por separado. Se conservaron 11 fichas residentes en cada carga.

| Cripta | Solicitudes: caché vacía / reutilizada | Presupuesto | Máximo de ciclo (ms) |
| --- | --- | --- | --- |
| 01 | 6 / 4 | 9 | 0.9759 |
| 02 | 15 / 14 | 23 | 2.7184 |
| 03 | 29 / 25 | 42 | 3.6073 |
| 04 | 36 / 29 | 52 | 1.5630 |

Son mediciones de las versiones y recorridos registrados en la evidencia. No prueban todas las secuencias posibles ni garantizan el mismo tiempo en otro equipo. Los prompts importados sin fecha o modelo se identifican como no registrados; las fechas aproximadas de Kendall se conservan como declaradas, pendientes de confirmación.
