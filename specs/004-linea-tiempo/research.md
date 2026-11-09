# Investigación: Línea de tiempo y puntos de control

**Fecha**: 2026-11-09. **Especificación**: [spec.md](spec.md).
**Estado**: decisiones D-LT-01 a D-LT-06 elegidas explícitamente por el usuario
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
