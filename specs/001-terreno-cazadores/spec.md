# Feature Specification: Terreno y cazadores

**Feature Branch**: `main` (rama actual; no se ha creado una rama de capacidad)

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: «Continuemos», tras crear la constitución de Cripta Parte II.
Se toma como siguiente etapa la primera capacidad de P2 §2.2: terreno y cazador,
incluida la validez de las rutas de §§5.1–5.2. Esta etapa solo especifica comportamientos.

## User Scenarios & Testing *(mandatory)*

Los identificadores de requisito `FR-TC-*` y `PR-TC-*` son estables y exclusivos de esta
capacidad. Los escenarios `AC-TC-*` servirán de referencia para tareas y pruebas posteriores.
Los ejemplos son cargas sintéticas de aceptación, no datos de una cripta oficial.

### User Story 1 - Movimiento según el terreno (Priority: P1)

Como jugador, quiero que atravesar una salida tarde según su costo y la velocidad del
actor, para que el terreno afecte a todos de acuerdo con las mismas reglas.

**Why this priority**: Es la regla base que permite comparar rutas y conserva el reloj
virtual de la primera parte.

**Independent Test**: Ejecutar movimientos por salidas con costos declarados y omitidos,
comparar los tiempos observados y repetir con cambios de velocidad.

**Acceptance Scenarios**:

1. **AC-TC-001** — **Given** una salida abierta sin costo declarado y un actor con velocidad
   100, **When** la atraviesa, **Then** su intervalo es 100; el trayecto inverso tiene el
   mismo costo base. Requisitos: FR-TC-001, FR-TC-002.
2. **AC-TC-002** — **Given** una salida abierta de costo 250, **When** un jugador, un errante,
   un rastreador o un cazador la cruza con velocidad 125, **Then** su intervalo es 200 en
   cualquiera de los dos sentidos. Requisitos: FR-TC-001, FR-TC-002, FR-TC-004.
3. **AC-TC-003** — **Given** una salida de costo 1 y un actor con velocidad 500, **When**
   la atraviesa, **Then** su intervalo es 1, nunca cero. Requisito: FR-TC-002. Apéndice B.6.
4. **AC-TC-004** — **Given** un movimiento de costo 300, velocidad inicial 100 y final
   previsto en reloj 300, **When** en reloj 100 la velocidad cambia a 200, **Then** las
   200 unidades restantes se convierten en 100 y el final previsto pasa a reloj 200;
   no se reinicia el movimiento completo. Requisito: FR-TC-003. Apéndice B.7.
5. **AC-TC-005** — **Given** actores con sus comportamientos previos y una salida costosa,
   **When** atacan, esperan o escogen destino como errantes o rastreadores, **Then** los
   costos de las acciones no relacionadas con moverse y las decisiones de esos enemigos
   conservan las reglas de P1. Requisito: FR-TC-004.

---

### User Story 2 - Persecución por costo mínimo y rango (Priority: P1)

Como jugador, quiero enfrentar cazadores que persigan por la ruta abierta de menor costo
dentro de su rango y que esperen cuando no pueden alcanzarme, para que su conducta sea
predecible a partir de las reglas.

**Why this priority**: Define la capacidad nueva y evita confundir la menor cantidad de
salas con el menor costo de tránsito.

**Independent Test**: Usar mapas sintéticos con caminos de costo conocido, puertas cerradas,
rangos en el límite y caminos empatados; observar un turno de cazador en cada caso.

**Acceptance Scenarios**:

1. **AC-TC-006** — **Given** un cazador vivo que comparte sala con el jugador, **When** llega
   su turno, **Then** ataca según P1, sin condicionar el ataque a su rango. Requisito: FR-TC-005.
2. **AC-TC-007** — **Given** que no hay ruta abierta hacia el jugador, **When** el cazador
   decide, **Then** espera con costo base 100 y no abre puertas, aunque exista una llave
   disponible. Requisitos: FR-TC-006, FR-TC-007. Apéndice B.1.
3. **AC-TC-008** — **Given** una ruta abierta mínima de costo 600, **When** decide un cazador
   con rango 599, **Then** espera con costo base 100; con rango 600, inicia un paso por
   una ruta mínima. Requisitos: FR-TC-007, FR-TC-008. Apéndice B.2.
4. **AC-TC-009** — **Given** dos rutas abiertas al jugador, una de dos salidas de costo 200
   cada una y otra de tres salidas de costo 100 cada una, y rango al menos 300, **When**
   decide el cazador, **Then** elige el primer paso de la segunda ruta, cuyo costo total
   es 300, y ese paso consume el intervalo correspondiente a costo 100.
   Requisitos: FR-TC-006, FR-TC-008. Apéndice B.3.
5. **AC-TC-010** — **Given** dos vecinas con IDs 3 y 8 que inician rutas mínimas de costo
   total 300, **When** decide el cazador y su rango permite la persecución, **Then** se
   mueve a la sala 3, incluso si la otra salida se enumeró primero o las rutas tienen
   distinta cantidad de salas. Requisito: FR-TC-009. Apéndice B.4.
6. **AC-TC-011** — **Given** el mismo esqueleto, puertas y posiciones, **When** varía qué
   contenido de salas se ha descargado o qué salas conoce el jugador, **Then** la decisión
   del cazador es idéntica; calcularla no necesita descargar contenido de salas de la ruta.
   Requisito: FR-TC-010.

---

### User Story 3 - Persecución coherente con los cambios (Priority: P1)

Como jugador, quiero que cada cazador reaccione al estado vigente de puertas y posiciones,
para que una ruta calculada antes no permita atravesar una puerta ya cerrada ni perseguir
una posición antigua.

**Why this priority**: Reutilizar información no puede cambiar las decisiones exigidas por
las reglas; esta propiedad debe conservarse con uno o muchos cazadores.

**Independent Test**: Comparar las decisiones observadas antes y después de cambios de
puertas o posición con las que corresponden al estado actual considerado desde cero.

**Acceptance Scenarios**:

1. **AC-TC-012** — **Given** una ruta mínima abierta elegida en un turno anterior, **When**
   una de sus puertas se cierra antes del siguiente turno, **Then** el cazador escoge la
   nueva ruta mínima abierta o espera si no existe una dentro de su rango.
   Requisito: FR-TC-011. Apéndice B.5.
2. **AC-TC-013** — **Given** una puerta cerrada que impide una ruta más barata, **When** se
   abre antes del siguiente turno, **Then** el cazador considera esa ruta y aplica el
   rango y el desempate sobre el estado actual. Requisitos: FR-TC-009, FR-TC-011.
3. **AC-TC-014** — **Given** que el jugador cambia de sala entre turnos del cazador,
   **When** este vuelve a decidir, **Then** el objetivo es la sala actual del jugador.
   Si coinciden, ataca. Requisitos: FR-TC-005, FR-TC-011.
4. **AC-TC-015** — **Given** varios cazadores activos y cambios intercalados de puertas,
   posiciones, velocidad o muerte de otros actores, **When** cada cazador decide,
   **Then** su resultado coincide con evaluar desde cero las reglas de ese instante,
   independientemente de la información reutilizada en turnos anteriores.
   Requisito: FR-TC-011.

---

### User Story 4 - Información visible y partida reproducible (Priority: P2)

Como jugador, quiero ver los costos de las salidas y distinguir a los cazadores, y poder
reproducir o reanudar una partida sin que cambien sus resultados por esta capacidad.

**Why this priority**: Permite comprender las decisiones observadas y conserva las garantías
existentes de reproducción, guardado y retroceso.

**Independent Test**: Consultar una sala con cazador y costos distintos; registrar acciones,
reproducirlas y comparar con una ejecución que guarde/cargue o retroceda un intervalo.

**Acceptance Scenarios**:

1. **AC-TC-016** — **Given** una sala actual con salidas y un cazador, **When** se presenta
   la información de la sala, **Then** se muestran los costos de esas salidas y el cazador
   se distingue de los demás enemigos. Requisito: FR-TC-012.
2. **AC-TC-017** — **Given** la misma cripta, versiones, semilla y acciones, **When** se
   repite o reproduce la partida sin interfaz, **Then** coinciden movimientos, decisiones,
   tiempos y resultados; una espera de red no modifica el reloj virtual.
   Requisito: FR-TC-013.
3. **AC-TC-018** — **Given** una partida con movimiento de costo variable y un cazador,
   **When** se guarda y carga con datos compatibles y se repiten las acciones restantes,
   **Then** coinciden decisiones y tiempos con la continuación sin interrupción.
   Requisito: FR-TC-014.
4. **AC-TC-019** — **Given** un intervalo reversible con movimiento de costo variable y
   cambios de puertas o acciones de cazadores, **When** se usa un pergamino, **Then**
   se restaura el estado que corresponde a P1, incluidos posiciones, reloj y acciones
   pendientes; el pergamino mantiene las excepciones de P1. La siguiente decisión del
   cazador corresponde al estado restaurado. Requisitos: FR-TC-011, FR-TC-014.

---

### Edge Cases

- Costo omitido: 100; costo mínimo permitido: 1; intervalo mínimo: 1 (AC-TC-001/003).
- Distancia mínima exactamente igual al rango: el cazador se mueve (AC-TC-008).
- Jugador y cazador en la misma sala: prevalece atacar (AC-TC-006).
- Sala desconectada o todas las rutas bloqueadas: esperar; no abrir puertas (AC-TC-007).
- Múltiples rutas mínimas: desempatar por el ID de la primera vecina (AC-TC-010).
- Cierre automático entre dos turnos: tratarlo como cambio vigente de puerta (AC-TC-012).
- Contenido no descargado y conocimiento parcial del jugador: no limitan al cazador
  (AC-TC-011); esto no autoriza revelar el mapa completo al jugador.
- Efectos de velocidad durante un movimiento costoso: escalar solo lo restante (AC-TC-004).
- Datos fuera del contrato, como costos no enteros o menores que 1, no son terrenos válidos.
  El manejo concreto de entradas malformadas no se redefine en esta capacidad.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-TC-001**: Cada salida puede declarar un costo entero mayor o igual que 1. Ausente,
  equivale a 100. El costo es el mismo en ambos sentidos (P2 §3.1).
- **FR-TC-002**: Todo actor que se mueve usa el costo de la salida como costo base y tarda
  `max(1, costo_salida * 100 // velocidad)` unidades de reloj virtual (P2 §3.1).
- **FR-TC-003**: Un cambio de velocidad durante el movimiento escala el tiempo restante
  conforme a P1 §2.3, conservando el intervalo restante mínimo de 1; no vuelve a cobrar el
  costo completo (P2 apéndice B, terreno, último caso).
- **FR-TC-004**: Los costos de atacar, esperar y otras acciones no cambian. Errantes y
  rastreadores conservan su comportamiento; solo cambia la duración del movimiento
  (P2 §3.1).
- **FR-TC-005**: Un cazador que comparte sala con el jugador ataca según P1 §2.8 antes de
  considerar búsqueda, distancia o rango (P2 §3.2).
- **FR-TC-006**: Si no comparte sala, el cazador considera el mínimo costo total hasta la
  sala actual del jugador, sumando costos de salidas abiertas en ese instante; no abre
  puertas cerradas (P2 §3.2).
- **FR-TC-007**: Sin ruta abierta o con distancia mínima mayor que el rango declarado en
  su ficha, el cazador espera con costo base 100 (P2 §3.2).
- **FR-TC-008**: Con ruta mínima dentro del rango, el cazador avanza exactamente un paso
  por una ruta de costo mínimo y paga el costo de la salida atravesada (P2 §3.2).
- **FR-TC-009**: Entre vecinas que inician rutas de costo mínimo, el cazador elige la de
  menor ID, independientemente del orden de presentación de las salidas (P2 §3.2).
- **FR-TC-010**: El cazador conoce el esqueleto completo, sus costos y el estado actual de
  todas las puertas; su decisión no depende del conocimiento del jugador ni de si está
  descargado el contenido de una sala (P2 §§3.2 y 4.1).
- **FR-TC-011**: Toda decisión coincide con calcular desde cero sobre el estado vigente,
  también después de aperturas, cierres, movimiento del jugador, cambios de velocidad,
  movimiento o muerte de otros actores y retroceso. Reutilizar cálculos no puede alterar
  el resultado (P2 §§3.2 y 5.2; conservación de retroceso de P1).
- **FR-TC-012**: La información de la sala actual muestra costos de salidas y distingue a
  los cazadores de los demás enemigos, respetando el conocimiento del jugador cuando
  se integre la niebla de guerra (P2 §7.3).
- **FR-TC-013**: Se conserva el determinismo de partida y replay sin vista; las esperas de
  red no consumen tiempo virtual (constitución, principios II y III).
- **FR-TC-014**: Guardado/carga y pergamino conservan sus garantías de P1 al incorporar
  costos y cazadores; los datos restaurados producen decisiones y tiempos coherentes
  con ese estado, respetando compatibilidad de versiones (P2, vigencia de P1 y §4.3).

### Performance Requirements

- **PR-TC-001**: Cada ciclo de eventos entre decisiones del jugador tarda menos de
  20 ms (tiempo < 20 ms) en la cripta de referencia con decenas de cazadores activos, medido localmente
  sin red ni renderizado (P2 §6.1; sujeto a enmienda oficial).
- **PR-TC-002**: El trabajo de la decisión de un cazador de rango pequeño depende de la
  región dentro de su rango y no crece proporcionalmente con toda la cripta. La medición
  debe distinguir ese caso del de rangos grandes (P2 §5.1).
- **PR-TC-003**: La evidencia compara uno y muchos cazadores, rangos pequeños y grandes,
  cálculo compartido e individual, y reutilización frente a recálculo siempre con puertas
  estables e inestables. También repite mediciones de agenda y retroceso con la nueva carga;
  no se declara ganadora una alternativa sin medirla (P2 §§5.1–5.2, 5.6 y 6.3).

### Key Entities *(include if feature involves data)*

- **Salida**: conexión entre salas, con costo de tránsito y estado de puerta, cuando la hay.
- **Cazador**: enemigo con sala, estadísticas, velocidad y rango de persecución por costo.
- **Jugador**: objetivo cuya sala actual determina el destino de la persecución.
- **Ruta válida**: secuencia de salidas abiertas en el instante de decisión; su costo es la suma
  de costos de tránsito. Solo su primer paso se ejecuta en un turno.
- **Partida**: estado del reloj, actores y puertas, junto con semilla y acciones que permiten
  reproducir su evolución.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-TC-001**: Los siete casos obligatorios de terreno y cazador del apéndice B tienen el
  resultado previsto: AC-TC-007, 008, 009, 010, 012, 003 y 004, respectivamente.
- **SC-TC-002**: El 100 % de los escenarios AC-TC-001 a AC-TC-019 obtiene el resultado
  esperado en las pruebas o reproducciones asociadas; cada evidencia cita sus requisitos.
- **SC-TC-003**: Con iguales versiones, cripta, semilla y acciones, dos ejecuciones y su
  reproducción coinciden en estado observable, decisiones y tiempos (FR-TC-013).
- **SC-TC-004**: En la cripta de referencia con decenas de cazadores, cada ciclo medido tarda
  menos de 20 ms; un ciclo de 20 ms o más incumple (PR-TC-001). Se excluyen red y renderizado. Se informa el máximo observado y la
  carga utilizada; la aceptación queda pendiente si no está disponible esa referencia.
- **SC-TC-005**: La evidencia muestra el costo de persecución con región de rango fijo y
  más salas fuera de ella, y cubre todas las comparaciones de PR-TC-003 sin sacrificar
  las decisiones de FR-TC-011. No se fija una mejora porcentual que el enunciado no exige.

## Assumptions

- Fuente normativa: [Cripta - Parte II.pdf](../../Cripta%20-%20Parte%20II.pdf), §§3.1–3.2,
  4.1, 4.3, 5.1–5.2, 5.6, 6.1, 6.3, 7.3 y apéndice B; también rige la
  [constitución](../../.specify/memory/constitution.md).
- La capacidad comprende terreno, cazador e información de rutas que debe seguir siendo
  válida. Niebla de guerra e «ir a», resolubilidad y línea de tiempo tendrán especificaciones
  propias; no se diseñan aquí. Se conservan las integraciones de P1 afectadas por esta capacidad.
- La regla de reajuste de velocidad se conserva de P1. El ejemplo AC-TC-004 corresponde a
  lo documentado y al comportamiento actual de P1; falta su enunciado original para
  contrastar todos los casos límite, sin inventar otra fórmula para esta etapa.
- Los datos del servicio cumplen el contrato de costos simétricos y rango entero. No se
  inventa un valor de rango por defecto ni una política nueva para datos inválidos.
- Los costos y datos de cazadores se reutilizan solo con las versiones de cripta y catálogo
  correspondientes; no se introducen excepciones por IDs de criptas oficiales.
- La cripta de referencia, su versión y la carga concreta de «decenas de cazadores» deben
  identificarse antes de afirmar cumplimiento de PR-TC-001. Las cargas sintéticas permiten
  preparar la verificación, pero no sustituyen esa evidencia.
- Cada escenario necesitará prueba automatizada o log de reproducción en las fases de
  tareas e implementación. Esta revisión comprueba la especificación, no el juego ejecutado.
- Antes del código, esta especificación debe confirmarse en Git conforme a la constitución.
