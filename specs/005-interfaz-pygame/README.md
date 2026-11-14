# Capacidad 005 — Interfaz gráfica con Pygame

Esta rama prepara una ampliación del proyecto. **Contiene la especificación;
todavía no contiene una interfaz gráfica implementada.**

- Rama de trabajo: `005-interfaz-pygame`.
- Base publicada: `6107b98` de `main`, sin cambiar su estado de Parte II ni EX-01.
- [Especificación](spec.md): siete historias, 24 requisitos funcionales y 23 escenarios.
- [Revisión de calidad](checklists/requirements.md): 16/16 criterios revisados.
- [Plan técnico completado](plan.md) y [decisiones investigadas](research.md): las tres elecciones del usuario están confirmadas.
- [Modelo de datos](data-model.md), contratos de [interfaz](contracts/interfaz-grafica.md) y [recuerdos v6](contracts/recuerdos-v6.md), y [guía de validación](quickstart.md).
- [53 tareas de implementación](tasks.md), ordenadas por las siete historias, con dependencias y matriz de cobertura; todas pendientes.
- Carpeta de trabajo local usada: `C:/Users/pipro/Downloads/Proyecto-Estructura-de-datos-AJK-pygame`.

## Avance exclusivo de Pygame

**Estimación actual: ~30 %**, orientativa. Especificación, aclaraciones,
planificación técnica, descomposición y análisis de consistencia completados:
estructuras elegidas, arquitectura, modelo de datos, contratos, guía y 53 tareas.
El análisis de solo lectura verificó cobertura prevista de 35/35 requisitos
construibles y 23/23 escenarios, sin bloqueos críticos/altos identificados.
Se verificaron en cargas temporales
la aceptación de una clave primitiva opcional en v6 y el recorrido base de cinco
retrocesos, incluido usar un pergamino desde el inventario.
La implementación gráfica, sus pruebas y la validación visual todavía no han
comenzado; el porcentaje corresponde a preparación, no a funciones disponibles.

El siguiente paso es `$speckit-implement`, comenzando por T001 y los fundamentos
compartidos. El primer MVP jugable incluye US1, US2 y US3. Esta ampliación es una
exigencia personal del usuario, independiente de la nota y del avance de Parte II.
En adelante se reporta únicamente su propio progreso. La integración en `main`
se evaluará cuando funcione y se haya validado la compatibilidad.

## Qué se construirá

Mapa 2D con salas en cuadritos, sprites de enemigos, paneles y botones para
las acciones actuales. El juego sigue siendo por turnos. Las salas solo
avistadas no revelan contenido; fuera de la sala actual, los enemigos se
muestran como recuerdos de la última observación presencial, no como posiciones
remotas en tiempo real. Se conservan la antorcha, el viaje, el pergamino,
la historia y las partidas existentes.

## Cómo funciona la separación con Git

`main` conserva la entrega actual. Los commits de esta capacidad se publican
solo en `005-interfaz-pygame`; no se incorporan automáticamente a `main`.
La integración futura requerirá una decisión explícita del usuario.

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
| Implementar (`$speckit-implement`) | No iniciada | Código, pruebas y validación visual por tareas |

La preparación SDD está cerrada y la implementación todavía no ha comenzado.
El usuario eligió explícitamente
D-IG-05/06/07: índice propio con vectores y cambios por turno, datos visuales
opcionales dentro del `.bin` y croquis por direcciones. No quedan decisiones
de diseño pendientes para descomponer en tareas. Cualquier estructura nueva
no cubierta por estas elecciones seguirá requiriendo alternativas y elección
del usuario según AGENTS.md.

Los escenarios nuevos se probarán al implementar; la revisión documental no
los marca aprobados y todas las casillas T001–T053 permanecen sin completar.
