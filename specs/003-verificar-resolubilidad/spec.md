# Especificación: Verificación de resolubilidad

**Rama Git**: `main` (actual; no se crea otra rama).
**Creación**: 2026-11-09.
**Estado**: Aclaraciones e interpretaciones del equipo completadas; diseño en plan.md,
sin implementación.
**Entrada del usuario**: «Continuemos», después de confirmar resolubilidad como
siguiente capacidad.

**Fuentes**: [Cripta — Parte II](../../Cripta%20-%20Parte%20II.pdf),
§§2.2–2.6, 3.5, 4.2–4.3, 5.4, 6.1–6.3, 7.3 y apéndices A/B; constitución y
documentación heredada. Esta etapa describe comportamiento y evidencia exigida;
no elige estructuras, clases, módulos ni algoritmos.

## Escenarios de usuario y aceptación

Identificadores estables propios: FR-RS, PR-RS, AC-RS y SC-RS. Los ejemplos son
criptas sintéticas de aceptación, no datos oficiales incorporados al programa.

### Historia 1 — Saber si se puede escapar (Prioridad: P1)

Como jugador, quiero conocer antes de iniciar si puedo obtener la llave de
salida y alcanzar la salida por una puerta que la requiere.

**Motivo**: Evita iniciar inadvertidamente una cripta sin solución.
**Prueba independiente**: Verificar mapas pequeños con llaves y puertas conocidas,
sin ejecutar movimientos, combate ni eventos de partida.

**Escenarios de aceptación**:

1. **AC-RS-001** — **Dada** una sala inicial con acceso abierto a la llave de
   salida y una puerta que requiere esa llave hacia la sala de salida, **cuando**
   se verifica, **entonces** la cripta es resoluble y se presenta un orden válido
   que incluye la llave de salida. Requisitos: FR-RS-001/002/003/004.
2. **AC-RS-002** — **Dado** que llegar a la salida requiere primero obtener A,
   abrir con A el acceso a B y luego obtener la llave de salida usando B,
   **cuando** se verifica, **entonces** se descubre la secuencia completa sin
   detenerse en el primer bloqueo provisional. Requisitos: FR-RS-002/004/005.
3. **AC-RS-003** — **Dada** la llave de salida en una sala aislada de la región
   inicial, **cuando** se verifica, **entonces** no se declara resoluble solo
   porque la sala de salida sea alcanzable sin esa llave.
   Requisitos: FR-RS-003/006.
4. **AC-RS-004** — **Dado** que la llave de salida es obtenible y la sala de
   salida tiene un acceso abierto, pero no puede alcanzarse mediante ninguna
   puerta que requiera esa llave, **cuando** se verifica, **entonces** no basta
   llegar a la sala para declarar resolubilidad. Requisitos: FR-RS-003/006.
5. **AC-RS-005** — **Dadas** dos puertas sucesivas que requieren la misma llave
   obtenida previamente, con enemigos, trampas y cierre automático en el camino,
   **cuando** se verifica, **entonces** la llave sirve para ambas puertas y esos
   peligros no causan un resultado negativo bajo los supuestos de §3.5.
   Requisitos: FR-RS-002/003.

### Historia 2 — Entender el orden y los bloqueos (Prioridad: P1)

Como jugador, quiero un orden de llaves válido si existe solución, y un informe
de las llaves no obtenibles, puertas bloqueadas y ciclos cuando no existe.

**Motivo**: Un resultado negativo debe explicar qué impide el avance.
**Prueba independiente**: Comparar informes con bloqueos y dependencias
conocidos, rutas alternativas y ejecuciones repetidas.

**Escenarios de aceptación**:

1. **AC-RS-006** — **Dadas** varias llaves obtenibles en distinto orden y más de
   un orden válido, **cuando** se verifica dos veces con los mismos datos,
   **entonces** se presenta el mismo orden y cada llave puede obtenerse usando
   solo llaves anteriores del orden. No se exige un orden específico del profesor.
   Requisitos: FR-RS-004/009. Apéndice B, resolubilidad, caso 3.
2. **AC-RS-007** — **Dada** una llave en `suelta` de un enemigo errante que
   empieza en B, **cuando** se verifica, **entonces** se considera obtenible al
   alcanzar B y no se simulan sus desplazamientos para decidir dónde está.
   Requisitos: FR-RS-001/002. Apéndice B, resolubilidad, caso 2.
3. **AC-RS-008** — **Dada** una región alcanzable con una puerta cerrada hacia
   una región inaccesible, que requiere la llave K ubicada en esta última,
   **cuando** no existe solución, **entonces** el informe incluye K no obtenible,
   la puerta de frontera, la llave que requiere y su ubicación.
   Si una puerta física aparece en las salidas de ambas salas, se informa una
   sola vez con sus extremos, sin fusionar puertas físicas distintas que
   conecten las mismas salas.
   Según la interpretación del equipo, las salidas recíprocas compatibles
   comparten puerta cuando su emparejamiento es único. Si no puede identificarse
   una pareja inequívoca, se informa la ambigüedad sin fusionar conexiones.
   Requisitos: FR-RS-006/007.
4. **AC-RS-009** — **Dada** la llave de salida detrás de la única puerta que
   ella misma abre, **cuando** se verifica, **entonces** se informa no resoluble
   y se señala concretamente el ciclo de esa llave consigo misma.
   Requisitos: FR-RS-003/006/007/008.
   Apéndice B, resolubilidad, caso 1.
5. **AC-RS-010** — **Dada** una llave A bloqueada por B y B bloqueada por A,
   sin acceso alternativo que permita obtener alguna, **cuando** no hay solución,
   **entonces** el informe identifica el ciclo concreto A → B → A en un orden
   reproducible, no solo la frase «hay un ciclo».
   Requisitos: FR-RS-006/007/008/009.
6. **AC-RS-011** — **Dada** una puerta que parece crear dependencia circular,
   pero una ruta alternativa permite obtener una llave del supuesto ciclo,
   **cuando** se verifica, **entonces** se aprovecha esa alternativa y no se
   presenta el ciclo aparente como bloqueo inevitable.
   Si varios accesos siguen bloqueados por llaves del mismo grupo, se presenta
   el grupo completo, sus puertas y alternativas, junto con un ciclo concreto
   que explique por qué ninguna llave del grupo puede obtenerse primero. No
   se afirma que cada flecha entre llaves sea exclusiva en todas las rutas.
   Requisitos: FR-RS-002/003/005/008.
7. **AC-RS-012** — **Dadas** llaves no obtenibles en salas aisladas, sin ciclos
   de dependencia entre ellas, **cuando** se informa una cripta no resoluble,
   **entonces** se enumeran las llaves no obtenibles y los bloqueos existentes
   sin inventar un ciclo. Requisitos: FR-RS-006/007/008.

### Historia 3 — Elegir entre verificar, jugar o forzar (Prioridad: P1)

Como usuario, quiero consultar la verificación sin interfaz de juego y poder
iniciar expresamente una cripta no resoluble solo mediante `--forzar`.

**Motivo**: Separa el diagnóstico del inicio del juego y hace explícita la excepción.
**Prueba independiente**: Ejecutar los modos con datos controlados, comprobar
si se crea vista, se inicia partida o se modifica el estado.

**Escenarios de aceptación**:

1. **AC-RS-013** — **Dada** una cripta no resoluble y un inicio normal sin
   `--forzar`, **cuando** se solicita jugar, **entonces** se muestra el informe y
   no inicia la partida. Requisitos: FR-RS-006/010.
   Apéndice B, resolubilidad, caso 4.
2. **AC-RS-014** — **Dada** la misma cripta con `--forzar`, **cuando** se solicita
   jugar, **entonces** se permite iniciar aunque el informe siga siendo negativo;
   no se cambian topología, llaves ni condiciones de victoria.
   Requisitos: FR-RS-010/011.
3. **AC-RS-015** — **Dada** la orden `--verificar <cripta>`, **cuando** la cripta
   es resoluble o no resoluble, **entonces** se presenta el resultado correspondiente
   sin instanciar la vista ni comenzar una simulación interactiva.
   Requisitos: FR-RS-003/006/012.
   Al cargar una partida o reproducir un log no se repite automáticamente esta
   verificación ni se exige `--forzar` por su resultado; se conservan las
   validaciones existentes de formato, identidad y versiones.
   El proceso termina con código 0 si es resoluble, 1 si no es resoluble y
   2 si ocurre un error que impide completar la verificación.
   Combinar `--verificar` con otro modo de ejecución o con `--forzar` se rechaza
   con error de uso y explicación, sin iniciar juego ni ejecutar otro modo.
   Las opciones compatibles de fuente de datos, como `--offline`, siguen admitidas.
4. **AC-RS-016** — **Dada** una verificación anterior al juego, **cuando** termina
   y se permite iniciar, **entonces** no ha consumido acciones, tiempo virtual,
   azar de la partida ni llaves reales, ni ha marcado salas como exploradas.
   El conocimiento inicial del jugador conserva las reglas de niebla.
   Requisitos: FR-RS-009/011/013.

### Historia 4 — Usar datos válidos dentro del presupuesto (Prioridad: P1)

Como usuario, quiero que el resultado provenga de los datos de la cripta
seleccionada y sea válido para su versión, respetando el presupuesto de solicitudes.

**Motivo**: El veredicto no puede depender de una respuesta precalculada para
una cripta conocida o de ubicaciones de llaves de otra versión.
**Prueba independiente**: Proporcionar ubicaciones válidas, versiones cambiantes
y fallos de obtención; comprobar solicitudes y resultado informado.

**Escenarios de aceptación**:

1. **AC-RS-017** — **Dada** una cripta nueva con esqueleto y ubicaciones de llaves
   disponibles, **cuando** se verifica, **entonces** el resultado se obtiene de
   esos datos, sin depender de que el contenido de sus salas se haya descargado
   ni de conocer de antemano si esa cripta es resoluble.
   Requisitos: FR-RS-001/014.
2. **AC-RS-018** — **Dada** la obtención de ubicaciones de llaves y los datos
   necesarios de la cripta, **cuando** se hacen solicitudes y reintentos,
   **entonces** todos cuentan en `presupuesto_solicitudes` y nunca se supera.
   Requisito: FR-RS-014.
3. **AC-RS-019** — **Dadas** ubicaciones persistidas de una versión anterior,
   **cuando** se verifica otra versión de esa cripta, **entonces** no se reutilizan
   como válidas; se aplica validación de versión sin exigir borrado manual.
   Requisitos: FR-RS-014/015.
4. **AC-RS-020** — **Dado** que no se pueden obtener o validar los datos
   necesarios, **cuando** se intenta verificar, **entonces** se informa el error
   de obtención/validez; la falta de datos no se presenta como prueba de que la
   cripta sea resoluble ni de que no lo sea. Requisitos: FR-RS-001/015.

### Casos límite

- Una puerta inicialmente abierta no exige haber obtenido su llave para cruzarla
  en esta verificación, según los supuestos de §3.5.
- Una misma llave puede habilitar varias puertas y regiones; no se consume.
- Una llave puede ser obtenible sin que por eso se cumpla la condición completa
  de salida. Una sala de salida alcanzable por otro acceso tampoco basta.
- Un ciclo aparente con acceso alternativo no equivale a una dependencia inevitable.
- La ausencia de una ruta entre regiones no implica que exista un ciclo entre llaves.
- Un informe de llaves no obtenibles se exige en el resultado negativo; no se
  exige que todas las llaves de una cripta sean necesarias para escapar.
- Tener enemigos muy fuertes o movimiento costoso no convierte el análisis
  abstracto en una estimación de supervivencia o de tiempo de juego.

## Requisitos

### Requisitos funcionales

- **FR-RS-001**: Verificar antes de iniciar una partida nueva usando el esqueleto y
  la ubicación de llaves válida de la cripta seleccionada. Escenarios:
  AC-RS-001/007/017/020.
- **FR-RS-002**: Aplicar los supuestos de §3.5: salidas abiertas transitables;
  cerradas transitables con su llave; llaves no consumidas; enemigos derrotables;
  botín de llave obtenible en la sala inicial del enemigo; trampas y cierres
  automáticos no bloquean. Escenarios: AC-RS-001/002/005/007/011.
- **FR-RS-003**: Declarar resoluble solo si desde la sala inicial se puede obtener
  `llave_salida` y llegar a `sala_salida` mediante una puerta que la requiere,
  bajo esos supuestos. Escenarios: AC-RS-001/003/004/005/009/011/015.
- **FR-RS-004**: Si es resoluble, presentar un orden de obtención en el que cada
  llave sea obtenible con las anteriores; cualquier orden válido es aceptable
  si es determinista. Escenarios: AC-RS-001/002/006.
- **FR-RS-005**: Obtener una llave debe habilitar el avance adicional que permita,
  incluso regiones enteras con otras llaves, sin tratar bloqueos provisionales
  como definitivos. Escenarios: AC-RS-002/011.
- **FR-RS-006**: Si no es resoluble, presentar resultado negativo y las llaves
  que no pueden obtenerse, sin confundirlo con errores de datos.
  Escenarios: AC-RS-003/004/008/009/010/012/013/015.
- **FR-RS-007**: En el resultado negativo, informar puertas cerradas de la
  frontera bloqueada adyacente a la región alcanzable, con la llave requerida
  y la ubicación de cada una de esas llaves. Mostrar una entrada por puerta
  física con sus extremos, aunque tenga salidas recíprocas; no fusionar puertas
  físicas distintas entre las mismas salas. Escenarios: AC-RS-008/009/010/012.
  Interpretación del equipo: compartir puerta entre salidas recíprocas compatibles
  solo cuando el emparejamiento sea único; si es ambiguo, explicarlo y conservar
  las conexiones separadas, sin inventar identidad física.
- **FR-RS-008**: Señalar el ciclo concreto cuando una llave solo es accesible
  tras puertas que requieren esa misma llave directa o indirectamente, con
  detección determinista. No inventar ciclos por aislamiento o rutas alternativas.
  Conforme a la interpretación aprobada, el informe puede justificar un grupo
  circular mediante sus puertas, todas sus alternativas y un ciclo concreto
  dentro del grupo que explique la ausencia de un primer desbloqueo. No exige
  que cada flecha entre dos llaves sea individualmente inevitable en todas
  las rutas ni enumerar todos los ciclos posibles.
  Escenarios: AC-RS-009/010/011/012.
- **FR-RS-009**: Con los mismos datos y versiones, el resultado, orden válido
  elegido e informe deben ser reproducibles sin consumir el azar del juego.
  Escenarios: AC-RS-006/010/016.
- **FR-RS-010**: Una partida nueva en cripta no resoluble no debe iniciar sin `--forzar`; mostrar
  el reporte de verificación al iniciar. Escenarios: AC-RS-013/014.
- **FR-RS-011**: `--forzar` permite iniciar pese al resultado negativo, sin
  cambiar reglas de partida ni producir llaves, movimiento o exploración por
  la verificación previa. Escenarios: AC-RS-014/016.
- **FR-RS-012**: `--verificar <cripta>` ejecuta solo la verificación e imprime
  su resultado sin instanciar la vista ni iniciar juego interactivo.
  La verificación automática se limita a partidas nuevas; cargar y replay no
  la repiten ni incorporan un nuevo bloqueo por resolubilidad. Conservan sus
  validaciones de formato, identidad y versiones.
  En `--verificar`, devolver 0 para resoluble, 1 para no resoluble y 2 para error
  que impide completar la verificación; distinguir también el resultado en el texto.
  Rechazar con error de uso y explicación la combinación de `--verificar` con
  otro modo de ejecución (`--cripta`, `--cargar`, `--replay`, `--bench`, `--listar`
  o `--ver-puntajes`) o con `--forzar`, sin ejecutar esos modos. Conservar opciones
  compatibles de fuente de datos, como `--offline`.
  Escenario: AC-RS-015.
- **FR-RS-013**: La verificación no debe alterar conocimiento del mapa, reloj,
  inventario, actores, acciones o historial del juego que se iniciará.
  El reporte previo no concede conocimiento utilizable por `ir a`.
  Escenario: AC-RS-016.
- **FR-RS-014**: Toda solicitud de datos, incluida ubicación de llaves y reintentos,
  debe respetar el presupuesto. Si se reutilizan ubicaciones persistidas,
  deben coincidir con la versión de la cripta. No depender del contenido
  descargado para decidir obtenibilidad de llaves.
  Escenarios: AC-RS-017/018/019.
- **FR-RS-015**: No usar ubicaciones inválidas o de otra versión como datos
  válidos ni convertir un error de obtención/validez en un veredicto de
  resolubilidad. Escenarios: AC-RS-019/020.

### Requisitos de rendimiento

- **PR-RS-001**: Verificar en menos de 200 ms en el equipo local con la cripta
  publicada más grande, excluyendo red y renderizado (§6.1). Identificarla y
  comprobar sus versiones al medir; no suponer que es la referencia de otra capacidad.
- **PR-RS-002**: El trabajo total debe crecer aproximadamente de forma lineal
  con salas, salidas y llaves; no repetir un recorrido completo por cada llave.
  La frontera y dependencias deben obtenerse del mismo proceso, sin recorridos
  adicionales por cada llave (§5.4).
- **PR-RS-003**: `--bench` debe comparar la verificación incremental con repetir
  el recorrido por llave en cargas sintéticas con muchas llaves encadenadas,
  deterministas por semilla, y respaldar PR-RS-001/002 (§§5.4, 6.3).
  Las cifras de cazadores o niebla no acreditan estos límites.

### Entidades del juego

- **Cripta a verificar**: Identidad, versión, sala inicial, sala de salida,
  llave de salida, salas y conexiones.
- **Llave y ubicación**: Identidad, sala de colocación o sala inicial del enemigo
  que la suelta, y enemigo de origen si lo hay.
- **Región alcanzable**: Salas que pueden alcanzarse bajo los supuestos con las
  llaves obtenibles desde el inicio.
- **Frontera bloqueada**: Puertas cerradas adyacentes a la región alcanzable y
  las llaves que impiden continuar.
- **Resultado**: Veredicto y orden válido, o llaves no obtenibles, frontera,
  ubicaciones y ciclos concretos cuando corresponda.

## Criterios de éxito

### Resultados medibles

- **SC-RS-001**: Los 20 escenarios tienen prueba automatizada o registro
  reproducible que cite los requisitos atendidos, incluidos los cuatro casos de
  resolubilidad del apéndice B. La evidencia de ejecución está pendiente.
- **SC-RS-002**: En todos los escenarios válidos, el veredicto y el orden/reportes
  cumplen los supuestos y la condición completa de victoria, y se repiten iguales
  con los mismos datos.
- **SC-RS-003**: En los escenarios negativos se identifica cada bloqueo exigido
  y se justifican los grupos circulares con sus alternativas y ciclos concretos
  conforme a FR-RS-008; los casos sin ciclo o con alternativa obtenible no
  reciben diagnósticos circulares falsos. No se exige enumeración exhaustiva
  de todos los ciclos posibles.
- **SC-RS-004**: Se verifica el inicio bloqueado salvo `--forzar`, la consulta
  sin vista y cero acciones, tiempo, azar o exploración producidos por verificar.
- **SC-RS-005**: Las mediciones cumplen PR-RS-001 y documentan crecimiento y
  comparación exigidos por PR-RS-002/003 con condiciones reproducibles.

## Supuestos, dependencias y límites

- Los datos completos del esqueleto y ubicaciones no equivalen al conocimiento
  explorado del jugador. El informe previo exigido por §3.5 no modifica el mapa
  conocido ni autoriza usar datos ocultos en viajes posteriores.
- La ubicación de botín es la sala inicial que entrega el servicio; no se ejecutan
  combates ni se predice el movimiento real del enemigo.
- Persistir ubicaciones está permitido mientras coincida su versión; el enunciado
  no obliga a elegir aquí una estrategia particular de almacenamiento.
- Si hay datos offline, deben aportar información equivalente y válida; su formato
  y la integración concreta se precisarán en el plan.
- La verificación automática se aplica a partidas nuevas; cargar y replay
  mantienen su comportamiento sin repetirla. `--verificar` es consulta independiente.
  `--verificar` termina con códigos 0/1/2 para resoluble/no resoluble/error.
  Se rechaza combinar `--verificar` con otros modos o con `--forzar`; las opciones
  compatibles de fuente de datos siguen disponibles.
- Frontera y dependencias se reportan conforme a §3.5, con una entrada por puerta
  física y sin confundir puertas distintas entre las mismas salas. Los accesos
  alternativos se resuelven conforme a FR-RS-008 y AC-RS-011, sin inventar ciclos.
- El equipo aprueba el certificado del grupo circular con sus alternativas y
  un ciclo concreto, y la identidad compartida de salidas recíprocas compatibles
  únicamente con emparejamiento único. Son interpretaciones explícitas del
  equipo: el contrato HTTP por sí solo describe salidas dirigidas sin ID de puerta.
- Sigue faltando el enunciado original de P1 para contrastar íntegramente sus reglas.
- Esta especificación no implementa funcionalidades ni sustituye plan o tareas.
  Todas las decisiones de estructuras pertenecen al usuario.

## Aclaraciones

### Sesión del 2026-11-09

- **P**: ¿La verificación automática también se ejecuta al cargar una partida
  o reproducir un log? → **R**: A, automática solo para partidas nuevas y
  `--verificar` como consulta independiente; cargar y replay no la repiten.
  Se conservan sus validaciones existentes. Aplicado a FR-RS-001/010/012 y AC-RS-015.

- **P**: ¿Qué códigos devuelve `--verificar` al terminar? → **R**: A, 0 para
  resoluble, 1 para no resoluble y 2 para error. Aplicado a FR-RS-012 y AC-RS-015.

- **P**: ¿Cómo mostramos una misma puerta si aparece en las salidas de ambas
  salas? → **R**: A, una entrada por puerta física, identificando sus extremos
  y distinguiendo puertas físicas distintas entre las mismas salas.
  Aplicado a FR-RS-007 y AC-RS-008.

- **P**: ¿Qué hacemos si se combina `--verificar` con otro modo o con `--forzar`?
  → **R**: A, rechazar la combinación y explicar el uso correcto; conservar
  opciones compatibles como `--offline`. Aplicado a FR-RS-012 y AC-RS-015.

### Interpretaciones del equipo durante la planificación — 2026-11-09

- **P**: ¿Cómo se justifica un ciclo cuando hay accesos alternativos dentro de
  un grupo bloqueado? → **R**: Certificado del grupo y ciclo concreto, con
  puertas y alternativas; sin exigir exclusividad individual de cada flecha.
  Aplicado a FR-RS-008, AC-RS-011 y SC-RS-003.
- **P**: ¿Qué salidas recíprocas representan una puerta física? → **R**:
  Recíprocas únicas compatibles comparten puerta; ambigüedad se informa sin
  fusionar conexiones. Interpretación del equipo, no garantía de Swagger.
  Aplicado a FR-RS-007 y AC-RS-008.
