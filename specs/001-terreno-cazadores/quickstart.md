# Guía de validación — Terreno y cazadores

**Fecha de diseño**: 2026-11-08. **Verificación**: 2026-11-09, 469 pruebas aprobadas.
Referencias: [spec.md](spec.md), [plan.md](plan.md), [contratos](contracts/terreno-cazadores.md).

## Preparación

Desde la raíz del repositorio, en PowerShell, usar Python 3.11 o superior con las
dependencias de `documentacion/requirements.txt`. Configuración documentada en README:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r documentacion/requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
```

La suite contiene las pruebas nuevas y las regresiones de P1. No se ejecuta desde el botón
que abre directamente un archivo de prueba. Las 437 pruebas históricas de P1 permanecen
identificadas como antecedentes; el resultado actual está en la evidencia de esta capacidad.

La especificación se confirmó antes del código, se generaron tareas y se realizó el
análisis de consistencia. La ejecución posterior está registrada en tasks.md y en
documentacion/evidencia/pruebas_terreno_cazadores.txt. Esta guía se escribió durante el
diseño y se actualiza ahora con lo efectivamente verificado.

La especificación y sus artefactos iniciales quedaron confirmados en `290f173`
(2026-11-08), antes de la implementación. El análisis del 2026-11-09 comprobó cobertura
documental y dependencias; su aclaración del límite establece tiempo estrictamente
menor que 20 ms, conforme al benchmark heredado que rechaza tiempos mayores o iguales.

## Comprobaciones automatizadas ejecutadas

| Grupo | Ejecución de aceptación después de implementar | Resultado esperado |
| --- | --- | --- |
| Terreno: AC-TC-001 a 005 | Costos ausentes, 250/velocidad125, costo1/velocidad500 y velocidad en curso | Intervalos 100, 200 y mínimo1; reajuste solo del tiempo restante; demás acciones sin cambio |
| Persecución: AC-TC-006 a 011 | Ataque, desconexión, límites de rango, rutas ponderadas, empate y contenido no cargado | Conducta exacta de la especificación; sin solicitudes al calcular |
| Cambios: AC-TC-012 a 015 | Cerrar/abrir puertas, mover objetivo y cambiar otros actores | Igualdad con el cálculo de referencia desde cero |
| Integración: AC-TC-016 a 019 | Presentación, replay, guardado/carga y pergamino | Costos/cazadores visibles; continuación y estado restaurado equivalentes |
| Hash y heap | Colisiones deliberadas, mejoras de clave, crecimiento y extracción | Referencias estables, sondeo acotado, orden correcto y posiciones sincronizadas |
| Reutilización | Consultas iguales, origen distinto, puerta lejana, carga y retroceso | Solo el último resultado compatible se reutiliza; ningún resultado obsoleto cambia la decisión |

Los archivos de prueba concretos y los FR-TC están enlazados en la sección
«Trazabilidad verificada» de tasks.md. La suite completa se ejecutó con
`python -m pytest -q -p no:cacheprovider --basetemp=.test_tmp/cierre --tb=short`:
469 aprobadas en 4.69 s, usando el Python 3.14.6 instalado y creando previamente .test_tmp.

## Ejecución de la capacidad

Usar una cripta publicada compatible que contenga costos variables y cazadores; elegir
el ID obtenido del servicio, no asumir que una cripta histórica los incorpora.

```powershell
.\.venv\Scripts\python.exe main.py --listar
.\.venv\Scripts\python.exe main.py --cripta <ID> --semilla 2026 --bitacora terreno.log
.\.venv\Scripts\python.exe main.py --replay terreno.log
```

Sustituir `<ID>` antes de ejecutar y usar una ruta nueva para el log. El resultado esperado
es ver costos en la sala, distinguir al cazador y reproducir las acciones sin vista.
Los comandos están implementados; el replay sin vista también se verificó con datos
offline sintéticos de costos variables y cazadores.

Para un paquete offline compatible, añadir `--offline <CARPETA>` conforme al README.
La caché de catálogo no sustituye el paquete ni garantiza que existan esos datos offline.

## Medición ejecutada y reproducible

```powershell
.\.venv\Scripts\python.exe main.py --bench
.\.venv\Scripts\python.exe main.py --bench --cripta <ID> --semilla 2026 --repeticiones 5
```

Los benchmarks comprueban las comparaciones de PR-TC-003: uno/muchos,
rangos pequeños/grandes, individual/compartido y reutilización/recálculo con puertas
estables/inestables. La alternativa compartida es de medición; el juego sigue individual.

Variar el tamaño de regiones no visitadas y contar operaciones de búsqueda. Incluir los
picos de crecimiento de la hash, preparación y liberación del espacio de trabajo. Repetir
agenda y retroceso bajo carga nueva; excluir HTTP y renderizado del cronómetro.

La referencia publicada identificada es cripta-06, versión f9ed9afa683d, con 300 salas y
36 cazadores. El benchmark prepara hasta 32 activos con posiciones/estadísticas originales,
antes del cronómetro. Cinco repeticiones, semilla 2026:225 ciclos, máximo15.1171ms, ninguno
de 20 ms o más, usando 38/63 solicitudes. Es una carga experimental, no una nueva regla del
juego. Para repetir, sustituir <ID> por el ID actual de la referencia obtenida de --listar.
Las mediciones pueden variar con equipo, versión, recorrido y estado de caché.

Detalles: [referencia](../../documentacion/evidencia/referencia_terreno_cazadores.json),
[comparaciones](../../documentacion/evidencia/mediciones_terreno_cazadores.json) y
[salida completa](../../documentacion/evidencia/bench_terreno_cazadores.txt).

## Criterio de cierre

Los 19 escenarios tienen evidencia ligada a requisitos; las regresiones pertinentes de
P1 pasan; las decisiones coinciden con referencia; guardar/cargar y retroceder conservan
el estado; las mediciones quedan en el Documento de Decisiones enlazando spec y plan.
Si una estructura no cumple, presentar los resultados y alternativas al usuario antes
de reemplazarla. No confundir esta guía revisada con verificaciones ejecutadas.
