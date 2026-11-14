# Plan técnico: Habitación cenital y combate integrado

**Rama Git**: `005-interfaz-pygame`. **Capacidad**: `006-salas-combate-visual`.
**Fecha**: 2026-11-14. **Spec**: [spec.md](spec.md).
**Estado**: Diseño completado; implementación pendiente de tareas y análisis.

## Resumen

Habitación cenital ilustrada como escena principal, con personaje, puertas,
enemigos y objetos seleccionables. Combate dentro de la misma sala. Reutilizar
el mapa de 005 como minimapa y panel ampliable. Una animación activa por turno,
sin cola de acciones ni modificaciones de las reglas.

## Contexto técnico

- Python 3.11+; referencia local 3.13.2; Pygame 2.6.1 opcional, pytest.
- Ventanas mínimas de 1024 × 768 y referencia de 1280 × 800; interfaz de escritorio.
- Recursos PNG locales y transparentes, independientes del guardado v6.
- Elecciones del usuario: cenital, combate integrado, ilustración de fantasía
  oscura; vectores por sala y una animación activa (D-EV-04 confirmada).
- Base verificada de 005: 831 pruebas con Pygame, 813 sin él y un módulo gráfico
  omitido. Se repetirá tras los cambios; no se atribuye esa ejecución a 006.
- Objetivo inicial: efectos de 250–500 ms, reducibles/saltables, eventos atendidos
  sin bloquear. Medir dibujo y acción por separado; EX-01 sigue vigente.
- Escala: cualquier cripta compatible; contenido numeroso se pagina, con un
  máximo de 12 enemigos y 8 objetos representados simultáneamente por página.

## Revisión constitucional

| Principio | Tratamiento | Estado de diseño |
|---|---|---|
| I / AGENTS.md | Vectores y una animación elegidos por usuario; no índice espacial, dict/set ni cola de biblioteca | Conforme |
| II | Efectos reciben hechos confirmados; sin azar ni ejecución de juego desde la vista | Conforme |
| III | Trabajador dueño del modelo; vista usa DTO y envía intenciones vigentes | Conforme |
| IV | Solo puertas y contenido procedentes de la proyección actual | Conforme |
| V | Arte local, sin HTTP nuevo ni campos de animación en v6 | Conforme |
| VI | Mediciones futuras separadas; no acreditar legibilidad con vídeo dummy | Conforme al plan |
| VII | Spec confirmado antes de código; plan, tareas y análisis previos | Conforme |
| VIII/IX | Matriz de 14 FR, 15 AC, 6 SC, prompts y recursos trazados | Conforme al diseño |

Puerta previa y posterior de diseño superadas. Sin aclaraciones o excepciones
constitucionales nuevas. Esto no acredita la implementación ni sus mediciones.

## Arquitectura

### Escena, regiones y recursos

`PresentacionGrafica` ya contiene el estado actual permitido. `sala.py` coloca
elementos dentro de una habitación escalable: jugador, hasta 12 enemigos y 8
objetos por página, con regiones de clic en un vector. Las puertas se obtienen
solo de `SalaVisual.actual`; una puerta seleccionada ofrece mover/abrir con
dirección y costo visibles. Las posiciones no introducen distancias jugables.

`recursos.py` carga tres PNG: fondo sin actores ni puertas, atlas de actores
de 3 × 2 celdas y atlas de puertas/objetos de 4 × 3. Se recortan las celdas al
cargar con operaciones de superficies de Pygame, conservando alfa. Catálogo en
vector de registros; variantes escaladas solo para los tamaños activos, no un
dict de caché. Un recurso genérico cubre contenido nuevo. El mapa conserva sus
sprites esquemáticos como información secundaria.

### Hechos y animaciones

`EfectoVisual` es un valor inmutable de tipo, actor, sala, instante, cantidad y
datos mínimos del actor observado. `Partida._informar_inicio` y
`Partida._ejecutar_evento` pueden notificar hechos mediante un callback opcional
pasado como argumento. Las operaciones comunes pasan este callback a sus
ejecutores de eventos y a su informe final. No se guarda en Partida/MotorEventos,
ni se añaden campos a `_ESQUEMAS`. Consola y replay usan el valor predeterminado.

El trabajador recopila efectos en un vector por operación y los publica como
tupla junto al resultado. Solo comunica hechos observables cuando suceden.
Desaparición no significa muerte; no se analiza texto ni se consulta vida remota
posterior. La curación inicial de una poción se notifica antes de eventos; el
daño inicial y la derrota ya se conocen en `_informar_inicio`.

`animaciones.py` retiene un registro activo con generación/revisión y vector de
efectos. El reloj real interpola desplazamiento breve, flash, corte, cifra o
desvanecimiento; nunca modifica vida ni envía órdenes. Normal: hasta 500 ms;
reducida: hasta 180 ms; sin efectos: publicación inmediata. Espacio durante un
efecto lo salta sin ejecutar esperar; nueva activación tras soltar la tecla sí
puede ejecutar esperar. Foco/carga/retroceso/cierre invalidan el efecto.

La ventana conserva atención de eventos. Mientras anima, descarta acciones
ordinarias; permite saltar, detener viaje, cerrar y navegar presentación. La
intención interruptora durante un paso de viaje pertenece al coordinador de
005, no a una nueva cola visual. El siguiente paso se solicita solo al finalizar
o saltar su transición, después de procesar eventos.

### Aplicación

HUD compacto, habitación dominante, minimapa lateral y acciones inferiores.
Sprites y listas complementarias comparten `ObjetivoActual`; la lista mantiene
identidades para contenido abundante. Inventario, historia, ayuda, mensajes,
guardado, carga y resultados continúan disponibles. Mapa ampliable conserva
costos, recuerdos y enlaces; no muestra una escena remota. Historia permanece
en su panel de pasado con datos de su propio resumen.

## Estructura del proyecto

```text
specs/006-salas-combate-visual/
  spec.md, plan.md, research.md, data-model.md, quickstart.md
  contracts/escena-animaciones.md
  propuesta-visual.md, referencia-visual.prompt.txt, referencias/
vista/pygame_ui/
  aplicacion.py, sala.py, animaciones.py, recursos.py
  assets/sala.png, actores.png, elementos.png, README.md
controlador/
  efectos_visuales.py, controlador.py, controlador_grafico.py, partida.py
Pruebas/
  prueba_sala_visual.py, prueba_animaciones_visuales.py
  prueba_eventos_pygame.py, prueba_sesion_grafica.py
```

## Complejidad y riesgos

Vectores de tamaño P para colocación/clic O(P), con P limitado por paginación;
memoria O(P + F) con F efectos de la operación activa. Comparaciones por ID de
actores visibles son lineales; no se necesita un índice espacial. Recursos se
cargan una vez, se escalan al cambiar el área y se reutilizan al redibujar.
El mapa sigue las cotas aprobadas en 005. No se afirma una latencia sin medir.

Riesgos y cobertura: notificar sin afectar checkpoints (prueba de esquema y
comparación con consola); información remota (evento de salida no equivale a
derrota); desalineación del atlas (inspección de PNG y render); bloqueo o entradas
duplicadas (reloj inyectado, salto/foco); muchos objetivos (páginas a ventana mínima).

## Arte y fuentes

Referencia conceptual generada con imagegen incorporado y conservada en
`referencias/concepto-sala-v1.png`; no se incorpora como fondo del juego porque
contiene actores y puertas de ejemplo. Los tres recursos finales se generan
por separado, se inspeccionan y copian al proyecto, con prompts registrados.
Sin descargas de bibliotecas gráficas ni dependencias nuevas de ejecución.

Fase 0 completada en [research.md](research.md); fase 1 en [modelo](data-model.md),
[contrato](contracts/escena-animaciones.md) y [guía](quickstart.md).
No existen hooks en `.specify/extensions.yml`.
