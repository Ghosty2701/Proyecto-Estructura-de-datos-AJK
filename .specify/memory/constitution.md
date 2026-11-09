# Constitución de Cripta — Parte II

## Principios fundamentales

### I. Estructuras de datos implementadas manualmente

Las estructuras de los problemas evaluados se implementan a mano, incluidos los auxiliares
de las búsquedas. Se pueden reutilizar estructuras propias de P1 si cumplen las propiedades
requeridas con la carga nueva. Está prohibido usar `dict` como índice o caché o como
sustituto de una estructura evaluada; `set` está prohibido en las mismas condiciones.
Para esos problemas tampoco se permiten `heapq`, `bisect`, `collections` (`deque`,
`OrderedDict`, `defaultdict`, `Counter`), `networkx` ni bibliotecas de grafos o búsqueda
de rutas. Las dependencias propuestas por agentes se revisan con estas restricciones;
las herramientas de proceso no autorizan dependencias prohibidas en el código entregado.

Se conserva la implementación manual de los ordenamientos evaluados: al menos dos
algoritmos con características distintas y selección según propiedades medibles, sin
`sorted()` ni `list.sort()`. La constitución no impone una estructura o algoritmo concreto:
la elección y sus alternativas pertenecen al plan y al Documento de Decisiones.

**Fundamento:** P2 §§2.3, 5.1 y 6.2; P1 §7, conservado por P2; Documento de Decisiones,
sección «Problema 8 — Ordenamiento dinámico».

### II. Determinismo de la simulación

La misma cripta, semilla y secuencia de acciones, con versiones compatibles de los datos,
producen la misma partida observable. Los desempates y la utilización del azar deben
conservar este resultado, incluido replay. Las esperas de red no avanzan el reloj virtual.
Las criptas sintéticas de `--bench` también son deterministas por semilla.

Reutilizar resultados de búsquedas solo es válido si la decisión observable coincide con
un cálculo desde cero en ese instante. Si la reconstrucción histórica utiliza
re-simulación, el punto de control incluye el estado de `random.Random`.

**Fundamento:** P2 §§2.3, 3, 3.2, 3.6 y 6.3; documentación heredada de motor, precarga y replay.

### III. Separación MVC y modos sin vista

El modelo contiene las reglas y estructuras y no depende de la vista ni de HTTP. El
controlador coordina las acciones; la vista presenta información; los adaptadores atienden
red y persistencia. Se conserva la separación existente entre `modelo/`, `controlador/`,
`vista/` y `adaptadores/`, sin impedir reorganizaciones justificadas que respeten MVC.

`--replay`, `--bench` y `--verificar` no instancian la vista. La reproducción con `--hasta`
imprime el resumen requerido sin vista. Imprimir resultados de estos modos no equivale a
crear la interfaz de juego. Las mediciones de procesamiento excluyen red y renderizado.

La infraestructura puede consultar el esqueleto completo; lo mostrado al jugador y las
rutas de «ir a» se derivan exclusivamente de su conocimiento del mapa.

**Fundamento:** P2 §§2.3, 3.3, 3.5, 3.6 y 6.1; README y apertura del Documento de Decisiones.

### IV. Datos de criptas externos al código

Ningún dato de una cripta concreta se escribe en el código de la aplicación: topología,
costos particulares, ubicación de llaves, entidades y resolubilidad se obtienen del
servicio o de datos offline compatibles. El programa debe funcionar con una cripta nueva,
sin casos especiales por identificador ni respuestas precalculadas.

Los valores predeterminados definidos por las reglas, como costo 100 cuando falta el
campo, son reglas generales. Las cargas sintéticas de pruebas y `--bench` no sustituyen
los datos externos de una partida real.

**Fundamento:** P2 §§2.3, 3.1, 4.3 y 6.3; README, ejecución y modo offline.

### V. Presupuesto de solicitudes y validez por versión

Toda solicitud al servicio, incluidos reintentos y la consulta de ubicación de llaves,
cuenta dentro de `presupuesto_solicitudes`; nunca se supera ese presupuesto. La precarga,
la persistencia y la reutilización de datos deben respetarlo. La caché conserva el tope
de fichas residentes configurado mediante `--cache-size`.

La reutilización de datos persistidos valida las versiones correspondientes: cripta para
esqueleto, costos y ubicación de llaves; catálogo para fichas de entidades. Los datos de
P1 invalidados por versiones nuevas se descartan mediante esa validación, sin exigir
borrado manual. Replay comprueba identidad y versiones para informar incompatibilidades
en lugar de prometer una reproducción fiel con datos distintos.

Los cambios del formato binario detectan guardados incompatibles de P1 o los migran
explícitamente; nunca los cargan en silencio. Guardar y cargar debe conservar el estado
añadido por P2, incluida la línea de tiempo completa.

**Fundamento:** P2 §§2.3, 3.6, 4.2–4.3, 6.1 y apéndices A/B; README y decisiones heredadas
de caché, guardado y replay.

### VI. Decisiones de rendimiento respaldadas por mediciones

Toda afirmación de rendimiento se respalda con `--bench`. Cada decisión de estructura
documenta problema, alternativas, decisión, complejidad, evidencia empírica y límites
conocidos. El Documento de Decisiones enlaza la especificación y el plan, recoge las
mediciones finales y explica cualquier cambio respecto de lo planificado.

El benchmark incluye las comparaciones de P2 §6.3: uno y muchos cazadores, rangos pequeños
y grandes, cálculo compartido e individual; reutilización frente a recálculo con puertas
estables e inestables; mapa conocido e «ir a»; resolubilidad incremental frente a recorrido
repetido por llave; línea de tiempo con al menos tres valores de K y sin puntos de control;
y estructuras de P1 bajo la carga nueva. El K predeterminado se justifica con mediciones.

Se verifican en el equipo local, sin red ni renderizado, los límites de P2 §6.1: ciclo de
eventos de 20 ms con decenas de cazadores, resolubilidad de 200 ms en la cripta publicada
más grande, consulta histórica de 50 ms con al menos 5 000 acciones y K predeterminado, y
paso de «ir a» de 5 ms con el mapa conocido completo de la cripta de referencia. Cualquier
ajuste requiere la enmienda comunicada del enunciado. Una medición histórica de P1 no
demuestra cumplimiento bajo las cargas nuevas.

**Fundamento:** P2 §§2.3, 5.1–5.6, 6.1, 6.3 y 7.1; documentación de mediciones de P1.

### VII. Especificaciones anteriores a la implementación

Cada capacidad nueva sigue el flujo de spec-kit: especificar, aclarar, planificar,
descomponer en tareas, analizar consistencia e implementar. El historial de Git debe
mostrar la especificación confirmada antes del código que la implementa. Si cambia una
regla durante el desarrollo, primero se corrige y confirma la especificación y después
el código, en confirmaciones separadas.

`spec.md` contiene reglas del juego, historias, escenarios y requisitos funcionales y de
rendimiento numerados; no contiene nombres de estructuras, clases o módulos. `plan.md`
contiene estructuras elegidas, alternativas, complejidad, módulos y mediciones previstas;
no inventa reglas. `tasks.md` contiene tareas verificables y sus dependencias, cada una
asociada a requisitos. Las especificaciones entregadas deben coincidir con el programa.

**Fundamento:** P2 §§1, 2.2, 2.4 y 2.6.

### VIII. Trazabilidad verificable de extremo a extremo

Cada requisito funcional tiene un identificador estable. Cada caso del apéndice B figura
como escenario de aceptación en alguna especificación. Cada escenario tiene al menos una
prueba automatizada o un `partida.log` que lo ejercita; las pruebas citan el identificador
del requisito. Cada tarea referencia los requisitos que atiende.

Debe poder recorrerse la relación requisito → escenario → tarea → código → prueba o log
de reproducción. Los artefactos y sus referencias deben permitir mostrar esta cadena en
la defensa sin depender de la memoria de quien implementó la capacidad.

**Fundamento:** P2 §§2.5 y 7.4; apéndice B.

### IX. Bitácora de prompts y comandos de spec-kit

Los prompts utilizados se registran en `documentacion/PROMPTS_LLM.md`, incluida cada
invocación de spec-kit con texto propio. Se conserva el formato existente por integrante,
con entradas numeradas, texto del prompt y fecha; los metadatos desconocidos se indican
como no registrados y no se inventan. La asistencia de un agente no exime al grupo de
revisar restricciones, consistencia ni resultados.

**Fundamento:** P2 §2.6, que remite a P1 §10.3; formato de la bitácora existente.

## Alcance y fuentes

Esta constitución gobierna la continuación del repositorio de P1 en Python 3.11 o superior.
La fuente normativa es [Cripta - Parte II.pdf](../../Cripta%20-%20Parte%20II.pdf), en adelante
P2. Todo P1 sigue vigente salvo modificación explícita de P2. El README y el
[Documento de Decisiones](../../documentacion/DOCUMENTO_DECISIONES.md) aportan contexto de
P1, pero no sustituyen al enunciado ni prevalecen sobre él.

El enunciado original de P1 no está en el repositorio revisado. Las reglas heredadas aquí
recogidas se apoyan en las remisiones de P2 y en la documentación disponible; no se
reconstruyen excepciones desconocidas de P1 §7 o metadatos ausentes de P1 §10.3.

Se reconocen las modificaciones expresas de P2: el cazador realiza búsqueda de rutas,
mientras el rastreador conserva su comportamiento local; la línea de tiempo permite
puntos de control completos con la frecuencia limitada por K. Esto no autoriza copiar
el estado en cada acción fuera de los límites de P2 §3.6. El pergamino sigue limitado a
cinco acciones y es independiente de la consulta histórica. Las demás reglas heredadas
de reloj, inventario, efectos, retroceso, mensajes, ordenamientos y persistencia se
conservan donde P2 no las modifique.

La constitución fija restricciones y proceso, sin resolver el diseño de las cuatro
capacidades. No prescribe algoritmos ni convierte las decisiones históricas del equipo
en requisitos inmutables.

## Flujo de trabajo y revisión

Antes de implementar una capacidad, el grupo comprueba que especificación, plan y tareas
cumplen estos principios. Los agentes consultan la constitución en cada fase. Un plan o
una tarea contradictorios se corrigen antes de ejecutar su implementación.

Las cuatro capacidades requieren como mínimo sus respectivas especificaciones: terreno
y cazador, niebla de guerra con «ir a», resolubilidad y línea de tiempo. Dividir una
capacidad en varias especificaciones requiere justificación (P2 §2.2). Este documento
no genera esos artefactos ni adelanta su implementación.

Los artefactos `.specify/`, los comandos del agente y `specs/<NNN-capacidad>/` se versionan.
Todo el grupo usa una misma versión concreta de spec-kit; el README registra esa versión,
el agente, los comandos nuevos y cómo ejecutar las pruebas de aceptación (P2 §§2.1 y 7.2).
La evidencia de rendimiento se incorpora al Documento de Decisiones; la evidencia de
escenarios se conserva como pruebas o logs de reproducción.

Las plantillas y comandos dependientes leen esta constitución al ejecutarse. La revisión
de un plan comprueba su sección `Constitution Check`; la revisión de tareas comprueba
referencias a requisitos y cobertura de escenarios, aunque una plantilla genérica
presente las pruebas como opcionales. P2 §2.5 exige evidencia por escenario, que puede ser
una prueba automatizada o un log de reproducción.

## Gobernanza

El enunciado y sus enmiendas prevalecen sobre esta constitución; esta prevalece sobre los
planes, tareas y sugerencias del agente. Las decisiones técnicas se pueden revisar con
evidencia sin alterar las reglas del juego.

Toda enmienda a la constitución identifica la regla afectada, su motivo y la fuente que la
respalda; actualiza versión y fecha; y revisa el impacto sobre especificaciones, planes y
tareas existentes. El grupo verifica el cumplimiento en el análisis previo a implementar
y en la revisión de los cambios, incluida la coherencia de documentación y evidencia.

La versión sigue semántica MAJOR.MINOR.PATCH: MAJOR para eliminar o redefinir principios
de forma incompatible; MINOR para añadir principios o ampliar materialmente su alcance;
PATCH para aclaraciones sin cambio normativo. Esta versión 1.0.0 es la primera adopción:
la plantilla anterior no contenía principios ratificados ni una versión efectiva.

**Versión**: 1.0.0 | **Ratificación**: 2026-11-07 | **Última enmienda**: 2026-11-07
