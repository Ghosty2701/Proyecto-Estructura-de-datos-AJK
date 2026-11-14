# Capacidad 006 — Salas y combate visual

Ampliación personal en `005-interfaz-pygame`, separada de la evaluación y de `main`.
Elecciones confirmadas: sala desde arriba, minimapa, combate en la misma habitación,
vectores por sala y una animación activa. Tras probarla, el usuario sustituyó
ilustración por pixel art de RPG de 16 bits y pidió comandos compactos.

**Avance estimado: ~90 %**. Funcionalidad integrada y verificada automáticamente;
revisión interactiva de escritorio y auditoría final pendientes. El porcentaje
de la base 005 es independiente y no se usa como avance de esta escena.

## Implementado y probado

- Arte original local de 16 bits: habitación, jugador/familias, ocho especies y
  un símbolo neutral para criaturas desconocidas, doce elementos y
  ocho puertas N/S/E/O abiertas/cerradas, con alfa y escalado de vecinos próximos.
- Personaje y objetivos seleccionables, puertas existentes por dirección y costo,
  minimapa ampliable, HUD y controles ordinarios sin órdenes de consola.
- Combate en la sala: corte, daño/curación, derrota y transiciones breves. Hechos
  confirmados, sin inferir muerte por desaparición ni leer vida remota posterior.
- Una animación activa; espacio la salta sin esperar otro turno. Modos normal,
  reducida y sin efectos. Foco, carga y retroceso invalidan efectos anteriores.
- Páginas de 12 enemigos y 8 objetos, selección vigente, inventario, historia,
  recuerdos, guardado v6, viaje y resultados conservados.
- De 30 botones en la habitación anterior a cuatro o cinco comandos habituales;
  máximo seis por contexto. Persistencia/historia/ajustes agrupados en Menú.
- Especie elegida por nombre observable, no por conducta: rata gigante,
  sabueso óseo y espectro tienen arte correspondiente. Desconocidos usan símbolo
  neutral y conservan nombre; no se promete arte único para todo nombre futuro.
- Inicio/nueva/carga diferenciados, cripta resaltada y resumida, búsqueda de `.bin`
  y confirmación antes de cargar; errores recuperables y selector nativo opcional.
- Inventario explica orden ascendente, muestra peso/valor y resalta criterio;
  botones con bisel, sombra, remates y brillo de cursor/selección.
- Barra de actividad indeterminada y tiempo real durante operaciones lentas,
  con descripción y cierre seguro; nunca porcentaje ficticio ni turnos extra.
- **858 pruebas con Pygame** y **819 sin Pygame**, con cuatro módulos gráficos
  omitidos en este último entorno. Matriz con lector real `main@6107b98` incluida.
- 300 redibujados durante **60,582 s reales** sin cambiar juego, azar ni órdenes.

Evidencia actual: [regresión y claridad](../../documentacion/evidencia/claridad_revision.md),
[mediciones](../../documentacion/evidencia/escena_mediciones.md),
[render jugable](../../documentacion/evidencia/retro_jugable.png) y
[revisión visual y límites](../../documentacion/evidencia/retro_revision_visual.md).
Las mediciones enlazadas corresponden a la presentación anterior a 16 bits;
no se presentan como una medición nueva del rediseño.

## Pendientes reales

T020: revisión interactiva nativa completa. Se observó la ventana inicial de
1280 × 800, pero un aviso de actividad de usuario y una captura posterior ajena
al objetivo impidieron seguir operando con seguridad. No se aprobaron teclado,
foco, resize y recorrido completo de escritorio por esos intentos.

T023 y T024: documentación actualizada parcialmente y auditoría final todavía
condicionadas a T020. Las casillas de [tareas](tasks.md) reflejan estas dependencias.
No se fusionó con `main`; EX-01 no se considera resuelta.

## Arte y SDD

[Spec](spec.md) (21 FR, 23 AC y 10 SC), [plan](plan.md), [investigación](research.md),
[modelo](data-model.md), [contrato](contracts/escena-animaciones.md) y
[guía](quickstart.md). Checklist de calidad 16/16. El análisis previo revisó
20 requisitos y 15 escenarios con 24 tareas y sin bloqueos críticos/altos.
La revisión de estilo incorpora T025–T032, FR-EV-015/016 y SC-EV-007/008;
la nueva cobertura documental se comprobó sin introducir estructuras nuevas.
La revisión de claridad incorpora T033–T041, FR-EV-017–021 y AC-EV-018–023;
cobertura de todos los identificadores en tareas, sin estructuras nuevas.

La [referencia conceptual](propuesta-visual.md) precedió al código. El juego usa
recursos separados en `vista/pygame_ui/assets/`; prompts y procedencia están
en su README. La imagen conceptual no se utiliza como fondo jugable.
