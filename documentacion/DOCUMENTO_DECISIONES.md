# Decisiones de diseño — Cripta

Andrey: motor, agenda, retroceso y rastro. Juan: red, catálogo, caché y persistencia. Kendall: inventario, consola y ordenamiento. Las integraciones conectan las tres partes mediante el controlador; el motor no depende de la vista ni de HTTP.

Las secciones corresponden a §4.1–§4.11 del enunciado. Las cifras proceden de los [benchmarks actualizados](evidencia/bench_subsistemas.txt) y las [comparaciones adicionales](evidencia/mediciones.json), con Python 3.14.6 en Windows. El JSON distingue las comparaciones sintéticas previas de la verificación oficial actual y conserva sus huellas de código. Los benchmarks de estructuras informan mínimos de cinco repeticiones; el ciclo completo informa su máximo. Las frecuencias indicadas corresponden a cada carga experimental.

## 1. Agenda de eventos

- **Problema:** seleccionar el siguiente evento y gestionar cancelaciones y cambios de velocidad; la carga medida realiza 2000 inserciones, 500 cancelaciones y 1500 extracciones activas.
- **Alternativas:** lista ordenada o heap binario. Se descarta la lista porque cada inserción desplaza hasta H posiciones; el benchmark compara ambas.
- **Decisión:** heap propio, desempate por secuencia y cancelación perezosa. El ascenso/descenso mueve un hueco para evitar intercambios y tuplas de comparación por nivel.
- **Complejidad:** insertar/extraer O(log H); marcar cancelación O(1). Descartar varios cancelados requiere varias extracciones.
- **Evidencia:** 2000 inserciones, 500 cancelaciones y 1500 eventos activos extraídos: heap 8.462 ms frente a lista 246.837 ms.
- **Límite:** los eventos cancelados permanecen hasta ser extraídos y pueden acumularse.

## 2. Precarga de salas

- **Problema:** preparar destinos sin gastar solicitudes ni memoria innecesarias; se miden recorridos de tres y 200 salas para comparar consultas y anticipaciones.
- **Alternativas:** cargar al entrar, anticipar vecinas o completar lotes amplios. Cargar solo al entrar desaprovecha lotes; ampliar siempre descarga salas que quizá no se visiten.
- **Decisión:** vecindad abierta por defecto y agrupación hasta diez cuando la estimación de presupuesto lo requiere. El margen preventivo del 20 % redondeado hacia arriba orienta la precarga; las consultas necesarias pueden consumirlo sin superar el presupuesto total, incluidos reintentos.
- **Complejidad:** buscar una sala O(log S); seleccionar vecindad O((d + 1) log S). Ampliar lotes y estimar tipos puede recorrer contenido acumulado.
- **Evidencia:** corredor sintético de 200 salas: vecindad 100 llamadas de contenido; lotes amplios 20. Visitando solo tres salas, cargan cuatro y diez respectivamente.
- **Límite:** son llamadas locales de prueba, no HTTP real; la estimación no garantiza completar cualquier cripta.

## 3. Resolución del catálogo

- **Problema:** convertir IDs de tipos y botín en fichas compartidas, conservando estados independientes por instancia; se miden consultas por ficha en índices de 25, 100 y 1000 IDs.
- **Alternativas:** búsqueda lineal, árbol simple o AVL propio. Se descartan las dos primeras por su peor caso O(T) al resolver repetidamente tipos, especialmente con IDs ordenados.
- **Decisión:** AVL para localizar fichas y referencias ligeras compartidas por ID.
- **Complejidad:** localizar una referencia O(log T); resolver un lote añade IO y deduplicaciones que pueden costar O(m²).
- **Evidencia:** con 1000 IDs ordenados, altura AVL 10 frente a 1000 del árbol simple; búsquedas de 0.810 frente a 39.205 µs/ficha.
- **Límite:** el índice de referencias ligeras crece con los tipos conocidos, aunque se liberen sus datos completos.

## 4. Caché persistente

- **Problema:** reutilizar fichas y recuperar las liberadas sin repetir red; se miden accesos residentes y 500 recuperaciones desde disco.
- **Alternativas:** FIFO o LRU; memoria solamente o persistencia por versión. FIFO ignora los accesos recientes; sin disco, una ficha desalojada requiere otra solicitud.
- **Decisión:** AVL, lista doble LRU y JSON por ficha y versión. Desalojar vacía los datos de la referencia compartida; no elimina su identidad. El tope es estricto: la precarga opcional puede quedarse solo en disco; se comprueba la capacidad antes de preparar una acción.
- **Complejidad:** acierto O(log C), enlaces LRU O(1); seleccionar una ficha no protegida puede recorrer candidatos y entidades en uso.
- **Evidencia:** acierto 0.673 µs; recuperar desde disco, reinsertar y desalojar 169.558 µs. Se midieron 500 recuperaciones sin HTTP.
- **Límite:** si las fichas protegidas necesarias superan `--cache-size`, la acción se rechaza sin avanzar ni consumir pergaminos. Se informa el mínimo para reanudar con más capacidad: conservar todas y respetar un tope menor es imposible. El tope mide fichas residentes, no todos los bytes del proceso.

## 5. Inventario

- **Problema:** recorrer en ambos sentidos, equipar, soltar el objeto seleccionado y producir vistas ordenadas; la carga ejecuta 1000 inserciones, recorrido al centro, equipo y 1000 retiros.
- **Alternativas:** arreglo o lista doble. Se descarta el arreglo para el orden real porque retirar por cursor desplaza elementos; se mantiene como alternativa medida y para vistas temporales.
- **Decisión:** lista doble con cursor; enlaces adicionales para separar objetos reversibles de pergaminos. Las vistas se ordenan aparte.
- **Complejidad:** recoger, mover cursor y retirar el nodo actual O(1); buscar/listar O(I). Validar o restaurar un cambio reversible puede recorrer O(I).
- **Evidencia:** carga de 1000 inserciones y retiros: 1.825 ms. En la comparación adicional previa, solo retiros centrales: lista 0.3681 ms, arreglo 0.1771 ms.
- **Límite:** el arreglo de Python fue más rápido en esa muestra; se elige la lista por el retiro por referencia sin desplazamientos, no por ganar todos los tiempos.

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

## 10. Guardado binario

- **Problema:** recuperar una sala sin cargar todo el archivo y restaurar las referencias compartidas del modelo; se miden guardado completo, restauración completa y lectura de una sala en un modelo de 200 salas con dos acciones de historial.
- **Alternativas:** JSON completo o formato binario indexado por bloques. Se descarta JSON como guardado principal porque recuperar una sala exige leer el documento completo; permanece como referencia de tamaño y tiempos.
- **Decisión:** contenedor `CRPT` versión 1, índice de ID/offset/longitud y esquema explícito de entidades versión 3. El AVL resuelve referencias al cargar. La lectura selectiva devuelve una vista de sala, no un motor parcialmente reconstruido.
- **Complejidad:** sala selectiva O(log S + B_s); captura/carga aproximada O(B + (N + E) log N), más ordenamiento de salas al guardar.
- **Evidencia:** modelo de 200 salas: binario 56789 bytes, JSON equivalente 132292. Restauración completa 22.893 ms; vista selectiva 0.17967 ms. JSON fue más rápido al decodificar a registros.
- **Límite:** offsets de 32 bits, rechazo de esquemas anteriores y ausencia de garantía ante corte eléctrico. Una restauración completa no es un ciclo normal de juego.

## 11. Bitácora y replay

- **Problema:** repetir acciones con la misma semilla y versiones, sin interacción; la comparación adicional registra y reproduce 100 acciones.
- **Alternativas:** comandos solos o comandos con encabezado de identidad y versiones. Se descartan comandos solos porque no permiten rechazar un catálogo o una cripta incompatibles ni reproducir el azar.
- **Decisión:** log de texto nuevo, encabezado `CRIPTA-LOG 1` y comandos añadidos tras acciones exitosas. Replay comparte el ejecutor del controlador sin crear vista.
- **Complejidad:** escribir O(L) por comando; leer O(B) y reproducir según el costo acumulado de las acciones. El lector mantiene las acciones en memoria.
- **Evidencia:** 100 acciones, log de 923 bytes y replay de 5.2759 ms, con igualdad de estado y azar.
- **Límite:** requiere datos compatibles. Se puede guardar mientras se graba, pero no cargar; el log no representa ese salto de historia.

## Validación general

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
