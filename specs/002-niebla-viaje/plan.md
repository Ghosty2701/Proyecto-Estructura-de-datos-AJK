# Plan de implementación: Niebla de guerra y viaje «ir a»

**Rama Git real**: `main` | **Fecha**: 2026-11-09 | **Especificación**: [spec.md](spec.md).
**Entrada**: `specs/002-niebla-viaje/spec.md`.
**Estado**: Diseño aprobado e implementación verificada el 2026-11-09.
Las 30 tareas de [tasks.md](tasks.md) se cerraron con evidencia de ejecución.
El script devuelve `002-niebla-viaje` como identificador de capacidad; no es
una rama Git nueva. La implementación fue autorizada por el usuario después del
cierre del diseño y precedida por tareas y análisis.

## Summary

Mantener conocimiento separado del esqueleto y del contenido descargado; observar
puertas, revelar por antorcha y revertir esos cambios. Incorporar `ver mapa` y
viajes por costo mínimo sobre conocimiento, con acciones, paradas y replay
ordinarios. La especificación y sus aclaraciones están confirmadas antes del
código en `8c20823` y `9a534fd`.

D-NV-01 está aprobada: arreglo de conocimiento por posiciones compactas del
esqueleto, con acceso O(1) por posición y espacio O(S). D-NV-02 también está
aprobada: tabla hash propia ID → posición, con consulta O(1) esperada y O(S)
en peor caso. D-NV-02a aprobada: colisiones mediante doble hashing.
D-NV-02b aprobada: reserva inicial con máximo 70 %, capacidad potencia de dos,
salto impar y sondeo acotado. D-NV-03 aprobada: listas de salidas conocidas por
sala con recuerdo de puerta compartido por ambos sentidos, separado de la puerta
real. D-NV-04 aprobada: núcleo Dijkstra compartido, con accesos separados al
esqueleto real del cazador y al mapa conocido del jugador. D-NV-04a aprobada:
arreglo de registros por posición compacta y reutilización del heap indexado
propio, con instancias separadas. D-NV-04b aprobada: marcas de generación;
se inicializan solo registros alcanzados en cada búsqueda nueva.
D-NV-05 aprobada: deltas de atributos y referencias en la lista de cambios
existente, restaurados en orden inverso, sin snapshots del mapa por acción.
D-NV-06 aprobada: resolver nombres recorriendo el arreglo existente una vez
al recibir la orden, comparando solo nombres revelados de salas exploradas.
Las aprobaciones D-TC de terreno y cazadores no se
extienden automáticamente al mapa conocido o a «ir a».
D-NV-07 aprobada: referencia directa puerta → recuerdo reservado al iniciar,
sin observar y sin otro índice. Las alternativas y aprobaciones están en
[research.md](research.md). El diseño de entidades está en
[data-model.md](data-model.md), los contratos en
[contracts/niebla-viaje.md](contracts/niebla-viaje.md) y la validación prevista
en [quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python 3.11 o superior; entorno documentado 3.14.6.
**Primary Dependencies**: requests y pytest existentes; ninguna dependencia nueva propuesta.
**Storage**: ampliar el formato binario explícito de modelo 4 a 5, conservando
conocimiento y deltas reversibles. Rechazar versiones anteriores con diagnóstico
claro. Reconstruir índices y auxiliares derivados al cargar.
**Testing**: pytest. Línea base de 469 pruebas; cierre de 492 aprobadas, con
evidencia de AC-NV-001 a AC-NV-022 en tasks.md.
**Target Platform**: consola en Windows/PowerShell; modelo y replay sin vista.
**Project Type**: aplicación MVC con adaptadores de datos externos.
**Performance Goals**: PR-NV-001, paso de «ir a» <5 ms con conocimiento completo
de la referencia; PR-NV-002, actualizar en función de revelación; PR-NV-003, medir.
**Constraints**: estructuras propias; sin dict/set como índices, heapq, bisect,
collections ni bibliotecas de grafos; sin filtrar conocimiento desde infraestructura.
Presupuesto y validación de versiones vigentes.
**Scale/Scope**: conocimiento vacío/parcial/completo; IDs dispersos; puertas
recordadas distintas de las reales; viajes y antorcha con retroceso.
**Decisiones técnicas**: D-NV-01 a D-NV-07 y variantes aprobadas explícitamente;
ninguna elección de estructura pendiente. Una sustitución posterior requiere
presentar alternativas y esperar elección del usuario.

### Integraciones revisadas

- `controlador/comandos.py:parsear` convierte todo el texto a minúsculas y solo
  conserva el primer argumento. Debe preservar nombres completos y su capitalización
  para FR-NV-008, además de conservar los comandos anteriores.
- `controlador/controlador.py:_registrar` también convierte a minúsculas. Los
  pasos se registrarán como movimientos ordinarios; el comentario del viaje debe
  quedar separado de las acciones ejecutables y no duplicarlas (FR-NV-014).
- `modelo/rutas.py:buscar_ruta` usa las salas y las puertas reales y exige rango
  entero. No puede usarse directamente con salas reales para el viaje: revelaría
  conexiones y estados no conocidos. D-NV-04 comparte el núcleo con accesos
  separados; D-NV-04a/04b define arreglo, heap indexado y generaciones para viaje.
- `modelo/tabla_hash.py:TablaDistancias` es especializada en distancias y no
  tiene borrado. No se declara reutilizable sin cambios para conocimiento reversible.
- `adaptadores/cache_catalogo.py:ArbolAVL` ya implementa búsqueda, inserción y
  borrado. Su existencia no autoriza usarlo como índice del conocimiento.
- `controlador/partida.py:estado` expone nombres de destinos reales y
  `_ejecutar_evento` forma mensajes usando salas reales. Revisar ambos y la vista
  para AC-NV-003; no basta con añadir una pantalla de mapa.
- `modelo/motor_eventos.py` delimita acciones y entradas. La revelación y las
  observaciones deben registrarse en la acción correspondiente, no al renderizar.
- `modelo/retroceso.py` ya invierte deltas en orden inverso. D-NV-05 usa sus
  deltas de atributos/referencias, sin copiar todo el conocimiento.
- `adaptadores/estado_binario.py` mantiene tipos y campos explícitos y valida
  deltas. El nuevo conocimiento y sus cambios requieren integración explícita;
  añadir atributos sin ampliar el esquema rompe el guardado.
- Interrupción: coordinar entrada de consola y pasos completos, permitiendo
  `retroceder` entre pasos sin pedir confirmación obligatoria. El mecanismo técnico
  queda en la vista como detección opcional de entrada pendiente entre pasos;
  el controlador cancela el viaje y procesa el comando. En Windows, msvcrt
  permite detectar teclas sin esperar una confirmación en cada paso. Inyectar
  detección y lectura para pruebas; no introducir hilos ni colas. Sin vista en replay.
- El replay actual ejecuta todas las líneas: integrar el comentario de viaje sin
  ejecutarlo como comando. Detectar daño por los sucesos de la acción, no solo
  por la vida final, que podría haber aumentado por regeneración.

## Constitution Check

La revisión previa a tareas confirmó diseño conforme a la constitución y
elecciones explícitas. La ejecución posterior y sus límites se registran en
tasks.md y al final de este plan; no se dedujo cumplimiento solo del diseño.

| Principio | Comprobación prevista | Estado |
| --- | --- | --- |
| I. Estructuras propias | Comparaciones y elecciones explícitas D-NV | Conforme en diseño |
| II. Determinismo | Desempate por ID; no consumir azar al consultar; replay equivalente | Regla definida |
| III. MVC | Conocimiento en modelo; pantalla recibe proyección; bench/replay sin vista | Integración identificada |
| IV. Datos externos | Ningún mapa oficial incorporado a código | Verificado en auditoría |
| V. Presupuesto/versiones | Esqueleto existente, sin contenido por revelación; formato 5 explícito | Conforme en diseño |
| VI. Rendimiento | Medir consultas, revelación, inversión y ruta; límite <5 ms | Ejecutado; resultados y límites al final |
| VII. Especificación previa | Commits 8c20823 y 9a534fd anteriores a implementación | Cumplido hasta esta etapa |
| VIII. Trazabilidad | Mantener 17 FR, 3 PR y 22 AC; enlazar tareas y pruebas | Cadena ejecutada en tasks.md |
| IX. Prompts | Entrada de esta sesión en bitácora existente | Registrado |

## Project Structure

### Documentación de esta capacidad

- `spec.md` y `checklists/requirements.md`: existentes.
- `plan.md` y `research.md`: diseño y decisiones aprobadas.
- `data-model.md`, `contracts/niebla-viaje.md` y `quickstart.md`: diseño de fase 1.
- `tasks.md`: solo después del plan, mediante speckit-tasks.

### Código que requiere integración tras aprobar el diseño

Modelo: conocimiento, rutas, motor y retroceso en `modelo/`.
Controlador: `comandos.py`, `controlador.py`, `partida.py` y `cargar_partida.py`.
Adaptadores: `estado_binario.py` y `bitacora_partida.py`.
Vista: `vista_consola.py`.
Verificación: `Pruebas/` y modo `--bench`.
Archivos nuevos previstos tras las elecciones: `modelo/conocimiento.py` para
conocimiento, índice estático y registros; `modelo/bench_conocimiento.py` para
cargas y mediciones. Reutilizar `modelo/heap_rutas.py`; adaptar `modelo/rutas.py`
con accesos y almacenamiento inyectados. La tabla especializada de cazadores
permanece en su responsabilidad previa. No duplicar el núcleo Dijkstra.

## Investigación y mediciones previstas

D-NV-01 aprobada el 2026-11-09: arreglo por posiciones compactas. El ID de una sala
no es el índice del arreglo. Reservar espacio O(S) una vez; acceso O(1) cuando se
conoce la posición. El conocimiento inicialmente desconocido no se convierte en
información visible por reservarle espacio. D-NV-02 aprobada el 2026-11-09:
tabla hash propia para localizar posiciones por ID. El índice corresponde al
esqueleto completo; no revela qué salas están exploradas ni sustituye la consulta
de su estado. D-NV-02a aprobada: doble hashing. D-NV-02b aprobada: menor potencia
de dos C ≥ 2 que cumpla 10·S ≤ 7·C; salto impar, mezcla determinista y límite de
C sondeos. Se reserva una vez para los S IDs, sin crecimiento por exploración.
No consume azar del juego. D-NV-03 aprobada: listas por sala y un recuerdo
compartido por puerta. D-NV-04 aprobada: compartir un núcleo Dijkstra adaptado con
accesos separados. D-NV-04a aprobada: arreglo de registros y heap indexado propio
existente para el viaje; el cazador conserva sus auxiliares aprobados. D-NV-04b
aprobada: generaciones por búsqueda, sin limpiar S registros en cada paso.
El registro de cambios reversibles aprobado en D-NV-05 utiliza la lista de
cambios existente, con deltas de atributos y referencias. Guardar/cargar debe
conservar esos valores anteriores y las identidades compartidas.
D-NV-06 aprobada: recorrer el arreglo existente al recibir la orden por nombre;
no repetir esta resolución en cada paso ni crear un índice adicional. D-NV-07
aprobada: cada puerta tiene referencia a un recuerdo separado, reservado una vez
sin observar; las salidas conocidas comparten el recuerdo desde ambos extremos.
La medición por paso debe incluir preparación y liberación de candidatos pendientes.

Medir conocimiento parcial y completo; consultas de presentes/ausentes con IDs
densos y dispersos; revelación con antorcha y sin ella manteniendo igual región
revelada al crecer el resto del mapa; registro/inversión de cambios; cálculo de
cada paso con puertas recordadas y reales divergentes. Separar construcción
inicial, cambios, consultas y memoria para no ocultar costes.

La referencia se identificó nuevamente en el servicio como cripta-06 y se
verificaron versiones al medir esta capacidad. No reutilizar los tiempos de cazadores como evidencia
del límite de «ir a». Conservar versiones, semilla, tamaño y condiciones de cada
medición, reportar máximos y límites y llevar resultados finales al Documento de
Decisiones. El diseño inicial precedió las pruebas y mediciones descritas abajo.

## Complexity Tracking

No se propone excepción constitucional. D-NV-01, D-NV-02, D-NV-02a y D-NV-02b
aprobadas, junto a D-NV-03, D-NV-04, D-NV-04a, D-NV-04b, D-NV-05 y D-NV-06.
D-NV-07 también aprobada. No se propone ninguna excepción ni estructura adicional.

## Secuencia de integración y validación

1. Estructuras y estados del conocimiento: índices compactos, recuerdos compartidos,
   salidas reveladas y deltas; probar aislamiento de partidas y revelación local.
2. Motor: iniciar el conocimiento en reloj 0; registrar entradas/antorcha y
   observaciones de puertas dentro del intervalo reversible; no mutar al consultar.
3. Búsqueda: adaptar núcleo compartido; regresiones del cazador y pruebas de
   recorrido restringido al conocimiento, generaciones y empate de primer salto.
4. Controlador y vista: preservar nombres completos/capitalización, `ver mapa`,
   proyección de destinos avistados, pasos automáticos e interrupción inyectable.
5. Persistencia y replay: esquema 5, referencias/deltas completos, reconstrucción
   de derivados, comentarios ignorados y un movimiento individual por paso.
6. Pruebas de aceptación y mediciones reproducibles; actualizar README y Documento
   de Decisiones con resultados y límites reales. No marcar éxito antes de ejecutar.

Los contratos incluyen la cadena prevista FR → AC → componente → evidencia.
`speckit-tasks` añadirá tareas con referencias a requisitos; después corresponde
`speckit-analyze`. Este plan no genera ni ejecuta esas tareas.

Revisión documental final: decisiones, enlaces, entidades y cobertura prevista
de 22 AC y 17 FR comprobados, incluida revisión delegada de solo lectura exigida
por la habilidad. Sin elecciones adicionales ni bloqueos de diseño encontrados.
Esto no sustituye el análisis de consistencia con tasks.md ni evidencia empírica.

## Ejecución y evidencia final

Tareas confirmadas antes del código en cb7ae25; análisis sin bloqueos, 17 FR y
3 PR cubiertos y checklist 16/16. Las 30 tareas se verificaron con 492 pruebas.
La implementación conserva las estructuras; se adelantó el esquema básico a
fundamentos por su validación estricta, como prevé T004. Formato final 5.

Referencia: 3 000 cálculos, máximo 2,1130 ms; 225 ciclos oficiales con 32 cazadores,
máximo 18,6757 ms; 39/63 solicitudes. El ensayo original no encontró rutas entre
sus destinos y se conservó antes de añadir estrés de recuerdos abiertos.
En una corrida sintética hubo un ciclo ≥20 ms (21,7271 ms de máximo); no se
presenta cumplimiento universal. Ver documentacion/evidencia/mediciones_niebla.json
y DOCUMENTO_DECISIONES.md para resultados y límites. Teclado físico no probado
manualmente; interrupción automática verificada con entrada inyectada.
