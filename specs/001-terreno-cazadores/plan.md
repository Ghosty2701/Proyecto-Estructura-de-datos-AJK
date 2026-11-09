# Implementation Plan: Terreno y cazadores

**Branch**: `main` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: `specs/001-terreno-cazadores/spec.md`

**Estado**: diseño aprobado y ejecución completada el 2026-11-09. Las decisiones D-TC-01
hasta D-TC-08 y sus variantes fueron elegidas por el usuario. Las 38 tareas de
[tasks.md](tasks.md) tienen evidencia de código, pruebas y mediciones. Los resultados
finales y sus límites se incorporaron a documentacion/DOCUMENTO_DECISIONES.md.
El identificador de capacidad es `001-terreno-cazadores`; la rama Git real es `main`.

## Summary

Añadir costo a las salidas existentes y rango al cazador. Resolver cada persecución con
Dijkstra limitado por rango, heap binario indexado propio y tabla hash propia con doble
hashing. Conservar las listas de adyacencia del modelo, el determinismo y las garantías
heredadas de reloj, efectos, retroceso, guardado y replay.

La investigación y la historia de las elecciones están en [research.md](research.md).
El diseño está en [data-model.md](data-model.md), los contratos en
[contracts/terreno-cazadores.md](contracts/terreno-cazadores.md) y la validación prevista
en [quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python 3.11 o superior; README documenta la ejecución anterior en 3.14.6.

**Primary Dependencies**: requests 2.34.2 y pytest 9.1.1 existentes. Ninguna dependencia nueva.

**Storage**: contenedor binario propio y esquema explícito del modelo; persistir costo y
rango, versionar el esquema y rechazar versiones anteriores incompatibles. Las estructuras
de búsqueda y el último resultado son derivados; no se serializan y se invalidan al cargar.

**Testing**: pytest; evidencia futura para AC-TC-001 a AC-TC-019 y regresiones de P1.

**Target Platform**: consola, entorno de desarrollo Windows y PowerShell.

**Project Type**: aplicación de consola MVC con adaptadores de red y persistencia.

**Performance Goals**: PR-TC-001 a PR-TC-003: ciclo de 20 ms sin red/renderizado, trabajo
local por rango y comparación de las alternativas exigidas por P2.

**Constraints**: estructuras manuales, sin dict/set como índice ni bibliotecas equivalentes;
presupuesto y versiones; las elecciones de estructuras pertenecen al usuario.

**Scale/Scope**: uno y muchos cazadores, rangos pequeños/grandes y puertas estables/inestables.
La aceptación oficial de 20 ms requiere identificar la cripta y carga de referencia.

### Decisiones aprobadas el 2026-11-08

| ID | Elección del usuario |
| --- | --- |
| D-TC-01 | Dijkstra limitado por rango con heap propio separado de la agenda |
| D-TC-02 | Tabla hash propia para distancias por ID de sala |
| D-TC-02a | Colisiones mediante doble hashing |
| D-TC-03 | Heap indexado, actualizando prioridad sin duplicados por mejora |
| D-TC-03a | Posición del heap dentro del registro hash de distancia |
| D-TC-04 | Búsqueda individual desde cada cazador |
| D-TC-05 | Reutilización conservadora, con recálculo al cambiar condiciones |
| D-TC-06 | Listas de adyacencia existentes; sustituyen la matriz inicialmente considerada |
| D-TC-06a | Resuelta al retirar la matriz; sin índice adicional de vecinos |
| D-TC-07 | Solo el último resultado y sus condiciones por cazador |
| D-TC-08 | Capacidad inicial 32, duplicación, salto impar y ampliación antes de superar 70 % |

La configuración de tabla es un punto de partida aprobado, no una garantía de tiempo.
Cambiar la estructura o su política acordada exige volver a consultar al usuario.

## Constitution Check

| Control | Antes del diseño | Después del diseño |
| --- | --- | --- |
| Estructuras manuales y restricciones | Exigidas | Hash y heap propios; ninguna dependencia nueva o índice dict/set |
| Determinismo | Exigido | Etiqueta distancia/primer paso; desempate explícito; búsqueda sin consumo de azar |
| MVC y modos sin vista | Exigidos | Estructuras en modelo/; adaptadores cargan datos; replay y bench sin vista |
| Datos externos | Exigidos | Costos y rango se cargan de datos versionados, sin casos por cripta |
| Presupuesto y versiones | Exigidos | Búsqueda sobre esqueleto vivo; no descarga contenido para calcular la ruta |
| Evidencia de rendimiento | Pendiente al diseñar | 225 ciclos oficiales preparados con 32 cazadores, máximo 15,1171 ms; resultados conservados |
| Búsqueda local por rango | Exigida | Tabla pequeña por búsqueda, adyacencia local y corte por rango; sin escaneo global |
| Especificación antes del código en Git | Exigida | 290f173 y aclaración 1071237 preceden al código de la capacidad |
| Trazabilidad | Spec y escenarios presentes | Tareas ejecutadas; pruebas y ubicaciones reales en tasks.md |
| Prompts | Registro existente | Prompt de aprobación añadido a documentacion/PROMPTS_LLM.md |
| Elección del usuario | Decisiones abiertas | D-TC-01 a D-TC-08 resueltas, con historia en research.md |

**Resultado**: diseño sin excepciones a la constitución, implementado y verificado con
469 pruebas y mediciones identificadas. No garantiza otras versiones, cargas o equipos.
El commit de la especificación debe anteceder al commit del código que la implemente.

## Project Structure

### Documentation (this feature)

```text
specs/001-terreno-cazadores/
    spec.md
    plan.md
    research.md
    data-model.md
    quickstart.md
    contracts/terreno-cazadores.md
    checklists/requirements.md
    tasks.md
```

tasks.md registra la ejecución posterior al diseño y sus referencias de evidencia.

### Source Code (repository root)

Ubicaciones previstas para la implementación; no son archivos nuevos ya creados:

| Área | Cambio previsto | Requisitos |
| --- | --- | --- |
| modelo/tabla_hash.py | Registros dispersos, doble hashing y redimensionamiento | FR-TC-006, FR-TC-009; PR-TC-002 |
| modelo/heap_rutas.py | Heap indexado de referencias a registros | FR-TC-006, FR-TC-009; PR-TC-002 |
| modelo/rutas.py | Búsqueda individual y resultado reutilizable | FR-TC-005 a FR-TC-011 |
| modelo/rastro.py | Costo en salida, conservando las listas y puertas actuales | FR-TC-001 |
| modelo/motor_eventos.py | Cazador, costo del movimiento de todos los actores y revisión de cambios | FR-TC-002 a FR-TC-011 |
| controlador/cargar_partida.py | Costo normalizado, rango y coherencia de puertas en ambos sentidos | FR-TC-001, FR-TC-010, FR-TC-014 |
| controlador/partida.py y vista/vista_consola.py | Mostrar costos y distinguir cazadores | FR-TC-012 |
| adaptadores/estado_binario.py | Esquema, validaciones y vista selectiva con costo/rango | FR-TC-014 |
| adaptadores/bitacora_partida.py y main.py | Verificar replay por el mismo ejecutor sin vista | FR-TC-013 |
| modelo/bench_modelo.py y adaptadores/bench_adaptadores.py | Nuevas cargas y comparaciones requeridas | PR-TC-001 a PR-TC-003 |
| modelo/bench_rutas.py | Separa las cargas nuevas del benchmark; conserva las estructuras y modalidades aprobadas | PR-TC-001 a PR-TC-003 |
| Pruebas/ | Casos de aceptación, estructuras y regresiones de P1 | Todos los FR-TC |

**Structure Decision**: ampliar MVC existente. Las nuevas estructuras de búsqueda viven
en el modelo y no importan el AVL ni servicios desde adaptadores. Se conservan las
estructuras de P1 en sus usos actuales; no se las sustituye para resolver esta capacidad.

## Diseño y secuencia de integración

1. Implementar y verificar hash y heap conforme al modelo de datos y contratos.
2. Incorporar costo a las salidas, normalizar ausencia a 100 y conservar simetría de
   costos/puertas. El cargador actual crea puertas por dirección: no se presupone que
   ambas direcciones compartan objeto o se actualicen correctamente sin comprobarlo.
3. Añadir búsqueda pura sobre las salas del modelo. Mantener etiquetas ordenadas por
   distancia y primer vecino; terminar al extraer objetivo o agotar candidatos en rango.
4. Integrar cazador y costos de movimiento de jugador, errante y rastreador. Conservar
   activación, azar, efectos, reprogramación de velocidad y límites del intervalo de P1.
5. Conectar invalidación conservadora por revisión monotónica de conexiones/costos y
   datos de consulta. Avanzar la revisión tras restaurar puertas, cargar o retroceder;
   no restaurarla a un valor antiguo que pueda revalidar resultados de otra historia.
6. Persistir rango/costo y actualizar validaciones del esquema binario y lectura selectiva.
   Invalidar datos derivados al restaurar; conservar el estado de juego y de azar.
7. Integrar presentación, replay y evidencia automatizada. Después medir y documentar
   resultados finales en el Documento de Decisiones, enlazando spec y plan.

Esta secuencia orienta la futura descomposición en tareas; no reemplaza tasks.md.

La integración adelantó la persistencia del campo costo a US1 porque el serializador
existente rechaza atributos sin esquema. T029 completó después rango, validaciones y
lectura selectiva. Fue una corrección de dependencia, sin cambiar estructuras o reglas.

## Mediciones previstas

- Cargas sintéticas deterministas con un cazador y varias decenas; rangos pequeños y grandes.
- Crecer el mapa fuera de una región fija de búsqueda; contar salas, salidas y operaciones
  para detectar reinicialización, validación o limpieza global oculta por consulta.
- Registrar sondeos, ocupación y picos de redistribución de la hash; claves ordenadas y
  colisiones deliberadas; verificar índice del heap después de cada crecimiento.
- Comparar individual y compartido como exige P2, reutilizando las estructuras aprobadas
  para la alternativa de medición; la estrategia del juego sigue siendo individual.
- Comparar reutilización y recálculo siempre, con puertas estables/inestables, y comprobar
  igualdad de decisiones. Incluir aperturas fuera de la ruta anterior y retroceso.
- Medir el ciclo completo, incluidas preparación y liberación de búsquedas dentro de él,
  sin HTTP ni vista. Informar máximo, carga, semilla, versiones y equipo.
- Repetir mediciones de agenda y retroceso con la carga nueva. Si no cumplen, presentar
  evidencia y alternativas al usuario antes de cambiar las estructuras elegidas.
- Identificar cripta/carga oficial antes de afirmar el cumplimiento de los 20 ms.

## Complexity Tracking

Sin excepciones normativas. El mapa consume O(S + E); para una búsqueda con R salas
registradas y E_R salidas examinadas, el heap ocupa O(R) y tiene operaciones O(log R).
La hash tiene consulta esperada O(1) y ampliación amortizada esperada O(1) por inserción;
una ampliación aislada es lineal esperada en R. Bajo esas condiciones, la búsqueda cuesta
O((R + E_R) log(R + 1)) esperado amortizado y espacio O(R), sin depender del mapa no visitado.
Las colisiones pueden empeorar esas cotas: no son garantías de peor caso ni de 20 ms.

La validez y lectura del último resultado son O(1) por cazador. Los resultados retenidos
ocupan O(C), con C cazadores; los espacios de búsqueda terminados no se acumulan en ellos.
