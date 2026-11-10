# Tareas: Verificación de resolubilidad

**Fecha**: 2026-11-09. **Estado**: 38/38 tareas ejecutadas y verificadas.
**Entrada**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [contrato](contracts/verificacion.md) y
[quickstart.md](quickstart.md). Rama real: `main`.

Las siete opciones A y las dos interpretaciones del equipo están aprobadas.
No elegir otras estructuras ni crear persistencia de ubicaciones. Usar solo
índices hash propios, arreglos, listas, FIFO/cursor y pilas/incidencias aprobados.
Los dict de transporte no autorizan índices/cachés de problemas evaluados.

Formato: `- [ ] Tnnn [P opcional] [USn en historias] acción, archivos y requisitos`.
Cada tarea incluye dependencias; [P] solo indica trabajo posible en archivos
distintos tras completar sus prerrequisitos. No autoriza delegación automática.
Las pruebas se incluyen por SC-RS-001 y constitución VIII. Escribir los casos
antes del comportamiento correspondiente y comprobar que detectan su ausencia;
no marcar una tarea solo por crear archivos ni conservar fallos pendientes.

## Fase 1 — Preparación compartida

Objetivo: datos sintéticos y contratos de prueba reproducibles, sin datos de
criptas oficiales dentro del código de aplicación. Sin nueva dependencia.

- [X] T001 Crear constructores de datos sintéticos en Pruebas/datos_resolubilidad.py para salas, llaves, puertas, varias ubicaciones y fuentes controladas, citando los AC de cada caso y sin sustituir las estructuras de producción por dict/set; cubrir los cuatro casos de apéndice B. Dep.: ninguna. Requisitos: FR-RS-001, FR-RS-002, FR-RS-003, FR-RS-008, FR-RS-009; SC-RS-001. Escenarios: AC-RS-001, AC-RS-006, AC-RS-007, AC-RS-009, AC-RS-010, AC-RS-011, AC-RS-012, AC-RS-013.

## Fase 2 — Fundamentos del modelo

Objetivo: posiciones, índices y normalización independientes de actores, HTTP
y vista. Bloquea las historias; los adaptadores de US4 se añaden después.

- [X] T002 Escribir en Pruebas/prueba_indice_llaves.py pruebas del índice entero reutilizado y del índice textual: claves ausentes, repetidas, dispersas/Unicode, colisiones y sondeo acotado; verificar "Capacidad potencia de dos, carga de reserva máxima 70 %, paso impar y sondeo acotado" y que casillas no deciden el orden. Dep.: T001. Requisitos: FR-RS-005, FR-RS-009, FR-RS-015; PR-RS-002.
- [X] T003 Implementar el índice de texto en modelo/indice_llaves.py con la mezcla de research.md y reutilizar IndiceSalas de modelo/conocimiento.py para enteros; reservar por cota de IDs, comparar clave completa, no crecer durante cierre y pasar T002 sin modificar estructuras de rutas/cazadores. Dep.: T002. Requisitos: FR-RS-005, FR-RS-009, FR-RS-015; PR-RS-002.
- [X] T004 Escribir en Pruebas/prueba_normalizacion_resolubilidad.py casos de entrada y puertas: "IDs de sala únicos; no indexar por el ID máximo", "Referencias válidas", "Un ID puede tener varias ubicaciones: no rechazarlo como duplicado de sala", "enemigo puede ser null"; añadir recíprocas únicas, paralelas ambiguas, salida dirigida y cierre sin llave sin inventar invalidez. Dep.: T001. Requisitos: FR-RS-001, FR-RS-002, FR-RS-007, FR-RS-015. Escenarios: AC-RS-007, AC-RS-008, AC-RS-017, AC-RS-020.
- [X] T005 Crear registros de entrada y normalización básica en modelo/verificacion.py: identidad/versión, salas compactas "Posición 0..S-1, ID externo entero", salida con "dirección N/S/E/O", llaves/ubicaciones y avisos; aplicar "Identidad y versión coherentes; extremos y ubicaciones referencian salas existentes", "no perder dirección por compartir puerta" y listas por sala/llave; sin motor, HTTP ni vista. Dep.: T003, T004. Requisitos: FR-RS-001, FR-RS-002, FR-RS-013, FR-RS-015. Escenarios: AC-RS-007, AC-RS-017, AC-RS-020.
- [X] T006 Completar en modelo/verificacion.py la función compartible de emparejamiento: "Compartir solo recíprocas compatibles con emparejamiento único"; "Costes conservan simetría vigente de terreno; sin emparejamiento no fusionar"; ante ambigüedad "Se informa y conserva separación; no convierte por sí solo un dato válido en error". Hacer pasar T004 sin fusionar todas las salidas por extremos ni asumir direcciones opuestas. Dep.: T005. Requisitos: FR-RS-002, FR-RS-007, FR-RS-015. Escenarios: AC-RS-008, AC-RS-017, AC-RS-020.

## Fase 3 — US1: Saber si se puede escapar (P1, MVP del modelo)

Objetivo: veredicto, cierre y evidencia de victoria con datos normalizados.
Prueba independiente: llamar al modelo con los casos AC-RS-001 a 005, sin
servicio ni juego. Este MVP no representa entrega completa ni inicio seguro
del juego hasta completar US2, US4 y US3.

- [X] T007 [US1] Escribir en Pruebas/prueba_resolubilidad.py los casos de cadena de llaves, llave reutilizable, enemigos/trampas/cierres ignorados en el análisis y dos falsos positivos de sala de salida alcanzable; comparar cierre con referencia sencilla en casos pequeños. Dep.: T006. Requisitos: FR-RS-001, FR-RS-002, FR-RS-003, FR-RS-004, FR-RS-005, FR-RS-006. Escenarios: AC-RS-001, AC-RS-002, AC-RS-003, AC-RS-004, AC-RS-005.
- [X] T008 [US1] Implementar el cierre real en modelo/verificacion.py con FIFO lista/cursor, marcas por posición y puertas pendientes por llave: "No descubierta → encolada → procesada, sin volver atrás", llave "Falsa → verdadera al alcanzar cualquiera de sus ubicaciones" y orden con "Agregar solo la primera obtención"; obtener llaves antes de revisar salidas. Dep.: T007. Requisitos: FR-RS-002, FR-RS-004, FR-RS-005, FR-RS-009; PR-RS-002. Escenarios: AC-RS-001, AC-RS-002, AC-RS-005, AC-RS-006, AC-RS-007.
- [X] T009 [US1] Completar en modelo/verificacion.py la condición de victoria: "Solo con llave de salida obtenida y una salida habilitada que la requiere", desde origen alcanzado hacia sala_salida; conservar evidencia del acceso y terminar el cierre para el informe, sin aceptar solamente presencia en sala_salida. Dep.: T008. Requisitos: FR-RS-003, FR-RS-004, FR-RS-006. Escenarios: AC-RS-001, AC-RS-003, AC-RS-004, AC-RS-005.
- [X] T010 [US1] Ejecutar los casos de Pruebas/prueba_resolubilidad.py y añadir comprobaciones de no modificación de entrada, repetibilidad y contadores de trabajo para descubrir duplicación de salas/puertas; corregir antes de marcar. Dep.: T009. Requisitos: FR-RS-002, FR-RS-003, FR-RS-005, FR-RS-009, FR-RS-013; PR-RS-002; SC-RS-002. Escenarios: AC-RS-001, AC-RS-002, AC-RS-003, AC-RS-004, AC-RS-005, AC-RS-016.

## Fase 4 — US2: Entender el orden y los bloqueos (P1)

Objetivo: orden reproducible, frontera e informe negativo con certificado
completo, no solo la frase «hay un ciclo» ni un circuito de pasillos.
Prueba independiente: modelo y proyección de resultado sobre datos sintéticos,
comprobando todas las alternativas y el testigo, sin red ni partida.

- [X] T011 [US2] Escribir en Pruebas/prueba_certificados_resolubilidad.py los casos de orden válido, botín en sala inicial, frontera, autociclo, ciclo de dos llaves, alternativa obtenible, grupo A O B bloqueado, aislamiento, ubicación múltiple y pasillos recíprocos; incluir el contraejemplo S→X(B) por B o A y S→Y(A) por A sin afirmar exclusividad individual de B→B. Dep.: T010. Requisitos: FR-RS-004, FR-RS-006, FR-RS-007, FR-RS-008, FR-RS-009. Escenarios: AC-RS-006, AC-RS-007, AC-RS-008, AC-RS-009, AC-RS-010, AC-RS-011, AC-RS-012.
- [X] T012 [US2] Construir en modelo/verificacion.py el resultado negativo del cierre real: llaves no obtenibles, frontera con una entrada por puerta identificada, ubicaciones y avisos de ambigüedad; usar tablas compartidas y referencias para no repetir listas completas por puerta. Dep.: T011. Requisitos: FR-RS-006, FR-RS-007, FR-RS-009; PR-RS-002. Escenarios: AC-RS-003, AC-RS-004, AC-RS-008, AC-RS-012.
- [X] T013 [US2] Implementar en modelo/verificacion.py conectividad física y cierre diagnóstico privados; ignorar solo cerraduras abribles, sembrar hipotéticamente llaves físicamente aisladas, considerar una llave conectada si alguna ubicación lo está y conservar el veredicto/estado del cierre real. Dep.: T012. Requisitos: FR-RS-008, FR-RS-009, FR-RS-013; PR-RS-002. Escenarios: AC-RS-009, AC-RS-010, AC-RS-011, AC-RS-012, AC-RS-016.
- [X] T014 [US2] Registrar en modelo/verificacion.py reglas, procedencia y grafo negativo con incidencias directas/inversas: cada alternativa de sala aporta origen falso o llave faltante; llave residual apunta a TODAS sus ubicaciones físicamente accesibles; registrar aparte las imposibilidades estructurales sin convertirlas en ciclos. Dep.: T013. Requisitos: FR-RS-007, FR-RS-008, FR-RS-009; PR-RS-002. Escenarios: AC-RS-008, AC-RS-009, AC-RS-010, AC-RS-011, AC-RS-012.
- [X] T015 [US2] Implementar Kosaraju iterativo propio y selección de componentes sin enlaces salientes en modelo/verificacion.py, con marcas, orden y pila aprobados; inicializar arreglos una vez y conservar todas las reglas alternativas del certificado. Dep.: T014. Requisitos: FR-RS-008, FR-RS-009; PR-RS-002. Escenarios: AC-RS-009, AC-RS-010, AC-RS-011, AC-RS-012.
- [X] T016 [US2] Extraer en modelo/verificacion.py un ciclo concreto que incluya llave por grupo pertinente: elegir k→ubicación r y camino r→k dentro de su componente; limitar búsquedas a componentes disjuntas, adjuntar puertas/alternativas y no comprimirlo como exclusividad individual de cada flecha. Dep.: T015. Requisitos: FR-RS-008, FR-RS-009; PR-RS-002; SC-RS-003. Escenarios: AC-RS-009, AC-RS-010, AC-RS-011, AC-RS-012.
- [X] T017 [US2] Completar en modelo/verificacion.py el orden determinista del resultado y en Pruebas/prueba_certificados_resolubilidad.py la validación semántica del certificado completo, varias ubicaciones y muchas componentes; no recorrer casillas hash para imprimir ni consumir RNG del juego. Dep.: T016. Requisitos: FR-RS-004, FR-RS-007, FR-RS-008, FR-RS-009, FR-RS-013; PR-RS-002. Escenarios: AC-RS-006, AC-RS-007, AC-RS-008, AC-RS-009, AC-RS-010, AC-RS-011, AC-RS-012, AC-RS-016.
- [X] T018 [US2] Ejecutar Pruebas/prueba_resolubilidad.py y Pruebas/prueba_certificados_resolubilidad.py; verificar que aislamiento y barreras sin llave no crean ciclos, que un acceso obtenible rompe el supuesto ciclo y que las tablas de salida no introducen coste por puerta×ubicación. Dep.: T017. Requisitos: FR-RS-004, FR-RS-006, FR-RS-007, FR-RS-008, FR-RS-009; PR-RS-002; SC-RS-002, SC-RS-003. Escenarios: AC-RS-006, AC-RS-007, AC-RS-008, AC-RS-009, AC-RS-010, AC-RS-011, AC-RS-012.

## Fase 5 — US4: Datos válidos y presupuesto (P1)

US4 precede a US3 porque consola e inicio necesitan una carga real validada.
Objetivo: fuentes HTTP/offline equivalentes y datos reutilizables durante la
ejecución. Prueba independiente: fuentes simuladas y archivos temporales, sin
instanciar la vista ni construir actores. No requiere acceso a una cripta real.

- [X] T019 [P] [US4] Escribir en Pruebas/prueba_cliente.py los casos de ubicacion_llaves, conteo de petición/reintentos 429, agotamiento previo al siguiente intento y fallo HTTP/JSON; no exigir campo version dentro de la respuesta llaves. Dep.: T018. Requisitos: FR-RS-001, FR-RS-014, FR-RS-015. Escenarios: AC-RS-017, AC-RS-018, AC-RS-020.
- [X] T020 [P] [US4] Escribir en Pruebas/prueba_offline.py y Pruebas/prueba_servicio_cripta.py los casos de llaves.json, enemigo ausente/nulo, varias ubicaciones, archivo ausente/inválido, versiones cambiantes/anteriores, referencias inválidas y carga compartida sin contenido ni doble descarga. Dep.: T018. Requisitos: FR-RS-001, FR-RS-014, FR-RS-015. Escenarios: AC-RS-007, AC-RS-017, AC-RS-018, AC-RS-019, AC-RS-020.
- [X] T021 [US4] Añadir ubicacion_llaves(cripta_id) en adaptadores/fuente_datos.py y adaptadores/cliente_http.py por el _get existente; conservar presupuesto, reintentos y errores; no introducir persistencia ni un índice dict/set. Dep.: T019. Requisitos: FR-RS-001, FR-RS-014, FR-RS-015. Escenarios: AC-RS-017, AC-RS-018, AC-RS-020.
- [X] T022 [US4] Incorporar en adaptadores/modo_offline.py la lectura de criptas/ID/llaves.json con la misma envoltura; respetar "id y sala son requeridos; enemigo es opcional/nulo", múltiples ubicaciones y cero solicitudes HTTP; tratar ausencia/JSON inválido como error. Dep.: T020, T021. Requisitos: FR-RS-001, FR-RS-014, FR-RS-015. Escenarios: AC-RS-007, AC-RS-017, AC-RS-019, AC-RS-020.
- [X] T023 [US4] Preparar en adaptadores/servicio_cripta.py generales, páginas y ubicaciones en listas normalizadas, con identidad/versión coherentes y comprobación final de versión contada en presupuesto; conservar entrada reutilizable en memoria y no construir AVL, actores o descargar contenido para verificar. Dep.: T006, T021, T022. Requisitos: FR-RS-001, FR-RS-013, FR-RS-014, FR-RS-015. Escenarios: AC-RS-007, AC-RS-016, AC-RS-017, AC-RS-018, AC-RS-019, AC-RS-020.
- [X] T024 [US4] Ejecutar Pruebas/prueba_cliente.py, Pruebas/prueba_offline.py y Pruebas/prueba_servicio_cripta.py; comprobar que dato de versión antigua no se reutiliza, no se requiere borrar archivos manualmente y un error de fuente no se convierte en veredicto; sin nueva persistencia de ubicaciones. Dep.: T023. Requisitos: FR-RS-001, FR-RS-014, FR-RS-015. Escenarios: AC-RS-017, AC-RS-018, AC-RS-019, AC-RS-020.

## Fase 6 — US3: Verificar, jugar o forzar (P1)

Objetivo: consulta sin vista y control del inicio con datos reales de la fuente.
Prueba independiente: CLI con fuente offline/simulada, constructor de vista que
falla si se instancia al verificar y comprobaciones de comienzo/no comienzo.

- [X] T025 [US3] Escribir en Pruebas/prueba_cli_resolubilidad.py aceptación de --verificar con códigos 0/1/2, errores de uso antes de red/vista, fuente offline, inicio bloqueado salvo --forzar y errores no forzables; usar fuentes controladas y no hardcodear IDs oficiales. Dep.: T018, T024. Requisitos: FR-RS-003, FR-RS-006, FR-RS-010, FR-RS-011, FR-RS-012, FR-RS-015. Escenarios: AC-RS-013, AC-RS-014, AC-RS-015, AC-RS-020.
- [X] T026 [US3] Integrar --verificar en main.py: exclusión de otros modos y --forzar, permitir --offline, preparar/consultar/imprimir sin vista/actores/motor y devolver 0 soluble, 1 no soluble, 2 error; presentar tablas compartidas y avisos, sin un modo JSON nuevo. Dep.: T023, T025. Requisitos: FR-RS-003, FR-RS-004, FR-RS-006, FR-RS-007, FR-RS-008, FR-RS-009, FR-RS-012. Escenarios: AC-RS-008, AC-RS-009, AC-RS-010, AC-RS-011, AC-RS-015.
- [X] T027 [US3] Adaptar controlador/cargar_partida.py para construir desde datos ya validados y usar la normalización de modelo/verificacion.py; conservar reglas vigentes de costes, misma identidad de puertas, niebla inicial y entidades heredadas, sin repetir consultas de esqueleto/llaves al iniciar después de verificar. Dep.: T006, T023, T025. Requisitos: FR-RS-001, FR-RS-007, FR-RS-010, FR-RS-011, FR-RS-013, FR-RS-014. Escenarios: AC-RS-008, AC-RS-013, AC-RS-014, AC-RS-016, AC-RS-018.
- [X] T028 [US3] Integrar --forzar y el control previo de partidas nuevas en main.py, después de imprimir informe y antes de crear vista/actores; bloquear el resultado negativo sin bandera, permitirlo con bandera sin alterar reglas y no saltar errores; cargar/replay no repiten la verificación. Dep.: T026, T027. Requisitos: FR-RS-010, FR-RS-011, FR-RS-012, FR-RS-013, FR-RS-015. Escenarios: AC-RS-013, AC-RS-014, AC-RS-015, AC-RS-016, AC-RS-020.
- [X] T029 [US3] Añadir en Pruebas/prueba_cli_resolubilidad.py y Pruebas/prueba_bitacora_partida.py verificaciones de cero consultas nuevas de llaves en cargar/replay, no mutación de reloj/RNG/inventario/actores/historial/mapa conocido y equivalencia entre topología verificada y jugada, incluyendo puerta ambigua sin fusión. Dep.: T028. Requisitos: FR-RS-007, FR-RS-009, FR-RS-011, FR-RS-012, FR-RS-013, FR-RS-014. Escenarios: AC-RS-008, AC-RS-014, AC-RS-015, AC-RS-016, AC-RS-018.
- [X] T030 [US3] Ejecutar Pruebas/prueba_cli_resolubilidad.py, Pruebas/prueba_bitacora_partida.py y las regresiones de Pruebas/prueba_terreno.py, Pruebas/prueba_niebla_partida.py y Pruebas/prueba_estado_binario.py; verificar --help y los comandos del contrato sin presentar banderas no implementadas. Dep.: T029. Requisitos: FR-RS-007, FR-RS-010, FR-RS-011, FR-RS-012, FR-RS-013; SC-RS-004. Escenarios: AC-RS-008, AC-RS-013, AC-RS-014, AC-RS-015, AC-RS-016.

## Fase 7 — Rendimiento, evidencia y cierre

Todas las historias son P1 y forman la entrega requerida. No cambiar estructuras
para obtener mejores cifras sin elección del usuario. Si falla un límite,
registrarlo y corregir lo autorizado; no marcar la tarea como cumplimiento.

- [X] T031 Escribir en Pruebas/prueba_bench_resolubilidad.py casos de igualdad de veredicto con referencia lenta, semilla reproducible y contadores en cadenas, muchas componentes, ubicaciones/alternativas y preparación incluida; separar corrección de aserciones frágiles de tiempo. Dep.: T030. Requisitos: FR-RS-009; PR-RS-001, PR-RS-002, PR-RS-003; SC-RS-005.
- [X] T032 Implementar en modelo/bench_resolubilidad.py cargas sintéticas por semilla y referencia por recorridos repetidos, comparándola con el incremental; registrar preparación/cierre/diagnóstico/informe/total, sondeos y tamaño de entrada sin ocultar coste por llave/componente ni repetir tablas completas. Dep.: T031. Requisitos: FR-RS-009; PR-RS-001, PR-RS-002, PR-RS-003; SC-RS-005.
- [X] T033 Integrar el benchmark en modelo/bench_modelo.py y main.py manteniendo comparaciones existentes y modos sin vista; en referencia oficial reutilizar datos validados y medir procesamiento local completo excluyendo HTTP/renderizado, sin bloquear la medición de una cripta negativa como si fuera inicio interactivo. Dep.: T032. Requisitos: FR-RS-012, FR-RS-014; PR-RS-001, PR-RS-002, PR-RS-003; SC-RS-005.
- [X] T034 Ejecutar los benchmarks sintéticos y Pruebas/prueba_bench_resolubilidad.py; guardar resultados, semilla, equipo/Python, repeticiones, huellas, máximos/crecimiento y comparación en documentacion/evidencia/mediciones_resolubilidad.json y documentacion/evidencia/bench_resolubilidad.txt. Dep.: T033. Requisitos: FR-RS-009; PR-RS-002, PR-RS-003; SC-RS-005.
- [X] T035 Identificar la mayor cripta publicada al medir, verificar versiones, medir el límite local <200 ms sin red/renderizado y registrar solicitudes, preparación y diagnóstico en documentacion/evidencia/mediciones_resolubilidad.json; conservar cualquier incumplimiento y no usar cifras de niebla/terreno como prueba. Dep.: T034. Requisitos: FR-RS-014, FR-RS-015; PR-RS-001; SC-RS-005.
- [X] T036 Ejecutar aceptación de los 20 AC y regresión completa; guardar comandos/resultados reales en documentacion/evidencia/pruebas_resolubilidad.txt y comprobar en modelo/verificacion.py, modelo/indice_llaves.py, adaptadores/ y main.py ausencia de estructuras prohibidas, datos oficiales incrustados y vista en modos no interactivos. Dep.: T035. Requisitos: FR-RS-001, FR-RS-002, FR-RS-003, FR-RS-004, FR-RS-005, FR-RS-006, FR-RS-007, FR-RS-008, FR-RS-009, FR-RS-010, FR-RS-011, FR-RS-012, FR-RS-013, FR-RS-014, FR-RS-015; SC-RS-001, SC-RS-002, SC-RS-003, SC-RS-004.
- [X] T037 Actualizar README.md, documentacion/DOCUMENTO_DECISIONES.md, specs/003-verificar-resolubilidad/quickstart.md y specs/003-verificar-resolubilidad/contracts/verificacion.md con comandos realmente disponibles, decisiones, mediciones finales y límites; conservar referencias históricas e indicar cualquier limitación por P1 ausente. Dep.: T036. Requisitos: FR-RS-007, FR-RS-008, FR-RS-010, FR-RS-011, FR-RS-012, FR-RS-014; PR-RS-001, PR-RS-002, PR-RS-003; SC-RS-005.
- [X] T038 Completar en specs/003-verificar-resolubilidad/tasks.md la cadena requisito→AC→tarea→código→función de prueba/log ejecutado, registrar prompts de implementación en documentacion/PROMPTS_LLM.md y confirmar en Git tras verificar; no inventar evidencias ni marcar incumplimientos como terminados. Dep.: T037. Requisitos: FR-RS-001, FR-RS-002, FR-RS-003, FR-RS-004, FR-RS-005, FR-RS-006, FR-RS-007, FR-RS-008, FR-RS-009, FR-RS-010, FR-RS-011, FR-RS-012, FR-RS-013, FR-RS-014, FR-RS-015; PR-RS-001, PR-RS-002, PR-RS-003; SC-RS-001, SC-RS-005.

## Dependencias y oportunidades de trabajo independiente

Orden de fases: preparación → fundamentos → US1 → US2 → US4 → US3 → cierre.
Las dependencias explícitas por tarea son obligatorias. T004 puede redactarse
tras T001 antes de T003, pero no ejecutar implementación de historias antes
de completar T006. La fase US4 se adelanta a US3 por la carga y versiones;
no se simula como terminada una historia de CLI con adaptadores aún ausentes.

T019 y T020 son las dos tareas marcadas [P]: tras T018 pueden escribirse en
archivos distintos. Las demás comparten archivos o requieren resultados previos.
Ejemplos por historia, si un equipo humano coordina ramas/archivos:

- US1: preparar un caso de victoria mientras se revisan casos de puertas en
  datos temporales distintos; las ediciones de modelo/verificacion.py son secuenciales.
- US2: revisar manualmente el certificado de un caso mientras se documenta otro;
  no editar simultáneamente el mismo modelo o archivo de pruebas.
- US4: T019 (HTTP) y T020 (offline/servicio), sin conflictos de archivo.
- US3: contrastar salida esperada del CLI mientras se inspecciona un log existente;
  la integración de main.py y la escritura de pruebas compartidas son secuenciales.

Esto describe oportunidades, no delega trabajo ni elimina dependencias.
MVP: modelo US1 verificable; continuar US2/US4/US3 para una capacidad completa.
No desplegar ni presentar ese MVP como verificador de consola terminado.

## Trazabilidad prevista: requisitos, escenarios y tareas

La tabla siguiente conserva la planificación original. Al final figura la
cadena ejecutada con archivos y funciones reales; esa sección y la evidencia
son las referencias para comprobar ejecución, no la mera existencia de una tarea.

| Escenario | Requisitos funcionales | Tareas de implementación/validación | Prueba prevista |
| --- | --- | --- | --- |
| AC-RS-001 | FR-RS-001, FR-RS-002, FR-RS-003, FR-RS-004 | T005, T007, T008, T009, T010 | Pruebas/prueba_resolubilidad.py |
| AC-RS-002 | FR-RS-002, FR-RS-004, FR-RS-005 | T007, T008, T010 | Pruebas/prueba_resolubilidad.py |
| AC-RS-003 | FR-RS-003, FR-RS-006 | T007, T009, T010, T012 | Pruebas/prueba_resolubilidad.py |
| AC-RS-004 | FR-RS-003, FR-RS-006 | T007, T009, T010, T012 | Pruebas/prueba_resolubilidad.py |
| AC-RS-005 | FR-RS-002, FR-RS-003 | T007, T008, T009, T010 | Pruebas/prueba_resolubilidad.py |
| AC-RS-006 | FR-RS-004, FR-RS-009 | T008, T011, T017, T018 | Pruebas/prueba_certificados_resolubilidad.py |
| AC-RS-007 | FR-RS-001, FR-RS-002 | T004, T005, T008, T011, T020, T022, T023 | Pruebas/prueba_resolubilidad.py; Pruebas/prueba_offline.py |
| AC-RS-008 | FR-RS-006, FR-RS-007 | T004, T006, T011, T012, T014, T017, T018, T027, T029 | Pruebas/prueba_normalizacion_resolubilidad.py; Pruebas/prueba_certificados_resolubilidad.py; Pruebas/prueba_cli_resolubilidad.py |
| AC-RS-009 | FR-RS-003, FR-RS-006, FR-RS-007, FR-RS-008 | T011, T012, T013, T014, T015, T016, T017, T018 | Pruebas/prueba_certificados_resolubilidad.py |
| AC-RS-010 | FR-RS-006, FR-RS-007, FR-RS-008, FR-RS-009 | T011, T012, T013, T014, T015, T016, T017, T018 | Pruebas/prueba_certificados_resolubilidad.py |
| AC-RS-011 | FR-RS-002, FR-RS-003, FR-RS-005, FR-RS-008 | T011, T013, T014, T015, T016, T017, T018 | Pruebas/prueba_certificados_resolubilidad.py |
| AC-RS-012 | FR-RS-006, FR-RS-007, FR-RS-008 | T011, T012, T013, T014, T015, T016, T017, T018 | Pruebas/prueba_certificados_resolubilidad.py |
| AC-RS-013 | FR-RS-006, FR-RS-010 | T025, T027, T028, T030 | Pruebas/prueba_cli_resolubilidad.py |
| AC-RS-014 | FR-RS-010, FR-RS-011 | T025, T027, T028, T029, T030 | Pruebas/prueba_cli_resolubilidad.py |
| AC-RS-015 | FR-RS-003, FR-RS-006, FR-RS-012 | T025, T026, T028, T029, T030 | Pruebas/prueba_cli_resolubilidad.py; Pruebas/prueba_bitacora_partida.py |
| AC-RS-016 | FR-RS-009, FR-RS-011, FR-RS-013 | T010, T013, T017, T023, T027, T028, T029, T030 | Pruebas/prueba_cli_resolubilidad.py; Pruebas/prueba_resolubilidad.py |
| AC-RS-017 | FR-RS-001, FR-RS-014 | T004, T005, T006, T019, T020, T021, T022, T023, T024 | Pruebas/prueba_cliente.py; Pruebas/prueba_offline.py; Pruebas/prueba_servicio_cripta.py |
| AC-RS-018 | FR-RS-014 | T019, T020, T021, T023, T024, T027, T029 | Pruebas/prueba_cliente.py; Pruebas/prueba_servicio_cripta.py; Pruebas/prueba_cli_resolubilidad.py |
| AC-RS-019 | FR-RS-014, FR-RS-015 | T020, T022, T023, T024 | Pruebas/prueba_offline.py; Pruebas/prueba_servicio_cripta.py |
| AC-RS-020 | FR-RS-001, FR-RS-015 | T004, T005, T006, T019, T020, T021, T022, T023, T024, T025, T028 | Pruebas/prueba_normalizacion_resolubilidad.py; Pruebas/prueba_cliente.py; Pruebas/prueba_cli_resolubilidad.py |

Apéndice B: caso 1 → AC-RS-009; caso 2 → AC-RS-007;
caso 3 → AC-RS-006; caso 4 → AC-RS-013. T036 ejecuta la aceptación completa.

| Requisito de rendimiento / criterio | Tareas | Evidencia futura |
| --- | --- | --- |
| PR-RS-001 | T031, T032, T033, T035, T037 | mediciones_resolubilidad.json y bench_resolubilidad.txt |
| PR-RS-002 | T003, T008, T010, T012 a T018, T031 a T034 | Contadores, crecimiento, tiempos completos y límites de colisiones |
| PR-RS-003 | T031, T032, T033, T034, T037 | Comparación incremental/repetido con semilla y entradas crecientes |
| SC-RS-001 | T001, T036, T038 | Pruebas que citen AC/FR y trazabilidad ejecutada |
| SC-RS-002 | T010, T018, T036 | Veredicto, orden y repetibilidad |
| SC-RS-003 | T016, T018, T036 | Certificados con alternativas y testigo válido |
| SC-RS-004 | T030, T036 | CLI, forzar y no mutación |
| SC-RS-005 | T031 a T035, T037, T038 | Medición sintética/oficial y documentación de límites |

## Criterio de cierre

Marcar tareas solo con evidencia comprobable. Un resultado de análisis de
documentos no cuenta como prueba del verificador. Si falta acceso al servicio,
dejar pendiente la medición oficial, sin reemplazarla por una cifra sintética.
Conservar evidencia de cualquier incumplimiento. La línea de tiempo no forma
parte de estas tareas y el binario vigente no cambia por guardar resultados
temporales de verificación.

## Trazabilidad ejecutada

556 pruebas aprobadas en la regresión completa. Las siguientes funciones
existen y se ejecutaron; citan requisitos/escenarios en docstrings o comentarios.
El prefijo de requisito de esta tabla es FR-RS-. Los archivos de código son
relativos a la raíz. Los estados de tarea se marcaron tras verificar cada bloque.

| AC-RS | FR-RS | Tareas | Código | Función de prueba ejecutada |
| --- | --- | --- | --- | --- |
| 001 | 001/002/003/004 | T005, T007–010 | modelo/verificacion.py:normalizar/cerrar/verificar | Pruebas/prueba_resolubilidad.py:test_ac001_002_005_cadena_y_llaves_no_consumidas |
| 002 | 002/004/005 | T007–010 | modelo/verificacion.py:cerrar | Pruebas/prueba_resolubilidad.py:test_ac001_002_005_cadena_y_llaves_no_consumidas |
| 003 | 003/006 | T007, T009, T010, T012 | modelo/verificacion.py:resultado_de_cierre | Pruebas/prueba_resolubilidad.py:test_ac003_004_sala_salida_sola_no_basta |
| 004 | 003/006 | T007, T009, T010, T012 | modelo/verificacion.py:resultado_de_cierre | Pruebas/prueba_resolubilidad.py:test_ac003_004_sala_salida_sola_no_basta |
| 005 | 002/003 | T007–010 | modelo/verificacion.py:cerrar/resultado_de_cierre | Pruebas/prueba_resolubilidad.py:test_ac001_002_005_cadena_y_llaves_no_consumidas |
| 006 | 004/009 | T008, T011, T017, T018 | modelo/verificacion.py:cerrar | Pruebas/prueba_resolubilidad.py:test_ac006_007_016_repetible_sin_mutar_datos_y_botin_inicial |
| 007 | 001/002 | T004, T005, T008, T020, T022, T023 | modelo/verificacion.py:normalizar/cerrar; adaptadores/modo_offline.py:ubicacion_llaves | Pruebas/prueba_resolubilidad.py:test_ac006_007_016_repetible_sin_mutar_datos_y_botin_inicial; Pruebas/prueba_offline.py:test_rs_ac007_017_019_020_llaves_offline |
| 008 | 006/007 | T004, T006, T011, T012, T027, T029 | modelo/verificacion.py:agrupar_puertas/resultado_de_cierre; controlador/cargar_partida.py:_construir_esqueleto | Pruebas/prueba_certificados_resolubilidad.py:test_ac008_009_autobloqueo_concreto_y_frontera_unica; Pruebas/prueba_cli_resolubilidad.py:test_ac008_puertas_ambiguas_igual_en_modelo_y_juego |
| 009 | 003/006/007/008 | T011–018 | modelo/verificacion.py:_diagnosticar | Pruebas/prueba_certificados_resolubilidad.py:test_ac008_009_autobloqueo_concreto_y_frontera_unica |
| 010 | 006/007/008/009 | T011–018 | modelo/verificacion.py:_diagnosticar/_componentes | Pruebas/prueba_certificados_resolubilidad.py:test_ac010_ciclo_dos_llaves_y_orden_determinista |
| 011 | 002/003/005/008 | T011, T013–018 | modelo/verificacion.py:cerrar/_diagnosticar | Pruebas/prueba_certificados_resolubilidad.py:test_ac011_alternativa_obtenible_rompe_ciclo; Pruebas/prueba_certificados_resolubilidad.py:test_ac011_grupo_or_conserva_ambas_alternativas; Pruebas/prueba_certificados_resolubilidad.py:test_ac011_regresion_b_por_a_no_significa_b_exclusiva |
| 012 | 006/007/008 | T011–018 | modelo/verificacion.py:_diagnosticar | Pruebas/prueba_certificados_resolubilidad.py:test_ac012_aislamiento_y_pasillos_no_son_ciclos; Pruebas/prueba_certificados_resolubilidad.py:test_varias_ubicaciones_conserva_alternativas_y_aisladas |
| 013 | 006/010 | T025, T027, T028, T030 | main.py:main | Pruebas/prueba_cli_resolubilidad.py:test_ac013_no_inicia_sin_forzar |
| 014 | 010/011 | T025, T027–030 | main.py:main; controlador/cargar_partida.py:crear | Pruebas/prueba_cli_resolubilidad.py:test_ac014_forzar_llega_al_cargador_pero_no_salta_error; Pruebas/prueba_cli_resolubilidad.py:test_ac014_016_inicio_real_no_muta_y_reusa_carga |
| 015 | 003/006/012 | T025, T026, T028–030 | main.py:main/informe_verificacion | Pruebas/prueba_cli_resolubilidad.py:test_ac015_consulta_sin_vista_motor_ni_cargador; Pruebas/prueba_cli_resolubilidad.py:test_ac015_combinaciones_invalidas_antes_de_red; Pruebas/prueba_cli_resolubilidad.py:test_ac014_016_inicio_real_no_muta_y_reusa_carga |
| 016 | 009/011/013 | T010, T013, T017, T023, T027–030 | modelo/verificacion.py:verificar; controlador/cargar_partida.py:crear; main.py:main | Pruebas/prueba_cli_resolubilidad.py:test_ac014_016_inicio_real_no_muta_y_reusa_carga; Pruebas/prueba_resolubilidad.py:test_ac006_007_016_repetible_sin_mutar_datos_y_botin_inicial |
| 017 | 001/014 | T019–024 | adaptadores/servicio_cripta.py:preparar_verificacion; adaptadores/cliente_http.py:ubicacion_llaves | Pruebas/prueba_servicio_cripta.py:test_rs_ac017_018_carga_reutilizada_sin_contenido; Pruebas/prueba_cliente.py:test_rs_ac017_018_llaves_y_reintentos_cuentan |
| 018 | 014 | T019–024, T027, T029 | adaptadores/cliente_http.py:_get/ubicacion_llaves; adaptadores/servicio_cripta.py:cargar | Pruebas/prueba_cliente.py:test_rs_ac017_018_llaves_y_reintentos_cuentan; Pruebas/prueba_servicio_cripta.py:test_rs_ac017_018_carga_reutilizada_sin_contenido |
| 019 | 014/015 | T020, T022–024 | adaptadores/servicio_cripta.py:preparar_verificacion | Pruebas/prueba_servicio_cripta.py:test_rs_ac019_020_version_y_referencias_invalidas; Pruebas/prueba_offline.py:test_rs_ac007_017_019_020_llaves_offline |
| 020 | 001/015 | T004–006, T019–025, T028 | adaptadores/servicio_cripta.py:preparar_verificacion; main.py:main | Pruebas/prueba_cli_resolubilidad.py:test_ac020_error_no_es_no_resoluble; Pruebas/prueba_normalizacion_resolubilidad.py:test_datos_invalidos; Pruebas/prueba_cliente.py:test_rs_ac020_llaves_json_invalido_es_error |

PR-RS-001/002/003 y SC-RS-005: T031–035, T037–038;
`Pruebas/prueba_bench_resolubilidad.py:test_cadena_semilla_y_trabajo_incremental`
y `test_muchas_componentes_y_ubicaciones`. El oráculo independiente de
`Pruebas/prueba_certificados_resolubilidad.py:test_cierre_y_certificado_con_todas_alternativas_contra_oraculo`
contrasta 25 grafos dirigidos con cierres repetidos, barreras y ubicaciones múltiples.

Evidencia: [pruebas](../../documentacion/evidencia/pruebas_resolubilidad.txt),
[mediciones](../../documentacion/evidencia/mediciones_resolubilidad.json),
[salida de bench](../../documentacion/evidencia/bench_resolubilidad.txt) y
[entrada externa capturada](../../documentacion/evidencia/entrada_resolubilidad_oficial.json).
Mayor referencia publicada al medir: cripta-06, 300 salas, f9ed9afa683d, 25
repeticiones, máximo 7,5888 ms, 0 ≥200 ms y 10/63 solicitudes. Consulta de
cripta-05: código 1, ciclo concreto y 4/25 solicitudes. Sintéticos: nueve
cargas y tres repeticiones estructuradas, máximo total 38,1568 ms. La referencia
lenta compara cierre/veredicto, no certificados; esos tiempos no son totales
equivalentes. Se conservan sondeos, contadores, entorno y huellas vigentes.

Auditoría final: índices propios, sin imports de estructuras prohibidas ni
ordenamientos nativos; datos oficiales solo en evidencia externa, no en el
código de aplicación. El modelo no importa vista/HTTP. Normalización común
al juego y consulta, carga/replay sin verificación nueva y binario en versión 5.
P1 original sigue ausente; no se inventan reglas de ese documento.
