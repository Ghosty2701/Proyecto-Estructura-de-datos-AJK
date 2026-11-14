# Especificación: Interfaz gráfica de Cripta con Pygame

**Rama**: `005-interfaz-pygame`, separada de `main`.
**Base**: `6107b98`, versión funcional publicada de Parte II con EX-01.
**Creación**: 2026-11-13.
**Estado**: Especificada y planificada; implementación en curso. T001–T010 verificadas; 769 pruebas pasan. La ventana gráfica jugable sigue pendiente.
**Entrada**: Adaptar el proyecto a Pygame siguiendo SDD con GitHub spec-kit, en una rama adicional que conserve la versión actual.
**Restricción solicitada**: Pygame para la presentación gráfica. Es una elección explícita del usuario; esta especificación no elige estructuras, algoritmos, módulos ni formatos auxiliares.

**Fuentes**: [Constitución](../../.specify/memory/constitution.md),
[reglas actuales](../../README.md), specs [001](../001-terreno-cazadores/spec.md),
[002](../002-niebla-viaje/spec.md), [003](../003-verificar-resolubilidad/spec.md)
y [004](../004-linea-tiempo/spec.md), y [cierre EX-01](../../documentacion/REVISION_SESION_BLOQUEADA.md).
Esta capacidad es adicional al enunciado académico; no reemplaza las cuatro anteriores.

## Aclaraciones del usuario

### Sesión 2026-11-13

- Presentación: mapa 2D con salas en cuadritos y sprites que indiquen los enemigos; paneles y botones para cada acción; el juego sigue siendo por turnos.
- Niebla: mostrar salas visitadas y adyacentes según el conocimiento permitido. Una sala solo avistada no revela enemigos ni contenido. Se conserva la revelación por antorcha de las reglas actuales.
- Enemigos fuera de la sala actual: mostrar los últimos observados, identificados como recuerdo hasta volver a entrar; no mostrar sus movimientos remotos reales.
- Decisiones técnicas del 2026-11-13: índice propio con vectores y cambios por turno; recuerdos opcionales dentro del mismo `.bin` v6; croquis por direcciones con conflictos señalados. El detalle de diseño se registra en el plan y en la investigación.

## Escenarios de usuario y aceptación

Identificadores propios: FR-IG, PR-IG, AC-IG y SC-IG. Los escenarios describen
pruebas futuras, no comprobaciones ya ejecutadas. Las cargas son sintéticas o
proceden de datos externos compatibles; no se incorporan criptas concretas al juego.

### Historia 1 — Iniciar una partida gráfica (Prioridad: P1)

Como jugador, quiero seleccionar una cripta e iniciar o cargar una partida desde
una ventana para poder jugar sin escribir órdenes durante la sesión.

**Motivo**: Proporciona la entrada a la nueva interfaz sin alterar el inicio válido del juego.
**Prueba independiente**: Abrir la ventana, seleccionar una cripta y comenzar con una semilla conocida; comparar el estado inicial con la consola.

**Escenarios de aceptación**:

1. **AC-IG-001** — **Dadas** criptas disponibles, **cuando** se abre el inicio gráfico,
   **entonces** se puede elegir cripta, nombre y semilla, comenzar, cargar o salir;
   ninguna selección avanza el reloj. FR-IG-001, FR-IG-002.
2. **AC-IG-002** — **Dada** una cripta no resoluble, **cuando** se intenta comenzar,
   **entonces** se presenta el informe y no se inicia sin una elección explícita
   equivalente a forzar; los errores de datos no se omiten. FR-IG-003.
3. **AC-IG-003** — **Dados** un paquete offline válido y la red deshabilitada,
   **cuando** se configura ese origen e inicia o carga una partida,
   **entonces** se puede jugar con los mismos datos sin solicitudes HTTP. FR-IG-002, FR-IG-020.

### Historia 2 — Orientarse con el mapa y los enemigos recordados (Prioridad: P1)

Como jugador, quiero ver salas en una cuadrícula, mi ubicación, las conexiones
conocidas y sprites de enemigos para orientarme sin obtener información oculta.

**Motivo**: Es la presentación principal elegida por el usuario y conserva la niebla.
**Prueba independiente**: Recorrer un mapa pequeño con puertas y enemigos; provocar movimientos remotos y contrastar lo presentado con las observaciones realizadas.

**Escenarios de aceptación**:

1. **AC-IG-004** — **Dado** el inicio en A, con B adyacente y C desconocida,
   **cuando** se muestra el mapa, **entonces** A aparece como actual/visitada,
   B como avistada y C no aparece; B no revela nombre, enemigos, objetos ni
   otros datos que el conocimiento vigente no permite. FR-IG-004, FR-IG-005.
2. **AC-IG-005** — **Dadas** conexiones y puertas observadas, **cuando** se dibujan,
   **entonces** se pueden distinguir dirección, destino, costo y recuerdo de la
   puerta. La cercanía visual de dos cuadritos no implica una salida inexistente.
   Un cambio remoto no actualiza el recuerdo de la puerta. FR-IG-004, FR-IG-005.
3. **AC-IG-006** — **Dados** varios enemigos en la sala actual, **cuando** se
   muestra la sala o termina una acción, **entonces** sus sprites y cantidades
   corresponden al estado observable actual; se puede identificar el objetivo
   de un ataque sin depender solo del color. FR-IG-006, FR-IG-009, FR-IG-021.
4. **AC-IG-007** — **Dada** una sala previamente observada, **cuando** el jugador
   se aleja y un enemigo se mueve o cambia remotamente, **entonces** sus sprites
   conservan la última observación, indican que son un recuerdo y no revelan
   el cambio; al volver a entrar, se actualizan. FR-IG-007.
5. **AC-IG-008** — **Dada** una antorcha que revela una sala sin entrar,
   **cuando** se actualiza el mapa, **entonces** se aplica la revelación existente
   de salas/puertas, pero no se inventa una observación de enemigos ni se activa
   contenido remoto. Una sala sin observación de contenido no se presenta como
   comprobada vacía. FR-IG-005, FR-IG-007.

### Historia 3 — Jugar mediante paneles y botones (Prioridad: P1)

Como jugador, quiero ejecutar todas las acciones de una partida desde controles
gráficos para explorar, combatir y gestionar el inventario sin usar la consola.

**Motivo**: La ventana debe permitir jugar y no ser únicamente un visor.
**Prueba independiente**: Ejecutar una secuencia que incluya cada acción, rechazos y navegación, y compararla con la misma secuencia en consola.

**Escenarios de aceptación**:

1. **AC-IG-009** — **Dada** una partida en curso, **cuando** se utilizan los controles,
   **entonces** están disponibles mover por dirección, abrir, seleccionar y atacar
   enemigo, esperar, seleccionar y recoger objeto, consultar/recorrer/ordenar
   inventario, usar, equipar, soltar, retroceder, ver mapa, viajar, consultar
   historia, guardar, cargar cuando se permita, ayuda y salir. FR-IG-008, FR-IG-009.
2. **AC-IG-010** — **Dada** una tecla sostenida, una repetición automática de teclado
   o una acción todavía en procesamiento, **cuando** llegan eventos de entrada,
   **entonces** no aparecen turnos repetidos por mantener la tecla ni órdenes
   acumuladas para ejecutarse después. Una activación deliberada aceptada
   produce una operación y como máximo un turno de juego. Seleccionar un objeto
   del inventario puede emitir la navegación canónica necesaria, siempre sin
   turnos y sin encolar otra acción. Durante un viaje solo puede retenerse la única orden
   interruptora de AC-IG-013 hasta terminar el paso aceptado; no se acumulan
   activaciones adicionales. FR-IG-010, FR-IG-011.
3. **AC-IG-011** — **Dadas** una selección o acción inválida, **cuando** se intenta
   actuar, **entonces** se informa el rechazo, no cambia el tiempo/azar ni se
   registra una acción inexistente. Abrir paneles, seleccionar objetivos,
   consultar ayuda y ordenar inventario tampoco consumen turnos. FR-IG-009, FR-IG-011, FR-IG-014.

### Historia 4 — Viajar e interrumpir el recorrido (Prioridad: P1)

Como jugador, quiero elegir una sala explorada del mapa y viajar hasta ella,
pudiendo detener el recorrido entre pasos.

**Motivo**: Conserva la capacidad «ir a» sin convertirla en movimiento en tiempo real.
**Prueba independiente**: Iniciar un recorrido y provocar sus condiciones de parada y una interrupción gráfica.

**Escenarios de aceptación**:

1. **AC-IG-012** — **Dado** un destino explorado, **cuando** se selecciona y activa
   viajar, **entonces** cada paso usa las reglas existentes, actualiza la
   presentación y se registra como movimiento ordinario. Un destino avistado,
   desconocido o sin ruta válida se rechaza sin avanzar. FR-IG-012, FR-IG-014.
2. **AC-IG-013** — **Dado** un viaje en curso, **cuando** se pulsa detener, otra
   orden deliberada o retroceder, **entonces** se interrumpe entre pasos y se
   procesa esa orden una sola vez; retroceder revierte solo el último paso y
   el viaje no se reanuda solo. FR-IG-013.
3. **AC-IG-014** — **Dado** un viaje que encuentra enemigos, daño, puerta realmente
   cerrada o pérdida de ruta, **cuando** ocurre esa condición, **entonces** se
   detiene conforme a las reglas vigentes y explica el motivo en pantalla.
   No atraviesa paredes ni abre puertas automáticamente. FR-IG-012, FR-IG-014.

### Historia 5 — Consultar y retroceder sin revelar el futuro (Prioridad: P1)

Como jugador, quiero consultar la historia y usar pergaminos sin que los paneles
o recuerdos visuales modifiquen la partida ni conserven información del futuro.

**Motivo**: Una presentación nueva debe respetar el retroceso y la independencia de las consultas.
**Prueba independiente**: Observar enemigos, retroceder y consultar instantes anteriores; continuar la partida y compararla con la ejecución equivalente de consola.

**Escenarios de aceptación**:

1. **AC-IG-015** — **Dado** un instante o número de acción válido, **cuando** se
   consulta historia, **entonces** aparece un panel claramente histórico con
   el resumen requerido por 004; cerrarlo vuelve a la partida presente sin
   cambiar tiempo, azar, log, acciones ni solicitudes. No se reutilizan recuerdos
   actuales para añadir enemigos al pasado. FR-IG-015.
2. **AC-IG-016** — **Dados** un pergamino y observaciones realizadas después del
   estado al que se vuelve, **cuando** se retrocede, **entonces** se restauran el
   estado y conocimiento según las reglas vigentes, se descartan esas
   observaciones futuras y no quedan selecciones sobre objetivos inexistentes.
   Los recuerdos previos siguen siendo recuerdos, no posiciones remotas actuales.
   FR-IG-009, FR-IG-016.

### Historia 6 — Guardar y cambiar de interfaz (Prioridad: P1)

Como jugador, quiero guardar, cargar y conservar mis observaciones sin perder
compatibilidad con las partidas existentes.

**Motivo**: La capacidad adicional no debe inutilizar el trabajo de Parte II.
**Prueba independiente**: Cargar un guardado anterior, guardar desde la interfaz gráfica y continuar también desde consola.

**Escenarios de aceptación**:

1. **AC-IG-017** — **Dado** un guardado v6 anterior o producido por la nueva
   interfaz, **cuando** se carga en una interfaz compatible, **entonces** conserva
   el estado de juego, K, historia y continuación. Un archivo incompatible se
   rechaza con el diagnóstico existente. FR-IG-017.
2. **AC-IG-018** — **Dados** recuerdos gráficos asociados a una partida,
   **cuando** se guarda y carga, **entonces** se recuperan solo los compatibles
   con esa sesión. Si faltan o no corresponden, la partida válida sigue cargando
   y las salas sin observaciones se indican como tales; no se reconstruyen
   enemigos recordados leyendo posiciones remotas reales. FR-IG-007, FR-IG-018.
3. **AC-IG-019** — **Dada** una partida gráfica con grabación activa,
   **cuando** se realizan acciones y consultas, **entonces** el registro conserva
   las órdenes de juego necesarias para replay y no incluye redibujados ni
   clics de navegación. Cargar durante grabación conserva el rechazo existente.
   FR-IG-014, FR-IG-017.

### Historia 7 — Usar una ventana completa y conservar los otros modos (Prioridad: P2)

Como jugador, quiero mensajes legibles, ayuda y resultados, y poder seguir
utilizando los modos actuales cuando no necesito gráficos.

**Motivo**: Completa el uso de escritorio y evita hacer obligatoria la nueva dependencia.
**Prueba independiente**: Redimensionar y cerrar la ventana, finalizar una partida y ejecutar los modos actuales sin entorno gráfico.

**Escenarios de aceptación**:

1. **AC-IG-020** — **Dado** un mapa que no cabe completo o una ventana de al menos
   1024 × 768, **cuando** se navega o redimensiona, **entonces** todas las salas
   conocidas y acciones siguen siendo alcanzables; hay leyenda de niebla,
   recuerdos y sprites, estado del jugador y mensajes legibles. FR-IG-004, FR-IG-021.
2. **AC-IG-021** — **Dadas** victoria o derrota, **cuando** termina la partida,
   **entonces** se muestran resultado y puntaje sin aceptar más turnos ni
   registrar el resultado dos veces; se puede volver al inicio y consultar los
   puntajes locales con sus criterios existentes. Cerrar la ventana equivale
   a salir y no guarda automáticamente. FR-IG-019, FR-IG-022.
3. **AC-IG-022** — **Dada** una instalación sin la dependencia o pantalla gráfica,
   **cuando** se ejecutan consola, listar, verificar, replay, puntajes o bench,
   **entonces** siguen disponibles sin abrir una ventana. Solicitar la interfaz
   gráfica sin sus requisitos produce una explicación de instalación o entorno.
   FR-IG-001, FR-IG-023.
4. **AC-IG-023** — **Dados** fallos de datos, red, presupuesto, capacidad o archivo,
   **cuando** se intenta una operación gráfica, **entonces** se muestra el error
   y se permite salir o volver al inicio; una carga fallida no sustituye la
   partida válida. Los reintentos respetan el presupuesto vigente. FR-IG-020, FR-IG-024.

### Casos límite

- Varias entidades en una sala: representar cantidad y permitir distinguir objetivos sin superponer controles inaccesibles.
- Sala explorada por antorcha sin contenido observado: distinguir «sin observación» de «sin enemigos».
- Enemigos muertos o movidos lejos: el recuerdo no se actualiza remotamente ni promete que la sala sea segura.
- Mapas sin coordenadas espaciales, con ciclos o conexiones que no encajan en una cuadrícula física: la distribución es esquemática y las conexiones reales son explícitas.
- Objetivo que desaparece, inventario vacío/lleno y nombre repetido de sala: revalidar la selección y conservar los rechazos y desambiguación actuales.
- Redibujar, mover el mapa, perder el foco o dejar la ventana inactiva: no iniciar turnos nuevos ni ejecutar órdenes acumuladas. Una operación ya aceptada termina de forma segura; perder foco detiene la programación del siguiente paso de viaje.
- Recuerdos visuales de otro guardado o de una rama temporal revertida: no mostrarlos como observaciones válidas.
- Sin conexión y sin paquete offline válido: informar la falta de datos; no inventar una cripta de reemplazo.

## Requisitos

### Requisitos funcionales

- **FR-IG-001**: Permitir seleccionar explícitamente la interfaz gráfica y conservar la entrada actual de consola. AC-IG-001/022.
- **FR-IG-002**: Proporcionar inicio, elección de cripta, nombre, semilla, origen de datos y carga desde la ventana, sin requerir órdenes de consola durante el juego. AC-IG-001/003.
- **FR-IG-003**: Conservar la verificación de resolubilidad y la elección explícita de forzar; no omitir errores de datos. AC-IG-002.
- **FR-IG-004**: Presentar salas como cuadritos de un mapa 2D esquemático, ubicación actual y conexiones conocidas; permitir recorrer el mapa completo sin inferir salidas por proximidad visual. AC-IG-004/005/020.
- **FR-IG-005**: Distinguir desconocidas, avistadas y exploradas, respetando observaciones de puertas, adyacencia y antorcha del spec 002. Ningún gráfico ni panel puede revelar datos no conocidos. AC-IG-004/005/008.
- **FR-IG-006**: Representar los enemigos observables de la sala actual mediante sprites y cantidades actualizados tras las acciones. AC-IG-006.
- **FR-IG-007**: Representar fuera de la sala actual únicamente los últimos enemigos observados, identificados como recuerdo; actualizar al observar presencialmente y distinguir ausencia de observación de sala observada vacía. AC-IG-007/008/018.
- **FR-IG-008**: Ofrecer controles para todas las acciones, consultas y operaciones de inventario enumeradas en AC-IG-009. Ninguna requiere escribir el comando equivalente. AC-IG-009.
- **FR-IG-009**: Permitir identificar y seleccionar objetivos, objetos, direcciones y destinos; revalidar la selección al cambiar el estado sin actuar sobre otro objetivo automáticamente. AC-IG-006/009/011/016.
- **FR-IG-010**: Traducir cada activación deliberada aceptada a una operación y como máximo un turno de juego; seleccionar un objeto puede emitir su navegación canónica sin turnos. No generar repeticiones de turno por mantener una tecla o acumular acciones durante una operación. Solo se admite la única intención interruptora de viaje de AC-IG-013, sin aceptar activaciones adicionales mientras espera el final del paso. AC-IG-010/013.
- **FR-IG-011**: Conservar el juego por turnos: el tiempo real, los gráficos y la navegación no avanzan el reloj virtual; las acciones aceptadas pagan los costos actuales y las rechazadas no pagan tiempo ni azar. AC-IG-010/011.
- **FR-IG-012**: Permitir viajar a un destino explorado con las mismas rutas, costos, recalculado y paradas del spec 002. AC-IG-012/014.
- **FR-IG-013**: Permitir detener un viaje entre pasos y ejecutar una orden interruptora una sola vez, sin reanudación automática. AC-IG-013.
- **FR-IG-014**: Producir las mismas órdenes, acciones y efectos de juego que la consola, sin registrar navegación gráfica ni alterar las reglas de grabación/replay. AC-IG-011/012/014/019.
- **FR-IG-015**: Ofrecer consultas históricas por instante y por acción, claramente separadas del presente, sin mutar la partida ni añadir información visual futura. AC-IG-015.
- **FR-IG-016**: Descartar recuerdos y selecciones procedentes del futuro tras retroceder, conservando la semántica del pergamino. AC-IG-016.
- **FR-IG-017**: Conservar la compatibilidad del estado de juego v6, K, historia y continuación entre consola e interfaz gráfica; mantener rechazos de versiones incompatibles y de carga con grabación activa. AC-IG-017/019.
- **FR-IG-018**: Recuperar observaciones visuales compatibles al guardar/cargar, sin hacerlas obligatorias para cargar un guardado de juego válido; si faltan o no corresponden, indicar que no hay observación disponible. AC-IG-018.
- **FR-IG-019**: Mostrar el final de partida y los puntajes sin duplicar registros ni permitir nuevos turnos; ofrecer regreso al inicio y consulta de puntajes. AC-IG-021.
- **FR-IG-020**: Conservar origen externo, modo offline, límites de solicitudes y caché y errores de datos de la versión actual. AC-IG-003/023.
- **FR-IG-021**: Mostrar vida, ataque, defensa, efectos, reloj, inventario, mensajes, ayuda y leyenda; los controles y estados deben ser legibles y accesibles al recorrer o redimensionar la ventana, sin depender solo del color. AC-IG-006/020.
- **FR-IG-022**: Cerrar la ventana como una salida explícita, sin guardar automáticamente ni ejecutar órdenes pendientes. AC-IG-021.
- **FR-IG-023**: Mantener los modos sin interfaz y la consola utilizables sin instalar ni inicializar la presentación gráfica. AC-IG-022.
- **FR-IG-024**: Presentar fallos operativos en la ventana sin sustituir una partida válida por una carga fallida ni ejecutar reintentos fuera del presupuesto. AC-IG-023.

### Requisitos de compatibilidad y verificación

- **PR-IG-001**: La implementación debe conservar las 759 pruebas existentes y aportar evidencia por cada escenario AC-IG. La calidad del spec no acredita pruebas de la interfaz todavía inexistente.
- **PR-IG-002**: Secuencias equivalentes de consola y gráficos con mismos datos y semilla deben producir idéntico estado de juego, reloj, azar, historia y continuación. Los recuerdos gráficos no cambian las decisiones del motor.
- **PR-IG-003**: Se medirán por separado presentación y procesamiento de acciones; EX-01 sigue declarada y no se usará esta capacidad para afirmar cumplidos los límites originales de 20/50 ms.
- **PR-IG-004**: Las estructuras y el almacenamiento de recuerdos siguen las decisiones aprobadas y registradas en el plan. Cualquier estructura nueva no cubierta requiere alternativas y elección explícita del usuario conforme a AGENTS.md. La memoria visual no autoriza una segunda simulación.

### Entidades principales

- **Partida**: Estado de juego y reglas existentes; la interfaz presenta ese estado y solicita acciones.
- **Sala representada**: Identidad, grado de conocimiento, conexiones conocidas y condición de sala actual. Su posición dibujada no es una regla del mundo.
- **Observación de enemigos**: Sala e instante de la última observación presencial, tipos y cantidades observados; se distingue del contenido remoto actual y de la falta de observación.
- **Objetivo seleccionado**: Enemigo, objeto, salida o destino elegido para una operación y revalidado antes de actuar.
- **Consulta histórica**: Resumen de un instante o acción, separado del presente y de sus recuerdos.
- **Sesión visual**: Ventana y paneles de inicio, juego, inventario, historia, ayuda y resultados; no constituye otra partida.

## Criterios de éxito

### Resultados medibles

- **SC-IG-001**: Se completan los 23 escenarios AC-IG con evidencia automatizada o reproducible, además de mantener aprobada la regresión existente.
- **SC-IG-002**: El 100 % de las operaciones enumeradas en AC-IG-009 se ejecutan desde la ventana sin introducir órdenes de consola durante la partida.
- **SC-IG-003**: En recorridos equivalentes que incluyan combate, puertas, inventario, viaje, pergamino, guardado y consulta histórica, el estado de juego y su continuación coinciden entre ambas interfaces.
- **SC-IG-004**: En los escenarios de niebla, antorcha, movimiento remoto y retroceso no se presenta ninguna observación de enemigos no obtenida o perteneciente al futuro.
- **SC-IG-005**: Dejar la ventana inactiva durante 60 segundos, redibujar 300 veces y navegar paneles sin cambiar el cursor de inventario produce cero turnos, cero cambios de reloj/azar y cero órdenes registradas. Una activación de juego aceptada ejecuta como máximo un turno. La selección deliberada de inventario conserva sus órdenes canónicas de navegación para replay, siempre sin turnos.
- **SC-IG-006**: Un mapa de 300 salas conocidas permite alcanzar visualmente todas sus salas y controles en una ventana de al menos 1024 × 768, con distinción legible entre estado actual, recuerdo y ausencia de observación.
- **SC-IG-007**: Los guardados v6 anteriores y las partidas gráficas conservan el estado de juego al cargar; la falta de recuerdos visuales no impide continuar. Los modos de consola y sin vista funcionan en una instalación sin gráficos.

## Supuestos, dependencias y alcance

- Destino inicial: escritorio Windows, teclado y ratón; portabilidad adicional se evaluará después. Los botones ofrecen acceso a las acciones; los atajos concretos se definirán en el plan.
- Se conservan todas las reglas de las cuatro capacidades actuales, incluido el conocimiento ampliado por antorcha. «Adyacente» no autoriza mostrar su contenido.
- Los sprites de esta primera versión indican tipos y cantidades de enemigos; no se exige animación, arte final ni una posición física dentro de cada sala. Deben incluir una leyenda; cualquier recurso distribuido deberá contar con permiso de uso documentado.
- El mapa es una representación esquemática: los datos actuales no garantizan coordenadas ni una geometría física continua. No se agregan reglas de colisiones, orientación o desplazamiento dentro de las salas.
- La memoria de enemigos es una nueva observación para presentar información, elegida por el usuario. No revela salud remota actual, no actualiza cazadores fuera de observación y no reemplaza el conocimiento existente.
- Se mantienen los guardados de juego compatibles con v6. El mecanismo aprobado para conservar y validar recuerdos opcionales se define en el contrato de persistencia del plan; no se añade un formato nuevo de juego.
- Los datos de las criptas siguen requiriendo el servicio o un paquete offline compatible. No se incluye un paquete oficial que el proyecto no distribuye actualmente.
- Fuera de alcance: multijugador, combate en tiempo real, navegación física por píxeles, editor de criptas, 3D, audio obligatorio, animaciones obligatorias y empaquetado como ejecutable instalable.
- La rama parte de la versión actual con EX-01. El porcentaje de Parte II no mide esta ampliación; crear o aprobar este spec no significa que Pygame esté implementado.
- La planificación y las tres elecciones técnicas están documentadas; tareas, análisis de consistencia e implementación constituyen las fases siguientes. Esta entrega no modifica dependencias instalables ni código de producción.
