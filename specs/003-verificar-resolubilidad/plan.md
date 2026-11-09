# Plan: Verificación de resolubilidad

**Fecha**: 2026-11-09. **Rama real**: `main`.
**Capacidad activa de spec-kit**: `003-verificar-resolubilidad`.
**Especificación**: [spec.md](spec.md).
**Estado**: Borrador de fase 0; siete decisiones pendientes del usuario.
No autoriza implementación ni constituye un diseño final aprobado.

## Resumen

Determinar la posibilidad de escapar con esqueleto y ubicaciones de llaves,
sin vista ni simulación de actores. Entregar orden válido o informe negativo,
integrando bloqueo de partidas nuevas y forzar, sin cambiar carga/replay.
Las reglas están en spec.md; las alternativas en [research.md](research.md).
Se estudia un cierre incremental: alcanzar una sala permite obtener sus llaves;
obtener una llave activa los pasos que esperaban esa llave. Ninguna estructura
ha sido elegida para esta capacidad.

## Contexto técnico

- Python 3.11 o superior; CLI/MVC actuales; pytest; sin nueva dependencia propuesta.
- HTTP y JSON offline existentes; falta integrar consulta de ubicaciones mediante
  FuenteDatos, ClienteHTTP y ModoOffline, conservando presupuesto/reintentos.
- Estructuras: NEEDS CLARIFICATION, D-RS-01 a D-RS-06 de research.md.
- Persistencia opcional de ubicaciones: NEEDS CLARIFICATION, D-RS-07.
- PR-RS-001: menos de 200 ms locales en la mayor cripta publicada, excluyendo red
  y renderizado; PR-RS-002: crecimiento aproximadamente lineal; PR-RS-003:
  comparación incremental frente a recorrido completo repetido por llave.
- S = salas, E = salidas, K = llaves; contemplar también longitud de IDs textuales.
- Diagnóstico de ciclos: falta demostrar corrección con alternativas y ciclos
  aparentes. Aprobar la representación no acredita el algoritmo.

## Comprobación de la constitución

| Principio | Estado de fase 0 |
| --- | --- |
| I. Estructuras manuales | Restricción vigente; decisiones pendientes, sin índices dict/set ni bibliotecas prohibidas. |
| II. Determinismo | Orden explícito pendiente del diseño; no usar azar de partida. |
| III. MVC y modos sin vista | Consulta sobre datos, sin exigir actores ni conocimiento del jugador. |
| IV. Datos externos | Esqueleto y ubicaciones de la fuente; sin respuestas por ID de cripta. |
| V. Presupuesto/versiones | Integrar por _get, validar datos y evitar descarga duplicada al iniciar. |
| VI. Rendimiento | Medición prevista, todavía no acreditada. |
| VII. Especificación anterior | Spec y aclaraciones confirmadas antes del código; este plan es borrador. |
| VIII. Trazabilidad | Conservar FR/PR/AC/SC; tareas y pruebas se enlazarán tras cerrar el plan. |
| IX. Prompts | Inicio y decisiones agrupados en PROMPTS_LLM.md. |

**Salida de fase 0 pendiente**: elecciones del usuario y justificación del
análisis de ciclos. No generar diseño final, contratos ni tareas todavía.
No se solicitan excepciones a la constitución.

## Áreas de integración examinadas

- `modelo/`: verificador puro y auxiliares propios, ubicación concreta pendiente.
- `adaptadores/fuente_datos.py`, `cliente_http.py` y `modo_offline.py`: ubicaciones.
- `adaptadores/servicio_cripta.py`: carga y AVL existentes; contabilizar preparación.
- `controlador/cargar_partida.py`: compartir datos validados al iniciar sin repetir
  consultas; conservar alcance aprobado para carga/replay.
- `main.py`: modos excluyentes, códigos 0/1/2 y bloqueo salvo forzar.
- `Pruebas/`: AC-RS-001 a AC-RS-020 con referencias a requisitos.

## Validación y mediciones previstas

1. Casos de victoria completa, cierre incremental, botín en sala inicial,
   frontera sin duplicados, ciclos reales y aparentes con alternativas.
2. Comparar veredicto con recorrido repetido de referencia en casos sintéticos
   deterministas; la alternativa lenta se reserva a pruebas y bench.
3. Medir preparación, alcanzabilidad y diagnóstico por separado y total local,
   sin ocultar costes del AVL/normalización; excluir HTTP y renderizado.
4. Identificar mayor cripta publicada al medir y registrar versiones, solicitudes,
   entorno, repeticiones y huellas. Niebla no acredita resolubilidad.
5. Regresión apropiada de partida, niebla, replay, presupuesto y persistencia
   cuando exista implementación.

## Artefactos y siguiente paso

Generados: este borrador y research.md. Pendientes: cerrar fase 0, data-model.md,
contracts/, quickstart.md y revisión final de constitución. tasks.md pertenece
al flujo posterior de speckit-tasks. No hay implementación ni mediciones nuevas.
