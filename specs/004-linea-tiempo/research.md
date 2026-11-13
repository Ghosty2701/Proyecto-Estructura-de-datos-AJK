# Investigación: Línea de tiempo y puntos de control

## D-LT-07: K predeterminado elegido — 2026-11-13

Juan eligió explícitamente **K=10**: «K=10: menor memoria y consultas medidas
<50 ms (recomendado)». Sustituye 25 provisional para partidas nuevas y replay
sin opción; `--checkpoint-cada` continúa permitiendo otra elección. Cargar sin
esa opción conserva el K guardado, según FR-LT-015/AC-LT-025.

Base: misma producción con registros inmutables compartidos; 5 000 acciones,
300 salas, 32 cazadores y 36 consultas. K5: máximo 24,264 ms / 756,94 MiB;
K10: 43,052 ms / 398,70 MiB; K25: 54,885 ms / 191,93 MiB y dos excedidos.
[Evidencia](../../documentacion/evidencia/k_oficial_registros_reutilizados_memoria_juan.json).
Se prefiere el equilibrio de K10 frente al mayor consumo/frecuencia de puntos
de K5. Esto justifica la elección, no garantiza otra corrida ni cierra 20 ms.
La nueva validación oficial dio máximo 35,9904 ms, 0/36 excedidos y RSS 400,14 MiB;
[resultado](../../documentacion/evidencia/validacion_k10_entrega.json). No se activa ningún
capturador experimental. Las menciones posteriores a K pendiente son históricas.

**Fecha**: 2026-11-09. **Especificación**: [spec.md](spec.md).
**Estado original del 2026-11-09**: decisiones D-LT-01 a D-LT-06 elegidas explícitamente por el usuario
(Kendall) tras presentar alternativas, ventajas, desventajas y recomendación,
conforme a AGENTS.md. El K por defecto (D-LT-07) queda pendiente de mediciones.

## Punto de partida medido

Mediciones exploratorias del 2026-11-09, en el equipo local con Python 3.14,
sobre cargas sintéticas deterministas (semilla 2026). Los scripts fueron de
exploración y no forman parte del entregable; las cifras finales las producirá
`--bench` (PR-LT-005).

| Operación | 200 salas | 300 salas | 1 000 salas |
| --- | --- | --- | --- |
| Guardar el modelo con el serializador binario existente | 42,6 ms | 58,7 ms | 194,9 ms |
| Cargar ese archivo | 52,6 ms | 74,0 ms | 237,0 ms |
| Copia de grafo en memoria (prototipo) | 4,2 ms | 5,9 ms | 17,0 ms |
| `copy.deepcopy` (solo referencia) | 8,5 ms | 13,7 ms | 42,9 ms |
| Memoria por copia en memoria | — | ≈343 KiB | ≈1 117 KiB |

Modelo: salas en anillo con dos salidas, un guardián cada diez salas, cinco
acciones con veneno. El modelo real añade conocimiento y contenido; se espera
más costo, no menos.

| Por acción, 80 salas sintéticas | 0 cazadores | 8 cazadores | 32 cazadores |
| --- | --- | --- | --- |
| Re-simular una acción (promedio / máximo) | 0,022 / 0,059 ms | 0,345 / 7,3 ms | 0,976 / 26,0 ms |
| Deshacer una acción (promedio) | 0,016 ms | 0,039 ms | 0,157 ms |
| Cambios registrados por acción (promedio / máximo) | 12 / 12 | 98 / 292 | 348 / 882 |

Consecuencias:

- El serializador binario no cabe en 20 ms por ciclo ni en 50 ms por consulta.
- Reconstruir hacia atrás exige conservar todos los cambios: con 32 cazadores,
  5 000 acciones ≈ 1,7 millones de registros (del orden de 260 MB). Hacia adelante
  solo exige conservar las órdenes.
- Re-simular es más caro por acción que deshacer, pero su memoria entre puntos es
  despreciable; el K por defecto debe equilibrar copias y acciones re-simuladas.

## D-LT-01 — Dirección de reconstrucción (§3.6, §5.5) — Elegida: hacia adelante

| Opción | Ventajas | Desventajas |
| --- | --- | --- |
| **A. Hacia adelante (elegida)** | Entre puntos solo se guardan órdenes; reutiliza la ejecución determinista de replay; la igualdad con la partida real se apoya en el determinismo ya probado. | Cada consulta copia un punto y re-simula ≤ K acciones; la re-simulación debe aislarse de la red y de la precarga. |
| B. Hacia atrás | Deshacer es ≈6 veces más barato por acción; los cambios ya se registran. | Memoria proporcional a todos los cambios (≈260 MB medidos para 5 000 acciones con 32 cazadores); traducir cada tipo de cambio a la copia exige un registro de identidades nuevo. |
| C. Híbrido | Consultas ≤ K/2 acciones. | Implementa ambas mitades, con doble memoria y doble superficie de errores. |

Recomendación presentada: A. Las mediciones posteriores confirmaron la elección
(memoria de B). Evidencia final: PR-LT-006.

## D-LT-02 — Localizar el punto de control más cercano — Elegida: arreglo + búsqueda binaria

Los puntos se crean en orden creciente de posición de orden, número de acción e
instante. Se agregan al final de un arreglo y se buscan con búsqueda binaria
propia, sin `bisect`: O(log P) con P puntos. No se borran puntos (ver D-LT-05).
Funciona con K distinto por tramo después de cargar.

Alternativas: AVL propio existente (O(log P), pero borrar en el recorte cuesta
O(r log P) y nunca se inserta en medio); índice directo k // K (O(1), pero no
admite K variable por tramo y buscar por instante sigue exigiendo búsqueda).

## D-LT-03 — Registro de acciones — Elegida: arreglo indexado por k (ampliada en D-LT-05)

Las acciones vigentes ocupan la posición k − 1: `#k` es O(1) e instante → k es
búsqueda binaria propia sobre instantes de decisión estrictamente crecientes
(cada acción avanza el reloj al menos 1). Recortar tras un pergamino trunca el
final en O(acciones revertidas).

Alternativas: lista enlazada (sin acceso por posición); AVL por instante (más
complejo y sin ventaja, porque las acciones llegan en orden).

## D-LT-04 — Copia completa de un punto de control — Elegida: copiador de grafo propio

Recorrido iterativo propio del grafo del estado, con una tabla de identidades
propia (direccionamiento abierto con clave la identidad del objeto) que conserva
referencias compartidas y ciclos. Los campos copiados por tipo son los del
esquema explícito del guardado binario, de modo que «estado completo» significa
lo mismo al guardar y al crear un punto. Los auxiliares derivados (índices de
búsqueda de rutas, posiciones del conocimiento) se reconstruyen igual que al
cargar. `random.Random` se copia mediante su estado, requisito de §3.6 al
re-simular.

| Opción | Medición | Motivo |
| --- | --- | --- |
| **A. Copiador propio (elegida)** | 4–6 ms con 200–300 salas | Única opción medida compatible con 20 ms y 50 ms. |
| B. Serializador binario existente | 43–74 ms por operación | Incumple ambos límites; se mide en el bench como alternativa. |
| C. `copy.deepcopy` | 8–14 ms | Usa internamente un `dict` como índice de identidades: contradice el principio I. |

## D-LT-05 — Órdenes ejecutadas y acciones vigentes — Elegida: dos arreglos

El pergamino deja efectos que no se deshacen (P1: el pergamino consumido no se
restaura y un pergamino recogido no vuelve al suelo). Por eso la historia
vigente no se puede reproducir solo con las acciones que sobrevivieron.

- **Órdenes ejecutadas**: arreglo que solo crece, con cada orden reproducible en
  el orden real, incluidas las revertidas, `retroceder` y la navegación del
  inventario. Es la misma secuencia que registra `partida.log`.
- **Acciones vigentes**: arreglo k → (instante de decisión, posición de su orden).
  El pergamino trunca el final.
- Se crea un punto cada K órdenes ejecutadas que son acciones del jugador (las
  revertidas también cuentan). Entre dos puntos hay exactamente K acciones
  ejecutadas, así que ninguna consulta re-simula más de K, aunque haya
  pergaminos de por medio. Los puntos nunca se invalidan: un punto creado antes
  de un pergamino, seguido de sus órdenes posteriores (incluido `retroceder`),
  reproduce exactamente la historia vigente.

Alternativa descartada: un solo arreglo y un punto nuevo tras cada pergamino.
Ese punto puede quedar a menos de K acciones del anterior y cuesta una copia
por pergamino.

## D-LT-06 — Persistencia — Elegida: guardar todos los puntos

El archivo (formato versión 6) incluye las órdenes, las acciones vigentes, los
tramos de K y cada punto, codificados con el esquema binario existente. Al
cargar, la línea queda idéntica sin re-simular. El tamaño y el tiempo de
guardado crecen con los puntos (≈40–60 ms y ≈100–150 KB por punto con 200–300
salas, según la medición del serializador). Guardar es una orden manual sin
límite de tiempo en el enunciado. Los formatos anteriores se rechazan
(FR-LT-016).

Alternativas: guardar solo el punto inicial y regenerar al cargar (carga
proporcional a toda la partida, ≈5 s con 5 000 acciones y decenas de
cazadores); persistir uno de cada m puntos (un parámetro más y dos caminos que
probar).

## D-LT-07 — K por defecto — Pendiente de medición

Consultas medidas el 2026-11-11: con 5 000 acciones, 200 salas sintéticas y
32 cazadores, K = 25 dio 6/36 consultas ≥50 ms (máximo 63,502 ms). K = 10 dio
0/36 (máximo 44,587 ms); K = 50 y 100 dieron 19/36 y 23/36. Solo el inicial
dio máximo 3 121,560 ms. Los resúmenes son equivalentes y las consultas no
alteraron el estado. En `cripta-06` (300 salas, `f9ed9afa683d`), con 32 cazadores
activos iniciales, 5 000 acciones y K = 25, hubo 27/36 consultas ≥50 ms,
máximo 195,992 ms: PR-LT-001 no se cumple en esta carga. No se extrapola el
resultado sintético de K = 10 a la referencia. Faltan memoria, creación de
puntos/ciclo y la elección del usuario; K permanece provisional. Evidencia y
método en el [Documento de Decisiones](../../documentacion/DOCUMENTO_DECISIONES.md),
[JSON sintético](../../documentacion/evidencia/mediciones_consultas_juan.json) y
[JSON de referencia](../../documentacion/evidencia/mediciones_consultas_referencia_juan.json).

Evidencia parcial de Juan, 2026-11-11: tres rondas por K, 5 000 acciones
vigentes y 200 salas, costos variables/pergamino, sin cazadores. Guardar todos
los puntos produjo 62,60 MB y carga máxima 25,484 s con K = 10; 25,34 MB y
11,207 s con K = 25; 12,93 MB y 4,771 s con K = 50; 6,72 MB y 3,092 s con
K = 100. El copiador propio tardó 12,222–19,629 ms por estado base frente a
64,913–84,473 ms de ida y vuelta binaria. Son mediciones finales de este tramo,
distintas de las exploraciones anteriores: no certifican el ciclo con cazadores,
las consultas ni la memoria total. Se mantienen D-LT-04/06; D-LT-07 sigue
pendiente. Muestras, entorno y alcance en
[mediciones_persistencia_juan.json](../../documentacion/evidencia/mediciones_persistencia_juan.json)
y análisis en el [Documento de Decisiones](../../documentacion/DOCUMENTO_DECISIONES.md).

Candidatos que medirá `--bench`: K = 10, 25, 50 y 100, además de la alternativa
sin puntos de control (re-simular desde el inicio). Los criterios son el tiempo
máximo de consulta < 50 ms con ≥ 5 000 acciones (PR-LT-001), la memoria total
(PR-LT-003) y el costo de crear un punto dentro del ciclo. Estimación previa
con 300 salas: 5 000 / K puntos × ≈343 KiB, es decir ≈170 MB con K = 10 y
≈17 MB con K = 100. El usuario elegirá el valor con esos datos.

## Otras decisiones de diseño, sin estructura nueva

- **Instante dentro de un intervalo**: la re-simulación de la última acción
  admite un límite de tiempo: se procesan los eventos con tiempo ≤ t y el reloj
  mostrado es t. Solo se usa en copias; la partida real no cambia.
- **`--replay … --hasta t`**: reproduce el log completo registrando la misma
  línea de tiempo y luego consulta t con la misma rutina que `historia`, para
  que ambos resultados sean idénticos por construcción (SC-LT-002).
- **Re-simulación sin red**: el contenido de las salas ya descargado sigue en
  memoria del servicio y las fichas en la caché persistente. Un preparador de
  salas de solo lectura los usa sin pedir datos, sin precarga y sin alterar la
  caché viva. Si faltara un dato, la consulta falla con mensaje y no se consume
  presupuesto.
- **Tipo de orden**: se deduce al registrar comparando el contador de acciones
  antes y después (+1 acción; −1 pergamino; 0 navegación), sin duplicar reglas.


## Investigación aprobada: compartir metadatos inmutables (2026-11-11)

El usuario elige investigar compartir datos inmutables y copiar el estado
mutable. No equivale a elegir K ni a aprobar un nuevo formato de guardado.
Prototipo aislado: plantilla inmutable de enlaces f?sicos y metadatos de salas,
con tokens por identidad. Cada captura copia el grafo mutable y sus alias,
sustituyendo nodos est?ticos por tokens; reconstruir crea nodos independientes
y resuelve los tokens antes de reconstruir ?ndices. Estado de puertas, rastro,
contenido y conocimiento siguen siendo mutables e independientes. Los campos
supuestamente est?ticos se verifican en cada captura; una modificaci?n invalida
el contexto experimental explícitamente. No compartir objetos mutables vivos.
Se comparar? equivalencia, alias, tiempos y asignaciones antes de integrar en
partidas/replay/persistencia. Mientras tanto producción conserva formato 6 y K.


### Resultado de perfilar el prototipo compartido

Validación directa por identidad/metadatos, tipos precalculados y reserva de
capacidad de la tabla existente seg?n cantidad de nodos. El copiador evita
registrar tuplas que permanecen inmutables; conserva sustituciones y alias.
Ensayo de 500 acciones: restauraci?n mediana 31,795 ms frente a copia normal
39,830 ms. Sin embargo, en historia completa de 5 000 acciones/300 salas/32
cazadores/K=25: normal 16/36 consultas >=50 ms, compartido 17/36. No justifica
integración; sigue experimental, sin cambios de formato ni elección de K.


## D-LT-08: registros inmutables por ID (eleccion 2026-11-12)

El usuario elige extender el prototipo a registros inmutables por ID. Cada
punto conserva valores y referencias numericas en tuplas sin enlaces al grafo
vivo. Se reutilizan esquema explicito, arreglos y tabla de identidades propia;
las referencias compartidas y ciclos se restauran al crear una copia de trabajo.
Captura y consultas deben medirse antes de integrarlo. Se intenta conservar
formato 6 materializando los puntos para el codec existente al guardar y
compactandolos al cargar; si esto exige cambiar el contrato, se revisa antes.
K permanece provisional. No se deshabilita GC ni se excluye del ciclo el registro.

## Caché compartida de rutas: elección 2026-11-12

Tras el perfil oficial, el usuario aprueba investigar/medir una tabla hash propia
acotada para compartir rutas equivalentes entre cazadores. Detalles y garantías
en `001-terreno-cazadores/research.md`. Es derivada y se reconstruye vacía al
copiar/cargar, sin cambiar el formato v6 ni los registros inmutables. Medir
consultas completas contra caché individual, no solo búsquedas aisladas.

## Captura conservando tuplas: elección 2026-11-12

El usuario elige «Conservar las tuplas y optimizar su captura», frente a
empaquetar los registros por ID en bytes. No se implementa empaquetado.
Se conserva D-LT-08 y su codificación: mismas referencias numéricas, orden y
tuplas de campos. Investigar búsquedas redundantes de esquema, llamadas y
contenedores temporales; comparar ABBA contra la revisión anterior sobre el
mismo estado y comprobar igualdad de registros y bytes v6. Medir ciclos con
GC habilitado y puntos incluidos, sin dar por cumplido un límite por la mediana.

## Catálogo acotado de tuplas de ID: elección 2026-11-12

El usuario elige compartir las tuplas de ID con un catálogo acotado, frente a
mantener tokens propios y optimizar solo recorridos. Se conserva D-LT-08: cada
ID sigue refiriéndose exclusivamente a los registros de su punto.

Catálogo estático e inmutable de 16 384 tokens `(ID,)`, indexado mediante arreglo
de tuplas, compartido entre capturas. Se construye al importar el módulo y no
crece ni guarda modelos. IDs superiores crean un token propio como antes.
La capacidad es un parámetro inicial de implementación, distinto de K. El
catálogo inmutable permite capturas simultáneas sin mutaciones compartidas.

Verificar independencia entre puntos/capturas concurrentes, alias/ciclos, límite
y fallback, liberación de modelos y bytes v6. Comparar contra ed4b505, separando
memoria marginal de cada punto del costo fijo del catálogo; después medir
historias completas, consultas oficiales y RSS antes de declarar aceptación.

## Registros completos iguales: elección 2026-11-13

El usuario elige reutilizar también registros completos iguales. La captura
acepta un punto anterior opcional y compara código y datos completos en el
mismo ID. Solo reutiliza la tupla si es igual; conserva un arreglo propio de
registros y resuelve cada ID en el contexto del punto actual. No añade índice
ni referencia al punto anterior. Primer punto y captura genérica funcionan sin
antecesor. La línea proporciona su último punto y la carga aplica el mismo
criterio entre puntos decodificados, manteniendo v6.

Verificar registros cambiados, cambios de tamaño/IDs, alias/ciclos, liberación
del antecesor, independencia y mismos bytes. Medir memoria marginal sin
confundirla con memoria total, y comparar historias completas contra 537db26.


## Ruta incremental versionada: eleccion 2026-11-13

El usuario elige investigar y especificar captura incremental con indices propios.
Los indices concretos siguen pendientes: hash propio con vector inmutable de
casillas (recomendado para el piloto) o hash de cambios con AVL persistente.
No confundir esta eleccion de ruta con aprobacion de una estructura particular.
Auditoria, costos y criterios de salida en incremental.md; FR-CI/PR-CI en spec.md.
No hay implementacion ni cambios a produccion, K o formato v6.
