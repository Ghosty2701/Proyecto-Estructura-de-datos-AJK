# Investigación: Verificación de resolubilidad

**Fecha**: 2026-11-09. **Estado**: investigación completada; siete elecciones
aprobadas y dos interpretaciones finales aceptadas por el equipo.
El diagnóstico se justifica con el certificado de grupo descrito al final;
implementación, pruebas ejecutadas y mediciones siguen pendientes.
Fuentes: [spec.md](spec.md), constitución, PDF §§3.5/4.2/5.4 y código local.
Investigación delegada de solo lectura conforme a speckit-plan.
Los costes siguientes son teóricos; no son mediciones del proyecto.

## Hallazgos

- `modelo/conocimiento.py:IndiceSalas` y `modelo/tabla_hash.py:TablaDistancias`
  aceptan solo enteros. Los IDs de llaves son texto; requieren adaptación.
- `adaptadores/cache_catalogo.py:ArbolAVL` admite claves comparables, pero su
  reutilización para un problema nuevo requiere aprobación. Evitar que el modelo
  dependa de infraestructura por la ubicación actual de esa clase.
- FuenteDatos, ClienteHTTP y ModoOffline no tienen consulta de ubicaciones.
  P2 §4.2 define `/criptas/<id>/llaves`, con registros id/sala/enemigo opcional.
  Integrarla mediante `_get` conserva presupuesto y reintentos. No descargar
  contenido de todas las salas para averiguar dónde están las llaves.
- El cargador existente construye actores, motor y niebla. El verificador
  independiente debe poder trabajar sin esa construcción.
- El esqueleto está actualmente en AVL. Su coste de preparación no debe ocultarse
  al medir el total local, aunque se mida aparte del cierre incremental.

## D-RS-01 — Topología independiente del juego

**Decisión**: A, aprobada por el usuario el 2026-11-09 en el bloque
«1A, 2A, 3A, 4A, 5A, 6A, 7A». **Recomendación presentada**: A.
Atiende FR-RS-001/002/007/013 y PR-RS-002.

| Opción | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Arreglo de salas compactas, listas de salidas por sala y registros de puertas físicas compartidos | O(S+E) espacio; representación similar a la existente; acceso directo por posición | Preparar posiciones y validar referencias, extremos y reciprocidad |
| B. Arreglos planos de salidas con límites por sala | O(S+E), menos listas y almacenamiento contiguo | Construcción en varias pasadas y manejo de límites más complejo |
| C. Nodos y listas enlazadas propios | Referencias directas y estructura explícita | Más objetos, enlaces y código |

Conservar identidad de puerta: salidas recíprocas de una puerta comparten
registro, pero puertas distintas no se fusionan solo por tener los mismos
extremos. No construir vista, actores ni conocimiento del jugador para verificar.
No se propone matriz S×S por su memoria cuadrática para este mapa disperso.

## D-RS-02 — Índice de IDs de salas

**Decisión**: A, aprobada en el mismo bloque. **Recomendación presentada**: A.
Atiende FR-RS-001/005/015 y PR-RS-002.

| Opción | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Adaptar/reutilizar el índice hash propio entero → posición | O(1) esperado por consulta; admite IDs dispersos | Colisiones: peor caso lineal por consulta; memoria adicional |
| B. AVL propio existente | O(log S) en peor caso por consulta; ya implementado | Factores logarítmicos al resolver destinos; revisar ubicación MVC |

La propuesta A incluye doble hashing, reserva inicial potencia de dos con carga
máxima 70 %, salto impar y sondeo acotado, como el índice existente. No reservar
hasta el ID máximo. La aprobación de niebla no se transfiere automáticamente.

## D-RS-03 — Índice y registros de llaves

**Decisión**: A, aprobada en el mismo bloque. **Recomendación presentada**: A.
Atiende FR-RS-004/005/006/007/015 y PR-RS-002.

| Opción | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Hash propio texto → posición compacta y arreglo de registros | O(1) esperado después de procesar el texto; estados por posición | Nueva mezcla de texto y pruebas de colisiones |
| B. AVL propio texto → registro | O(log K) comparaciones en peor caso; sin nueva mezcla | Más nodos y factores logarítmicos |

La propuesta A incluye mezcla reproducible por caracteres, doble hashing,
reserva potencia de dos con carga máxima 70 %, salto impar y sondeo acotado.
La mezcla concreta se documentará antes del código. Usar una cota del total de
IDs referidos en ubicaciones y puertas para reservar sin crecer durante el
cierre; puede reservar más que el número de llaves únicas, con memoria O(E+K).
Validar duplicados/referencias. No usar dict/set ni hash(texto) aleatorio del
proceso; el orden observable no depende de las casillas. Contabilizar longitud
de identificadores al expresar costes, además de S, E y K.

## D-RS-04 — Salas pendientes

**Decisión**: A, aprobada en el mismo bloque. **Recomendación presentada**: A.
Atiende FR-RS-004/005/009 y PR-RS-002.

| Opción | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Cola FIFO propia con lista y cursor | Inserción amortizada y extracción O(1); sin desplazamientos | Retiene entradas procesadas hasta terminar, O(S) espacio |
| B. Pila propia con lista, append y pop al final | Pequeña implementación; operaciones amortizadas O(1) | Orden en profundidad diferente, aunque puede ser válido y determinista |
| C. Cola enlazada propia con cabeza/cola | Operaciones O(1), permite liberar nodos retirados | Más nodos, asignaciones y código |

Marcar salas para procesar cada una una vez. No usar pop(0), collections.deque
ni heap de costes: se busca alcanzabilidad, no el camino más barato.

## D-RS-05 — Llaves por sala y puertas pendientes por llave

**Decisión**: A, aprobada en el mismo bloque. **Recomendación presentada**: A.
Atiende FR-RS-002/004/005/007 y PR-RS-002.

| Opción | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Listas agrupadas por posición de sala/llave | Obtener K procesa solo las puertas que esperaban K; total de relaciones O(S+E+K) | Cuidar duplicados y activaciones repetidas |
| B. Listas enlazadas propias con cabezas por sala/llave | Mismo orden de complejidad; extracción sin desplazamientos | Más objetos y gestión de enlaces |

Una lista global reexaminada por cada llave no cumple PR-RS-002 en producción;
se reserva para la comparación lenta de bench.

## D-RS-06 — Conservar alternativas para diagnosticar ciclos

**Decisión de representación**: A, aprobada en el mismo bloque.
**Recomendación presentada**: A.
Atiende FR-RS-008/009 y PR-RS-002. La justificación del algoritmo se concreta
en el cierre de investigación; las comprobaciones de ejecución siguen pendientes.

| Opción | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Registros compactos de reglas y procedencia, listas de incidencias, arreglos de marcas y pila explícita propia | Conserva origen, puerta/llave y destino; análisis por posiciones sin recursión profunda | Más registros auxiliares; falta justificar cómo certificar ciclos reales |
| B. Nodos propios de reglas, referencias y enlaces de incidencias, marcas y pila enlazada propia | Misma información mediante referencias explícitas | Más objetos y enlaces; tampoco demuestra por sí sola los ciclos |

Conservar la condición conjunta «origen alcanzable Y llave obtenida permite
destino» y las varias alternativas que permiten llegar a un destino. No
convertir prematuramente alternativas en dependencias inevitables llave → llave.

Un cierre incremental O(S+E+K) esperado no demuestra el mismo coste y corrección
del diagnóstico. DFS o componentes fuertemente conexas en un grafo simplificado
no bastan para probar que una llave requiere inevitablemente de sí misma.

Contraejemplo de control: S conecta mediante B con X, que contiene A; X e Y
conectan mediante A; B está en Z aislada. La reciprocidad X↔Y puede crear un
ciclo estructural con A, aunque el bloqueo de entrada real de X sea B aislada.
No presentar aquel ciclo como prueba de que A solo se obtiene con A.

La fase 0 exige justificar diagnóstico con alternativas, aislamiento y
reciprocidad antes de cerrarse. El PDF pide detectar y señalar el ciclo
concreto; no exige enumerar todos los ciclos simples posibles. No introducir
una obligación exponencial de enumeración. Si se necesita otra estructura,
consultar al usuario antes de elegirla.

## D-RS-07 — Ubicaciones entre ejecuciones

**Decisión**: A, aprobada en el mismo bloque. **Recomendación presentada**: A.
Atiende FR-RS-014/015 y AC-RS-017/018/019/020.

| Opción | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Una consulta por ejecución y reutilización en memoria al iniciar | Menos integración; no duplica la consulta entre verificar e iniciar | Una nueva ejecución vuelve a consultar |
| B. Archivo JSON de registros con identidad/versión y los índices aprobados en memoria | Puede ahorrar solicitudes futuras | Validar versión y gestionar archivos incompletos/errores; más pruebas |

Persistir es opcional. Ambas opciones validan identidad y versión; B no autoriza
dict/set como índices. No modificar guardados de partida por esta elección sin
justificación. Las siete elecciones están aprobadas; no se transfiere esa
aprobación a otras estructuras. No se ejecutaron pruebas ni benchmarks.

## Integración concretada tras las elecciones

- La respuesta de ubicaciones del PDF no incluye un campo `version` obligatorio.
  Asociarla localmente con el ID y versión de los datos generales y comprobar
  estabilidad mediante el endpoint de versión; esta comprobación también cuenta
  en el presupuesto. No inventar un campo requerido en `/llaves`.
- Mantener las ubicaciones validadas en memoria y compartir esa carga al iniciar;
  no consultar otra vez esqueleto y llaves en el mismo flujo. No crear caché de
  ubicaciones en disco con D-RS-07A.
- El campo `enemigo` es una instancia, no un ID de ficha. No descargar contenidos
  para confirmar una ubicación que ya entrega este endpoint.
- No suponer unicidad de ubicación por ID si el contrato no la establece. Un
  registro de llave puede conservar varias ubicaciones en las listas aprobadas;
  alcanzar una ubicación basta para obtenerla. Esto conserva alternativas sin
  introducir otra estructura. Distinguir repetición de ID de referencia inválida.
- Offline usará el equivalente `criptas/ID/llaves.json`; ausencia o JSON inválido
  será error de datos, sin reinterpretarlo como resultado negativo.
- El cargador empareja actualmente conexiones por extremos, lo que no demuestra
  correspondencia inequívoca para puertas paralelas. Comprobar el contrato de
  direcciones/identidad antes de fijar la normalización del verificador.

## Justificación del cierre incremental aprobado

Mantener estados de sala descubierta/procesada y llave obtenida en los arreglos
aprobados. Encolar la sala inicial y marcarla antes de encolarla. Al procesar
una sala, obtener sus llaves antes de examinar sus salidas, registrando cada
llave por primera obtención. Obtener una llave reactiva solamente su lista de
puertas pendientes, agregadas desde orígenes ya alcanzados. Una salida abierta
o con llave obtenida descubre su destino; una cerrada sin llave queda pendiente.
Cada sala se encola como máximo una vez y cada relación pendiente se activa una
vez; no se necesita recorrer otra vez todas las salas al obtener una llave.

**Invariante**: toda sala descubierta admite un recorrido bajo los supuestos
con las llaves ya obtenidas; cada llave del orden se obtuvo en una sala
descubierta, sin necesitar una llave posterior. **Completitud**: al vaciar la
cola, ninguna salida transitable desde una sala alcanzada conduce a una sala
sin descubrir, ni queda una llave obtenible en una sala alcanzada. Ese conjunto
es el cierre de las reglas de §3.5. Mantener los registros de victoria aparte:
alcanzar la sala de salida sin obtener la llave y sin un acceso que la requiera
no basta. Para el informe, completar el cierre aunque la victoria se detecte antes.

El cierre y las incidencias tienen trabajo O(S+E+U) con posiciones resueltas,
donde U es el número de ubicaciones; con índices hash, la preparación tiene
coste esperado lineal en registros y longitud de IDs, no garantía de peor caso.
Esto todavía no demuestra la complejidad del diagnóstico de ciclos.

## Análisis previo del certificado de ciclos

Un certificado de autobloqueo para un conjunto C de llaves debe distinguir
aislamiento de dependencia circular. Como comprobación conceptual: aun
suponiendo disponibles las llaves externas a C, ninguna C se obtiene sin alguna
C; al permitir las de C, existen accesos hacia sus ubicaciones. Esta comprobación
no autoriza implementar un recorrido nuevo por cada llave o candidato: todavía
falta justificar la generación y validación del informe en el trabajo permitido.
No registrar DFS/componentes conexas sobre dependencias simplificadas como una
solución ya demostrada. Las elecciones de estructuras están cerradas; esta
obligación de corrección quedó abierta en esta revisión previa y se resuelve
con el certificado y la interpretación aprobada al final de este documento.

### Resultado de la revisión cruzada previa del certificado (histórico)

Se estudió un certificado colectivo que usa solo los arreglos, listas, índices
y cola aprobados, sin cambiar la partida ni sus llaves reales:

1. Marcar en un recorrido físico las ubicaciones conectadas al inicio al ignorar
   cerraduras abribles con llaves válidas. Mantener barreras permanentemente
   intransitables si el contrato las permite. Sea P la lista marcada de llaves.
2. Ejecutar un cierre diagnóstico, hipotéticamente disponibles las llaves fuera
   de P, que son físicamente aisladas. Sea C el grupo que aún no se obtiene.
3. C está físicamente conectado y, aun disponibles las llaves externas a C,
   ninguna de C puede ser la primera: el cierre ya era un punto fijo. Separa un
   bloqueo colectivo circular de las consecuencias del aislamiento.

Este certificado colectivo tiene justificación, pero no resuelve por sí solo
el ciclo concreto requerido. Se rechazó una extracción propuesta: elegir para
cada llave la primera llave de C que bloquea una ruta de un árbol físico y
buscar ciclos en esa función. Puede señalar una dependencia individual falsa.

**Contraejemplo de rechazo**: S conecta con X, que contiene B, por dos accesos,
uno exige B y otro A; S conecta con Y, que contiene A, mediante A. C={A,B} es
un grupo bloqueado, pero elegir el acceso B del árbol genera B → B pese a que
A permite obtener B sin B. El ciclo inevitable de este ejemplo es A → A.
El grupo no permite certificar arbitrariamente todos sus ciclos de rutas.

No se adopta ese algoritmo de extracción ni se rebaja FR-RS-008 para hacerlo
pasar. Queda identificado el trabajo pendiente: producir el ciclo concreto
respaldado por las alternativas, sin recorridos completos por llave ni coste
cuadrático encubierto. La revisión cruzada fue razonamiento sobre casos, no
ejecución de pruebas ni benchmark. El acceso web al OpenAPI del servicio no
estuvo disponible en esta revisión; la correspondencia de puertas paralelas
sigue pendiente de contrastar con el contrato exacto en esa revisión histórica.

## Revisión posterior: contrato verificado y propuesta de certificado con alternativas

**Estado**: propuesta técnica revisada, posteriormente aceptada por el equipo.
Las siete decisiones de estructuras siguen aprobadas y no se sustituyen.

### Evidencia del contrato

Se leyó el [OpenAPI oficial](https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/openapi.json),
API 1.1.0, y se conservó un extracto con su huella en
[evidencia de contrato](../../documentacion/evidencia/contrato_resolubilidad_openapi_2026-11-09.json).
SHA256 del documento completo:
`e68e8c7a9316b60c98227c1fc47f7a8bff2cea6d65522611aa9cd67c1fb38d36`.

- Exit se describe como salida dirigida, con `sala` obligatorio. No hay ID de
  puerta, correspondencia inversa ni garantía de direcciones opuestas.
- `costo`, `cerrada`, `llave` y `cierre_automatico` son opcionales y admiten null.
  El esquema no prohíbe una salida cerrada sin llave; no declararla inválida
  solo por esa ausencia. Bajo §3.5, una salida cerrada sin llave obtenible no
  aporta un paso habilitable. No atravesarla hipotéticamente como si tuviera llave.
- KeyLocation requiere id/sala, admite enemigo nulo y no impone una sola
  ubicación por llave. LlavesResponse no contiene versión.
- La interpretación de identidad física de salidas recíprocas necesita una
  regla del equipo o P1; no deducirla del Swagger. La detección de ambigüedad
  no autoriza fusionar puertas distintas ni modifica por sí sola la partida.

Las consultas fueron a documentación pública, no a endpoints de datos de una
cripta. El acceso por socket requirió autorización automática de solo lectura;
la lectura terminó correctamente. No se cambió el cliente del juego.

### Propuesta de certificado circular de reglas

Esta propuesta conserva los antecedentes conjuntos y todas las alternativas;
no demuestra que cada flecha comprimida entre llaves sea individualmente
inevitable. El equipo aceptó esa distinción, incorporada a FR-RS-008 en spec.md.

1. Mantener el cierre real y su informe, sin modificarlo. Para el diagnóstico,
   usar la conectividad física y el cierre hipotético con llaves aisladas ya
   descritos. No sembrar esas llaves en la partida ni mostrarlas como obtenidas.
2. Construir, con las incidencias ya registradas, un grafo de justificación
   negativa de salas y llaves aún no obtenibles pero físicamente accesibles.
   Para CADA alternativa entrante de una sala: si su origen no es alcanzado,
   enlazar a ese origen; si el origen sí fue alcanzado, enlazar a la llave que
   falta. Cada llave enlaza a TODAS sus ubicaciones físicamente accesibles.
   Conservar los antecedentes y la puerta de procedencia en los registros.
3. Una alternativa desde un origen físicamente inaccesible, una ubicación
   físicamente aislada o una barrera sin llave permanece documentada como
   imposibilidad estructural. No convertirla en una dependencia circular ni
   omitirla del razonamiento sobre alternativas por carecer de nodo activo.
4. Estudiar componentes fuertemente conexas sin enlaces salientes del grafo
   residual. La propuesta es obtenerlas con recorridos iterativos propios,
   listas de incidencias directas/inversas y pilas/arreglos ya aprobados.
   Conservar todas las reglas que justifican el cierre de cada componente.
5. Para una componente con una llave k, elegir determinísticamente una de sus
   ubicaciones r dentro de la componente y buscar un camino r → k restringido
   a ella. La arista k → r completa un ciclo concreto que incluye una llave,
   evitando presentar únicamente un ciclo físico de pasillos recíprocos.

**Justificación del certificado**: cada alternativa de producir un nodo del
grupo tiene al menos un antecedente no satisfecho dentro del mismo grupo, o
una imposibilidad estructural explícita. Por tanto no existe un primer nodo
del grupo que pueda obtenerse. La extracción del camino se apoya en la
conectividad fuerte. El informe debe mostrar grupo, alternativas y ciclo de
reglas con puertas identificadas, no afirmar exclusividad individual de sus
aristas entre llaves.

**Coste previsto**: número constante de recorridos globales y cierres, no uno
por llave. Incidencias y sus inversas tienen O(S+E+U) registros. Las búsquedas
de testigos quedan limitadas a componentes disjuntas; inicializar arreglos una
vez, no por componente. El trabajo esperado incluye índices y longitud de
IDs; falta contrastarlo con pruebas y bench. Una propuesta y su razonamiento
no se registran como funcionalidad implementada o verificada.

### Dos interpretaciones aprobadas por el equipo

1. Aceptar el certificado de grupo con alternativas y un ciclo concreto de
   reglas, o exigir que cada flecha entre llaves sea individualmente inevitable
   en todas las rutas. El equipo aprobó la primera lectura.
2. Conservar el convenio heredado de puerta compartida cuando las salidas
   recíprocas admiten un emparejamiento único y compatible, informando la
   ambigüedad sin fusionar conexiones; o considerar cada salida dirigida una
   unidad independiente. El equipo aprobó la primera interpretación;
   Swagger por sí solo no la establece.

Se presentaron juntas por preferencia del usuario. Respuestas literales:
«Certificado del grupo y ciclo concreto (recomendado)» y «Recíprocas únicas
comparten puerta; ambigüedad se informa (recomendado)».

## Cierre de investigación

La revisión cruzada confirma el certificado de grupo bajo la interpretación
aprobada. Para no perder alternativas, una llave es físicamente conectada si
AL MENOS UNA de sus ubicaciones lo es; el grafo residual incluye TODAS sus
ubicaciones físicamente conectadas. Una alternativa de origen aislado o de
barrera cerrada sin llave se conserva en el informe con esa justificación.
No se exige que produzca un enlace circular. Cada alternativa posible aporta
su antecedente falso al certificado. Un primer nodo obtenible del grupo
contradiría alguno de esos antecedentes, por lo que el bloqueo es circular.

Una componente cerrada relevante no puede estar formada solo por salas:
el primer ingreso de un camino físico desde el inicio a ese grupo produciría
un enlace hacia una sala exterior o una llave faltante, contradiciendo que
no haya enlaces salientes. El testigo elegido incluye por tanto una llave,
no simplemente un circuito de corredores.

Se empleará Kosaraju iterativo propio para las componentes, con las listas de
incidencias directas/inversas, arreglos de marcas, orden de finalización y pila
ya aprobados en D-RS-06A. Es una concreción del algoritmo sobre las estructuras
elegidas, sin bibliotecas de grafos ni recursión dependiente del tamaño del mapa.
La extracción de un testigo por componente cerrada con llave se limita a esa
componente; no inicializar un arreglo global nuevo por componente ni repetir
el recorrido de la cripta por llave. El certificado se genera solo para el
informe negativo; el veredicto siempre procede del cierre real.

Las salidas se recorren en orden N, S, E, O y las salas en el orden estable de
las páginas del esqueleto. Las ubicaciones conservan el orden de respuesta.
No recorrer casillas hash para producir el orden del informe. Al normalizar,
comparar como máximo las pocas salidas del destino para hallar una pareja
recíproca compatible y única; los costes dirigidos no identifican la puerta.
Compatibilidad de puerta: estado inicial, llave y cierre automático. Sin
emparejamiento único, conservar salidas separadas y advertir ambigüedad. No
rechazar una cripta válida solo por no poder inferir identidad física.

Para texto, concretar la mezcla de D-RS-03A mediante un acumulador entero fijo
de 64 bits: iniciar en 0xcbf29ce484222325 y aplicar la mezcla entera propia
existente a acumulador XOR ord(caracter) por cada carácter. Inicio por máscara;
segundo salto por mezcla del acumulador XOR 0x9e3779b97f4a7c15, enmascarado e
impar. Comparar siempre la clave completa. Es reproducible, no criptográfico;
no garantiza ausencia de colisiones ni tiempo constante en peor caso. Se
documentarán sondeos y límites en bench antes de afirmar ventaja empírica.

La carga de verificación leerá páginas en listas y normalizará directamente
con los índices aprobados, sin construir el AVL del juego. Al iniciar después,
la carga heredada podrá construir su AVL a partir de los mismos datos ya leídos,
sin nuevas solicitudes. Medir el procesamiento completo de verificación, no
ocultar preparación; el coste de construir una partida se informa por separado.
Compartir también la normalización de puertas entre verificador y cargador,
conservando la simetría de costes vigente de FR-TC-001. Para que la presentación
siga siendo lineal, mostrar ubicaciones y alternativas una sola vez en tablas
compartidas; puertas y grupos las referencian sin duplicar listas completas.

No quedan decisiones de estructuras ni interpretaciones abiertas para el diseño.
Las limitaciones conocidas (P1 ausente, colisiones y evidencia de ejecución
pendiente) se conservan sin atribuir resultados inexistentes al código actual.

Revisión documental final: 10 archivos Markdown revisados, enlaces locales
válidos, UTF-8 válido, 15 FR/3 PR/5 SC/20 AC conservados y checklist 16/16.
No se generó tasks.md. No son pruebas de ejecución del verificador ni mediciones.
