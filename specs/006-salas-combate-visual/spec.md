# Especificación: Salas habitables y combate visual

**Rama**: `005-interfaz-pygame`, separada de `main`.
**Creación**: 2026-11-14.
**Estado**: Implementada y verificada automáticamente; aceptación visual nativa y auditoría final pendientes.
**Entrada**: El mapa sirve para orientarse, pero el usuario quiere habitaciones,
personaje y enemigos con sprites; referencias de exploración a The Binding of
Isaac y de combate a RPG Maker. La finalidad es hacer más visual el juego.

Esta capacidad evoluciona la presentación de [005](../005-interfaz-pygame/spec.md)
dentro de la misma rama adicional. Las pruebas y el avance de 005 no acreditan
esta nueva experiencia. Las referencias comunican composición y experiencia;
los personajes, escenarios y recursos tendrán diseños propios.

## Aclaraciones del usuario — 2026-11-14

- Vista principal: habitación desde arriba con personaje, enemigos y objetos;
  minimapa como apoyo y mapa completo ampliable.
- Combate dentro de la misma habitación, con animaciones por turno; no cambia a
  una escena de batalla separada.
- Dirección artística: ilustración 2D de fantasía oscura.

## Escenarios de usuario y aceptación

### Historia 1 — Explorar una habitación con el personaje (Prioridad: P1)

Como jugador, quiero ver al personaje dentro de la habitación actual, con puertas,
objetos y enemigos visibles, para sentir que exploro la cripta.

**Motivo**: La sala se convierte en la experiencia principal.
**Prueba independiente**: Recorrer una sala vacía y otra con contenido; reconocer
personaje, objetivos y salidas sin consultar listas.

1. **AC-EV-001** — Iniciar o cargar muestra una habitación y el personaje con
   sprites. Sus puertas corresponden a las salidas existentes y su dirección;
   la decoración no inventa puertas utilizables. FR-EV-001/002/004.
2. **AC-EV-002** — Seleccionar una puerta y activar mover o abrir ejecuta la
   operación vigente, con los mismos costos y rechazos. Una transición solo
   presenta llegada tras confirmar el movimiento. FR-EV-004/008.
3. **AC-EV-003** — Los objetos actuales tienen sprites seleccionables y nombre.
   Contenido nuevo sin ilustración particular recibe una representación genérica
   identificable, sin inutilizar esa cripta. FR-EV-002/005/013.
4. **AC-EV-004** — Las posiciones dibujadas no introducen distancias, alcance,
   colisiones o costos nuevos de caminar dentro de la sala. Observar una escena
   o sus animaciones no consume turnos. FR-EV-008/009.

**Presentación elegida**: sala desde arriba y minimapa.

### Historia 2 — Combatir con personajes y enemigos visibles (Prioridad: P1)

Como jugador, quiero ver mi personaje y los enemigos, elegir visualmente a quién
atacar y reconocer el resultado de cada acción.

**Motivo**: Comunicar el combate mediante personajes y efectos, manteniendo los
mensajes detallados como apoyo.
**Prueba independiente**: Seleccionar enemigos con nombres repetidos, atacar,
recibir daño y derrotar uno, comparando el resultado con la consola.

1. **AC-EV-005** — Si hay enemigos observables actuales, el combate en la misma
   habitación muestra al
   personaje y sprites reconocibles de las familias de criaturas. Los iconos
   esquemáticos anteriores dejan de ser su representación principal. FR-EV-001/003/006.
2. **AC-EV-006** — Elegir un enemigo resalta su sprite e identifica nombre y vida
   observable; nombres repetidos siguen siendo objetivos distintos. Un objetivo
   caducado no se sustituye automáticamente por otro. FR-EV-005/006.
3. **AC-EV-007** — Ataque, daño, curación y derrota confirmados reciben respuesta
   visual. Los valores finales proceden del juego real; reducir o saltar efectos
   no repite acciones ni altera el resultado. No se inventa una secuencia exacta
   de golpes si los datos observados no permiten reconstruirla. FR-EV-007/008/009.
4. **AC-EV-008** — Los controles ofrecen las acciones vigentes pertinentes:
   atacar, esperar, inventario/objetos y desplazarse cuando se permita. Presentar
   combate no bloquea puertas ni obliga a derrotar a todos si las reglas actuales
   permiten salir; tampoco añade habilidades o defensa nuevas. FR-EV-006/008.

**Presentación elegida**: combate dentro de la misma sala, con animaciones por turno.

### Historia 3 — Orientarse sin revelar contenido oculto (Prioridad: P1)

Como jugador, quiero consultar el mapa durante la exploración, conservando niebla
y recuerdos sin reemplazar el escenario principal.

**Motivo**: Conservar las capacidades útiles del mapa actual.
**Prueba independiente**: Recorrer, revelar con antorcha, retroceder y consultar
historia, contrastando cada representación con la información permitida.

1. **AC-EV-009** — La habitación es la vista principal; un minimapa y el mapa
   completo ampliable conservan conocimiento, conexiones, costos, recuerdos y
   enlaces esquemáticos de 005. No aparecen habitaciones desconocidas. FR-EV-010/011.
2. **AC-EV-010** — Habitación y combate solo muestran contenido observable actual.
   La antorcha no crea una escena de contenido remoto; el mapa conserva los últimos
   enemigos observados, marcados como recuerdos. FR-EV-011.
3. **AC-EV-011** — Cargar o retroceder descarta transiciones y objetivos caducados
   y presenta el estado confirmado. Historia se identifica como pasado y no
   recibe enemigos ni recuerdos del presente. FR-EV-011/012.
4. **AC-EV-012** — Viajar conserva rutas, costos y paradas. Cada paso puede mostrar
   una transición; detener, perder foco o cerrar impide nuevos pasos y conserva
   el tratamiento de la operación ya aceptada definido en 005. FR-EV-009/010/012.

### Historia 4 — Disfrutar una presentación coherente y legible (Prioridad: P2)

Como jugador, quiero que habitaciones, personajes, objetos y controles compartan
estilo, con acceso a todas las funciones existentes.

**Motivo**: La experiencia debe comunicar exploración y combate visualmente.
**Prueba independiente**: Completar el recorrido con ventana mínima, seleccionando
objetivos visuales y usando también inventario y guardado.

1. **AC-EV-013** — Suelo, límites, puertas y ambientación forman una habitación
   coherente. Personaje, enemigos y objetos comparten estilo y escala compatibles;
   la decoración se distingue de elementos interactivos. FR-EV-001/002/003/013.
2. **AC-EV-014** — Desde 1024 × 768 son legibles y alcanzables personaje, objetivos
   y controles. Muchos objetivos se recorren sin perder identidad; no se fusionan
   varios enemigos atacables en un único contador. FR-EV-005/014.
3. **AC-EV-015** — Continúan disponibles inventario, ayuda, mensajes, viaje,
   historia, retroceso, guardado/carga y resultados. Consultar paneles no consume
   turno. Partidas existentes y modos de consola conservan su funcionamiento.
   FR-EV-012/014.

**Dirección artística elegida**: ilustración 2D de fantasía oscura.

### Casos límite

- Sala vacía, muchos enemigos/objetos y nombres repetidos: todos los objetivos
  siguen siendo distinguibles y seleccionables.
- Enemigo que muere, llega o sale durante una acción: representar el estado
  confirmado sin conservar objetivos que dejaron de estar presentes.
- Rechazo o error de red: no mostrar éxito ni llegada ficticia.
- Carga, retroceso, foco o cierre durante un efecto: no repetir acciones para
  completar una animación y no conservar datos de la revisión anterior.
- Puerta cerrada o enlace esquemático: la escena no promete otra topología.
- Entidad nueva sin arte específico: representación genérica con nombre,
  disponible offline; una cripta nueva no depende de descargar ilustraciones.

## Requisitos

### Requisitos funcionales

- **FR-EV-001**: Presentar la habitación desde arriba, personaje y enemigos como escenas con
  sprites reconocibles; el mapa pasa a ser apoyo. AC-EV-001/005/013.
- **FR-EV-002**: Mostrar suelo, límites, puertas y objetos actuales, distinguiendo
  decoración y elementos utilizables. AC-EV-001/003/013.
- **FR-EV-003**: Diferenciar las familias de enemigos y dar al jugador una
  representación propia, consistente entre exploración y combate. AC-EV-005/013.
- **FR-EV-004**: Seleccionar puertas y ejecutar mover/abrir conforme a conexiones,
  costos y rechazos vigentes. AC-EV-001/002.
- **FR-EV-005**: Seleccionar sprites con nombre, indicador e identidad vigente;
  mantener acceso a todos si el espacio visible resulta insuficiente. AC-EV-003/006/014.
- **FR-EV-006**: Mostrar el combate dentro de la misma habitación con personaje, enemigos, vida observable, objetivo
  y acciones actuales pertinentes. AC-EV-005/006/008.
- **FR-EV-007**: Dar respuesta visual breve a ataque, daño, curación y derrota
  confirmados, sin inventar resultados. AC-EV-007.
- **FR-EV-008**: Conservar reglas, costos, orden de eventos, azar y registro para
  una misma secuencia; posiciones y efectos no afectan el resultado. AC-EV-002/004/007/008.
- **FR-EV-009**: Mantener turnos y exclusión de activaciones: efectos, inactividad,
  transiciones y teclas mantenidas no crean acciones. Saltar efectos tampoco
  repite una operación confirmada. AC-EV-004/007/012.
- **FR-EV-010**: Ofrecer mapa secundario accesible y viaje conocido por pasos,
  con sus paradas vigentes. AC-EV-009/012.
- **FR-EV-011**: Respetar niebla, antorcha, observación presencial, recuerdos e
  historia; ninguna escena añade contenido remoto o futuro. AC-EV-009/010/011.
- **FR-EV-012**: Sincronizar escenas al cargar/retroceder/consultar historia y
  conservar guardados, otros modos y cierre seguro. AC-EV-011/012/015.
- **FR-EV-013**: Mantener ilustración 2D de fantasía oscura coherente, diseños originales y
  recursos genéricos para contenido nuevo, disponibles offline. AC-EV-003/013.
- **FR-EV-014**: Mantener funciones, texto legible y objetivos/controles alcanzables
  desde 1024 × 768. AC-EV-014/015.

### Entidades principales

- **Habitación presentada**: escenario actual con elementos observables y posiciones
  exclusivamente de presentación.
- **Personaje presentado**: representación del jugador y su estado confirmado.
- **Objetivo visual**: enemigo, objeto o puerta seleccionable, con identidad y
  datos permitidos por el estado presentado.
- **Resultado visual**: efecto o transición de una operación confirmada,
  descartable sin alterar el juego.
- **Mapa secundario**: conocimiento y recuerdos ya existentes.

## Criterios de éxito

- **SC-EV-001**: Inicio, recogida, cambio de habitación, ataque y regreso se
  realizan desde las escenas sin escribir órdenes; el personaje permanece visible
  durante exploración y combate normales.
- **SC-EV-002**: Las cuatro familias actuales de enemigos y las clases actuales
  de objetos tienen representación identificable; nombres repetidos conservan
  selección individual.
- **SC-EV-003**: Misma cripta, semilla y acciones producen idéntico estado, reloj,
  azar y órdenes con efectos normales, reducidos o saltados. Sesenta segundos
  de inactividad y 300 redibujados no añaden turnos.
- **SC-EV-004**: Todos los escenarios de niebla, antorcha, recuerdo, historia,
  retroceso y carga de esta capacidad pasan sin revelar contenido remoto.
- **SC-EV-005**: Revisión visual real a 1024 × 768 y 1280 × 800 confirma objetivos
  y controles alcanzables y legibles; personaje, objetos y enemigos se reconocen
  antes de abrir una lista textual.
- **SC-EV-006**: Guardados previos y posteriores conservan continuación; la
  instalación sin gráficos mantiene sus modos actuales.

## Supuestos, alcance y dependencias

- Se conservan las reglas, turnos, datos de criptas, determinismo, presupuesto
  HTTP y compatibilidad de 001–005. EX-01 no se reabre.
- Las referencias a otros juegos no implican adoptar sus reglas de combate,
  movimiento continuo, niveles o personajes.
- La composición de una habitación es escénica; no añade una rejilla de movimiento,
  obstáculos jugables, distancias ni posiciones guardadas nuevas.
- Los enemigos actúan cuando dispone el motor vigente; una escena de combate no
  introduce otra secuencia de turnos alternados.
- Decoración y variantes no afirman atributos de la cripta que sus datos no
  proporcionan. Los recursos acompañan a la distribución del juego.
- Audio, diálogos, creación de personajes y mecánicas nuevas quedan fuera del
  primer incremento; los efectos se limitan a comunicar las acciones actuales.
- Las preferencias visuales quedaron resueltas el 2026-11-14. Las estructuras siguen requiriendo
  elección explícita del usuario conforme a AGENTS.md durante la planificación.
