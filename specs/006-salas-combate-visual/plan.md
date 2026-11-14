# Plan técnico: Habitación cenital y combate integrado

**Rama Git**: `005-interfaz-pygame`. **Capacidad**: `006-salas-combate-visual`.
**Fecha**: 2026-11-14. **Spec**: [spec.md](spec.md).
**Estado**: Diseño implementado; T001–T019, T021 y T022 verificadas; cierre nativo pendiente.

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

## Revisión de 16 bits y reducción de comandos — 2026-11-14

Solicitud explícita posterior: reemplazar el aspecto ilustrado por pixel art
original de RPG de 16 bits, con ventanas azul profundo y marcos claros.
Escalado de vecinos próximos para conservar píxeles; cámara y reglas sin cambios.

Se reutilizan los vectores de recursos, botones y regiones y el campo de panel
actual ya aprobados. No se introduce un árbol de menús, índice o cola nuevos.
Habitación normal: acción contextual, esperar, inventario, mapa y menú; como
sexto control, objetivos numerosos o detener/saltar cuando corresponda.
Menú de pausa agrupa persistencia, pergamino, historia, registro y ajustes.
Inventario y lista de objetivos aparecen solo al solicitarlos.

Recursos nuevos versionados: `sala_16bits.png`, `actores_16bits.png`,
`elementos_16bits.png` y `puertas_16bits.png`. Los atlas de actores/objetos conservan
sus órdenes anteriores. Puertas: cuatro columnas N/S/E/O y dos filas
cerradas/abiertas; cada orientación se dibuja como parte de una pared, sin
rotar 180 grados una puerta frontal. La colocación deja el hueco dentro de la
pared y el paso hacia el suelo, sin cambiar su región de interacción lógica.

Pruebas previas al cambio: límites de botones, contexto, alcance de todos los
paneles, inventario ordenado, cerrar con Escape, selección caducada y ocho
combinaciones de puerta. Regresión de reglas, v6 y modos sin Pygame obligatoria.

## Revisión de claridad — 2026-11-14

Se amplía el mismo catálogo vectorial de recursos aprobado con especies de
criaturas; resolución por nombre observable normalizado, antes del comportamiento.
Comportamiento sigue siendo una regla del motor, no una especie. El sustituto
desconocido es neutral. No hay un índice ni estructura nueva.
Los estados de inicio/nueva/carga usan el selector de panel existente; el archivo
se guarda en el Campo ya disponible. Selector nativo estándar opcional mediante
tkinter, sin dependencia pip; si no está disponible se permite editar la ruta.
Cancelar no cambia la ruta; cargar confirma el comando vigente del trabajador.
La carga en pausa conserva su semántica de reanudar el guardado configurado.

El indicador usa tiempo real solo visual, operación pendiente y tiempo de inicio
escalares. Se dibuja cada cuadro sin bloquear ni inventar porcentaje; no hay otro
trabajador o cola. Se prueban inicio/catálogo/carga/orden deliberadamente lentos,
rechazo de duplicados y cierre seguro. Contornos y brillo se dibujan en Pygame,
sin generar imágenes de botones. Misma colección de controles/regiones aprobada.

## Exploración y revisión final

Se reutilizan Mapa, su clave/croquis/índice existentes, el snapshot inmutable y
una animación activa aprobados. La identidad de la última presentación evita
recomparar topología cada cuadro, sin un índice/caché nuevos. La precarga y
política de solicitudes existentes no se modifican. Perfil local previo en
`documentacion/evidencia/exploracion_perfil_antes.txt`; el motor no justifica
añadir complejidad: acción mediana ~0,51 ms con perfil, dibujo ~3,39 ms.
Se reduce transición de movimiento a 160/80 ms, dejando combate 500/180 ms.
No se añaden campos a Partida/MotorEventos ni estructuras nuevas.

Minimapa: marco ~286 px de alto y escala inicial 0,60; estado debajo y leyenda
tenue en sala. Durante juego, indicador compacto sin botones tras 150 ms de
actividad; inicio y cierre conservan detalle. El umbral solo decide dibujo.
H usa la intención de ayuda ya existente. Pruebas de tamaños, identidad de
croquis, invalidación por snapshot nuevo, PNG cargado una sola vez y duraciones.
Después de regresión/medidas, revisión nativa mediante computer-use sobre una
partida sintética local y archivos aislados; registrar límites observados sin
confundir renders dummy con interacción de escritorio. Rama sin merge.
