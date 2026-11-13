# Especificación: Línea de tiempo y puntos de control

**Rama Git**: `main` (actual; no se crea otra rama).
**Creación**: 2026-11-09.
**Estado**: funcionalidad implementada y probada; cierre de rendimiento y elección de K pendientes.
**Entrada del usuario**: «Línea de tiempo de Cripta Parte II (P2 §3.6, §5.5, §6.1,
§6.3, §7.3 y apéndice B, casos de línea de tiempo). Consultar sin modificar la
partida el estado en cualquier instante desde el inicio: comandos historia <t> e
historia #k, consulta sin interacción --replay partida.log --hasta <t>, puntos de
control limitados a uno cada K acciones con --checkpoint-cada K, interacción con
el pergamino de retroceso, persistencia en el guardado e incompatibilidad con
archivos anteriores, límite de 50 ms por consulta con al menos 5 000 acciones y
mediciones con al menos tres valores de K y sin puntos de control. Sin elegir
estructuras de datos.»

**Fuentes**: [Cripta — Parte II](../../Cripta%20-%20Parte%20II.pdf),
§§2.2–2.6, 3.3, 3.6, 5.5, 5.6, 6.1–6.3, 7.2–7.3 y apéndice B (línea de tiempo);
constitución y documentación heredada. Esta etapa describe comportamiento y
evidencia exigida; no elige estructuras, clases, módulos ni algoritmos, ni decide
si la reconstrucción será hacia adelante o hacia atrás.

## Escenarios de usuario y aceptación

Identificadores estables propios: FR-LT, PR-LT, AC-LT y SC-LT. Los ejemplos usan
criptas y partidas sintéticas de aceptación, no datos oficiales incorporados al
programa.

**Vocabulario**:

- **Instante t**: valor entero del reloj virtual, desde 0.
- **Estado en t**: el estado después de ejecutar todos los eventos con tiempo
  menor o igual que t; si a t le corresponde una decisión del jugador, el estado
  justo antes de tomarla (§3.6).
- **Acción número k**: la k-ésima acción del jugador de la historia vigente,
  contada desde 1. Las consultas y el uso del pergamino no son acciones numeradas.
- **Historia vigente**: la partida tal como quedó tras los pergaminos usados; las
  acciones revertidas no forman parte de ella.
- **Resumen histórico**: reloj, sala del jugador, vida y estadísticas,
  inventario, efectos activos, enemigos vivos de esa sala con su vida y mapa
  conocido en ese momento (§3.6).

### Historia 1 — Consultar un instante pasado durante la partida (Prioridad: P1)

Como jugador, quiero ver cómo estaba la partida en un instante anterior o antes
de una acción concreta, sin que esa consulta cambie mi partida.

**Motivo**: Permite revisar decisiones pasadas y depurar comportamientos.
**Prueba independiente**: Jugar una secuencia conocida, consultar instantes y
números de acción, y comparar el resumen con el estado registrado en ese momento
y con el estado actual antes y después de consultar.

**Escenarios de aceptación**:

1. **AC-LT-001** — **Dada** una partida con varias acciones, **cuando** se pide
   `historia <t>` con t entre 0 y el reloj actual, **entonces** se muestra el
   resumen histórico completo del estado en t, idéntico al que existía en ese
   instante. Requisitos: FR-LT-001/002/003.
2. **AC-LT-002** — **Dada** una partida con N acciones vigentes, **cuando** se pide
   `historia #k` con 1 ≤ k ≤ N, **entonces** se muestra el estado justo antes de
   la acción número k. Con k = N + 1 se muestra el estado actual, justo antes de
   la decisión pendiente. Requisitos: FR-LT-001/002/004.
3. **AC-LT-003** — **Dado** un instante t en el que el jugador debe decidir,
   **cuando** se pide `historia <t>`, **entonces** se muestra el estado justo antes
   de esa decisión, no después de ejecutarla. Requisitos: FR-LT-002/003.
4. **AC-LT-004** — **Dados** varios eventos programados en el mismo instante t,
   **cuando** se pide `historia <t>`, **entonces** el resumen refleja el estado
   después de todos ellos. Requisitos: FR-LT-003. Apéndice B, línea de tiempo,
   caso 3.
5. **AC-LT-005** — **Dado** un instante t entre dos decisiones del jugador en el que
   actúan enemigos o expiran efectos, **cuando** se consulta t, **entonces** el
   resumen incluye esos cambios con tiempo menor o igual que t y ninguno posterior.
   Requisitos: FR-LT-003.
6. **AC-LT-006** — **Dado** un momento con salas exploradas, avistadas y puertas
   recordadas distintas de las actuales, **cuando** se consulta, **entonces** el
   mapa conocido mostrado es el del jugador en ese momento, derivado solo de su
   conocimiento de entonces, sin revelar salas exploradas después.
   Requisitos: FR-LT-002/005.

### Historia 2 — Consultar sin alterar nada (Prioridad: P1)

Como jugador, quiero que consultar la historia sea gratuito y no deje rastro en
la partida, el log ni el pergamino.

**Motivo**: Una consulta que cambia el juego rompería determinismo y replay.
**Prueba independiente**: Comparar reloj, estado, historial de retroceso,
`partida.log` y azar antes y después de consultas repetidas.

**Escenarios de aceptación**:

1. **AC-LT-007** — **Dada** una partida en curso, **cuando** se ejecuta `historia`
   una o varias veces, **entonces** no avanza el reloj virtual, no se registra en
   `partida.log`, no cambia el historial de retroceso ni consume el azar, y la
   partida continúa igual que sin consultar. Requisitos: FR-LT-006.
   Apéndice B, línea de tiempo, caso 4.
2. **AC-LT-008** — **Dado** `historia <t>` con t mayor que el reloj actual,
   **cuando** se pide, **entonces** se rechaza con un mensaje y no se altera nada.
   Requisitos: FR-LT-006/007. Apéndice B, línea de tiempo, caso 1.
3. **AC-LT-009** — **Dadas** consultas mal formadas (t negativo o no entero, k menor
   que 1, k mayor que N + 1, o ausencia de argumento), **cuando** se piden,
   **entonces** se rechazan con explicación del uso, sin efectos.
   Requisitos: FR-LT-006/007.
4. **AC-LT-010** — **Dado** un viaje «ir a» interrumpido por escribir `historia`,
   **cuando** se consulta, **entonces** el viaje se detiene como ante cualquier
   otra orden, la consulta no consume tiempo y el siguiente paso solo ocurre si el
   jugador lo pide de nuevo. Requisitos: FR-LT-006.

### Historia 3 — Línea de tiempo coherente con el pergamino (Prioridad: P1)

Como jugador, quiero que la línea de tiempo describa la partida tal como quedó
después de usar un pergamino de retroceso.

**Motivo**: Las acciones deshechas ya no ocurrieron; mostrarlas sería falso.
**Prueba independiente**: Jugar, consultar, retroceder con pergamino y repetir
las consultas sobre los mismos instantes y números de acción.

**Escenarios de aceptación**:

1. **AC-LT-011** — **Dadas** acciones revertidas con un pergamino, **cuando** se
   consulta la historia, **entonces** no se muestra ningún estado producido por
   ellas, y consultar un instante posterior al reloj restaurado se rechaza.
   Requisitos: FR-LT-008/007. Apéndice B, línea de tiempo, caso 2.
2. **AC-LT-012** — **Dado** un pergamino seguido de nuevas acciones distintas,
   **cuando** se consultan instantes y números de acción posteriores al punto
   restaurado, **entonces** se muestran los estados de las acciones nuevas y la
   numeración k continúa desde las acciones vigentes; el uso del pergamino no
   ocupa un número k. Requisitos: FR-LT-004/008.
3. **AC-LT-013** — **Dado** el uso de un pergamino en una partida larga,
   **cuando** se recorta la línea de tiempo, **entonces** el trabajo no depende de
   la longitud total de la historia anterior al punto restaurado.
   Requisitos: FR-LT-008, PR-LT-004.
4. **AC-LT-014** — **Dado** que el pergamino sigue limitado a cinco acciones,
   **cuando** se consulta un instante anterior a esas cinco, **entonces** la
   consulta funciona igual; la línea de tiempo no amplía el alcance del pergamino
   ni el pergamino limita el de la consulta. Requisitos: FR-LT-001/009.

### Historia 4 — Reproducir hasta un instante sin interfaz (Prioridad: P1)

Como desarrollador o evaluador, quiero reproducir un `partida.log` hasta un
instante y obtener el mismo resumen sin abrir la interfaz.

**Motivo**: Permite comprobar estados pasados de forma automatizada.
**Prueba independiente**: Grabar una partida, reproducirla con `--hasta` para
varios t y comparar con `historia <t>` durante la partida original.

**Escenarios de aceptación**:

1. **AC-LT-015** — **Dado** un `partida.log` válido, **cuando** se ejecuta
   `--replay partida.log --hasta <t>` con t dentro de la partida, **entonces** se
   imprime el mismo resumen histórico que `historia <t>` en la partida original,
   sin instanciar la vista. Requisitos: FR-LT-010/002.
2. **AC-LT-016** — **Dado** t posterior al final de la partida reproducida,
   **cuando** se ejecuta `--replay … --hasta <t>`, **entonces** se muestra el estado
   final e indica que la partida terminó antes de t. Requisitos: FR-LT-010.
   Apéndice B, línea de tiempo, caso 5.
3. **AC-LT-017** — **Dado** un log que incluye usos de pergamino, **cuando** se
   reproduce hasta t, **entonces** el resumen corresponde a la historia vigente
   después de esos pergaminos. Requisitos: FR-LT-008/010.
4. **AC-LT-018** — **Dado** `--hasta` sin `--replay`, con t inválido o combinado
   con modos incompatibles, **cuando** se ejecuta, **entonces** se rechaza con error
   de uso y explicación, sin iniciar juego ni reproducción. Requisitos: FR-LT-011.

### Historia 5 — Configurar los puntos de control (Prioridad: P2)

Como usuario, quiero fijar cada cuántas acciones se permite guardar una copia
completa del estado, y que el valor por defecto esté justificado.

**Motivo**: El intervalo equilibra memoria y tiempo de consulta (§5.5).
**Prueba independiente**: Ejecutar la misma partida con varios K y comprobar el
máximo de copias completas, el trabajo por consulta y que el resultado no cambia.

**Escenarios de aceptación**:

1. **AC-LT-019** — **Dado** `--checkpoint-cada K` con K entero positivo, **cuando**
   se juega, **entonces** no se guarda más de una copia completa del estado cada K
   acciones del jugador. Requisitos: FR-LT-012/013.
2. **AC-LT-020** — **Dado** cualquier instante consultable y cualquier K válido,
   **cuando** se consulta, **entonces** la consulta no aplica ni deshace cambios de
   más de K acciones del jugador. Requisitos: FR-LT-013, PR-LT-002.
3. **AC-LT-021** — **Dadas** la misma cripta, semilla y acciones con valores
   distintos de K, **cuando** se consultan los mismos instantes, **entonces** los
   resúmenes son idénticos; K solo cambia memoria y tiempo. Requisitos:
   FR-LT-014.
4. **AC-LT-022** — **Dado** K no entero, cero o negativo, **cuando** se ejecuta,
   **entonces** se rechaza con error de uso. Sin la opción se usa el valor por
   defecto documentado. Requisitos: FR-LT-012.

### Historia 6 — Guardar y cargar conservando la historia (Prioridad: P1)

Como jugador, quiero guardar y reanudar sin perder la línea de tiempo, y que un
archivo antiguo no se cargue como si fuera válido.

**Motivo**: §3.6 exige persistir la línea completa y §3.3 el conocimiento.
**Prueba independiente**: Guardar tras varias acciones, cargar en otra ejecución y
comparar consultas históricas antes y después; intentar cargar archivos antiguos.

**Escenarios de aceptación**:

1. **AC-LT-023** — **Dada** una partida guardada con historia, **cuando** se carga,
   **entonces** `historia <t>` e `historia #k` devuelven los mismos resúmenes que
   antes de guardar para todos los instantes desde 0, y la partida continúa
   registrando historia. Requisitos: FR-LT-015.
2. **AC-LT-024** — **Dado** un archivo de partida de la primera parte o de una
   versión anterior de formato, **cuando** se intenta cargar, **entonces** se
   informa la incompatibilidad de formato y no se carga; no se migra.
   Requisitos: FR-LT-016.
   Apéndice B, línea de tiempo, caso 6.
3. **AC-LT-025** — **Dada** una partida guardada con un K, **cuando** se carga con
   `--checkpoint-cada` distinto, **entonces** la historia guardada conserva sus
   puntos de control y el nuevo K rige desde la carga. Cada tramo respeta «no más
   de una copia cada K acciones» con su propio K, y una consulta no aplica ni
   deshace cambios de más acciones que el K del tramo consultado. Sin la opción
   al cargar se conserva el K guardado. Requisitos: FR-LT-012/013/015.

### Casos límite

- `historia 0` y `historia #1` muestran el estado inicial, con la sala inicial
  explorada desde el instante 0 (§3.3).
- t igual al reloj actual muestra el estado actual, antes de la decisión pendiente.
- Un t sin evento propio muestra el último estado con tiempo menor o igual que t.
- Una partida sin acciones admite `historia 0` y `historia #1`; rechaza `#2`.
- Si un instante incluye la muerte de enemigos, la caída de trampas o el cierre
  automático de puertas, el resumen refleja esos cambios solo si su tiempo es
  menor o igual que t.
- La consulta muestra el mapa conocido de entonces aunque la memoria de una puerta
  difiera del estado real de ese momento (§3.3).
- La línea de tiempo se reconstruye igual con una partida jugada en vivo, una
  cargada y una reproducida desde log.
- Un pergamino consumido no aparece en el inventario de instantes anteriores a su
  uso solo porque la historia posterior fue revertida; el estado de cada instante
  vigente es el que existió en la historia vigente.

## Requisitos

### Requisitos funcionales

- **FR-LT-001**: Ofrecer en la partida las órdenes `historia <t>` e `historia #k`
  para consultar cualquier instante de la historia vigente, desde 0 hasta el
  reloj actual. Escenarios: AC-LT-001/002/014.
- **FR-LT-002**: Mostrar como mínimo el resumen histórico: reloj, sala del jugador,
  vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su
  vida y mapa conocido en ese momento. Se muestran todos los enemigos vivos de la
  sala en ese instante, activos o dormidos, con vida actual y máxima, indicando
  los dormidos y distinguiendo a los cazadores como en la vista normal.
  Escenarios: AC-LT-001/002/003/006/015.
- **FR-LT-003**: El estado en t es el resultado de todos los eventos con tiempo
  menor o igual que t; si a t le corresponde una decisión del jugador, es el
  estado justo antes de tomarla. Escenarios: AC-LT-001/003/004/005.
- **FR-LT-004**: `historia #k` muestra el estado justo antes de la acción número k
  de la historia vigente; k = N + 1 equivale al estado actual. El uso del
  pergamino no es una acción numerada: k cuenta solo las acciones vigentes.
  Escenarios: AC-LT-002/012.
- **FR-LT-005**: El mapa conocido histórico se deriva solo del conocimiento del
  jugador en ese instante, con estados de salas y memoria de puertas de entonces.
  Escenario: AC-LT-006.
- **FR-LT-006**: Una consulta no consume tiempo virtual, no es acción, no se
  registra en `partida.log`, no consume azar y no altera estado del juego ni
  historial de retroceso. Escenarios: AC-LT-007/008/009/010.
- **FR-LT-007**: Rechazar con mensaje y sin efectos los instantes posteriores al
  reloj actual y los argumentos inválidos. Escenarios: AC-LT-008/009/011.
- **FR-LT-008**: Al usar un pergamino, las acciones revertidas y todo estado
  posterior al reloj restaurado dejan de existir en la línea de tiempo, tanto en
  vivo como en replay. Escenarios: AC-LT-011/012/013/017.
- **FR-LT-009**: El pergamino conserva su límite de cinco acciones; la línea de
  tiempo es independiente y no modifica ese límite. Escenario: AC-LT-014.
- **FR-LT-010**: `--replay partida.log --hasta <t>` reproduce sin vista hasta t e
  imprime el mismo resumen; si t es posterior al final, muestra el estado final e
  indica que la partida terminó antes. Escenarios: AC-LT-015/016/017.
- **FR-LT-011**: Rechazar con error de uso `--hasta` sin `--replay`, con t no
  entero o negativo, o combinado con modos incompatibles. Escenario: AC-LT-018.
- **FR-LT-012**: `--checkpoint-cada K` acepta un entero positivo; sin la opción se
  usa un valor por defecto escogido por el equipo y justificado con mediciones.
  Escenarios: AC-LT-019/022/025.
- **FR-LT-013**: No guardar más de una copia completa del estado cada K acciones
  del jugador; fuera de ellas solo se almacena lo necesario para reconstruir
  cambios. Ninguna consulta aplica o deshace cambios de más de K acciones.
  Si la reconstrucción re-simula, la copia incluye el estado del generador de
  azar. Para estos límites, «acciones del jugador» son las acciones ejecutadas,
  incluidas las que luego revierte un pergamino; el uso del pergamino no cuenta
  como acción. Escenarios: AC-LT-019/020.
- **FR-LT-014**: Los resúmenes no dependen de K, de haber cargado la partida ni de
  reconstruir desde log: misma cripta, semilla y acciones dan el mismo resultado.
  Escenarios: AC-LT-021/023.
- **FR-LT-015**: Guardar y cargar conserva la línea de tiempo completa y permite
  seguir registrándola. El K guardado acompaña a la partida; un
  `--checkpoint-cada` distinto al cargar rige desde la carga sin alterar los
  puntos de control previos. Escenarios: AC-LT-023/025.
- **FR-LT-016**: Un archivo de partida de la primera parte o de un formato
  anterior se rechaza informando la incompatibilidad de formato; no se migra ni
  se carga en silencio. Escenario: AC-LT-024.

### Requisitos de rendimiento

- **PR-LT-001**: Cada consulta `historia` tarda menos de 50 ms en el equipo local,
  sin red ni renderizado, en una partida de al menos 5 000 acciones del jugador
  con el K por defecto (§6.1).
- **PR-LT-002**: Ninguna consulta aplica o deshace cambios de más de K acciones;
  ubicar el punto de control más cercano no debe recorrer toda la historia (§5.5).
- **PR-LT-003**: La memoria total crece con la cantidad de cambios ocurridos más
  una copia completa cada K acciones; nunca con «acciones por tamaño del estado».
- **PR-LT-004**: Recortar la línea al usar un pergamino no recorre toda la historia.
- **PR-LT-005**: `--bench` mide memoria y tiempo de consulta para al menos tres
  valores de K y la alternativa sin puntos de control, con partidas sintéticas
  deterministas por semilla, y respalda el K por defecto (§§5.5, 6.3). El comando
  estándar incluye estas comparaciones sin requerir una bandera adicional.
- **PR-LT-006**: `--bench` documenta con evidencia si se reconstruye hacia adelante
  o hacia atrás (§5.5).
- **PR-LT-007**: Registrar la historia no hace superar el límite de 20 ms por ciclo
  de eventos con decenas de cazadores; se repiten las mediciones de agenda de
  eventos e historial de retroceso de P1 con la carga nueva y se documenta si
  alguna decisión cambia (§§5.6, 6.1).
- **PR-LT-008**: La ejecución estándar de mediciones conserva parámetros,
  entorno y resultados nuevos en una carpeta de salida configurable. Por defecto
  no sobrescribe la evidencia versionada de la entrega. Si una medición o su
  exportación falla, informa el error y termina con código distinto de cero.
  No crea vista ni usa red en las cargas sintéticas (§§6.1, 6.3, 7.1).

### Entidades del juego

- **Instante**: valor del reloj virtual consultable.
- **Acción del jugador**: decisión numerada de la historia vigente.
- **Resumen histórico**: información mínima mostrada para un instante.
- **Punto de control**: copia completa del estado permitida como máximo una vez
  cada K acciones.
- **Cambio registrado**: información mínima para reconstruir un estado a partir
  de otro.
- **Historia vigente**: secuencia de acciones y cambios que permanece tras los
  pergaminos usados.

## Criterios de éxito

### Resultados medibles

- **SC-LT-001**: Los 25 escenarios tienen prueba automatizada o registro
  reproducible que cite los requisitos atendidos, incluidos los seis casos de
  línea de tiempo del apéndice B.
- **SC-LT-002**: En una partida de prueba, el resumen de cada instante consultado
  coincide con el estado observado en vivo en ese instante y con el de
  `--replay … --hasta`, para al menos tres valores de K.
- **SC-LT-003**: Tras cualquier número de consultas, reloj, log, historial de
  retroceso y continuación de la partida son idénticos a una ejecución sin
  consultas.
- **SC-LT-004**: Con al menos 5 000 acciones y K por defecto, el 100 % de las
  consultas medidas termina en menos de 50 ms.
- **SC-LT-005**: Las mediciones muestran memoria y tiempo de consulta para al menos
  tres K y sin puntos de control, justifican el K por defecto y repiten las
  mediciones de P1 afectadas.

## Supuestos, dependencias y límites

- Toda acción del jugador avanza el reloj al menos una unidad, por lo que cada
  instante tiene a lo sumo una decisión del jugador.
- `--hasta` acepta solo instantes; la forma `#k` es exclusiva de la orden en partida.
- Al ganar o morir la sesión interactiva termina, como ya ocurre; el estado final
  se consulta con `--replay … --hasta`.
- El resumen reutiliza la presentación existente del estado y de `ver mapa`; el
  formato exacto se precisará en el plan sin cambiar su contenido mínimo.
- El valor por defecto de K y la dirección de reconstrucción son decisiones de
  diseño que el usuario tomará en el plan con evidencia.
- Las consultas no exigen solicitudes de red y no afectan `presupuesto_solicitudes`.
- Sigue faltando el enunciado original de P1 para contrastar íntegramente sus reglas.
- Esta especificación no implementa funcionalidades ni sustituye plan o tareas.
  Todas las decisiones de estructuras pertenecen al usuario.

## Ampliación: captura incremental versionada (2026-11-13)

Ruta de investigación elegida por el usuario; hash propio con vector inmutable
elegido para el piloto. Conserva el contenido de historia, las reglas, K y los presupuestos.

- **FR-CI-001**: Captura inicial completa; después representar todos los cambios
  sin inspeccionar atributos de todas las entidades inalteradas en cada punto.
- **FR-CI-002**: Identificadores preservan alias/ciclos y tienen política explícita
  de altas, bajas y reutilización de direcciones. `id(obj)` aislado no basta.
  Cada versión interpreta sus propios registros y permanece inmutable.
- **FR-CI-003**: Cubrir atributos, listas/dict, heap/secuencias, enlaces, inventario,
  cursor/equipo, suelo/botín, conocimiento, carga diferida y azar. También las
  órdenes que cambian estado sin avanzar reloj o contador de acciones.
- **FR-CI-004**: Seguimiento independiente de la ventana de cinco acciones de undo;
  no perder cambios cuando K es mayor. Deshacer registra restauraciones y respeta
  el consumo del pergamino fuera del historial reversible.
- **FR-CI-005**: Registrar objetos nuevos y referencias antes de publicar, incluidos
  nacimientos/bajas entre puntos. Definir retirada y límites de memoria de índices
  sin retener modelos originales innecesariamente.
- **FR-CI-006**: Publicación atómica: un fallo no publica una versión parcial ni
  descarta cambios pendientes. Una mutación no soportada se detecta; no produce
  silenciosamente una versión obsoleta o una consulta con más de K acciones.
- **FR-CI-007**: Materialización independiente conserva tipos y bits de float y
  permite reproducir a lo sumo K acciones. No depende de una cadena creciente
  de puntos ni de reproducir desde el inicio.
- **FR-CI-008**: Intentar conservar v6 materializando al guardar y reconstruyendo
  el capturador al cargar, incluso con cambio de K. Si no es viable, revisar
  el contrato antes de cambiar la versión de archivo.
- **FR-CI-009**: Oráculo contra captura completa después de cada orden, undo y
  carga en trazas pequeñas: modelo persistible/bytes normalizados y continuación,
  no solamente el resumen visible.
- **PR-CI-001**: Medir registro de cambios, publicación, crecimiento/bajas,
  mantenimiento y fallback, con GC habilitado y todos los picos incluidos.
  Informar inicio completo aparte; no desplazar costo fuera del cronómetro.
- **PR-CI-002**: Con 5 000 acciones informar entidades visitadas/campos leídos,
  cambios pendientes, memoria fija/marginal/RSS y consulta para tres K y solo
  inicial. No certificar 20/50 ms con instrumentación o solo por la mediana.

El piloto no reemplaza producción hasta demostrar equivalencia y reducción
real de trabajo/costo. Si pierde estado, crece sin control o desplaza el costo,
se descarta o revisa. El diseño y el piloto están en [incremental.md](incremental.md).

## Aclaraciones

### Elección del grupo, 2026-11-13

- **P**: ¿Qué valor por defecto elegir tras comparar consultas, memoria y ciclos?
  → **R de Juan**: K=10, por equilibrio de consultas medidas y memoria. Aplicado
  a FR-LT-012/PR-LT-005. No altera el K guardado al cargar sin opción explícita
  ni equivale a certificar PR-LT-001/007 antes de la validación final.

### Sesión del 2026-11-09 (especificación)

- **P**: Si una partida guardada con un K se carga con `--checkpoint-cada`
  distinto, ¿qué ocurre? → **R**: A, la historia guardada conserva sus puntos de
  control y el nuevo K rige desde la carga; cada tramo cumple el límite con su
  propio K. Sin la opción se conserva el K guardado. Aplicado a AC-LT-025 y
  FR-LT-015.

### Sesión del 2026-11-09 (aclaración)

- **P**: ¿Usar un pergamino cuenta como acción numerada para `historia #k`? →
  **R**: A, no cuenta; k numera solo las acciones vigentes. Aplicado al
  vocabulario, FR-LT-004 y AC-LT-012.
- **P**: ¿Qué pasa al cargar un archivo de la primera parte o de un formato
  anterior? → **R**: A, se rechaza explicando la incompatibilidad; no se migra.
  Aplicado a FR-LT-016 y AC-LT-024.
- **P**: ¿Qué enemigos de la sala muestra el resumen de `historia`? → **R**: A,
  todos los vivos, activos o dormidos, con vida y estado, marcando cazadores.
  Aplicado al vocabulario y FR-LT-002.
- **P**: ¿Qué acciones cuentan para «una copia cada K acciones» y para el límite
  de K acciones por consulta? → **R**: Las acciones ejecutadas, incluidas las
  revertidas después por un pergamino; el uso del pergamino no cuenta.
  Interpretación del equipo aprobada tras `/speckit-analyze`. Aplicado a FR-LT-013.
