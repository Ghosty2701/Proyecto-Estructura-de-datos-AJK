# Investigación: Verificación de resolubilidad

**Fecha**: 2026-11-09. **Estado**: fase 0 en curso; ninguna estructura elegida.
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

**Decisión**: pendiente. **Recomendación**: A.
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

**Decisión**: pendiente. **Recomendación**: A.
Atiende FR-RS-001/005/015 y PR-RS-002.

| Opción | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Adaptar/reutilizar el índice hash propio entero → posición | O(1) esperado por consulta; admite IDs dispersos | Colisiones: peor caso lineal por consulta; memoria adicional |
| B. AVL propio existente | O(log S) en peor caso por consulta; ya implementado | Factores logarítmicos al resolver destinos; revisar ubicación MVC |

La propuesta A incluye doble hashing, reserva inicial potencia de dos con carga
máxima 70 %, salto impar y sondeo acotado, como el índice existente. No reservar
hasta el ID máximo. La aprobación de niebla no se transfiere automáticamente.

## D-RS-03 — Índice y registros de llaves

**Decisión**: pendiente. **Recomendación**: A.
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

**Decisión**: pendiente. **Recomendación**: A.
Atiende FR-RS-004/005/009 y PR-RS-002.

| Opción | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Cola FIFO propia con lista y cursor | Inserción amortizada y extracción O(1); sin desplazamientos | Retiene entradas procesadas hasta terminar, O(S) espacio |
| B. Pila propia con lista, append y pop al final | Pequeña implementación; operaciones amortizadas O(1) | Orden en profundidad diferente, aunque puede ser válido y determinista |
| C. Cola enlazada propia con cabeza/cola | Operaciones O(1), permite liberar nodos retirados | Más nodos, asignaciones y código |

Marcar salas para procesar cada una una vez. No usar pop(0), collections.deque
ni heap de costes: se busca alcanzabilidad, no el camino más barato.

## D-RS-05 — Llaves por sala y puertas pendientes por llave

**Decisión**: pendiente. **Recomendación**: A.
Atiende FR-RS-002/004/005/007 y PR-RS-002.

| Opción | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Listas agrupadas por posición de sala/llave | Obtener K procesa solo las puertas que esperaban K; total de relaciones O(S+E+K) | Cuidar duplicados y activaciones repetidas |
| B. Listas enlazadas propias con cabezas por sala/llave | Mismo orden de complejidad; extracción sin desplazamientos | Más objetos y gestión de enlaces |

Una lista global reexaminada por cada llave no cumple PR-RS-002 en producción;
se reserva para la comparación lenta de bench.

## D-RS-06 — Conservar alternativas para diagnosticar ciclos

**Decisión**: pendiente. **Recomendación de representación**: A.
Atiende FR-RS-008/009 y PR-RS-002. La corrección del algoritmo sigue pendiente.

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

**Decisión**: pendiente. **Recomendación**: A.
Atiende FR-RS-014/015 y AC-RS-017/018/019/020.

| Opción | Ventajas | Costes y riesgos |
| --- | --- | --- |
| A. Una consulta por ejecución y reutilización en memoria al iniciar | Menos integración; no duplica la consulta entre verificar e iniciar | Una nueva ejecución vuelve a consultar |
| B. Archivo JSON de registros con identidad/versión y los índices aprobados en memoria | Puede ahorrar solicitudes futuras | Validar versión y gestionar archivos incompletos/errores; más pruebas |

Persistir es opcional. Ambas opciones validan identidad y versión; B no autoriza
dict/set como índices. No modificar guardados de partida por esta elección sin
justificación. Se consultan las siete decisiones juntas por petición del usuario.
No se ejecutaron pruebas, benchmarks ni consultas al servidor.
