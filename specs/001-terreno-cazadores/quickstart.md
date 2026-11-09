# Guía de validación — Terreno y cazadores

**Fecha**: 2026-11-08. Protocolo para la implementación futura; no hay resultados nuevos.
Referencias: [spec.md](spec.md), [plan.md](plan.md), [contratos](contracts/terreno-cazadores.md).

## Preparación

Desde la raíz del repositorio, en PowerShell, usar Python 3.11 o superior con las
dependencias de `documentacion/requirements.txt`. Configuración documentada en README:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r documentacion/requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
```

La suite actual sirve de base de regresión, no demuestra la capacidad nueva antes de
añadir sus pruebas. No se ejecuta desde el botón que abre directamente un archivo de prueba.
La evidencia histórica de 437 pruebas corresponde a P1; no se presenta como ejecución actual.

Antes del código, confirmar la especificación en Git. Generar tasks.md, ejecutar el
análisis de consistencia y después implementar las tareas. Ningún comando de esta guía
ya fue ejecutado como prueba de P2 durante la planificación.

La especificación y sus artefactos iniciales quedaron confirmados en `290f173`
(2026-11-08), antes de la implementación. El análisis del 2026-11-09 comprobó cobertura
documental y dependencias; su aclaración del límite establece tiempo estrictamente
menor que 20 ms, conforme al benchmark heredado que rechaza tiempos mayores o iguales.

## Comprobaciones automatizadas previstas

| Grupo | Ejecución de aceptación después de implementar | Resultado esperado |
| --- | --- | --- |
| Terreno: AC-TC-001 a 005 | Costos ausentes, 250/velocidad125, costo1/velocidad500 y velocidad en curso | Intervalos 100, 200 y mínimo1; reajuste solo del tiempo restante; demás acciones sin cambio |
| Persecución: AC-TC-006 a 011 | Ataque, desconexión, límites de rango, rutas ponderadas, empate y contenido no cargado | Conducta exacta de la especificación; sin solicitudes al calcular |
| Cambios: AC-TC-012 a 015 | Cerrar/abrir puertas, mover objetivo y cambiar otros actores | Igualdad con el cálculo de referencia desde cero |
| Integración: AC-TC-016 a 019 | Presentación, replay, guardado/carga y pergamino | Costos/cazadores visibles; continuación y estado restaurado equivalentes |
| Hash y heap | Colisiones deliberadas, mejoras de clave, crecimiento y extracción | Referencias estables, sondeo acotado, orden correcto y posiciones sincronizadas |
| Reutilización | Consultas iguales, origen distinto, puerta lejana, carga y retroceso | Solo el último resultado compatible se reutiliza; ningún resultado obsoleto cambia la decisión |

Las futuras tareas deben identificar los archivos de prueba concretos y enlazar FR-TC
en sus casos. No se incluyen comandos hacia pruebas que todavía no existen.

## Ejecución manual prevista tras implementar

Usar una cripta publicada compatible que contenga costos variables y cazadores; elegir
el ID obtenido del servicio, no asumir que una cripta histórica los incorpora.

```powershell
.\.venv\Scripts\python.exe main.py --listar
.\.venv\Scripts\python.exe main.py --cripta <ID> --semilla 2026 --bitacora terreno.log
.\.venv\Scripts\python.exe main.py --replay terreno.log
```

Sustituir `<ID>` antes de ejecutar y usar una ruta nueva para el log. El resultado esperado
es ver costos en la sala, distinguir al cazador y reproducir las acciones sin vista.
No ejecutar estas órdenes ahora como si la capacidad ya estuviese implementada.

Para un paquete offline compatible, añadir `--offline <CARPETA>` conforme al README.
La caché de catálogo no sustituye el paquete ni garantiza que existan esos datos offline.

## Medición prevista

```powershell
.\.venv\Scripts\python.exe main.py --bench
.\.venv\Scripts\python.exe main.py --bench --cripta <ID> --semilla 2026 --repeticiones 5
```

Después de extender los benchmarks, comprobar las comparaciones de PR-TC-003: uno/muchos,
rangos pequeños/grandes, individual/compartido y reutilización/recálculo con puertas
estables/inestables. La alternativa compartida es de medición; el juego sigue individual.

Variar el tamaño de regiones no visitadas y contar operaciones de búsqueda. Incluir los
picos de crecimiento de la hash, preparación y liberación del espacio de trabajo. Repetir
agenda y retroceso bajo carga nueva; excluir HTTP y renderizado del cronómetro.

Registrar equipo, versión de código/datos, semilla, carga y máximo de ciclo. El cumplimiento
oficial exige identificar la cripta de referencia y decenas de cazadores activos y cumplir
el límite de 20 ms. Sin esos datos, reportar la medición como sintética y dejar pendiente
la aceptación oficial, sin sustituirla por tiempos históricos de P1.

## Criterio de cierre

Los 19 escenarios tienen evidencia ligada a requisitos; las regresiones pertinentes de
P1 pasan; las decisiones coinciden con referencia; guardar/cargar y retroceder conservan
el estado; las mediciones quedan en el Documento de Decisiones enlazando spec y plan.
Si una estructura no cumple, presentar los resultados y alternativas al usuario antes
de reemplazarla. No confundir esta guía revisada con verificaciones ejecutadas.
