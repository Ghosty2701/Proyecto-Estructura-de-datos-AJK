# Capacidad 005 — Interfaz gráfica con Pygame

Esta rama desarrolla una ampliación del proyecto. **Interfaz gráfica jugable con
las siete historias implementadas y aceptadas; 53/53 tareas (2026-11-14).**

Tras probarla, el usuario pidió que la escena principal represente habitaciones,
personaje y enemigos, con el mapa como apoyo. Esa evolución está en el
[spec 006](../006-salas-combate-visual/spec.md), ya implementado y probado
automáticamente y revisado en escritorio real (48/48 tareas). El porcentaje de
esta página describe el alcance original de 005.

- Rama de trabajo: `005-interfaz-pygame`.
- Base publicada: `6107b98` de `main`, sin cambiar su estado de Parte II ni EX-01.
- [Especificación](spec.md): siete historias, 24 requisitos funcionales y 23 escenarios.
- [Revisión de calidad](checklists/requirements.md): 16/16 criterios revisados.
- [Plan técnico completado](plan.md) y [decisiones investigadas](research.md): las tres elecciones del usuario están confirmadas.
- [Modelo de datos](data-model.md), contratos de [interfaz](contracts/interfaz-grafica.md) y [recuerdos v6](contracts/recuerdos-v6.md), y [guía de validación](quickstart.md).
- [53 tareas de implementación](tasks.md), ordenadas por las siete historias; 53/53 completadas y verificadas.
- Carpeta de trabajo local usada: `C:/Users/pipro/Downloads/Proyecto-Estructura-de-datos-AJK-pygame`.

## Avance exclusivo de Pygame

**Estimación actual: 100 % del alcance de 005**, orientativa. Especificación, aclaraciones,
planificación técnica, descomposición y análisis de consistencia completados:
estructuras elegidas, arquitectura, modelo de datos, contratos, guía y 53 tareas.
El análisis de solo lectura verificó cobertura prevista de 35/35 requisitos
construibles y 23/23 escenarios, sin bloqueos críticos/altos identificados.
Se verificaron en cargas temporales
la aceptación de una clave primitiva opcional en v6 y el recorrido base de cinco
retrocesos, incluido usar un pergamino desde el inventario.
Se implementaron dependencia opcional, fixtures, proyección inmutable, selección
validada, resultado compartido de órdenes y coordinador de propietario único.
US1 incorpora selector opcional, menú, listado, forzado y preparación candidata
compartida con consola. US2/US3 incorporan croquis, cámara, sprites originales,
memoria presencial y controles ordinarios con selección vigente de objetivos.
US4–US7 incorporan viaje por pasos e interrupción, historia separada, cinco deltas
reversibles, recuerdos opcionales v6, resultados únicos, puntajes y cierre con
cancelación de esperas HTTP. El lector congelado de `main` continúa y vuelve a
guardar partidas gráficas correctamente.
Regresión completa: **831 pruebas pasan con Pygame** y **813 sin Pygame**, con
un módulo gráfico omitido en ese segundo entorno; esa omisión no acredita la UI.
Salidas en [regresión](../../documentacion/evidencia/pygame_regresion.txt).
Las pruebas de ventana usan vídeo dummy y no acreditan legibilidad real.

T050–T053 cerradas el 2026-11-14: [mediciones separadas](../../documentacion/evidencia/pygame_mediciones.md),
[revisión visual real consolidada](../../documentacion/evidencia/pygame_revision_visual.md)
(el primer intento detenido con Esc se reemplazó por la revisión de escritorio de 006),
documentación y auditoría: 58/58 identificadores con tarea. Regresión vigente:
866 con Pygame y 819 sin Pygame. Esta ampliación es una
exigencia personal del usuario, independiente de la nota y del avance de Parte II.
En adelante se reporta únicamente su propio progreso. Integrada en `main` el
2026-11-14 con aprobación explícita del usuario, tras validar funcionamiento y compatibilidad.

## Qué se construirá

Mapa 2D con salas en cuadritos, sprites de enemigos, paneles y botones para
las acciones actuales. El juego sigue siendo por turnos. Las salas solo
avistadas no revelan contenido; fuera de la sala actual, los enemigos se
muestran como recuerdos de la última observación presencial, no como posiciones
remotas en tiempo real. Se conservan la antorcha, el viaje, el pergamino,
la historia y las partidas existentes.

## Cómo funciona la separación con Git

La capacidad se desarrolló en `005-interfaz-pygame` y se integró en `main` el
2026-11-14 mediante un merge sin fast-forward, con aprobación explícita del usuario.
La consola sigue siendo la interfaz predeterminada y la entrega de Parte II no cambia.

Para obtener una copia separada de esta rama:

```powershell
git clone --branch 005-interfaz-pygame --single-branch https://github.com/Ghosty2701/Proyecto-Estructura-de-datos-AJK.git Cripta-Pygame
```

El selector local `.specify/feature.json` apunta a `specs/005-interfaz-pygame`
en el entorno de trabajo creado. Spec-kit lo ignora en Git por ser un estado
local; el nombre de esta rama también permite detectar la capacidad al clonar.

## Flujo SDD con spec-kit 1.3.2

Se usa la instalación existente del repositorio, con sus habilidades de Codex,
plantillas compuestas y constitución. No se cambia de versión de spec-kit.

| Fase | Estado | Resultado |
|---|---|---|
| Especificar (`$speckit-specify`) | Completada | Comportamiento y escenarios en `spec.md` |
| Resolver ambigüedades | Decisiones visuales aclaradas durante la especificación | Mapa, niebla, turnos y recuerdos registrados |
| Planificar (`$speckit-plan`) | Completada | Elecciones confirmadas, arquitectura, modelo de datos, contratos y guía de validación |
| Descomponer (`$speckit-tasks`) | Completada | 53 tareas, siete historias, dependencias y cobertura completa prevista |
| Analizar (`$speckit-analyze`) | Completada, solo lectura | 35/35 requisitos y 23/23 escenarios con tareas; sin bloqueos críticos/altos identificados |
| Implementar (`$speckit-implement`) | Completada; 53/53 tareas | Siete historias implementadas, regresión 866/819, mediciones y revisión visual con límites |

La preparación SDD y la implementación están cerradas.
El usuario eligió explícitamente
D-IG-05/06/07: índice propio con vectores y cambios por turno, datos visuales
opcionales dentro del `.bin` y croquis por direcciones. No quedan decisiones
de diseño pendientes para descomponer en tareas. Cualquier estructura nueva
no cubierta por estas elecciones seguirá requiriendo alternativas y elección
del usuario según AGENTS.md.

Los escenarios nuevos se probarán al implementar; la revisión documental no
los marca aprobados por sí sola. Las casillas solo se completan con verificación;
el estado vigente de cada tarea está en `tasks.md`.
