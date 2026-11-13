# Capacidad 005 — Interfaz gráfica con Pygame

Esta rama prepara una ampliación del proyecto. **Contiene la especificación;
todavía no contiene una interfaz gráfica implementada.**

- Rama de trabajo: `005-interfaz-pygame`.
- Base publicada: `6107b98` de `main`, sin cambiar su estado de Parte II ni EX-01.
- [Especificación](spec.md): siete historias, 24 requisitos funcionales y 23 escenarios.
- [Revisión de calidad](checklists/requirements.md): 16/16 criterios revisados.
- Carpeta de trabajo local usada: `C:/Users/pipro/Downloads/Proyecto-Estructura-de-datos-AJK-pygame`.

## Avance exclusivo de Pygame

**Estimación inicial: ~10 %**, orientativa y pendiente de afinar con el plan.
Se completaron la especificación, las aclaraciones visuales y la revisión de
calidad. La implementación gráfica, sus pruebas y la validación visual todavía
no han comenzado; ese 10 % corresponde a la preparación, no a funciones gráficas
ya disponibles.

El siguiente paso es planificar la integración técnica. Esta ampliación es una
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
| Planificar (`$speckit-plan`) | Siguiente paso | Alternativas, decisiones aprobadas, arquitectura y contratos |
| Descomponer (`$speckit-tasks`) | Pendiente del plan | Tareas enlazadas a requisitos, escenarios y pruebas |
| Analizar (`$speckit-analyze`) | Pendiente de los artefactos anteriores | Revisión de consistencia y cobertura |
| Implementar (`$speckit-implement`) | No iniciada | Código, pruebas y validación visual por tareas |

El próximo comando es `$speckit-plan` trabajando en esta rama. Debe revisar
la integración de la vista, los turnos, los sprites y las observaciones
recordadas, con alternativas para cualquier estructura nueva. Según AGENTS.md,
una recomendación del agente no sustituye la elección del usuario.

No se introducen aquí dependencias, arte ni código gráfico. Los escenarios
nuevos se probarán al implementar; la revisión documental no los marca aprobados.
