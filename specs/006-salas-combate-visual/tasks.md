# Tareas: Habitación ilustrada y combate integrado

**Rama**: `005-interfaz-pygame`. **Entrada**: spec, plan, research, modelo y contrato.
Pruebas antes de su implementación; marcar únicamente después de verificar.
El checklist 16/16 es calidad de especificación, no avance de código.

## Fase 1 — Preparación

- [X] T001 Verificar base y dependencia opcional con `documentacion/evidencia/pygame_regresion.txt` y `documentacion/requirements-pygame.txt`; conservar referencia 831/813 y EX-01. Dep.: ninguna. FR-EV-012, SC-EV-006.
- [X] T002 Generar e inspeccionar los tres PNG originales en `vista/pygame_ui/assets/`, conservar alfa y registrar prompts/procedencia en `assets/README.md`; no usar mockup como fondo. Dep.: T001. FR-EV-001, FR-EV-002, FR-EV-003, FR-EV-013; AC-EV-001, AC-EV-003, AC-EV-005, AC-EV-013; SC-EV-002.

## Fase 2 — Fundamentos

- [X] T003 Escribir pruebas de recursos en `Pruebas/prueba_sala_visual.py`: atlas por celdas, tipos genéricos, alfa y carga local sin HTTP. Dep.: T002. FR-EV-003, FR-EV-013; AC-EV-003, AC-EV-013.
- [X] T004 Implementar `vista/pygame_ui/recursos.py` con catálogo vectorial aprobado, carga única y escalado fuera del redibujado normal; hacer pasar T003. Dep.: T003. FR-EV-001, FR-EV-003, FR-EV-013; SC-EV-002.

## Fase 3 — US1: Habitación y personaje (P1)

Prueba independiente: entrar, elegir suelo/puertas y recoger sin escribir órdenes.

- [X] T005 [US1] Probar disposición, selección y puertas solo conocidas en `Pruebas/prueba_sala_visual.py`; posiciones sin influencia en costos y selección exacta por objetivo. Dep.: T004. FR-EV-001, FR-EV-002, FR-EV-004, FR-EV-005, FR-EV-008; AC-EV-001, AC-EV-002, AC-EV-003, AC-EV-004.
- [X] T006 [US1] Implementar habitación, personaje, puertas y vectores de regiones en `vista/pygame_ui/sala.py`; aplicar «hasta 12 enemigos y 8 objetos por página» y posiciones escénicas; hacer pasar T005. Dep.: T005. FR-EV-001, FR-EV-002, FR-EV-004, FR-EV-005; AC-EV-001, AC-EV-003, AC-EV-004.
- [X] T007 [US1] Integrar sala principal, HUD, minimapa y controles actuales en `vista/pygame_ui/aplicacion.py`, preservando acceso a inventario, mapa, historia y mensajes. Dep.: T006. FR-EV-001, FR-EV-004, FR-EV-005, FR-EV-014; AC-EV-001, AC-EV-002, AC-EV-003, AC-EV-015; SC-EV-001.
- [X] T008 [US1] Verificar eventos de clic en sprite/puerta y comparación con acción canónica en `Pruebas/prueba_sala_visual.py` y `Pruebas/prueba_eventos_pygame.py`, incluidos rechazo y objetivo caducado. Dep.: T007. FR-EV-004, FR-EV-005, FR-EV-008; AC-EV-002, AC-EV-003, AC-EV-004; SC-EV-001.

## Fase 4 — US2: Combate en la habitación (P1)

Prueba independiente: atacar, recibir daño y derrotar sin cambiar de escena ni reglas.

- [X] T009 [US2] Escribir `Pruebas/prueba_animaciones_visuales.py` para hechos observables: daño+curación neta cero, derrota confirmada, salida sin muerte, rechazo sin efecto y equivalencia con consola. Dep.: T008. FR-EV-006, FR-EV-007, FR-EV-008, FR-EV-011; AC-EV-005, AC-EV-006, AC-EV-007, AC-EV-008.
- [X] T010 [US2] Implementar `controlador/efectos_visuales.py` y callback opcional en `controlador/partida.py` y `controlador/controlador.py`; no añadir campos persistidos, no interpretar texto ni leer actor remoto posterior. Dep.: T009. FR-EV-006, FR-EV-007, FR-EV-008, FR-EV-011; AC-EV-005, AC-EV-007, AC-EV-008.
- [X] T011 [US2] Recopilar y publicar tupla de efectos por operación en `controlador/controlador_grafico.py`; consultas, rechazos y retrocesos no producen efectos de combate. Hacer pasar T009. Dep.: T010. FR-EV-006, FR-EV-007, FR-EV-008; AC-EV-006, AC-EV-007, AC-EV-008.
- [X] T012 [US2] Probar tiempo inyectado, salto, reducción, sin efectos, 300 cuadros y 60 s inactivos en `Pruebas/prueba_animaciones_visuales.py`. Dep.: T011. FR-EV-007, FR-EV-008, FR-EV-009; AC-EV-004, AC-EV-007; SC-EV-003.
- [X] T013 [US2] Implementar una `AnimacionActiva` en `vista/pygame_ui/animaciones.py`, «Normal: hasta 500 ms; reducida: hasta 180 ms; sin efectos: publicación inmediata», sin ejecutar órdenes. Dep.: T012. FR-EV-007, FR-EV-009; AC-EV-007; SC-EV-003.
- [X] T014 [US2] Integrar corte/flash/cifras y desvanecimiento en `vista/pygame_ui/sala.py` y `aplicacion.py`; espacio salta efecto sin esperar, no se acumulan órdenes; verificar selección de enemigos con nombres repetidos. Dep.: T013. FR-EV-005, FR-EV-006, FR-EV-007, FR-EV-009; AC-EV-005, AC-EV-006, AC-EV-007, AC-EV-008; SC-EV-001, SC-EV-003.

## Fase 5 — US3: Orientación y privacidad (P1)

Prueba independiente: mapa, antorcha, carga, historia y retroceso sin contenido remoto.

- [X] T015 [US3] Añadir pruebas de minimapa/panel, antorcha, recuerdo, historia y cancelación de efectos por carga/retroceso/foco en `Pruebas/prueba_sala_visual.py` y `Pruebas/prueba_animaciones_visuales.py`. Dep.: T014. FR-EV-010, FR-EV-011, FR-EV-012; AC-EV-009, AC-EV-010, AC-EV-011, AC-EV-012; SC-EV-004.
- [X] T016 [US3] Completar minimapa ampliable, panel histórico e invalidación de escenas/objetivos en `vista/pygame_ui/aplicacion.py`; conservar mapa conocido y recuerdos de 005. Hacer pasar T015. Dep.: T015. FR-EV-010, FR-EV-011, FR-EV-012; AC-EV-009, AC-EV-010, AC-EV-011; SC-EV-004.
- [X] T017 [US3] Coordinar siguiente paso de viaje con final/salto de transición y prioridad detener/foco/cierre en `aplicacion.py`; probar en `Pruebas/prueba_eventos_pygame.py`. Dep.: T016. FR-EV-009, FR-EV-010, FR-EV-012; AC-EV-012; SC-EV-004.

## Fase 6 — US4: Coherencia y legibilidad (P2)

Prueba independiente: tamaños mínimo/referencia, muchos objetivos y funciones completas.

- [X] T018 [US4] Escribir pruebas de paginación para «12 enemigos y 8 objetos por página», controles y selección alcanzables a 1024 × 768 en `Pruebas/prueba_sala_visual.py`. Dep.: T017. FR-EV-003, FR-EV-005, FR-EV-014; AC-EV-013, AC-EV-014, AC-EV-015; SC-EV-002.
- [X] T019 [US4] Completar escala, páginas, contraste, leyenda, genéricos y modo de efectos en `sala.py`, `recursos.py` y `aplicacion.py`; hacer pasar T018. Dep.: T018. FR-EV-003, FR-EV-005, FR-EV-013, FR-EV-014; AC-EV-013, AC-EV-014, AC-EV-015; SC-EV-002, SC-EV-005.
- [ ] T020 [US4] Ejecutar revisión visual real de `quickstart.md`, guardar capturas pertinentes y registrar límites en `documentacion/evidencia/escena_revision_visual.md`; vídeo dummy no acredita esta tarea. Dep.: T019. FR-EV-001, FR-EV-013, FR-EV-014; AC-EV-001, AC-EV-005, AC-EV-013, AC-EV-014, AC-EV-015; SC-EV-001, SC-EV-005.

## Fase 7 — Validación y entrega

- [X] T021 Ejecutar regresión completa con/sin Pygame, matriz v6 y comparación de secuencias normal/reducida/sin efectos; registrar salidas en `documentacion/evidencia/escena_regresion.txt`. Dep.: T019. FR-EV-008, FR-EV-009, FR-EV-011, FR-EV-012; AC-EV-004, AC-EV-007, AC-EV-011, AC-EV-015; SC-EV-003, SC-EV-004, SC-EV-006.
- [X] T022 Medir dibujo y acción separadamente con fixtures locales; registrar tamaño, datos, equipo y min/mediana/máximo en `documentacion/evidencia/escena_mediciones.md`, sin afirmar EX-01 resuelta. Dep.: T021. FR-EV-009, FR-EV-014; SC-EV-003, SC-EV-005.
- [ ] T023 Actualizar `README.md`, `specs/006-salas-combate-visual/README.md`, `quickstart.md`, `documentacion/DOCUMENTO_DECISIONES.md` y `documentacion/PROMPTS_LLM.md` con uso, arte, pruebas, avance exclusivo y pendientes reales. Dep.: T020, T022. FR-EV-012, FR-EV-013, FR-EV-014; SC-EV-005, SC-EV-006.
- [ ] T024 Auditar cobertura de 14 FR/15 AC/6 SC en `specs/006-salas-combate-visual/tasks.md`, confirmar commits y push en rama adicional sin fusionar `main`. Dep.: T023. FR-EV-001, FR-EV-008, FR-EV-011, FR-EV-012, FR-EV-013, FR-EV-014; SC-EV-001, SC-EV-002, SC-EV-003, SC-EV-004, SC-EV-005, SC-EV-006.

## Dependencias y estrategia

Orden principal T001–T019; después T020 y T021 pueden verificarse de forma
independiente, T022 depende de T021, y cierre T023–T024 requiere ambos caminos.
US1 deja un primer incremento jugable ilustrado. US2 añade los efectos;
US3 valida continuidad y US4 legibilidad. Cada prueba antecede a su implementación.

Hay independencia de lectura entre arte y diseño de pruebas, pero no se autoriza
trabajo de agentes paralelo durante implementación ni edición concurrente de
`aplicacion.py`. La revisión nativa puede ocurrir mientras se ejecuta regresión,
sin confundir sus evidencias. Todas las tareas contienen rutas y trazabilidad;
ninguna se completa por el hecho de generar estos documentos.

## Fase 8 — Revisión solicitada: comandos compactos y RPG de 16 bits

- [X] T025 Confirmar primero la revisión de estilo y alcance de controles en `spec.md`, `plan.md` y `contracts/escena-animaciones.md`; reutilizar estructuras aprobadas, sin cambios de reglas. Dep.: T019. FR-EV-013, FR-EV-015, FR-EV-016; AC-EV-016, AC-EV-017.
- [X] T026 Generar e inspeccionar cuatro recursos originales con sufijo `_16bits` en `vista/pygame_ui/assets/`, registrar prompts, alfa y orientación N/S/E/O. Dep.: T025. FR-EV-013, FR-EV-016; AC-EV-017; SC-EV-008.
- [X] T027 Escribir `Pruebas/prueba_interfaz_compacta.py` para máximo seis botones, acción contextual, inventario/pausa/historia/guardado/mapa, Escape y puertas orientadas; observar fallos antes de implementar. Dep.: T025; las pruebas de contexto usan recursos existentes mientras se genera T026. FR-EV-014, FR-EV-015, FR-EV-016; AC-EV-016, AC-EV-017; SC-EV-007, SC-EV-008.
- [X] T028 Reorganizar `vista/pygame_ui/aplicacion.py` en habitación, contexto y paneles agrupados; nombres intuitivos, funciones completas y sin comandos acumulados. Adaptar recorridos de `Pruebas/prueba_eventos_pygame.py` a los paneles reales. Dep.: T027. FR-EV-005, FR-EV-014, FR-EV-015; AC-EV-009, AC-EV-014, AC-EV-015, AC-EV-016; SC-EV-007.
- [X] T029 Aplicar marcos/tipografía de RPG clásico, recursos y escalado pixelado en `componentes.py`, `recursos.py` y `sala.py`; encajar las ocho puertas sin invertirlas. Dep.: T028. FR-EV-013, FR-EV-016; AC-EV-013, AC-EV-017; SC-EV-008.
- [X] T030 Ejecutar regresión con/sin Pygame y matriz v6; registrar resultados en `documentacion/evidencia/retro_regresion.txt`. Dep.: T029. FR-EV-008, FR-EV-009, FR-EV-011, FR-EV-012, FR-EV-015; SC-EV-003, SC-EV-004, SC-EV-006, SC-EV-007.
- [X] T031 Revisar renders a 1024 × 768 y 1280 × 800 con sala vacía/combate, menús y ocho puertas; registrar capturas y límites de revisión nativa en `documentacion/evidencia/retro_revision_visual.md`. Dep.: T029. FR-EV-013, FR-EV-014, FR-EV-016; SC-EV-005, SC-EV-008.
- [X] T032 Actualizar uso, avance, arte y evidencia en `README.md`, `specs/006-salas-combate-visual/README.md` y `documentacion/PROMPTS_LLM.md`; commits y push en rama adicional. Dep.: T030, T031. FR-EV-013, FR-EV-015, FR-EV-016; SC-EV-007, SC-EV-008.
