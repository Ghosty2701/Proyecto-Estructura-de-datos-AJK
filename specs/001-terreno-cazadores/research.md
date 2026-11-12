# Investigación y decisiones — Terreno y cazadores

**Fecha**: 2026-11-08
**Estado**: fase 0 completa; D-TC-01 y tabla hash propia de D-TC-02 aprobadas;
doble hashing de D-TC-02a y heap indexado de D-TC-03 aprobados;
registro de posiciones en la misma tabla (D-TC-03a) aprobado;
búsquedas individuales de D-TC-04 y reutilización conservadora de D-TC-05 aprobadas;
listas de adyacencia existentes como decisión final de D-TC-06; D-TC-06a resuelta.
Último resultado por cazador (D-TC-07) y configuración de tabla D-TC-08 aprobados.
Las decisiones de estructuras están resueltas y ejecutadas; la evidencia del cierre
original está en tasks.md. Las mediciones posteriores a niebla se distinguen en
README y DOCUMENTO_DECISIONES.md; no se sobrescriben las cifras históricas.
**Referencias**: [spec.md](spec.md), [plan.md](plan.md), [AGENTS.md](../../AGENTS.md).

El usuario y su equipo eligieron la opción A de D-TC-01 el 2026-11-08. Después, el usuario
aprobó una tabla hash propia para D-TC-02, doble hashing para sus colisiones
y actualización de prioridad en un heap indexado para D-TC-03.
Las recomendaciones restantes son análisis
teórico y de código; no son decisiones aprobadas ni resultados de benchmark. No se
ejecutaron pruebas ni mediciones.

## Hallazgos del código existente

- `modelo/agenda_eventos.py`, AgendaEventos: heap binario propio que ordena eventos por
  tiempo y secuencia, con cancelación perezosa. No es una frontera genérica: usa campos y
  reglas de identidad de eventos. Usarlo directamente para rutas mezclaría dos problemas.
  Su implementación puede servir de referencia si el usuario autoriza otro heap.
- `adaptadores/cache_catalogo.py`, ArbolAVL: búsqueda e inserción por clave; actualizar una
  clave reemplaza su valor. Es candidato a reutilización, pero su ubicación actual en
  adaptadores impide introducirlo como dependencia del modelo sin revisar la separación MVC.
- `adaptadores/servicio_cripta.py`: descarga el esqueleto completo y lo separa del contenido.
  Las salidas conservan sus campos de datos; la búsqueda no necesita contenido de salas.
- `controlador/cargar_partida.py`: construye salas y salidas del modelo a partir del
  esqueleto. Se debe consultar el estado mutable de las puertas, no confundirlo con el
  estado inicial recibido del servidor.
- `modelo/rastro.py`: SalaRastro contiene una lista de salidas con referencias a destinos;
  SalidaRastro no tiene costo de tránsito. No se ha elegido sustituir esta representación.
- `modelo/motor_eventos.py`: rastreador y errante programan acciones con costo fijo 100;
  las validaciones de comportamiento aún no incluyen cazador.
- `adaptadores/estado_binario.py`: el esquema y sus validaciones de comportamiento deben
  revisarse para conservar los datos nuevos de costos y cazadores al guardar/cargar.

## D-TC-01 — Ruta ponderada y menor costo pendiente

**Decisión**: aprobada el 2026-11-08 por el usuario, quien informa el acuerdo del equipo:
opción A, Dijkstra limitado por rango con heap binario propio para rutas, separado de la
agenda de eventos. Respuesta original: «La opcion que concorde con mi equipo fue la A».

**Justificación técnica**: los costos positivos permiten detener la búsqueda
cuando ya no hay candidatos dentro del rango. El desempate por primer vecino debe
tratarse expresamente: ordenar únicamente por ID de extracción no garantiza FR-TC-009.
El heap permite operaciones de frontera logarítmicas. La evidencia de --bench se
incorporó al cierre en tasks.md; esta elección no autoriza otras estructuras ni variantes.

Alternativas consideradas al tomar la decisión:

| Opción | Ventaja teórica | Desventaja |
| --- | --- | --- |
| A. Dijkstra con heap propio de rutas | Insertar y extraer mínimo en O(log F); permite explorar por costo sin examinar toda la frontera para cada extracción | Requiere implementar/verificar el heap y definir las mejoras de distancia |
| B. Dijkstra con lista no ordenada | Insertar en O(1); implementación simple y referencia de comparación | Buscar y extraer el mínimo exige O(F); puede acumular trabajo cuadrático |
| C. Dijkstra con lista ordenada manualmente | Mínimo accesible sin recorrer toda la frontera; orden explícito | Insertar puede requerir O(F) desplazamientos; necesita mantener el orden |

F es el número de entradas pendientes. Estas cotas son de las operaciones de frontera,
no del algoritmo completo: el costo total también depende del registro de distancias,
las mejoras, el acceso al mapa y las salidas examinadas; sus elecciones finales están
recogidas en las decisiones posteriores y en data-model.md.

Otras alternativas consideradas: un árbol balanceado por prioridad permite operaciones
logarítmicas, con mayor mantenimiento; Bellman-Ford admite pesos negativos que aquí no
se necesitan y su forma usual repite recorridos globales, inadecuados para el objetivo
local de rango pequeño. Una búsqueda por cantidad de pasos con cola FIFO no cumple
la regla de costos variables y no se propone como solución correcta.

## D-TC-02 — Distancias y registros auxiliares

**Decisión**: tabla hash propia para guardar distancias por ID de sala, aprobada por el
usuario el 2026-11-08. Respuesta original: «Ok demosle con eso entonces».

**Justificación del usuario**: interés por la rapidez esperada y su utilidad para el
problema; reconoce que las colisiones tienen métodos de resolución. Se explicó antes de
la aceptación que esto no garantiza por sí solo los límites del profesor.

**Justificación técnica**: permite buscar y actualizar registros en O(1) esperado con
dispersión y ocupación adecuadas. Su peor caso puede ser lineal y una ampliación debe
redistribuir registros. Hay que medir colisiones, crecimiento y el ciclo completo, sin
reinicializar toda la cripta por búsqueda. No se permite sustituirla por dict o set.

Alternativas consideradas:

- AVL propio disperso: O(log R) por consulta/actualización, registra solo salas alcanzadas;
  la reutilización del AVL heredado necesita decidir su ubicación sin dependencia inversa.
- Tabla hash propia: O(1) esperado; requiere resolver colisiones, crecimiento y medición.
- Arreglos por índice interno: O(1) por índice; exigen mapear IDs arbitrarios y evitar
  inicializar/limpiar todo el mapa para cada búsqueda. El costo de ese mapa auxiliar cuenta.

R es la cantidad de salas registradas en la búsqueda. La tabla hash es la elegida;
AVL y arreglos quedan como alternativas consideradas, sin autorización de implementación.

La recomendación inicial de reutilizar el AVL no fue la elección del usuario y no se
mantiene como propuesta activa para el registro de distancias.

### D-TC-02a — Resolución de colisiones

**Decisión**: doble hashing, aprobado por el usuario el 2026-11-08. Tras expresar
«Double hashing suen bastante bien», confirma explícitamente: «Confirmo».

**Justificación técnica**: una segunda función determina el salto de sondeo y evita la
agrupación primaria propia del sondeo lineal. El salto debe ser coprimo con la capacidad
para permitir visitar todas las posiciones. La fórmula concreta, las capacidades y el
umbral de crecimiento aún no están fijados; deben documentarse y validarse sin asumir
garantías de rendimiento. Dos claves con igual posición y salto aún pueden colisionar.

Alternativas consideradas:

| Variante propia | Ventaja | Desventaja |
| --- | --- | --- |
| Sondeo lineal | Usa posiciones sucesivas del arreglo; sencillo y sin nodos por enlace | Puede formar grupos de posiciones ocupadas y exige controlar la ocupación |
| Encadenamiento con listas enlazadas | Cada posición mantiene su cadena; separa los registros que colisionan | Añade nodos, referencias y recorridos de cadenas |
| Doble hashing | Una segunda dispersión determina los saltos y reduce la agrupación primaria | Más cálculo y cuidado para que los saltos permitan recorrer la tabla |

La recomendación inicial de sondeo lineal no fue la elección del usuario. Se adopta
doble hashing; su rapidez y la ampliación se verificarán con mediciones. Los tiempos de
redistribución cuentan en la operación que los provoca.

La función de dispersión debe ser reproducible; el desempate del juego nunca dependerá
del orden de recorrido de la tabla. El registro de posiciones fue aprobado en D-TC-03a.
No se ha elegido un método de borrado para la tabla.

## D-TC-03 — Mejoras de distancia

**Decisión**: opción B, heap indexado con actualización de prioridad, aprobada por el
usuario el 2026-11-08 mediante «B» en respuesta a la comparación A/B.

**Justificación técnica**: conservar una sola entrada pendiente por sala evita duplicados
por mejoras. Cuando disminuye la prioridad, se localiza la entrada y se restaura el orden
del heap; toda entrada desplazada debe actualizar su posición registrada. La corrección
de esa correspondencia se debe verificar también al insertar y extraer.

Alternativas consideradas:

- Insertar una nueva entrada y descartar las obsoletas al extraer: mantenimiento más
  sencillo, pero puede retener entradas duplicadas y gastar más memoria.
- Actualizar una entrada existente por su posición: limita duplicados, pero exige localizar
  posiciones y mantener su correspondencia después de cada cambio de orden.

No se autoriza implícitamente una estructura auxiliar para resolver este problema.

**Comparación presentada al usuario**:

| Opción | Ejemplo al mejorar sala 7 de costo 250 a 180 | Ventaja | Desventaja |
| --- | --- | --- | --- |
| A. Nuevas entradas y descarte de obsoletas | Actualizar el registro a 180 e insertar otra entrada; ignorar la de 250 al extraerla | Heap sencillo, sin mantener posiciones de cada sala | Puede aumentar las entradas pendientes y el trabajo de descarte |
| B. Heap indexado con actualización de prioridad | Localizar la entrada de sala 7 y bajar su costo a 180, restaurando el orden | Una entrada pendiente por sala, sin duplicados por mejoras | Hay que guardar y actualizar la posición de cada entrada en cada movimiento del heap |

La recomendación inicial A no fue la elección del usuario. Se adopta B, sin afirmar
ventaja empírica hasta medir. El registro concreto de posiciones fue elegido en D-TC-03a.

La prioridad debe respetar el menor primer vecino en empates. Una mejora de primer paso
con igual distancia también debe reflejarse en la entrada y el orden que corresponda.

### D-TC-03a — Registro de posiciones del heap

**Decisión**: opción A, aprobada por el usuario el 2026-11-08 mediante «A».
Cada registro hash de sala contiene su distancia y su posición en el heap. No se crea
otra tabla de posiciones. Cada desplazamiento de una entrada debe actualizar ese campo.

**Justificación**: aprovechar la tabla propia ya elegida evita mantener otro índice y
sus ampliaciones. Se debe verificar la correspondencia en ambos sentidos entre cada
entrada del heap y el registro de la sala, también después de redimensionar la tabla.

Alternativas consideradas:

| Opción | Ventaja | Desventaja |
| --- | --- | --- |
| A. Campo de posición en el registro hash de cada sala, junto a su distancia | Aprovecha la tabla elegida y evita otro índice | El registro reúne distancia y estado de participación en el heap; se deben actualizar juntos |
| B. Otra tabla hash propia para sala → posición del heap | Separa el índice del registro de distancias | Mantiene dos tablas, con su memoria, colisiones y posibles ampliaciones |

Se adopta A. La implementación usa -1 fuera del heap y D-TC-08 define el crecimiento.
La posición en el heap no debe confundirse con la casilla de
la tabla hash, que puede cambiar al redistribuir los registros.

## D-TC-04 — Trabajo individual o compartido

**Decisión**: opción A, búsqueda individual limitada por rango, aprobada por el usuario
el 2026-11-08 mediante «A». Cada cazador busca desde su sala hasta la sala actual del
jugador dentro de su rango; no se adopta una estrategia compartida o combinada para juego.

**Justificación técnica**: limita directamente la exploración a la región del cazador y
evita mantener una política que seleccione entre modalidades. Puede repetir trabajo con
muchos cazadores; se debe medir ese costo. No garantiza por sí sola el límite de 20 ms.

Alternativas consideradas:

- Búsqueda individual limitada por rango: respeta la región del cazador, puede repetir trabajo.
- Búsqueda compartida desde el jugador: puede amortizar trabajo entre muchos perseguidores;
  su alcance/preparación debe medirse para no penalizar consultas de rango pequeño.
- Combinación: puede adaptarse a cargas distintas, pero necesita criterios medidos y agrega
  complejidad de validación. No se fija un umbral sin autorización y evidencia.

**Comparación presentada al usuario**:

| Opción | Comportamiento | Ventaja | Desventaja |
| --- | --- | --- | --- |
| A. Individual | Cada cazador busca desde su sala, limitado por su rango | Limita directamente el trabajo a la región del cazador | Puede repetir exploraciones entre muchos cazadores |
| B. Compartida | Una búsqueda desde el jugador produce distancias aprovechables por varios cazadores para el mismo estado de puertas y objetivo | Puede amortizar trabajo cuando muchos persiguen al mismo jugador | Puede explorar mucho trabajo innecesario para cazadores aislados o de rango pequeño |
| C. Combinada | Usa la modalidad individual o compartida según la carga | Permite atender escenarios pequeños y muchos perseguidores | Requiere dos modalidades y una política de selección justificada con mediciones |

La recomendación inicial C no fue la elección del usuario. Se adopta A y se conserva la
comparación obligatoria de cálculo individual y compartido en --bench (PR-TC-003), sin
convertir esa alternativa de medición en una política de juego aprobada. El diseño de
las estructuras de la comparación se revisará con el usuario si requiere otras nuevas.

La modalidad compartida aprovecha la simetría de costos y puertas: con distancias hasta
el jugador, cada cazador elige la vecina de menor ID que inicia una ruta mínima dentro
de su propio rango. No basta con compartir el primer paso de otro cazador. Una búsqueda
compartida global no puede ignorar PR-TC-002 para consultas de rango pequeño.
Compartir durante un mismo estado no autoriza reutilizar datos después de cambios;
esa validez se decide y demuestra en D-TC-05.

## D-TC-05 — Vigencia de resultados

**Decisión**: opción B, reutilización conservadora, aprobada por el usuario el
2026-11-08 mediante «B». Recalcular ante cambios de las condiciones de la consulta
o ante duda sobre su validez.

**Justificación técnica**: permite evitar repetir una consulta idéntica sin mantener
dependencias selectivas de cada ruta. La validez comprende origen del cazador, objetivo,
rango, costos y puertas. Se invalida también ante carga o retroceso si no se demuestra
compatibilidad. El resultado reutilizado debe coincidir con recalcular desde cero.

Alternativas consideradas:

- Recalcular siempre: facilita comparar con las reglas actuales, repite trabajo.
- Reutilizar con invalidación conservadora: puede ahorrar trabajo mientras no cambien los
  datos relevantes, pero hay que identificar puertas, objetivo y estado restaurado.
- Invalidación selectiva: puede reducir recálculos, exige registros adicionales y demostrar
  que las dependencias elegidas no permiten decisiones obsoletas.

Se conserva la comparación obligatoria con recálculo siempre para puertas estables e
inestables. La aprobación de la política no elige implícitamente una estructura adicional
para almacenar resultados ni un mecanismo concreto de detección de cambios.

**Comparación presentada al usuario**:

| Opción | Regla | Ventaja | Desventaja |
| --- | --- | --- | --- |
| A. Recalcular siempre | Ejecutar la búsqueda en cada decisión del cazador | Facilita la corrección y sirve como referencia | Repite trabajo incluso cuando la consulta no cambió |
| B. Reutilización conservadora | Reutilizar solo si origen del cazador, objetivo, rango, costos y estado de puertas siguen siendo compatibles; ante un cambio o duda, recalcular | Puede evitar repeticiones sin rastrear dependencias finas | Un cambio de puerta lejana también puede obligar a recalcular |
| C. Invalidación selectiva | Demostrar qué cambios afectan a cada resultado y conservar los restantes | Puede evitar más recálculos | Exige dependencias adicionales y demostrar que detecta nuevas rutas más baratas |

Se adopta B. La ganancia puede ser pequeña si los actores o puertas cambian en cada
consulta: --bench debe contrastar puertas estables e inestables con A. La comprobación
de validez no debe ocultar un recorrido completo del mapa en cada decisión.

La condición de validez debe incluir origen y objetivo, no solo puertas. El retroceso y
la carga no pueden dejar resultados de otro estado como válidos. Abrir una puerta fuera
de la ruta anterior puede crear una alternativa mejor; revisar únicamente las puertas
de esa ruta no demuestra equivalencia con recalcular desde cero.

## D-TC-06 — Acceso al mapa

**Decisión final**: conservar las listas de adyacencia existentes, aprobada por el
usuario el 2026-11-08 mediante «hagamoslo con las listas existentes».

Esta elección sustituye la aprobación anterior de matriz de adyacencia. El cambio se
produce tras discutir su memoria O(S²), el costo de escanear filas y las alternativas
dispersas. La matriz queda como alternativa descartada, no como parte del diseño activo.

**Justificación**: cada sala conserva solo sus salidas existentes, con referencias a
destinos y puertas; se añade el costo de tránsito. Se enumeran sus vecinos en O(grado),
con memoria O(S + E), sin construir otra representación del estado de las puertas.
No se requiere una matriz ni un índice compacto adicional para representar el mapa.

**Comparación presentada al usuario**:

| Opción | Representación | Ventaja | Desventaja |
| --- | --- | --- | --- |
| A. Listas de adyacencia existentes | Cada sala conserva sus salidas con referencias a destino y puerta; se añade el costo | Reutiliza el modelo y consulta directamente las puertas actuales; memoria O(S + E) | Recorre objetos y referencias, con su costo de acceso |
| B. Adyacencia en arreglos compactos | Índices internos y arreglos de conexiones, costos y referencias al estado de puertas | Puede reducir el costo de recorrer objetos; memoria O(S + E) | Requiere mapear IDs y coordinar la representación con el estado mutable del juego |
| C. Matriz de adyacencia | Una celda por cada par de salas | Consulta directa de la conexión entre dos salas | Memoria O(S²) y recorrido de filas, poco apropiados con pocas salidas por sala |

S es el número de salas y E el número de salidas almacenadas.

La tabla hash de distancias y el heap siguen siendo auxiliares independientes de la
representación del mapa; sus datos se crean para la región explorada por la búsqueda,
sin copiar todas las salas en cada consulta.

### D-TC-06a — Enumeración local de vecinos (resuelta)

**Resolución**: se conserva únicamente la lista de salidas por sala; se retira la matriz.
La aprobación final de D-TC-06 elimina la necesidad de un índice auxiliar junto a ella.

**Problema detectado**: recorrer S celdas de la fila para descubrir las salidas de cada
sala introduce un costo proporcional al tamaño total de la cripta incluso con rango
pequeño. Esa versión de Dijkstra sobre matriz no cumple PR-TC-002 (P2 §5.1). Limitar la
distancia de búsqueda no elimina el costo de escanear cada fila. La tabla hash y el
heap tampoco corrigen este costo.

Se consideraron matriz con listas auxiliares, listas solas y una representación dispersa
propia. El usuario eligió listas solas para evitar el costo cuadrático y reutilizar el
modelo. No se genera correspondencia ID → índice para una matriz ya descartada.

Esta resolución permite un recorrido de vecinos local; no constituye una medición del
ciclo ni demuestra todavía el cumplimiento de los 20 ms.

## D-TC-07 — Almacenamiento de resultados reutilizables

**Decisión**: opción A, un último resultado por cazador, aprobada por el usuario el
2026-11-08 mediante «A». Se asocia al actor un registro de resultado y condiciones de
validez; no se crea una caché de varias consultas ni una política de reemplazo.

**Justificación**: acota los datos conservados a un registro por cazador. El resultado
incluye primer paso y costo mínimo, o ausencia de ruta dentro del rango. No se retienen
automáticamente el heap ni todas las distancias de búsquedas anteriores.

Alternativas consideradas:

| Opción | Ventaja | Desventaja |
| --- | --- | --- |
| A. Un último resultado por cazador, en un registro asociado al actor | Almacenamiento acotado por cazador; sin otra tabla de consultas | Solo aprovecha la última consulta si conserva las condiciones de validez |
| B. Varios resultados por cazador en una caché de consultas | Puede reutilizar consultas anteriores si vuelve a coincidir su estado | Exige otra estructura, límite y política de reemplazo, todavía no elegidos |

La validez requiere comparar origen, objetivo, rango y estado de conexiones/costos; la
comparación no recorrerá todo el mapa. Una revisión escalar de cambios puede invalidar
conservadoramente resultados sin un índice adicional. Al cargar o retroceder se pueden
descartar estos resultados derivados sin modificar el estado observable del juego.

## D-TC-08 — Capacidad y crecimiento de la tabla con doble hashing

**Decisión**: opción A, aprobada por el usuario el 2026-11-08 mediante «A entonces»:
32 posiciones iniciales, capacidades potencia de dos, duplicación, salto impar y
ampliación antes de superar el 70 % de ocupación.

Se usarán dos dispersiones deterministas propias y se mantendrán como entradas los
registros de las salas alcanzadas. El 70 % es el parámetro inicial acordado, revisable
con mediciones; no es garantía de tiempo ni regla del enunciado. Actualizar una clave
existente no incrementa la ocupación. Las colisiones siempre comparan la clave.

| Opción | Capacidad y salto | Ventaja | Desventaja |
| --- | --- | --- | --- |
| A. Potencias de dos | Comenzar con 32 posiciones, duplicar; la segunda dispersión produce un salto impar menor que la capacidad | Salto coprimo garantizado, crecimiento sencillo y sin buscar primos | Requiere mezclar bien los bits del ID para evitar distribuciones pobres |
| B. Capacidades primas | Comenzar con 31 posiciones, crecer al siguiente primo al menos doble; salto entre 1 y capacidad menos 1 | Cualquier salto permitido es coprimo con la capacidad prima | Añade búsqueda/verificación de primos durante el crecimiento |

**Justificación**: concreta el doble hashing elegido sin otra estructura ni búsqueda de
primos. El salto impar es coprimo con cualquier capacidad potencia de dos. Deben medirse
distribución, sondeos y picos de redistribución con claves ordenadas y claves que colisionen.
No se inicializa una tabla del tamaño de toda la cripta por turno. No se necesita borrado
individual para esta búsqueda: los registros permanecen hasta finalizarla y luego se
libera su espacio de trabajo; extraer del heap solo cambia el estado del registro.

## Riesgos que debe resolver el diseño elegido

- Una frontera eficiente no basta si cada búsqueda copia o reinicializa todas las salas.
- El empate solicitado es el menor ID del primer vecino de una ruta mínima, no el menor
  ID arbitrario de cualquier sala pendiente.
- Compartir resultados solo es correcto con decisiones equivalentes a calcular desde cero.
- Un resultado posterior a un pergamino debe corresponder al estado restaurado.
- La integración debe preservar presupuesto, versiones, estado del azar y MVC.

## Cierre de investigación

### Ampliación elegida: caché compartida acotada (2026-11-12)

El usuario eligió «Caché compartida acotada con tabla hash propia» frente a
mantener solo la caché individual y medir K menores. Se conserva Dijkstra y
el desempate vigente; se comparten únicamente resultados con el mismo origen,
objetivo, rango y revisión del motor. Se comprueban referencias por identidad.

La tabla propia usa 256 posiciones, doble hashing y salto impar. No crece:
al superar el 70 % se vacía antes de insertar. Este límite es un parámetro
inicial del ensayo, no una decisión sobre K. No conserva tablas ni heaps de
Dijkstra. Aciertos y fallos no consumen azar ni reloj virtual. Apertura/cierre,
cambio de costo y retroceso vacían la caché; carga y copia parten de una vacía.
Es un auxiliar derivado por motor: no se persiste ni entra en deltas o puntos.

Validar colisiones, límite, resultados negativos, rangos distintos, identidad,
puertas, costo, retroceso y carga; comparar las mismas consultas oficiales
con caché individual y compartida antes de declarar una mejora o aceptación.

No quedan elecciones de estructuras pendientes para esta capacidad. El diseño detallado
está en [data-model.md](data-model.md), los contratos en
[contracts/terreno-cazadores.md](contracts/terreno-cazadores.md) y la validación prevista
en [quickstart.md](quickstart.md). La especificación deberá confirmarse en Git antes del
código: se cumplió con 290f173 y 1071237. El análisis se completó el 2026-11-09 y la
ejecución se registra en [tasks.md](tasks.md). Los resultados finales se incorporaron a
documentacion/DOCUMENTO_DECISIONES.md, sin sustituir las decisiones del usuario.
