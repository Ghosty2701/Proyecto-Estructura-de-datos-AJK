# Capacidad 006 — Salas y combate visual

Evolución solicitada el 2026-11-14 después de probar la interfaz de mapa de 005.
Se mantiene la rama `005-interfaz-pygame`; `main` continúa independiente.

La propuesta lleva la experiencia principal a una habitación con personaje,
enemigos, objetos y puertas. El mapa pasa a ser secundario. El combate mantiene
las reglas actuales y utiliza sprites y respuesta visual a las acciones.

- [Spec aclarado](spec.md): cuatro historias, 14 requisitos y 15 escenarios.
- [Checklist](checklists/requirements.md): 16/16. Elecciones confirmadas: sala
  desde arriba con minimapa, combate en la misma sala e ilustración 2D de fantasía oscura.
- [Plan completado](plan.md) e [investigación](research.md): D-EV-04 confirmada,
  vectores por sala y una animación activa; modelo y contrato disponibles.
- [24 tareas](tasks.md) revisadas: 20/20 requisitos y 15/15 escenarios con cobertura
  prevista, sin hallazgos críticos/altos. Implementación todavía no iniciada.
- [Propuesta visual](propuesta-visual.md): referencia ilustrada generada,
  separada de los recursos finales del juego.
- Implementación de esta capacidad: **0 %**. El trabajo actual es documental.
- El ~85 % anterior correspondía al alcance de 005; no acredita esta ampliación
  de alcance ni se presenta como progreso de la nueva experiencia visual.

Avance estimado de la capacidad 006: **~20 %**, por especificación y trabajo de
investigación. Código nuevo: **0 %**; no se han ejecutado pruebas de esta capacidad.
Siguiente paso: implementar las tareas, empezando por recursos separados y la
habitación con personaje, antes de los efectos de combate y validación final.
