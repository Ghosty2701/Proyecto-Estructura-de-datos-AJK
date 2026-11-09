# Investigación: Niebla de guerra y viaje «ir a»

**Fecha**: 2026-11-09.
**Estado**: investigación completada; D-NV-01, D-NV-02, D-NV-02a y D-NV-02b
aprobadas, junto a D-NV-03, D-NV-04, D-NV-04a, D-NV-04b y D-NV-05;
D-NV-06 y D-NV-07 aprobadas. Investigación de estructuras completada.
**Fuentes**: [spec.md](spec.md), constitución y código local citado en [plan.md](plan.md).
Las complejidades siguientes son análisis teórico; no son mediciones del proyecto.

## D-NV-01 — Consultar el estado de conocimiento por ID de sala

**Problema**: FR-NV-001/002/004/005 y PR-NV-002/003 requieren distinguir estados
frecuentemente sin recorrer el mapa conocido en cada consulta o revelación.
Sea S el número total de salas, M las salas exploradas o avistadas almacenadas,
y R las salas/salidas afectadas por una revelación. Los IDs no se suponen densos.

**Decisión**: alternativa C, aprobada por el usuario el 2026-11-09 mediante «C».
Arreglo de conocimiento por posiciones compactas del esqueleto. No usar el ID
externo como índice ni reservar hasta el ID máximo. Esta aprobación no decide
el índice de resolución de IDs, recuerdos de puertas, rutas o cambios reversibles.
**Recomendación**: alternativa C, arreglo por posiciones compactas del esqueleto.
El esqueleto completo ya está cargado y la consulta por posición y actualización
de cada registro son O(1) en peor caso, sin ampliaciones durante la revelación.
Esto favorece la exigencia de PR-NV-002, con inicialización O(S) una vez y memoria
O(S) incluso si se conoce poco. La resolución por ID externo es un problema
separado que deberá diseñarse y aprobarse; no se promete O(1) para ella.
La revisión delegada respalda esta recomendación, aceptada por el usuario.
Medir memoria real y tiempos antes de afirmar superioridad empírica.

| Alternativa | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Tabla hash propia ID → conocimiento | Consulta O(1) esperada; inserción O(1) amortizada; funciona con IDs dispersos; capacidad relacionada con M | Peor caso O(M); ampliación puede recorrer M; colisiones, borrado y retroceso requieren diseño. La tabla de distancias actual no ofrece borrado ni registros genéricos |
| B. AVL propio ID → conocimiento | Consulta, inserción y borrado O(log M) en peor caso; IDs dispersos; implementación local con borrado ya disponible | Nodos y rebalanceo; actualizar R entradas cuesta O(R log M), que debe contrastarse con la exigencia de revelación de §5.3 |
| C. Arreglo por posiciones compactas del esqueleto | Acceso O(1) por posición ya conocida; sin colisiones ni ampliaciones por revelación | Reserva O(S), incluso con poco conocimiento; asignar posiciones al cargar y resolver ID → posición requiere diseño y su propio coste. No usar el ID directamente como índice ni reservar hasta el ID máximo |

**Aclaración de alcance**: elegir A, B o C solo aprueba el índice del estado de
las salas. No decide cómo representar salidas, compartir recuerdos de puerta,
registrar cambios, resolver nombres o buscar rutas. Las opciones heredadas no
están aprobadas automáticamente para esas responsabilidades.

**Reutilización examinada**:
- TablaDistancias en `modelo/tabla_hash.py`: registros especializados para
  distancias/heap, sin eliminación; separar la decisión del índice del diseño
  de sus registros y de cómo restaurar ausencias.
- ArbolAVL en `adaptadores/cache_catalogo.py`: buscar, insertar y quitar.
  Si se elige para lógica del modelo, revisar su ubicación para no hacer depender
  las reglas de infraestructura.
- Cargador en `controlador/cargar_partida.py`: índice del esqueleto y referencias
  a salas/puertas físicas ya existentes; no equivalen a conocimiento del jugador.

## D-NV-02 — Localizar la posición compacta por ID externo

**Problema**: D-NV-01 da acceso O(1) por posición; una orden con ID todavía debe
localizar la sala correspondiente. No confundir la topología completa interna con
la autorización de revelar sus datos al jugador (FR-NV-005/008).

**Decisión**: C, tabla hash propia ID → posición, aprobada por el usuario el
2026-11-09 mediante «C». Consulta O(1) esperada, peor caso O(S) y espacio O(S)
además del arreglo aprobado en D-NV-01. No se aprueba todavía método de colisiones
ni parámetros o reutilización de la tabla especializada de distancias.
**Recomendación presentada**: A, usar el AVL del cargador ya existente para resolver ID a
referencia de sala y consultar su posición compacta. Conserva O(log S) en peor
caso para esa resolución sin mantener un segundo índice. Las operaciones de
revelación y vecinos que ya tienen referencia deben acceder por posición O(1),
sin repetir búsqueda por ID para cada registro revelado.

| Alternativa | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Reutilizar el AVL existente de salas | Resolución O(log S) garantizada; no crear un segundo índice ID → posición; acceso directo al arreglo tras resolver la sala | Resolver un ID externo no es O(1); mantener asociación sala/posición al cargar y reanudar. El modelo no debe importar el adaptador para consultar conocimiento |
| B. Arreglo de pares ID/posición ordenado con búsqueda binaria manual | Consulta O(log S); representación estática y sin nodos; búsqueda propia sin bisect | Segundo arreglo O(S); construirlo en orden y reconstruirlo coherentemente al cargar; duplica la resolución que ya ofrece el cargador |
| C. Tabla hash propia ID → posición | Consulta O(1) esperada; adecuada si la resolución externa se vuelve muy frecuente | Segundo índice O(S), peor caso O(S), colisiones y construcción/ampliación; la tabla de distancias existente requiere adaptación |

**Límites de la decisión**: no modificar la estructura de esqueleto heredada ni
usar el conocimiento completo para autorizar destinos; comprobar siempre que
la posición resuelta corresponde a una sala explorada. El camino de resolución
por nombre recibió posteriormente aprobación separada en D-NV-06.

**Validación prevista**: resolver IDs densos, dispersos, ausentes y extremos;
comparar antes y después de guardar/cargar; distinguir tiempo de resolución por
ID del acceso por posición y del cálculo de un paso. No hay mediciones ejecutadas.

## D-NV-02a — Colisiones del índice ID → posición

**Problema**: dos IDs pueden iniciar en la misma casilla. Hay que encontrar
ambos y también terminar correctamente las consultas de IDs ausentes. El
esqueleto es fijo durante la partida: revertir exploración cambia el estado
en el arreglo, no elimina IDs de este índice del esqueleto. No se requiere
borrado por exploración o pergamino en esta tabla.

**Decisión**: A, doble hashing propio, aprobado por el usuario el 2026-11-09
mediante «A». Capacidad, ocupación y salto se aprobaron después en D-NV-02b.
**Recomendación**: A, doble hashing propio. Usa un segundo cálculo determinista
para variar el salto de sondeo y reduce la agrupación primaria del sondeo lineal.
Es coherente con una técnica ya conocida por el equipo y recibió aprobación
nueva. No garantiza mejor tiempo: el salto puede tener menor localidad de memoria
y el costo del segundo cálculo debe medirse.

| Alternativa | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Doble hashing | Distintos saltos para distintos IDs; evita la agrupación primaria del sondeo lineal; sin nodos adicionales | Segundo cálculo; acceso menos contiguo; coordinar capacidad y salto para visitar todas las casillas; consulta acotada para ausentes |
| B. Sondeo lineal | Implementación simple y visitas contiguas, con buena localidad | Agrupación de claves y sondeos largos al crecer la ocupación |
| C. Encadenamiento separado con listas enlazadas propias | Colisiones resueltas dentro de cada cubeta; sin buscar otra casilla vacía | Nodos, enlaces y asignaciones adicionales; cadenas largas y memoria extra |

**Resuelto posteriormente en D-NV-02b**: capacidad, ocupación máxima, reglas de
sondeo y construcción con S conocido. No se heredaron capacidad 32 ni umbral 70 %
de D-TC sin una elección explícita nueva. Medir construcción,
presentes y ausentes, colisiones forzadas e IDs dispersos. Las tres alternativas
tienen consulta esperada O(1) bajo sus supuestos y peor caso O(S).

## D-NV-02b — Capacidad y reglas de sondeo de la tabla estática

**Decisión**: A, reserva inicial con máximo 70 %, aprobada por el usuario el
2026-11-09 mediante «A». Elegir la menor potencia de dos C ≥ 2 tal que
10·S ≤ 7·C; usar salto impar entre 1 y C−1, mezclas deterministas propias y
como máximo C sondeos. No hay ampliaciones por insertar los S IDs previstos.
**Problema**: la tabla contiene los S IDs del esqueleto completo y se construye
al iniciar o reconstruir la partida; explorar y retroceder no añaden ni quitan IDs.
La capacidad debe depender de S, no del mayor ID. Debe quedar una casilla libre
y toda consulta ausente debe terminar tras un número acotado de sondeos.

**Recomendación**: A, dimensionar una vez con el total conocido y ocupación
máxima del 70 %. Evita reconstrucciones por crecimiento durante la construcción;
no presupone que 70 % sea óptimo. Contrastar memoria, sondeos y tiempos con B
y C mediante bench antes de afirmar superioridad empírica.

| Alternativa | Capacidad | Ventajas y límites |
| --- | --- | --- |
| A. Reserva inicial, máximo 70 % | Menor potencia de dos C ≥ 2 tal que 10·S ≤ 7·C | No hay ampliaciones al insertar los S IDs; deja margen de sondeo. El redondeo puede reservar bastante más que S/0,7 |
| B. Reserva inicial, máximo 50 % | Menor potencia de dos C ≥ 2 tal que 2·S ≤ C | Mayor margen y previsiblemente menos sondeos, sin garantía de tiempo; puede consumir más memoria. A veces A y B dan la misma capacidad por redondeo |
| C. Crecimiento gradual, máximo 70 % | Empezar en 32 y duplicar antes de superar 70 % | Patrón conocido del índice de distancias; asigna poco al principio, pero añade ampliaciones y reinserciones pese a conocer S de antemano |

**Reglas de sondeo propuestas para las tres alternativas**: usar mezclas enteras
deterministas propias para casilla inicial y segundo cálculo; capacidad potencia
de dos y salto impar entre 1 y C−1, de modo que se recorran todas las casillas.
Acotar una consulta a C sondeos. No consumir random.Random ni usar dict/set.
Si se aprueba una reserva inicial, comprobar la cantidad de IDs al construir y
no aceptar silenciosamente un esqueleto mayor que la capacidad planificada.
Si cambia la cripta se reconstruye el índice, sujeto a validación de versión.
El diseño no precisa borrado ni marcas de borrado para revertir conocimiento.

Elegir A, B o C aprueba ese conjunto de capacidad, ocupación y reglas de sondeo;
no aprueba aún generalizar TablaDistancias ni elegir estructuras de puertas/rutas.
Probar S cerca de los umbrales y colisiones forzadas; medir por separado la
construcción y las consultas presentes/ausentes. No se garantiza el límite de
5 ms de «ir a» por aprobar estos parámetros.

## D-NV-03 — Salidas conocidas y recuerdos de puertas

**Problema**: FR-NV-002/003/005/006/009/012/016 exige recorrer las salidas
reveladas de una sala, compartir una misma observación desde ambos extremos y
conservarla aunque cambie la puerta física. Una salida conocida solo es utilizable
en «ir a» si ambas salas están exploradas y se recuerda abierta.

**Decisión**: A, listas de salidas conocidas por sala con un único recuerdo de
puerta compartido entre ambos sentidos, aprobado el 2026-11-09 mediante «A».
El recuerdo almacena el valor observado separado del estado de la puerta física.
**Recomendación**: A, listas de salidas conocidas por sala con un registro de
puerta recordada compartido por los dos sentidos. Un único valor recordado evita
tener que sincronizar dos copias. El registro es distinto de la puerta física:
nunca consulta su valor actual para sustituir el recuerdo.

| Alternativa | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Listas por sala y recuerdo compartido | Recorrer vecinas cuesta O(grado); una observación actualiza un único recuerdo; espacio total O(S + E) si se conoce todo | Enlaces de ambos sentidos deben apuntar al mismo recuerdo; persistencia y retroceso conservan esa identidad |
| B. Listas por sala y recuerdo duplicado en cada sentido | Consulta local directa; cada salida contiene su recuerdo | Una observación debe actualizar ambas copias mediante enlace inverso; más datos y deltas, riesgo de discrepancia al cargar o deshacer |
| C. Matriz de conexiones y recuerdos | Acceso directo a un par de posiciones | Espacio O(S²) y recorrer vecinas examina una fila de S posiciones, aunque se revelen pocas; poco adecuada para PR-NV-002 |

E es el número de salidas dirigidas del esqueleto y grado las salidas de la sala.
A y B recorren solo sus salidas y usan espacio para las conexiones representadas;
no autorizan un índice auxiliar adicional. El coste O(S) ya aprobado para el
arreglo de salas no obliga a reservar una matriz O(S²).

**Validación prevista**: observar desde cualquiera de los extremos, cambios
remotos, revelación por antorcha, salas solo avistadas, guardar/cargar y retroceso
que restaura el recuerdo anterior. Medir consulta y actualización separadas.
Detalles de asignación de registros y asociación con puertas se precisarán en
el diseño, sin decidir otro índice de forma implícita.

## D-NV-04 — Compartir o separar la búsqueda de «ir a»

**Problema**: FR-NV-009/010/012 y PR-NV-001 requieren costo mínimo y desempate por
primer vecino de menor ID sobre salas exploradas y puertas recordadas. P2 §5.3
exige justificar compartir o separar implementación respecto del cazador.

**Decisión**: A, núcleo Dijkstra compartido con acceso separado a cada mapa,
aprobado por el usuario el 2026-11-09 mediante «A». El viaje consulta solo el
conocimiento; el cazador conserva su mapa real y rango. La aprobación no incluye
los auxiliares del viaje por sí sola; estos se aprobaron después en D-NV-04a.
**Recomendación**: A, adaptar un núcleo Dijkstra compartido con acceso explícito
a vecinos y costos de cada problema. El cazador sigue usando esqueleto real y
rango; el viaje utiliza exclusivamente conexiones exploradas y recuerdos de
puertas, sin rango de cazador. Evita duplicar la lógica de mejoras y desempates.
Nunca llamar al buscador actual sobre salas reales para resolver el viaje.

| Alternativa | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Núcleo Dijkstra compartido, con acceso separado a cada mapa | Una implementación de relajación y desempate; pruebas comunes de rutas y adaptadores específicos | Refactorizar con regresiones de cazadores; aislar bien las dos fuentes de conocimiento y comprobar el coste del acceso indirecto |
| B. Dijkstra independiente para «ir a» | No modifica la búsqueda del cazador; lógica de recorrido específica del mapa conocido | Duplica relajación y desempates, que podrían divergir; exige mantener pruebas equivalentes en ambas implementaciones |

**Alcance**: elegir A o B decide compartir o separar el algoritmo. Los auxiliares
de distancias y selección del siguiente candidato requirieron la decisión
explícita D-NV-04a; no se heredaron por esta elección la tabla de distancias ni
el heap de cazadores. Tampoco se decide reutilización de resultados: antes de cada paso se
respeta el recálculo exigido por FR-NV-012.

**Validación prevista**: costos no uniformes, empates de primer salto, recuerdos
distintos de puertas reales, salas solo avistadas y destinos explorados por
antorcha. Si se comparte núcleo, comprobar que el rango y la conducta del cazador
permanecen iguales con la misma semilla y acciones. Medir el cálculo de paso
sobre mapa completo contra el límite <5 ms, sin confundirlo con reloj virtual.

## D-NV-04a — Auxiliares de distancias y candidatos del viaje

**Problema**: el núcleo compartido debe registrar distancia, primer salto,
condición de definitivo y posición de candidato sin índices de biblioteca.
D-NV-01 proporciona posiciones compactas para las S salas del esqueleto.

**Decisión**: A, arreglo de registros por posición compacta y heap binario
indexado propio existente, aprobado el 2026-11-09 mediante «A». Se reutiliza
HeapRutas con instancias separadas; no se usa la tabla hash de distancias para
los registros del viaje. La preparación entre búsquedas se aprobó en D-NV-04b.
**Recomendación**: A, registros de búsqueda en arreglo por posición compacta y
heap binario indexado propio para candidatos. Reutilizar la implementación
HeapRutas, con una instancia separada por búsqueda, y sus referencias a registros
con posición de heap; nunca compartir una instancia activa con la agenda ni con
otra búsqueda. El arreglo evita otro hash para distancias cuando ya hay posiciones.

| Alternativa | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Arreglo de registros + heap binario indexado propio existente | Distancias por posición O(1) en peor caso; mejora/extracción O(log V); una entrada por sala candidata | Espacio auxiliar O(S); precisar inicialización y limpieza entre pasos, sin ocultar un recorrido O(S) en cada consulta |
| B. Tabla hash de distancias + heap binario indexado propios existentes | Solo registra salas alcanzadas; se parece al diseño aprobado para cazadores | Distancias O(1) esperado, O(V) peor caso; colisiones y ampliaciones. Aprobar el uso en viaje no hereda automáticamente parámetros de la tabla de IDs |
| C. Arreglo de distancias y búsqueda lineal del mínimo | Sin heap ni colisiones; menos operaciones auxiliares | Seleccionar el mínimo mediante recorridos cuesta O(V² + E) sobre V salas alcanzadas; menos favorable al crecer el mapa |

V y E son salas y salidas examinadas por la búsqueda conocida. Con A el trabajo
de búsqueda con heap es O((V + E) log(V + 1)), además de la inicialización/limpieza
que debe especificarse y medirse. En B esta cota es esperada por sus consultas
hash, no una garantía de peor caso. No confundir el índice estático ID → posición
con los registros temporales de distancias.

Elegir A aprueba el arreglo de registros y reutilizar HeapRutas para el viaje;
elegir B aprueba reutilizar TablaDistancias y HeapRutas para ese problema nuevo.
Los candidatos se ordenan por distancia, primer salto e ID como ya exige el
desempate; no son una agenda de eventos. Los auxiliares del cazador conservan
sus elecciones anteriores y la consulta del jugador no modifica azar ni reloj.
El mecanismo de limpieza de los registros de A se eligió después en D-NV-04b:
marcas de generación. Ninguna opción está medida.

**Validación prevista**: igual costo con mejora del primer salto, múltiples
consultas seguidas con distintos destinos y recuerdos de puertas, posiciones
dispersas entre las salas conocidas y ausencia de contaminación entre búsquedas;
medir cálculo completo incluyendo la preparación necesaria por paso.

## D-NV-04b — Preparar registros entre búsquedas

**Problema**: FR-NV-012 exige recalcular antes de cada paso. D-NV-04a reserva
registros por posición compacta; reiniciar S casillas para cada ruta corta añade
trabajo ajeno a la región recorrida. Los registros son auxiliares derivados,
no conocimiento que deba guardarse o restaurarse con un pergamino.

**Decisión**: A, marcas de generación, aprobada el 2026-11-09 mediante «A».
Cada búsqueda nueva invalida lógicamente los registros anteriores y prepara
solo los alcanzados; no reutiliza respuestas ni altera conocimiento persistente.
**Recomendación**: A, marcas de generación. Cada búsqueda tiene un número nuevo
y cada registro indica la generación a la que pertenece. Un registro de otra
generación se trata como no visitado y se inicializa al alcanzarlo, con distancia,
primer salto, definitivo y posición de heap restablecidos. No se reutiliza la
respuesta de la búsqueda anterior ni se omite el recálculo.

| Alternativa | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Generación por registro y contador de búsqueda | Cambiar generación no recorre las S casillas; solo se preparan los registros alcanzados; sin lista auxiliar de tocados | Marca adicional por registro; validar la generación en todos los accesos y reiniciar todos los campos al primer uso |
| B. Lista de posiciones tocadas | Se limpian solo los V registros alcanzados; no requiere marcas de generación | Lista auxiliar O(V); añadir cada posición una vez y limpiar también tras salidas anticipadas o errores |
| C. Reiniciar todo el arreglo en cada búsqueda | Implementación y estado fáciles de inspeccionar | Preparación O(S) por paso aunque la ruta sea corta |

La inicialización del arreglo cuesta O(S) una vez en las tres alternativas.
En A, avanzar el contador es O(1) en el modelo usual de costos; inicializar
registros alcanzados cuesta O(V). Esto no hace O(1) toda la preparación: limpiar
o liberar un heap con H candidatos pendientes puede costar O(H), también al
alcanzar el destino antes de vaciarlo. Incluir ese trabajo en las mediciones;
no ocultarlo fuera del tiempo por paso. No permitir consultas simultáneas que
modifiquen los mismos registros auxiliares; mantener separado el estado del cazador.

**Validación prevista**: rutas sucesivas distintas, consulta sin ruta, origen
igual a destino, salida temprana con candidatos pendientes, cambios de puerta
recordada y retroceso seguido de nueva búsqueda. Ninguna generación convierte
una sala desconocida en explorada. La implementación y sus pruebas están cerradas en tasks.md.

## D-NV-05 — Registrar e invertir cambios de conocimiento

**Problema**: FR-NV-003/006/016/017 y PR-NV-002 requieren restaurar estados de
salas, salidas reveladas y recuerdos de puertas al revertir la acción. No copiar
el mapa completo por paso. El historial actual almacena cambios en orden y los
invierte en orden inverso; soporta deltas de atributos además de otras operaciones.

**Decisión**: A, deltas de atributos y referencias en la lista de cambios
existente de cada acción, aprobada por el usuario el 2026-11-09 mediante «A».
Se restaura en orden inverso, sin copiar el mapa completo. No se introduce
un grupo especializado ni un índice de deduplicación por esta decisión.
**Recomendación**: A, registrar deltas de atributos y referencias en la lista
de cambios de la acción ya existente. Para un estado de sala o recuerdo, guardar
el valor anterior; si se publica una lista nueva de salidas, registrar la
referencia anterior y no modificarla después. Deshacer recupera lo anterior en
orden inverso, sin recorrer el mapa. Los recuerdos compartidos deben seguir
siendo el mismo objeto desde ambos sentidos al restaurar.

| Alternativa | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Deltas en la lista de cambios existente | Aprovecha registrar_atributo y el orden de deshacer del historial; trabajo proporcional a cambios reales; menos mecanismos nuevos | Auditar cada mutación; las listas anteriores retenidas no pueden modificarse, y deben serializarse junto a sus referencias |
| B. Grupo específico de cambios de conocimiento por acción | Agrupa transiciones de sala, salidas y puertas en un delta propio; contrato especializado fácil de revisar | Nueva estructura de registros y lógica de inversión/validación binaria; mantener su posición correcta entre los demás deltas |

Ambas almacenan solo información necesaria de lo cambiado y pueden costar O(D)
para registrar/deshacer D cambios, más el tamaño de salidas recién reveladas.
Ninguna autoriza snapshots del mapa completo por acción. A usa la lista del
historial explícitamente para este problema nuevo, sin incorporar un índice
de deduplicación. B tampoco elige implícitamente ese índice. Si un atributo se
modifica varias veces, conservar sus cambios en orden es correcto aunque guarde
más de un valor previo; no se presume que deduplicar sea necesario.

**Persistencia prevista**: ampliar campos/tipos y validaciones explícitos del
formato binario para el conocimiento y sus deltas; no persistir generaciones
de búsqueda como conocimiento. Comprobar compatibilidad o rechazo claro de
guardados anteriores. La decisión de representación no permite perder el historial.

**Validación prevista**: sala desconocida → avistada → explorada en un intervalo,
entrada con antorcha, observaciones sucesivas de la misma puerta, guardar/cargar
antes de retroceder y pergamino tras un paso de viaje. Medir memoria de cambios
por acción y costo de inversión, distinguiéndolos de memoria de todo el estado.

## D-NV-06 — Resolver destinos por nombre completo

**Problema**: FR-NV-008 y AC-NV-009 exigen nombres completos sensibles a
mayúsculas y rechazar nombres repetidos entre exploradas pidiendo ID. No buscar
en nombres del esqueleto oculto ni informar si allí existe una coincidencia.
La tabla aprobada ID → posición tiene claves enteras; no autoriza otro índice
de cadenas. El nombre se resuelve al iniciar la orden, no en cada paso de ruta.

**Decisión**: A, recorrer el arreglo de conocimiento existente al recibir la
orden por nombre, aprobada el 2026-11-09 mediante «A». Comparar solo nombres
revelados de exploradas; detectar duplicados sin un índice adicional. Resolver
una vez al iniciar la orden, no repetir el recorrido en cada paso.
**Recomendación**: A, recorrer el arreglo de conocimiento aprobado, filtrando
primero por explorada y comparando únicamente su nombre revelado. Conservar
una coincidencia y detectar una segunda sin construir otra lista o índice.
Es una consulta ocasional de entrada; no añade mantenimiento al explorar,
retroceder o cargar, ni un recorrido global por cada revelación. Medir su costo
por separado del cálculo de ruta, sin ocultar tiempo de respuesta total.

| Alternativa | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Recorrido del arreglo existente al recibir la orden | Ningún índice adicional; detecta ausencias y duplicados con el conocimiento vigente; retroceso no requiere sincronizarlo | Examina S estados por consulta y compara nombres de exploradas; O(S + M·L), con M exploradas y L longitud máxima comparada |
| B. AVL propio por nombre | Busca entre U nombres distintos en O(log(U + 1)) comparaciones | Índice adicional O(M); mantener altas y retroceso, gestionar duplicados y validar guardado; comparar cadenas también cuesta longitud |
| C. Tabla hash propia por nombre | Consulta esperada constante en cubetas, más costo de procesar el nombre | Índice adicional O(M), mezcla determinista de cadenas, colisiones y parámetros; gestionar duplicados y restaurar su estado. Peor caso lineal |

Con A, guardar una referencia al destino resuelto no es una caché de ruta: cada
paso recalcula con conocimiento vigente y no repite búsqueda por nombre. El
destino se invalida si una interrupción o retroceso cancela el viaje, conforme
a la especificación. B o C requerirían decisiones posteriores para representar
coincidencias múltiples y mantener el índice sin revelar datos ocultos.

**Validación prevista**: nombre de varias palabras, diferencia de mayúsculas,
ausente, dos exploradas con nombre igual, una explorada y otra oculta con igual
nombre, exploración por antorcha, retroceso que elimina una coincidencia y
guardar/cargar. A está aprobada; ninguna opción está medida.

## D-NV-07 — Asociar salidas al recuerdo compartido de puerta

**Problema**: D-NV-03 exige un único recuerdo por puerta física y enlaces desde
las salidas conocidas de ambos extremos. La puerta física ya es compartida en
el cargador; observarla no debe requerir buscar por todo el mapa ni leer su
estado real al consultar el recuerdo (FR-NV-003/005/016, PR-NV-002).

**Decisión**: A, referencia directa desde cada puerta física al recuerdo de
esa partida, aprobado el 2026-11-09 mediante «A». Reservar un recuerdo por
puerta al construir, inicialmente no observado; las salidas conocidas de ambos
sentidos conservan esa misma referencia. No se incorpora otro índice de puertas.
**Recomendación**: A, una referencia directa desde la puerta física a su registro
de memoria, perteneciente al conocimiento de esa partida. Los dos extremos
obtienen la misma referencia y sus salidas conocidas la conservan; actualizar
el recuerdo solo sucede en una observación autorizada. La referencia no convierte
el estado recordado en una propiedad calculada a partir del estado real.

| Alternativa | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Referencia directa en la puerta al recuerdo de la partida | Acceso O(1) sin otro índice; aprovecha identidad física ya compartida; no hay búsqueda global | Añade asociación entre entidades físicas y conocimiento; ampliar esquema binario y separar objetos entre partidas/reconstrucciones |
| B. Arreglo de recuerdos por posición compacta de puerta | Acceso O(1) con posición; conocimiento concentrado en su propio arreglo | Otro arreglo O(P) y posiciones de puerta que asignar/validar, además de las posiciones de sala; no evita mantener la asociación física con una posición |
| C. Tabla hash propia por identidad estable de puerta | Asociación externa sin campo de referencia al recuerdo en la puerta | Otro índice O(P), colisiones y definición de identidad de puerta sin confundir conexiones; parámetros adicionales |

P es el número de puertas físicas. Con A se puede reservar un registro por
puerta al construir la partida: inicialmente no observado, sin publicar salidas
ni estados reales al jugador. Revelar enlaza el registro existente y observa
su valor; deshacer restaura sus valores previos y las listas anteriores mediante
los deltas aprobados. El coste de reserva es O(P) una vez y la memoria O(P).
Esta opción incluye esa reserva inicial, sin crear otro índice. No recorrer P
puertas en cada entrada o acción. Puertas y recuerdos de partidas independientes
no se comparten. Un mapa histórico independiente no puede mutar el recuerdo vivo;
su reconstrucción se concretará en la capacidad de línea de tiempo.

**Validación prevista**: observar desde ambos extremos, cierre remoto que no
actualiza el recuerdo, antorcha, retroceso que vuelve a no observado, guardado
con referencias compartidas y dos partidas independientes. Las tres opciones
exigen respetar el filtrado de información; no están medidas.

## Cierre de investigación e integración

Todas las decisiones D-NV-01 a D-NV-07, incluidas variantes, tienen elección
explícita. Las alternativas y sus límites se conservan arriba como evidencia.
No se introducen índices adicionales de puertas, nombres o deduplicación.

- Conocimiento: observar en el modelo durante la acción y eventos locales;
  consultar/renderizar solo lee la proyección. Nunca observar por una precarga.
- Persistencia: ampliar a versión de modelo 5 y rechazar formatos anteriores
  explícitamente; mantener identidad de recuerdos y deltas, reconstruir derivados.
  Es una actualización del formato, no una estructura nueva.
- Interrupción: control por paso completo y consulta de entrada opcional en la
  vista de consola; Windows permite detectar entrada pendiente con msvcrt. Si
  existe, detener el bucle automático y leer el comando del jugador. No agregar
  confirmaciones por paso, hilos, colas de entrada ni esperas de reloj virtual.
  Los callbacks inyectados permiten probar el punto de interrupción sin teclado.
  Replay ejecuta los movimientos registrados y no necesita ese mecanismo.
- Comentarios del log: líneas con prefijo # se ignoran antes de ejecutar acciones;
  el comentario de viaje no cuenta como acción ni duplica los movimientos.
- Daño: señalar el suceso dentro del intervalo del paso, aunque la vida se
  recupere después; no deducirlo únicamente de vida final menos vida inicial.

La fase 1 concreta estas integraciones en data-model.md, contracts y quickstart.
La implementación y las 30 tareas están completadas. La evidencia empírica y sus
límites están en tasks.md y documentacion/evidencia/mediciones_niebla.json:
492 pruebas aprobadas y máximo de cálculo de ruta oficial 2,1130 ms. Las
alternativas anteriores conservan la evaluación de diseño, no mediciones de todas
las opciones; no se afirma superioridad empírica para las que no se midieron.
