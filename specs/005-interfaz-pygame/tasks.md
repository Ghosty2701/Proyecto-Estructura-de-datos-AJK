# Tareas: Interfaz gráfica con Pygame

**Rama**: `005-interfaz-pygame`. **Fecha**: 2026-11-13.
**Estado**: 53 tareas generadas y analizadas; ninguna implementación completada.
**Entrada**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [contrato de interfaz](contracts/interfaz-grafica.md),
[recuerdos v6](contracts/recuerdos-v6.md) y [quickstart.md](quickstart.md).

## Formato y reglas de ejecución

Todas las rutas parten de la raíz del repositorio. `[USn]` corresponde a las
siete historias del spec. `[P]` indica oportunidades de trabajo en archivos
distintos una vez satisfechas sus dependencias; no autoriza lanzar agentes
automáticamente ni ejecutar tareas que aún tienen prerrequisitos incompletos.

Las pruebas son exigidas por PR-IG-001/002 y la constitución. Escribir primero
los casos correspondientes, observar el fallo esperado y después implementar;
mantener la regresión anterior. Una casilla solo se marca tras completar y
verificar su resultado. Generar tareas no acredita código ni escenarios aprobados.

Las decisiones D-IG-05/06/07 ya están elegidas: índice propio, vectores y cinco
cambios reversibles; datos opcionales en el mismo `.bin` v6; croquis cardinal.
No ampliar estructuras, bibliotecas ni reglas sin revisar plan y autorización.

## Fase 1 — Preparación

**Objetivo**: fijar la base de comparación y el entorno opcional sin introducir gráficos en la instalación de consola.

- [X] T001 Ejecutar `python -m pytest -q` sobre la base y registrar versión, comando y salida real en `documentacion/evidencia/pygame_linea_base.txt`; verificar rama y commit de origen sin modificar `main`. La referencia conocida es 759 pruebas, no una salida que se deba inventar. Dep.: ninguna. Requisitos: PR-IG-001, SC-IG-001.
- [X] T002 Crear `documentacion/requirements-pygame.txt` con requisitos base y `pygame==2.6.1`, y `vista/pygame_ui/__init__.py` sin importar Pygame al cargar el paquete; validar instalación opcional en entorno aislado. Dep.: T001. Requisitos: FR-IG-023, PR-IG-001, SC-IG-007.
- [X] T003 Crear `Pruebas/datos_graficos.py` reutilizando los helpers offline existentes: sala actual/avistada/desconocida, antorcha, cinco pergaminos, enemigo remoto, IDs dispersos, ciclo conflictivo y mapa de 300 salas; incluir una carga resoluble y otra que requiera forzar explícitamente. Datos solo de pruebas, sin HTTP. Dep.: T001. Requisitos: PR-IG-001, SC-IG-001, SC-IG-004, SC-IG-006.

## Fase 2 — Fundamentos compartidos

**Objetivo**: interfaz entre ventana y motor, ejecución única y propiedad serializada.
**Puerta**: completar T004–T010 antes de integrar las historias en una ventana.

- [X] T004 Escribir casos en `Pruebas/prueba_sesion_grafica.py` y `Pruebas/prueba_mapa_grafico.py` para DTO, proyección permitida y objetivos obsoletos: «Copia profunda de valores; ninguna referencia al modelo; publicar solo al terminar una operación» y «posiciones de inventario/suelo válidas solo para esa revisión». Dep.: T003. Requisitos: FR-IG-005, FR-IG-009, PR-IG-002; AC-IG-004, AC-IG-006, AC-IG-011.
- [X] T005 Implementar DTO y proyección sin Pygame en `controlador/proyeccion_grafica.py`; generación, revisión y tokens de objetivos transportan solo valores. Aplicar «Enemigos solo de la sala actual» y «Posición de presentación, sin influencia sobre el motor»; no interpretar sufijos de nombres ni transmitir actores/salas físicas. Hacer pasar T004. Dep.: T004. Requisitos: FR-IG-005, FR-IG-006, FR-IG-009, PR-IG-002.
- [X] T006 Añadir a `Pruebas/prueba_controlador.py` casos del resultado compartido y registro único: acción, consulta, navegación, rechazo, carga y retroceso tanto por `usar` pergamino como por `retroceder`; mantener `sig`/`ant` registrados y sin turnos. Dep.: T003. Requisitos: FR-IG-011, FR-IG-014, PR-IG-002; AC-IG-011, AC-IG-019.
- [X] T007 Refactorizar `controlador/controlador.py` para exponer el resultado estructurado sin cambiar el contrato booleano de `procesar` ni duplicar `_registrar`; distinguir explícitamente carga de variaciones de contador y retroceso de una acción nueva. Usar receptor de valores sin Pygame para mensajes/mapa/inventario/historia del trabajador. Hacer pasar T006 y la regresión del controlador. Dep.: T005, T006. Requisitos: FR-IG-010, FR-IG-011, FR-IG-014, PR-IG-002.
- [X] T008 Escribir en `Pruebas/prueba_sesion_grafica.py` casos de propietario único, una operación ocupada, descarte de entradas adicionales, snapshots inmutables, error de operación y cierre sin iniciar guardado. Prohibir acceso de la vista al modelo vivo y cualquier llamada a Pygame desde el trabajador. Dep.: T005, T007. Requisitos: FR-IG-010, FR-IG-022, FR-IG-024, PR-IG-002; AC-IG-010, AC-IG-021, AC-IG-023.
- [X] T009 Implementar el coordinador serializado en `controlador/controlador_grafico.py`, con buzón de capacidad una operación y sincronización estándar; «Una sola sesión activa» y «Una operación aceptada a la vez». Publicar únicamente valores del receptor, liberar recursos sin matar hilos y dejar terminar la operación aceptada. Hacer pasar T008. Dep.: T008. Requisitos: FR-IG-010, FR-IG-022, FR-IG-024, PR-IG-002.
- [X] T010 Verificar la integración de fundamentos mediante `Pruebas/prueba_sesion_grafica.py`, `Pruebas/prueba_controlador.py` y `Pruebas/prueba_mapa_grafico.py`; revisar en `controlador/controlador_grafico.py` y `controlador/proyeccion_grafica.py` que solo se usan las estructuras aprobadas y no hay importación gráfica ni segunda simulación. Dep.: T002, T005, T007, T009. Requisitos: PR-IG-001, PR-IG-002, PR-IG-004.

## Fase 3 — US1: Iniciar una partida gráfica (P1)

**Objetivo**: abrir el menú, configurar y preparar una sesión válida.
**Prueba independiente**: crear/cargar una sesión de datos sintéticos, rechazar
una cripta no resoluble sin forzar y preservar una sesión válida si la candidata falla.

- [X] T011 [P] [US1] Escribir `Pruebas/prueba_cli_pygame.py` para selección explícita, menú sin cripta, cripta/carga mutuamente excluyentes y rechazo de combinaciones con modos sin vista antes de importar Pygame o crear HTTP; cubrir también `--sin-interfaz`. Dep.: T010. Requisitos: FR-IG-001, FR-IG-023, SC-IG-007; AC-IG-001, AC-IG-022.
- [X] T012 [US1] Añadir `--interfaz consola|pygame` e importación diferida en `main.py`, conservando defaults y validaciones actuales; validar ausencia de dependencia/pantalla con diagnóstico útil. No iniciar Pygame en ayuda ni modos sin vista. Hacer pasar T011. Dep.: T011. Requisitos: FR-IG-001, FR-IG-023; AC-IG-001, AC-IG-022.
- [X] T013 [P] [US1] Escribir en `Pruebas/prueba_sesion_grafica.py` casos de iniciar, verificar, forzar, offline y carga candidata fallida, con nombre/semilla/rutas/K/bitácora; una sesión inválida no sustituye la activa ni sobrepasa presupuesto/caché. Dep.: T010. Requisitos: FR-IG-002, FR-IG-003, FR-IG-020, FR-IG-024; AC-IG-001, AC-IG-002, AC-IG-003, AC-IG-023.
- [X] T014 [US1] Extraer preparación/finalización compartida en `controlador/sesion.py` y conectarla a `main.py`, sin duplicar el cargador: sesión candidata independiente, validaciones completas y publicación solo al éxito. Estados y recursos siguen `data-model.md`; la finalización se procesa una vez aunque vuelva al menú. Hacer pasar T013 y regresión CLI. Dep.: T012, T013. Requisitos: FR-IG-002, FR-IG-003, FR-IG-020, FR-IG-024.
- [X] T015 [US1] Crear en `vista/pygame_ui/componentes.py` botones, campos, listas y paneles mínimos del inicio, con texto legible, foco de entrada y controles ocupados; nombre, semilla, cripta, origen offline y ruta de carga no requieren órdenes de consola durante la sesión. Dep.: T002, T010. Requisitos: FR-IG-002, FR-IG-021; AC-IG-001, AC-IG-003.
- [X] T016 [US1] Implementar inicio y escenas de preparación/error en `vista/pygame_ui/aplicacion.py`, conectadas al trabajador y a `controlador/sesion.py`; ventana procesa eventos en el hilo principal, con informe y forzado explícito. Verificar T011/T013 desde menú y sin sesión previa. Dep.: T014, T015. Requisitos: FR-IG-001, FR-IG-002, FR-IG-003, FR-IG-020, FR-IG-024; AC-IG-001, AC-IG-002, AC-IG-003, AC-IG-023.

## Fase 4 — US2: Mapa y enemigos recordados (P1)

**Objetivo**: mapa conocido, sprites actuales/recordados y croquis sin solapes.
**Prueba independiente**: inyectar presentaciones y ejecutar recorridos con el
controlador existente; observar privacidad y cambios remotos sin depender de los botones de US3.

- [X] T017 [P] [US2] Escribir en `Pruebas/prueba_mapa_grafico.py` casos de salas conocidas únicamente, direcciones, puertas recordadas, ID disperso, componentes y ciclos cardinales incompatibles; cámara/límites no delatan salas ocultas y el croquis de 300 salas conserva conexiones sin solapes. Dep.: T016. Requisitos: FR-IG-004, FR-IG-005, PR-IG-004, SC-IG-004, SC-IG-006; AC-IG-004, AC-IG-005, AC-IG-008, AC-IG-020.
- [X] T018 [P] [US2] Escribir `Pruebas/prueba_memoria_visual.py` para observación inicial/postacción, sprites de sala actual, recuerdo remoto sin actualizar, antorcha y diferencia entre falta de observación y vacía: «None significa “sin observación”» y los grupos vacíos acreditan observación vacía. Dep.: T016. Requisitos: FR-IG-005, FR-IG-006, FR-IG-007, SC-IG-004; AC-IG-006, AC-IG-007, AC-IG-008.
- [X] T019 [US2] Implementar observaciones inmutables en `controlador/memoria_visual.py`, con índice propio y vector por sala, sin referencias a actores; actualizar exclusivamente al inicio válido y tras acción aceptada en la sala actual. El redibujado, las consultas, la antorcha y los cambios remotos no observan enemigos. Hacer pasar T018. Dep.: T018. Requisitos: FR-IG-005, FR-IG-006, FR-IG-007, PR-IG-004.
- [X] T020 [US2] Implementar el croquis puro en `controlador/disposicion_mapa.py` con vector/cursor, `IndiceSalas`, orden propio y la regla de carril libre del modelo de datos; «La cercanía visual de dos cuadritos no implica una salida inexistente». Reconstruir solo por cambio de conocimiento/carga/retroceso, nunca por cuadro. Hacer pasar T017. Dep.: T017. Requisitos: FR-IG-004, FR-IG-005, PR-IG-004, SC-IG-006.
- [X] T021 [US2] Crear en `vista/pygame_ui/sprites.py` sprites originales con dibujo de Pygame, almacenados en vector por tipo, leyenda y cantidad; distinguir recuerdo también por texto/estilo. Sin descarga de arte, animación obligatoria ni lógica de enemigos en la vista. Dep.: T002, T005. Requisitos: FR-IG-006, FR-IG-021; AC-IG-006, AC-IG-020.
- [X] T022 [US2] Implementar dibujo del croquis y conexiones en `vista/pygame_ui/mapa.py`, consumiendo `controlador/disposicion_mapa.py` y valores de presentación; marcar enlaces esquemáticos y dibujar desconocida/avistada/explorada y sprites según permiso. Dep.: T019, T020, T021. Requisitos: FR-IG-004, FR-IG-005, FR-IG-006, FR-IG-007, FR-IG-021; AC-IG-004, AC-IG-005, AC-IG-006, AC-IG-007, AC-IG-008, AC-IG-020.
- [X] T023 [US2] Integrar en `vista/pygame_ui/aplicacion.py` mapa, estado, inventario y mensajes de solo presentación, renovados por snapshots; verificar con `Pruebas/prueba_mapa_grafico.py` y `Pruebas/prueba_memoria_visual.py` que nunca se lee el mundo remoto ni se observa al dibujar. Dep.: T022. Requisitos: FR-IG-005, FR-IG-007, FR-IG-021, PR-IG-002; AC-IG-004, AC-IG-007, AC-IG-008, AC-IG-020.

## Fase 5 — US3: Acciones por paneles y botones (P1)

**Objetivo**: todas las acciones ordinarias disponibles con registro y costo idénticos a consola.
**Prueba independiente**: secuencia completa de botones frente a órdenes canónicas,
con ataques/recogidas inválidos, selección ordenada y entradas mantenidas.

- [X] T024 [US3] Escribir en `Pruebas/prueba_eventos_pygame.py` casos de botones ordinarios de AC-IG-009 y objetivos caducados; una revisión antigua no puede atacar/recoger otro objetivo ni producir un registro duplicado. Viaje, historia y guardado gráfico se verifican en sus historias posteriores, sin bloquear estos casos. Dep.: T023. Requisitos: FR-IG-008, FR-IG-009, FR-IG-014, SC-IG-002; AC-IG-006, AC-IG-009, AC-IG-011.
- [X] T025 [US3] Conectar paneles de acción en `vista/pygame_ui/componentes.py` y su despacho en `controlador/controlador_grafico.py`: mover, abrir, atacar, esperar, recoger, usar, equipar y soltar con argumentos vigentes. No llamar directamente al motor desde un widget. Hacer pasar T024. Dep.: T024. Requisitos: FR-IG-008, FR-IG-009, FR-IG-014, SC-IG-002.
- [X] T026 [US3] Implementar selección y orden visual de inventario en `vista/pygame_ui/componentes.py` y `controlador/controlador_grafico.py`; clic directo emite solo los `sig`/`ant` necesarios sin turnos y publica el cursor final, sin encolar usar/equipar. Probar selección sobre vista ordenada y rechazo de posición obsoleta en `Pruebas/prueba_eventos_pygame.py`. Dep.: T025. Requisitos: FR-IG-008, FR-IG-009, FR-IG-014, SC-IG-002; AC-IG-009, AC-IG-011, AC-IG-019.
- [X] T027 [US3] Añadir a `Pruebas/prueba_eventos_pygame.py` casos de tecla sostenida/repetida, foco de campos, operación ocupada, 300 redibujados y reloj de presentación inyectado equivalente a 60 segundos de inactividad; cero turnos/azar/órdenes salvo navegación canónica deliberada del inventario. Dep.: T026. Requisitos: FR-IG-010, FR-IG-011, SC-IG-005; AC-IG-010, AC-IG-011.
- [X] T028 [US3] Implementar eventos y atajos en `vista/pygame_ui/aplicacion.py`, con una operación y como máximo un turno por activación de juego, ignorando autorepetición y acciones mientras está ocupado; foco de texto captura teclas y perder foco limpia entradas sin iniciar acciones nuevas. Hacer pasar T027. Dep.: T027. Requisitos: FR-IG-008, FR-IG-010, FR-IG-011, SC-IG-005.
- [X] T029 [US3] Añadir y pasar comparación de secuencias reales consola/GUI en `Pruebas/prueba_sesion_grafica.py` y `Pruebas/prueba_eventos_pygame.py`: relojes, azar, estado, cursor, órdenes y continuación idénticos; incluir controles ordinarios de acción, rechazos y navegación, separando la selección sin turnos. Completar el resto del recorrido transversal tras US4–US7 en T049/T051. Dep.: T028. Requisitos: FR-IG-008, FR-IG-009, FR-IG-011, FR-IG-014, PR-IG-002, SC-IG-002, SC-IG-003, SC-IG-005; AC-IG-009, AC-IG-010, AC-IG-011, AC-IG-019.

## Fase 6 — US4: Viaje e interrupción (P1)

**Objetivo**: recorrer pasos ordinarios sin bloquear eventos ni duplicar lógica.
**Prueba independiente**: comparar viaje completo de consola con pasos gráficos,
incluyendo destinos inválidos, llegada, daño, enemigos, puertas e interrupción.

- [X] T030 [US4] Añadir a `Pruebas/prueba_niebla_partida.py` equivalencia entre viaje existente y operación de un paso: ruta → mover → registro → observación/presentación → paradas, una orden por paso y comentario sin turno. Cubrir objetivos avistados/desconocidos y sin ruta. Dep.: T029. Requisitos: FR-IG-012, FR-IG-014, PR-IG-002; AC-IG-012, AC-IG-014.
- [X] T031 [US4] Extraer en `controlador/partida.py` el paso compartido de viaje y conservar el envoltorio síncrono de consola; usar las rutas, costos y paradas existentes, sin otra búsqueda ni registro adicional. Hacer pasar T030 y regresión de niebla/replay. Dep.: T030. Requisitos: FR-IG-012, FR-IG-014, PR-IG-002, SC-IG-003.
- [X] T032 [US4] Añadir en `Pruebas/prueba_eventos_pygame.py` casos de detener, otra orden, pergamino, cambio de foco y cierre durante un paso; una intención interruptora nacida en la revisión anterior se revalida por identidad en la misma generación, sin aceptar índices antiguos ni activaciones adicionales. Dep.: T031. Requisitos: FR-IG-010, FR-IG-013, FR-IG-022; AC-IG-013, AC-IG-021.
- [X] T033 [US4] Implementar coordinación incremental de viaje en `controlador/controlador_grafico.py`: un paso aceptado, publicación y ciclo de eventos antes del siguiente; una única intención interruptora, prioridad de cerrar y cancelación por pérdida de foco. Retroceder no reanuda. Hacer pasar T032. Dep.: T032. Requisitos: FR-IG-010, FR-IG-012, FR-IG-013.
- [X] T034 [US4] Integrar destino explorado y botón detener en `vista/pygame_ui/mapa.py` y `vista/pygame_ui/componentes.py`; explicar las paradas y conservar selección por ID, con pruebas de llegada, daño, enemigos y ruta perdida en `Pruebas/prueba_eventos_pygame.py`. Dep.: T033. Requisitos: FR-IG-008, FR-IG-012, FR-IG-013; AC-IG-012, AC-IG-013, AC-IG-014.

## Fase 7 — US5: Historia y retroceso sin futuro (P1)

**Objetivo**: consultas independientes y recuerdos reversibles correctamente alineados.
**Prueba independiente**: cinco retrocesos, `usar` pergamino, nueva rama en el
mismo instante y consultas válidas/rechazadas sin cambios de partida.

- [X] T035 [US5] Ampliar `Pruebas/prueba_memoria_visual.py` para cinco deltas, pergamino por `usar` y `retroceder`, rechazo sin mutación, bifurcación con reloj/contador reutilizados y retroceso que cruza origen sin datos visuales; nunca reconstruir recuerdos leyendo salas remotas. Dep.: T034. Requisitos: FR-IG-007, FR-IG-009, FR-IG-016, PR-IG-002, SC-IG-003, SC-IG-004; AC-IG-007, AC-IG-016.
- [X] T036 [US5] Implementar `DeltaVisual` y su aplicación en `controlador/memoria_visual.py`: «máximo cinco» y asociación por posición de acción vigente, no solo reloj/contador. Acción ordinaria agrega delta; retroceso aceptado lo restaura/retira y reobserva solo sala actual; origen cruzado descarta incertidumbre. Hacer pasar T035. Dep.: T035. Requisitos: FR-IG-007, FR-IG-016, PR-IG-004, SC-IG-004.
- [X] T037 [US5] Añadir en `Pruebas/prueba_memoria_visual.py` y `Pruebas/prueba_eventos_pygame.py` consultas por instante/acción, futuro inválido y cierre del panel; comparar firma de juego/azar/log/HTTP y asegurar que no se superponen recuerdos actuales al mapa histórico. Dep.: T036. Requisitos: FR-IG-015, PR-IG-002, SC-IG-004; AC-IG-015.
- [X] T038 [US5] Implementar panel de historia y su coordinación en `vista/pygame_ui/componentes.py` y `controlador/controlador_grafico.py` usando `Partida.historia()` y `ResumenHistorico`, con separación explícita pasado/presente. Cerrar el panel no cambia la partida ni sus recuerdos. Hacer pasar T037. Dep.: T037. Requisitos: FR-IG-008, FR-IG-015; AC-IG-009, AC-IG-015.

## Fase 8 — US6: Guardado y cambio de interfaz (P1)

**Objetivo**: un solo `.bin` v6 con memoria opcional y continuación compatible.
**Prueba independiente**: v6 antiguo, GUI→GUI, GUI→lector base y re-guardado desde
consola; memoria inválida no invalida juego y carga fallida conserva sesión.

- [X] T039 [US6] Escribir `Pruebas/prueba_guardado_grafico.py` para clave visual ausente/válida/inválida, versión desconocida, IDs repetidos, tipos exactos, reloj futuro, marca/huella no correspondiente y deltas inconsistentes; distinguir invalidez semántica de binario truncado. Dep.: T038. Requisitos: FR-IG-017, FR-IG-018, FR-IG-024, SC-IG-007; AC-IG-017, AC-IG-018, AC-IG-023.
- [X] T040 [US6] Implementar exportación/validación en `adaptadores/estado_grafico.py`: clave `interfaz_grafica`, tupla de cinco componentes, «Entero exacto 1; bool no es un entero válido para este campo», «Hasta cinco cambios de acciones vigentes», huella y sufijo contrastados con línea/historial. Usar solo primitivas del codec y estructuras aprobadas. Hacer pasar T039. Dep.: T039. Requisitos: FR-IG-018, PR-IG-004, SC-IG-007.
- [X] T041 [US6] Extender opcionalmente `controlador/cargar_partida.py` para transportar el payload por la escritura atómica existente, sin cambiar `_ESQUEMAS`, `VERSION_MODELO=6`, campos de juego ni lectores actuales; conectar el adaptador sin introducir dependencias gráficas. Probar ausencia de payload sin cambio de semántica en `Pruebas/prueba_guardado_grafico.py`. Dep.: T040. Requisitos: FR-IG-017, FR-IG-018, PR-IG-002; AC-IG-017, AC-IG-018.
- [X] T042 [US6] Integrar guardar/cargar con memoria candidata en `controlador/controlador_grafico.py` y `controlador/sesion.py`; publicar memoria solo tras éxito del juego, reobservar solo sala actual, invalidar selección y conservar rechazo de carga con bitácora. Una carga fallida conserva juego/memoria previos. Dep.: T041. Requisitos: FR-IG-017, FR-IG-018, FR-IG-020, FR-IG-024; AC-IG-017, AC-IG-018, AC-IG-019, AC-IG-023.
- [X] T043 [US6] Ejecutar desde `Pruebas/prueba_guardado_grafico.py` o su ejecutor explícito la matriz cruzada con el lector real congelado de `main` en `6107b98`, extraído en una carpeta temporal y proceso separado; comparar continuación y aceptar pérdida de recuerdos tras re-guardar desde consola. Registrar comando y resultado real en `documentacion/evidencia/pygame_compatibilidad_v6.txt`, indicando preparación del lector si el historial Git no está disponible. Dep.: T042. Requisitos: FR-IG-017, FR-IG-018, PR-IG-002, SC-IG-003, SC-IG-007; AC-IG-017, AC-IG-018, AC-IG-019.

## Fase 9 — US7: Ventana completa y modos actuales (P2)

**Objetivo**: legibilidad, navegación, ayuda, resultados y cierre seguro.
**Prueba independiente**: redimensionar, cambiar foco y cerrar; iniciar dos
partidas consecutivas y comprobar que modos de consola siguen sin gráficos.

- [X] T044 [P] [US7] Añadir a `Pruebas/prueba_eventos_pygame.py` y `Pruebas/prueba_mapa_grafico.py` casos de cámara, zoom, scroll, leyenda, etiquetas y todos los controles alcanzables con 300 salas y ventana mínima 1024 × 768; las pruebas de vídeo no acreditan por sí solas legibilidad real. Dep.: T043. Requisitos: FR-IG-004, FR-IG-021, SC-IG-006; AC-IG-020.
- [X] T045 [US7] Completar cámara, paneles de ayuda/mensajes y navegación en `vista/pygame_ui/mapa.py`, `vista/pygame_ui/componentes.py` y `vista/pygame_ui/aplicacion.py`; «Sus límites se calculan solo con salas conocidas; no consume tiempo virtual». Mantener estado, inventario, recuerdo/ausencia y control ocupado legibles al redimensionar. Hacer pasar T044. Dep.: T044. Requisitos: FR-IG-008, FR-IG-021, SC-IG-006.
- [X] T046 [P] [US7] Añadir en `Pruebas/prueba_sesion_grafica.py` y `Pruebas/prueba_cliente.py` casos de resultado único, error al escribir puntaje, volver al menú, sesiones consecutivas y cierre durante red/espera 429; una operación aceptada termina segura y no se inicia un guardado automático. Dep.: T043. Requisitos: FR-IG-019, FR-IG-022, FR-IG-024; AC-IG-021, AC-IG-023.
- [X] T047 [US7] Completar resultados, puntajes y ciclo de cierre en `controlador/sesion.py`, `controlador/controlador_grafico.py` y `vista/pygame_ui/aplicacion.py`: finalización una sola vez, error visible sin repetición automática, escritor liberado y sin turnos tras victoria/derrota. Hacer pasar los casos de sesión de T046. Dep.: T045, T046. Requisitos: FR-IG-019, FR-IG-022; AC-IG-021.
- [X] T048 [US7] Añadir cancelación opcional de espera/nuevos intentos en `adaptadores/cliente_http.py` y conectarla al cierre del coordinador; preservar timeout, defaults y conteo/reservas. No prometer cancelar inmediatamente una solicitud ya iniciada ni matar un hilo en escritura. Hacer pasar casos de red de T046 y regresión del cliente. Dep.: T046, T047. Requisitos: FR-IG-020, FR-IG-022, FR-IG-024; AC-IG-023.

## Fase 10 — Validación transversal y entrega de la rama

**Objetivo**: demostrar cobertura y límites reales, sin fusionar automáticamente en `main`.

- [X] T049 Ejecutar la regresión completa con entorno gráfico opcional y las pruebas base en otro entorno que no tenga Pygame; registrar comandos, versiones y salidas reales en `documentacion/evidencia/pygame_regresion.txt`. Validar CLI/modos sin vista sin crear pantalla/red innecesaria y no presentar omisiones de pruebas gráficas como aprobación. Dep.: T048. Requisitos: FR-IG-011, FR-IG-023, PR-IG-001, PR-IG-002, SC-IG-001, SC-IG-003, SC-IG-007; AC-IG-022.
- [X] T050 Medir por separado presentación y acción completa mediante cargas de `Pruebas/datos_graficos.py` y registrar el ensayo reproducible en `documentacion/evidencia/pygame_mediciones.md`: equipo, datos, semilla, mínimo/mediana/máximo, inactividad 60 s/300 redibujados y mapa de 300 salas. No usar tiempo gráfico como turnos ni afirmar EX-01 resuelta. Dep.: T049. Requisitos: PR-IG-003, SC-IG-005, SC-IG-006. **Hecha 2026-11-14:** `Pruebas.medir_escena` → [pygame_mediciones.md](../../documentacion/evidencia/pygame_mediciones.md); Python 3.13.17, mediana escena 3,5–4,0 ms, mapa de 300 salas 15,9 ms, acción esperar 0,04 ms; 300 redibujados en 61,8 s sin cambios.
- [X] T051 Ejecutar la revisión visual real de `specs/005-interfaz-pygame/quickstart.md` y guardar capturas/salidas en `resultados/bench/pygame/`, con resumen versionado en `documentacion/evidencia/pygame_revision_visual.md`: teclado, foco, legibilidad, resize, cierre, niebla y todas las acciones; marcar los escenarios realmente verificados y declarar límites. Dep.: T049. Requisitos: FR-IG-021, PR-IG-001, SC-IG-001, SC-IG-002, SC-IG-004, SC-IG-006; AC-IG-001, AC-IG-009, AC-IG-020, AC-IG-021. **Hecha 2026-11-14:** revisión real de escritorio de Juan consolidada contra el quickstart en [pygame_revision_visual.md](../../documentacion/evidencia/pygame_revision_visual.md), con lo manual y lo automatizado separados y límites declarados.
- [X] T052 Actualizar `README.md`, `specs/005-interfaz-pygame/quickstart.md`, `documentacion/DOCUMENTO_DECISIONES.md` y `documentacion/PROMPTS_LLM.md` con instalación/uso reales, cambios frente al plan, decisiones, evidencia y límites; conservar avances de Pygame separados de Parte II y no documentar comandos pendientes como disponibles. Dep.: T050, T051. Requisitos: PR-IG-001, PR-IG-003, PR-IG-004. **Hecha 2026-11-14:** README (requisito Python ≤ 3.13 para pygame 2.6.1), quickstart, README de 005, decisiones y bitácora actualizados.
- [X] T053 Revisar `specs/005-interfaz-pygame/tasks.md`, `specs/005-interfaz-pygame/spec.md` y su matriz completa: ningún requisito/escenario sin evidencia, ninguna casilla marcada por documentos solos, estructuras aprobadas y rama publicada con commits verificables. Registrar pendientes reales en `specs/005-interfaz-pygame/README.md`; la integración con `main` requiere validación y decisión explícita, no se ejecuta aquí. Dep.: T052. Requisitos: PR-IG-001, PR-IG-004, SC-IG-001. **Hecha 2026-11-14:** los 58 identificadores FR/AC/SC/PR del spec tienen tarea; 53/53 tareas con evidencia; integración con `main` sin ejecutar, pendiente de decisión.

## Dependencias y estrategia de entrega

Las dependencias de cada línea son obligatorias y no forman ciclos. Orden
principal recomendado:

```text
T001 → preparación T002/T003 → fundamentos T004–T010
  → US1 T011–T016 → US2 T017–T023 → US3 T024–T029
  → US4 T030–T034 → US5 T035–T038 → US6 T039–T043
  → US7 T044–T048 → cierre T049–T053
```

Los fundamentos ofrecen lógica comprobable sin ventana. Las pruebas de cada
historia usan fixtures y el núcleo compartido: no dependen de poder operar
manualmente una historia posterior. La integración visible sigue el orden
recomendado para evitar modificaciones simultáneas de los mismos archivos.

**Primer incremento**: US1 permite iniciar/cargar/verificar una sesión desde la
ventana. **MVP jugable**: fundamentos + US1 + US2 + US3; ofrece mapa y acciones
ordinarias, todavía sin declarar completas las funciones de viaje/historia/
guardado gráfico de las historias siguientes. La aceptación total exige las siete.

## Trabajo paralelo posible

| Historia | Oportunidad después de sus prerrequisitos | Límite |
|---|---|---|
| US1 | T011 y T013: pruebas CLI y pruebas de sesión en archivos distintos | T012/T014 esperan sus pruebas; no editar `main.py` simultáneamente |
| US2 | T017 y T018: pruebas de croquis y memoria | T019 y T020 pueden desarrollarse después en archivos distintos, coordinando su integración en T022 |
| US3 | Revisar casos de objetivos y el catálogo de botones mientras se prepara T024 | No hay ejecución paralela marcada: se comparte `prueba_eventos_pygame.py` |
| US4 | Diseñar datos de rutas y revisar semántica de interrupción por lectura | T030–T034 son secuenciales para preservar el paso canónico |
| US5 | Revisar fixtures de historia mientras se implementan deltas | T035–T038 comparten memoria/eventos; evitar escrituras simultáneas |
| US6 | Preparar el checkout/lector base de T043 sin modificarlo | T039–T043 dependen del payload y la integración de carga, no anticipar resultados |
| US7 | T044 y T046 pueden prepararse tras T043 en archivos de pruebas distintos | T047 espera ambos caminos; T048 conserva la prueba completa del cliente |

Las oportunidades no sustituyen las dependencias ni autorizan múltiples
trabajadores sobre una partida. No se necesita dividir el trabajo entre agentes.

## Matriz requisito → tareas

Cada requisito tiene pruebas y trabajo concreto; la tabla es cobertura prevista,
no evidencia de ejecución. Los escenarios se enlazan desde las tareas y el spec.

| Requisito | Tareas |
|---|---|
| FR-IG-001 | T011, T012, T016 |
| FR-IG-002 | T013, T014, T015, T016 |
| FR-IG-003 | T013, T014, T016 |
| FR-IG-004 | T017, T020, T022, T044 |
| FR-IG-005 | T004, T005, T017, T018, T019, T022, T023 |
| FR-IG-006 | T005, T018, T019, T021, T022 |
| FR-IG-007 | T018, T019, T022, T023, T035, T036 |
| FR-IG-008 | T024, T025, T026, T028, T029, T034, T038, T045 |
| FR-IG-009 | T004, T005, T024, T025, T026, T029, T035 |
| FR-IG-010 | T007, T008, T009, T027, T028, T032, T033 |
| FR-IG-011 | T006, T007, T027, T028, T029, T049 |
| FR-IG-012 | T030, T031, T033, T034 |
| FR-IG-013 | T032, T033, T034 |
| FR-IG-014 | T006, T007, T024, T025, T026, T029, T030, T031 |
| FR-IG-015 | T037, T038 |
| FR-IG-016 | T035, T036 |
| FR-IG-017 | T039, T041, T042, T043 |
| FR-IG-018 | T039, T040, T041, T042, T043 |
| FR-IG-019 | T046, T047 |
| FR-IG-020 | T013, T014, T016, T042, T048 |
| FR-IG-021 | T015, T021, T022, T023, T044, T045, T051 |
| FR-IG-022 | T008, T009, T032, T046, T047, T048 |
| FR-IG-023 | T002, T011, T012, T049 |
| FR-IG-024 | T008, T009, T013, T014, T016, T039, T042, T046, T048 |
| PR-IG-001 | T001, T002, T003, T010, T049, T051, T052, T053 |
| PR-IG-002 | T004, T005, T006, T007, T008, T009, T010, T023, T029, T030, T031, T035, T037, T041, T043, T049 |
| PR-IG-003 | T050, T052 |
| PR-IG-004 | T010, T017, T019, T020, T036, T040, T052, T053 |
| SC-IG-001 | T001, T003, T049, T051, T053 |
| SC-IG-002 | T024, T025, T026, T029, T051 |
| SC-IG-003 | T029, T031, T035, T043, T049 |
| SC-IG-004 | T003, T017, T018, T035, T036, T037, T051 |
| SC-IG-005 | T027, T028, T029, T050 |
| SC-IG-006 | T003, T017, T020, T044, T045, T050, T051 |
| SC-IG-007 | T002, T011, T039, T040, T043, T049 |

## Criterio para comenzar

Revisar spec, plan y tareas con `$speckit-analyze`. No iniciar implementación
con hallazgos críticos o de alta gravedad abiertos. La generación y revisión
de estos documentos no marca T001–T053: todas representan trabajo futuro.

Revisión de solo lectura del 2026-11-13 completada: 35/35 requisitos construibles
y 23/23 escenarios tienen tareas, todas con formato y dependencias válidos,
sin tareas huérfanas ni bloqueos críticos/altos identificados. El informe se
emitió en la sesión sin modificar artefactos durante el análisis. Esta nota
registra después su resultado y no certifica escenarios funcionales.
