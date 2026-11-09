# Contratos: Niebla y viaje

**Fecha**: 2026-11-09. Contratos implementados y verificados; véase tasks.md.
**Referencias**: [especificación](../spec.md), [modelo de datos](../data-model.md).

## Consola

- `ver mapa`: consulta sin acción, tiempo virtual ni azar. Presenta exploradas,
  sus nombres/salidas/costos y puertas recordadas, y existencia de avistadas.
  No enumera desconocidas ni presenta nombres o contenido de avistadas.
- `ir a <sala>`: admite ID o nombre completo. Preservar el argumento completo
  y sus mayúsculas. Resolverlo exclusivamente como destino explorado; si el nombre
  coincide con varias exploradas, pedir ID sin acción ni tiempo. Los errores
  no revelan si hay coincidencias en salas ocultas.
- Sala actual: «Ya estás en esa sala», sin acción ni tiempo.
- Conservar `ir <n/s/e/o>`, w/a/s/d y todos los comandos anteriores.
- Viaje por pasos automáticos: no pedir confirmación para continuar. Si hay
  entrada del jugador entre pasos, cancelar y procesar su comando. Para
  `retroceder`, ejecutar el pergamino una sola vez tras el último paso completo
  y no reanudar el viaje. La entrada de interrupción se inyecta en pruebas.
- Detener e informar llegada, enemigos al entrar (activos o dormidos), daño o
  ausencia de ruta; muerte/victoria conserva el final ordinario. No abrir puertas.

## Modelo y vista

El modelo expone una proyección que solo contiene información permitida, no
objetos del esqueleto completo para que la vista los inspeccione. Tanto paneles
como mensajes de movimiento, apertura/cierre y enemigos deben respetarla:
no nombrar una sala avistada como si estuviera explorada. El contenido solo
se presenta cuando las reglas de P1 lo permiten; antorcha no lo revela.

Una consulta de estado o mapa no observa puertas ni produce deltas. El motor
actualiza conocimiento al iniciar y durante acciones/eventos locales autorizados.
Concluir una entrada con antorcha no precarga ni activa las vecinas reveladas.

Contrato de búsqueda: recibir origen/destino conocidos y obtener próximo paso
permitido, costo total o ausencia de ruta. Ninguna salida física sustituye el
recuerdo. Recalcular antes de cada paso; mantener el wrapper y rango del cazador.
No consumir reloj ni azar durante el cálculo.

## Registro y replay

Comentario de depuración propuesto: `# ir a <argumento original>`.
El escritor rechaza saltos de línea, como en P1. Replay ignora comentarios
prefijados por # antes de interpretar acciones, sin contarlos como acciones
del jugador. Cada paso ejecutado se registra una sola vez como movimiento
ordinario reproducible; no registrar la orden como acción compuesta.

Ejemplo sintético de formato, no ruta oficial ni guion de aceptación ejecutado:

```text
# ir a Biblioteca
w
d
retroceder
```

El comentario no ordena repetir el viaje. Replay usa versiones/semilla del
encabezado y las acciones; no crea vista ni requiere teclado o interrupción.
Los rechazos y `ver mapa` no se convierten en acciones del log.

## Persistencia

Modelo binario 5: conservar estado conocido, recuerdo posiblemente desactualizado,
identidad compartida y deltas. Reconstruir ID → posición y auxiliares derivados.
Validar índices y referencias; informar incompatibilidad de versiones anteriores,
sin cargarlas silenciosamente. No alterar presupuesto o versiones de datos.

## Trazabilidad prevista para tareas y evidencia

Cada grupo enumera los escenarios; las pruebas citan FR además del AC.
La cadena ejecutada y los nombres de pruebas se conservan en tasks.md.

| FR | AC | Integración prevista | Evidencia por crear |
| --- | --- | --- | --- |
| FR-NV-001/002 | 001/002/003/006/008 | conocimiento, inicialización y proyección | estados iniciales, transiciones, ocultación |
| FR-NV-003 | 004/005/006/013/021 | observación y recuerdo compartido | cierre remoto/local, ambos extremos, persistencia |
| FR-NV-004 | 001/004/005 | parser, controlador y vista | ver mapa sin mutar reloj/azar |
| FR-NV-005 | 003/010/017 | proyección, mensajes y búsqueda | precarga sin revelación y sin atajos ocultos |
| FR-NV-006/007 | 006/007/008/014 | entrada y antorcha | vecinas abiertas/cerradas, sin activación remota |
| FR-NV-008 | 009 | resolución de destino | ID/nombre exacto, repetidos, desconocido |
| FR-NV-009/010 | 010/011/013/016 | núcleo de ruta y acceso al conocimiento | ponderación, desempate, no abrir puertas |
| FR-NV-011/012 | 012/013/014/015/020 | pasos ordinarios y recálculo | tiempos, eventos, generaciones y retroceso |
| FR-NV-013 | 013/014/015/016/017 | ciclo de viaje y sucesos de entrada/daño | cada parada, enemigo que sale, daño seguido de cura |
| FR-NV-014/015 | 005/018/022 | comentarios, pasos y replay | igualdad de estado sin vista ni azar extra |
| FR-NV-016 | 019/020 | deltas existentes y cancelación | restaurar estados/listas/puertas y último paso |
| FR-NV-017 | 021/022 | formato binario y reconstrucción | guardar/cargar/retroceder, referencias compartidas |

Los AC se leen con prefijo AC-NV-. PR-NV-001/002/003 corresponden a mediciones
en bench_conocimiento y --bench: paso completo <5 ms en referencia conocida,
actualización proporcional a revelación y consultas de estados/puertas.
Los resultados finales y límites irán al Documento de Decisiones; este contrato
no sustituye una tarea ni una prueba.
