# Capacidad 006 — Salas y combate visual

Ampliación personal en `005-interfaz-pygame`, separada de la evaluación y de `main`.
Elecciones confirmadas: sala desde arriba, minimapa, combate en la misma habitación,
ilustración 2D de fantasía oscura, vectores por sala y una animación activa.

**Avance estimado: ~85 %**. Funcionalidad integrada y verificada automáticamente;
revisión interactiva de escritorio y auditoría final pendientes. El porcentaje
de la base 005 es independiente y no se usa como avance de esta escena.

## Implementado y probado

- Arte original local: habitación, seis personajes y doce elementos; atlas con alfa.
- Personaje y objetivos seleccionables, puertas existentes por dirección y costo,
  minimapa ampliable, HUD y controles ordinarios sin órdenes de consola.
- Combate en la sala: corte, daño/curación, derrota y transiciones breves. Hechos
  confirmados, sin inferir muerte por desaparición ni leer vida remota posterior.
- Una animación activa; espacio la salta sin esperar otro turno. Modos normal,
  reducida y sin efectos. Foco, carga y retroceso invalidan efectos anteriores.
- Páginas de 12 enemigos y 8 objetos, selección vigente, inventario, historia,
  recuerdos, guardado v6, viaje y resultados conservados.
- **845 pruebas con Pygame** y **819 sin Pygame**, con dos módulos gráficos
  omitidos en este último entorno. Matriz con lector real `main@6107b98` incluida.
- 300 redibujados durante **60,582 s reales** sin cambiar juego, azar ni órdenes.

Evidencia: [regresión](../../documentacion/evidencia/escena_regresion.txt),
[mediciones](../../documentacion/evidencia/escena_mediciones.md),
[render jugable](../../documentacion/evidencia/escena_jugable.png) y
[revisión visual y límites](../../documentacion/evidencia/escena_revision_visual.md).

## Pendientes reales

T020: revisión interactiva nativa completa. Se observó la ventana inicial de
1280 × 800, pero un aviso de actividad de usuario y una captura posterior ajena
al objetivo impidieron seguir operando con seguridad. No se aprobaron teclado,
foco, resize y recorrido completo de escritorio por esos intentos.

T023 y T024: documentación actualizada parcialmente y auditoría final todavía
condicionadas a T020. Las casillas de [tareas](tasks.md) reflejan estas dependencias.
No se fusionó con `main`; EX-01 no se considera resuelta.

## Arte y SDD

[Spec](spec.md), [plan](plan.md), [investigación](research.md),
[modelo](data-model.md), [contrato](contracts/escena-animaciones.md) y
[guía](quickstart.md). Checklist de calidad 16/16. El análisis previo revisó
20 requisitos y 15 escenarios con 24 tareas y sin bloqueos críticos/altos.

La [referencia conceptual](propuesta-visual.md) precedió al código. El juego usa
recursos separados en `vista/pygame_ui/assets/`; prompts y procedencia están
en su README. La imagen conceptual no se utiliza como fondo jugable.
