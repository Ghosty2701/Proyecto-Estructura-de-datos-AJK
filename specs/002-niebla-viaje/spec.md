# Especificación: Niebla de guerra y viaje «ir a»

**Rama**: `main` (actual; sin rama nueva).
**Creación**: 2026-11-09.
**Estado**: Aclaración completada; preparada para planificación.
**Entrada**: «Continemos con la niebla».

**Fuentes**: [Enunciado P2](../../Cripta%20-%20Parte%20II.pdf), §§2.2–2.6,
3.1–3.4, 3.6, 5.3, 6.1–6.3, 7.3 y apéndice B; constitución, README y
documentación heredada. Niebla e «ir a» forman una capacidad según §2.2.

## Escenarios de usuario y aceptación

Los identificadores FR-NV, PR-NV, AC-NV y SC-NV son estables y exclusivos de esta
capacidad. Los ejemplos son sintéticos; no representan datos incorporados al
programa de una cripta concreta.

### Historia 1 — Conocer lo explorado (Prioridad: P1)

Como jugador, quiero distinguir lo explorado de lo avistado y recordar mis
observaciones, para orientarme sin recibir información de lugares desconocidos.

**Motivo**: Define la información permitida en pantalla y durante el viaje.
**Prueba independiente**: Comparar el mapa al iniciar, entrar a salas y observar
puertas; contrastarlo con cambios remotos y precarga de contenido.

**Escenarios de aceptación**:

1. **AC-NV-001** — **Dado** el inicio en A, conectada a B, con C fuera de las
   salidas de A, **cuando** el reloj es 0 y se ejecuta `ver mapa`, **entonces** A está
   explorada, B avistada y C desconocida; solo A revela nombre, salidas, costos
   y puertas observadas. Requisitos: FR-NV-001, FR-NV-002, FR-NV-004.
2. **AC-NV-002** — **Dada** B avistada, **cuando** se entra por primera vez,
   **entonces** queda explorada y sus destinos aún no explorados quedan avistados;
   volver no elimina conocimiento previo. Requisitos: FR-NV-001, FR-NV-002.
3. **AC-NV-003** — **Dados** el esqueleto completo y contenido precargado de salas
   no exploradas, **cuando** se presenta información al jugador, **entonces** la
   precarga no revela nombres, conexiones, costos, contenido ni cambios remotos
   que su conocimiento no permite. Requisitos: FR-NV-002, FR-NV-005.
4. **AC-NV-004** — **Dada** una puerta observada abierta, **cuando** se cierra
   lejos del jugador, **entonces** se recuerda abierta hasta una nueva observación;
   al observarla desde cualquiera de sus extremos se recuerda cerrada como la
   misma puerta. Requisitos: FR-NV-003, FR-NV-004.
5. **AC-NV-005** — **Dado** el jugador junto a una puerta, **cuando** esta cambia
   y se muestra el estado, **entonces** el mapa refleja la observación; consultar
   el mapa no consume tiempo ni azar. Requisitos: FR-NV-003, FR-NV-004, FR-NV-015.

### Historia 2 — Explorar con antorcha (Prioridad: P1)

Como jugador, quiero revelar las vecinas al entrar con antorcha, sin que revelarlas
equivalga a entrar físicamente en ellas.

**Motivo**: Amplía la exploración conservando las reglas de activación de P1.
**Prueba independiente**: Entrar junto a puertas abiertas y cerradas con vecinos
que contengan enemigos dormidos y trampas armadas.

**Escenarios de aceptación**:

1. **AC-NV-006** — **Dada** la antorcha encendida al entrar en A con vecinas B y C
   por salidas abierta y cerrada, **cuando** se revela el entorno, **entonces**
   ambas quedan exploradas, se conocen nombres, salidas y costos, y se registra
   el estado de las puertas reveladas según la aclaración del equipo. Sus destinos
   aún no explorados quedan avistados. Requisitos: FR-NV-001, FR-NV-003,
   FR-NV-006. Apéndice B, niebla, caso 4.
2. **AC-NV-007** — **Dada** B explorada solo por antorcha con enemigos dormidos,
   objetos y trampas, **cuando** se revela, **entonces** no se muestra su contenido,
   no se activan sus enemigos ni trampas y no se propaga recursivamente la
   exploración desde B. Requisitos: FR-NV-006, FR-NV-007. Apéndice B, niebla, caso 4.
3. **AC-NV-008** — **Dada** la antorcha apagada al entrar en A, **cuando** se
   actualiza el mapa, **entonces** sus vecinas no pasan a exploradas por esa
   entrada; apagar la antorcha tampoco elimina conocimiento ya obtenido.
   Requisitos: FR-NV-001, FR-NV-006.

### Historia 3 — Viajar por el mapa conocido (Prioridad: P1)

Como jugador, quiero usar `ir a <sala>` para seguir una ruta conocida de costo
mínimo mediante movimientos ordinarios y conocer por qué se detuvo el viaje.

**Motivo**: Automatizar movimientos debe respetar el conocimiento y los riesgos.
**Prueba independiente**: Viajar por rutas de costos conocidos y provocar cierres,
enemigos, daño y falta de ruta entre pasos; revisar reloj y registro de acciones.

**Escenarios de aceptación**:

1. **AC-NV-009** — **Dado** un destino avistado o desconocido, **cuando** se ordena
   `ir a`, **entonces** se rechaza sin movimiento, acción ni tiempo virtual.
   Para un destino explorado único, indicar su ID o su nombre identifica la
   misma sala y aplica las mismas reglas de viaje.
   El nombre debe coincidir completo y distinguir mayúsculas y minúsculas;
   si coincide con varias salas exploradas, se rechaza sin acción ni tiempo
   y se pide indicar el ID, sin seleccionar una de ellas automáticamente.
   Requisito: FR-NV-008. Apéndice B, niebla, caso 1.
2. **AC-NV-010** — **Dadas** rutas conocidas abiertas al destino explorado, una
   de dos pasos de costo 200 y otra de tres de costo 100, **cuando** se calcula
   el paso, **entonces** se elige la de costo total 300, sin usar atajos
   desconocidos ni salas solo avistadas. Requisitos: FR-NV-005, FR-NV-009, FR-NV-010.
3. **AC-NV-011** — **Dadas** rutas mínimas empatadas iniciadas por vecinas 3 y 8,
   **cuando** se decide el paso, **entonces** se elige 3 independientemente del
   orden de enumeración. Requisito: FR-NV-010.
4. **AC-NV-012** — **Dado** un viaje de varios pasos, **cuando** avanza,
   **entonces** cada paso consume `max(1, costo_salida * 100 // velocidad)`,
   ocurren los eventos ordinarios y se recalcula antes de cada paso con el
   conocimiento vigente. Requisitos: FR-NV-011, FR-NV-012.
5. **AC-NV-013** — **Dada** una puerta remota recordada abierta pero realmente
   cerrada, **cuando** se llega a una sala desde la que se observa, **entonces**
   se actualiza el recuerdo y se recalcula: se usa otra ruta conocida si existe;
   si no, se detiene sin tiempo adicional por el cálculo fallido. Requisitos:
   FR-NV-003, FR-NV-009, FR-NV-012, FR-NV-013. Apéndice B, niebla, caso 2.
6. **AC-NV-014** — **Dado** un paso a una sala con enemigos dormidos, **cuando**
   se ejecuta la entrada conforme a P1, **entonces** se activan según P1 y el
   viaje se detiene sin otro paso automático; también se detiene si ya estaban
   activos. Requisitos: FR-NV-007, FR-NV-011, FR-NV-013. Apéndice B, niebla, caso 3.
7. **AC-NV-015** — **Dado** un paso durante el cual se recibe daño de un enemigo,
   trampa u otro efecto, **cuando** termina su procesamiento ordinario,
   **entonces** no comienza otro paso automático, aunque después se recupere
   vida. Requisitos: FR-NV-011, FR-NV-013.
8. **AC-NV-016** — **Dado** que se posee una llave pero no hay ruta conocida
   abierta, **cuando** se solicita o continúa el viaje, **entonces** no abre
   puertas, no consume una acción adicional y explica la falta de ruta.
   Requisitos: FR-NV-009, FR-NV-013.
9. **AC-NV-017** — **Dado** un viaje completado o interrumpido, **cuando** se
   informa su resultado, **entonces** se explica llegada, enemigos, daño o falta
   de ruta según lo ocurrido, sin revelar información desconocida.
   Si el destino es la sala actual, se informa «Ya estás en esa sala» sin
   movimiento, acción ni avance del reloj.
   Requisitos: FR-NV-005, FR-NV-013.
10. **AC-NV-018** — **Dado** un viaje de tres pasos, **cuando** se registra y
    reproduce, **entonces** cada paso figura como movimiento individual en
    `partida.log`, `ir a` figura además como comentario de depuración y la
    reproducción obtiene el mismo estado y conocimiento.
    Requisitos: FR-NV-014, FR-NV-015.

### Historia 4 — Conservar y revertir el conocimiento (Prioridad: P1)

Como jugador, quiero guardar mi conocimiento y que el pergamino restaure el mapa
correspondiente al momento al que retrocedo.

**Motivo**: El conocimiento es estado del juego, no información externa permanente.
**Prueba independiente**: Guardar, cargar y revertir entradas con y sin antorcha,
observaciones de puertas y pasos de viaje.

**Escenarios de aceptación**:

1. **AC-NV-019** — **Dada** una entrada con antorcha que revela varias vecinas,
   **cuando** se revierte mediante pergamino, **entonces** salas y puertas
   recuperan sus estados previos, incluso avistada o desconocida; se conserva lo
   conocido antes de la acción. Requisito: FR-NV-016. Apéndice B, niebla, caso 5.
2. **AC-NV-020** — **Dados** varios pasos automáticos ejecutados, **cuando** se usa
   un pergamino tras interrumpir entre pasos del viaje, **entonces** revierte solo el último paso,
   restaura su conocimiento y el viaje no continúa. Se conservan las excepciones
   de consumo de P1. Requisitos: FR-NV-011, FR-NV-016. Apéndice B, niebla, caso 6.
3. **AC-NV-021** — **Dado** un mapa con los tres estados y un recuerdo de puerta
   distinto de la realidad, **cuando** se guarda y carga, **entonces** se conserva
   ese conocimiento y el historial reversible; la carga no sustituye el recuerdo
   por el mapa completo ni por el estado real remoto.
   Requisitos: FR-NV-003, FR-NV-017.
4. **AC-NV-022** — **Dadas** misma cripta, versiones, semilla y movimientos,
   **cuando** se comparan ejecución manual y replay sin vista, **entonces**
   coinciden el juego y el conocimiento. Requisitos: FR-NV-014, FR-NV-015, FR-NV-017.

### Casos límite

- Una sala explorada por antorcha sin haber sido visitada es un destino explorado,
  pero puede carecer de ruta conocida abierta.
- Una puerta cerrada permite avistar y revelar por antorcha; no permite atravesarla
  mediante `ir a`.
- Revelar por varias salidas no duplica salas ni elimina conocimiento anterior.
- La antorcha revela vecinas; sus salidas pueden avistar otras salas, sin
  explorarlas recursivamente.
- Cambios sucesivos de una puerta remota no actualizan el recuerdo sin observación.
- Muerte o victoria conserva la terminación ordinaria y no permite más pasos.
- El viaje avanza automáticamente sin exigir confirmación después de cada paso;
  el jugador puede interrumpirlo entre pasos para ejecutar `retroceder`.
  No se interrumpe a mitad del procesamiento de una acción.
- Si el destino es la sala actual, se informa «Ya estás en esa sala» sin
  movimiento, acción ni avance del reloj.

## Requisitos

### Requisitos funcionales

- **FR-NV-001**: Clasificar cada sala como explorada, avistada o desconocida según
  §3.3; la inicial está explorada desde 0, y revelar con antorcha cuenta como
  explorar. Escenarios: AC-NV-001/002/006/008.
- **FR-NV-002**: Revelar de exploradas nombre, salidas, costos y puertas recordadas;
  de avistadas solo existencia detrás de una salida; de desconocidas nada.
  Escenarios: AC-NV-001/002/003.
- **FR-NV-003**: Recordar el último estado de puerta observado desde cualquiera de
  sus extremos y conservarlo ante cambios remotos. La antorcha registra el estado
  de puertas reveladas según la aclaración del equipo.
  Escenarios: AC-NV-004/005/006/013/021.
- **FR-NV-004**: Ofrecer el comando `ver mapa` para ver exploradas, sus salidas, costos y
  puertas recordadas, y salas avistadas; consultar no consume tiempo.
  Escenarios: AC-NV-001/004/005.
- **FR-NV-005**: Derivar toda presentación y decisión de `ir a` exclusivamente
  del conocimiento; ni esqueleto descargado ni precarga lo amplían.
  Escenarios: AC-NV-003/010/017.
- **FR-NV-006**: Al entrar con antorcha encendida, explorar todas las vecinas por
  salidas abiertas o cerradas, revelar nombres, salidas, costos y puertas según
  la aclaración; no contenido ni exploración recursiva.
  Escenarios: AC-NV-006/007/008.
- **FR-NV-007**: Revelar con antorcha no activa enemigos ni trampas vecinos;
  entrar físicamente conserva efectos y activación de P1.
  Escenarios: AC-NV-007/014.
- **FR-NV-008**: Admitir `ir a <sala>` a exploradas y rechazar avistadas o
  desconocidas sin acción ni tiempo. El destino puede indicarse por ID o por
  nombre de sala; ambos formatos identifican el mismo destino cuando corresponden
  a una única sala explorada. Los nombres deben coincidir completos y distinguir
  mayúsculas y minúsculas. Si varias exploradas tienen ese nombre, se rechaza
  sin acción ni tiempo y se pide el ID; no se elige una sala automáticamente.
  Escenario: AC-NV-009.
- **FR-NV-009**: Viajar solo por exploradas y salidas recordadas abiertas; no abrir
  puertas aunque se tenga llave; detenerse sin tiempo adicional si no hay ruta.
  Escenarios: AC-NV-010/013/016.
- **FR-NV-010**: Minimizar suma de costos y desempatar el primer paso por menor ID
  de vecina. Escenarios: AC-NV-010/011.
- **FR-NV-011**: Cada paso es una acción ordinaria completa, con costo, velocidad,
  eventos y retroceso ordinarios; no agrupar pasos en una sola acción.
  Escenarios: AC-NV-012/014/015/020.
- **FR-NV-012**: Recalcular antes de cada paso con el conocimiento vigente,
  incorporando las observaciones al llegar. Escenarios: AC-NV-012/013.
- **FR-NV-013**: Detenerse al llegar al destino, entrar con enemigos activos o
  dormidos, recibir daño o perder ruta conocida; explicar el motivo.
  Si el destino coincide con la sala actual, informar «Ya estás en esa sala»
  sin movimiento, acción ni avance del reloj.
  Escenarios: AC-NV-013/014/015/016/017.
- **FR-NV-014**: Registrar pasos como movimientos individuales y la orden como
  comentario de depuración; replay reproduce sin vista.
  Escenarios: AC-NV-018/022.
- **FR-NV-015**: Misma cripta, versiones, semilla y acciones producen mismo estado
  y conocimiento; consultar o presentar el mapa no consume reloj ni azar.
  Escenarios: AC-NV-005/018/022.
- **FR-NV-016**: Revertir el conocimiento junto a su acción, incluidas antorcha
  y observaciones. El viaje avanza automáticamente y permite interrumpir entre
  pasos para ejecutar `retroceder`, que revierte solo el último paso y no continúa.
  No se exige confirmación por paso ni se interrumpe una acción en curso. Conservar
  límite de cinco acciones y excepciones de pergamino de P1.
  Escenarios: AC-NV-019/020.
- **FR-NV-017**: Guardar/cargar conserva conocimiento e historial reversible.
  El conocimiento se conserva como estado para futura reconstrucción histórica,
  sin implementar todavía `historia`. Escenarios: AC-NV-021/022; la integración
  histórica se verificará en su capacidad.

### Requisitos de rendimiento

- **PR-NV-001**: Calcular un paso de `ir a` en menos de 5 ms en el equipo local,
  con mapa conocido completo de la cripta de referencia, sin red ni renderizado
  (§6.1). Distinguir este cálculo de la simulación de la acción.
- **PR-NV-002**: Explorar debe costar proporcionalmente a las salas reveladas y
  sus salidas, sin recorrer todo el mapa conocido por cada revelación. Registrar
  e invertir conocimiento atiende a cambios de la acción (§5.3 y retroceso P1).
- **PR-NV-003**: `--bench` mide consultas de estados de sala y puertas,
  actualizaciones de exploración y cálculo de `ir a`, con cargas reproducibles
  por semilla y excluyendo red y renderizado (§§5.3, 6.3). Permite contrastar
  PR-NV-001/002; no se declara cumplimiento antes de medir.

### Entidades del juego

- **Conocimiento de sala**: Identidad, condición de conocimiento e información
  permitida por esa condición.
- **Observación de puerta**: Puerta entre dos salas y último estado conocido,
  posiblemente distinto del real.
- **Viaje**: Destino explorado, pasos ordinarios y causa de detención.
- **Cambio de conocimiento**: Información revelada u observada en una acción
  y estado previo necesario para conservarla o revertirla.

## Criterios de éxito

### Resultados medibles

- **SC-NV-001**: Los 22 escenarios tienen prueba o registro reproducible asociado
  a requisitos, incluidos los seis casos de niebla del apéndice B. Hoy son
  escenarios especificados; la evidencia de ejecución sigue pendiente.
- **SC-NV-002**: Los escenarios de ocultación y memoria revelan cero información
  adicional por precarga o cambios remotos sin observar.
- **SC-NV-003**: Los viajes producen los mismos movimientos, tiempos y estado
  que ejecutar sus pasos manualmente, respetando desempates, paradas y replay.
- **SC-NV-004**: Guardar/cargar y revertir conserva o restaura exactamente el
  conocimiento de los escenarios correspondientes.
- **SC-NV-005**: Mediciones verifican PR-NV-001 y documentan la relación entre
  revelación y trabajo de actualización de PR-NV-002.

## Supuestos, dependencias y límites

- Se conservan costos, combate, activación, antorcha, pergamino, inventario y orden
  de eventos de P1 salvo cambios explícitos de P2. Terreno y cazadores ya está
  implementado; usar su comportamiento no decide reutilizar sus estructuras
  para este problema nuevo.
- Falta el enunciado original de P1. Código y documentación heredados no permiten
  contrastar íntegramente sus reglas.
- Se acepta `<sala>` por ID o nombre completo, distinguiendo mayúsculas y
  minúsculas; los nombres repetidos entre exploradas requieren indicar el ID.
  La consulta del mapa se solicita con `ver mapa`.
- No se añade revelación al encender antorcha sin entrar: §3.3 prescribe el
  efecto al entrar. Las demás reglas de antorcha se conservan.
- La integración con consultas históricas corresponde a línea de tiempo;
  aquí se exige conservar el conocimiento como estado del juego.
- No se crean plan, tareas o funcionalidades ni se eligen estructuras,
  algoritmos, clases o módulos; las decisiones técnicas requieren al usuario.

## Aclaraciones registradas

### Sesión del 2026-11-09

- **P**: ¿Qué comando consulta el mapa conocido? → **R**: Opción B, `ver mapa`.
  Se aplica a FR-NV-004 y AC-NV-001.

- **P**: ¿Qué ocurre si el destino es la sala actual? → **R**: Opción A,
  informar «Ya estás en esa sala», sin acción ni tiempo. Se aplica a FR-NV-013,
  AC-NV-017 y casos límite.

- **P**: ¿Cómo indicar la sala de destino? → **R**: Opción C, admitir tanto ID
  como nombre. Se aplica a FR-NV-008 y AC-NV-009.

- **P**: ¿Cómo tratar nombres repetidos y mayúsculas? → **R**: Opción B,
  nombre completo distinguiendo mayúsculas y minúsculas; si varias salas
  exploradas comparten ese nombre, rechazar y pedir ID. Se aplica a FR-NV-008
  y AC-NV-009.

- **P**: ¿Cómo permitir el pergamino entre pasos de «ir a»? → **R**: Opción A,
  avance automático con posibilidad de interrumpir entre pasos y ejecutar
  `retroceder`. Se aplica a FR-NV-016, AC-NV-020 y casos límite.

- **Pregunta**: La antorcha revela vecinas, pero la observación ordinaria exige
  estar en un extremo de la puerta. ¿Qué se conoce de puertas reveladas de una
  vecina que no conectan con la sala actual?
- **Respuesta del usuario**: «Registrar su estado al revelarlas con la antorcha,
  como interpretación del equipo.»
- **Aplicación**: AC-NV-006 y FR-NV-003/006 registran ese estado durante la
  revelación. Es una interpretación explícita del equipo ante una ambigüedad,
  no una cita literal del enunciado ni permiso para posteriores actualizaciones
  remotas sin observación.
