# Guía de validación prevista: Niebla y viaje

**Fecha**: 2026-11-09. Esta guía describe verificaciones por implementar.
No afirma que los comandos nuevos, pruebas o benchmarks ya funcionen.

## Preparación

Desde la raíz del repositorio, usar Python 3.11 o superior con requests/pytest
existentes. Leer [spec.md](spec.md), [contrato](contracts/niebla-viaje.md) y
[data-model.md](data-model.md). Obtener datos del servicio o un paquete offline
con versiones compatibles; no codificar una cripta concreta.
Falta el enunciado original de P1 para su contraste íntegro.

El comando existente para regresiones es:

```powershell
python -m pytest -q
```

La evidencia histórica más reciente es 469 pruebas aprobadas para el estado
previo a niebla; no se han vuelto a ejecutar en esta planificación. Tras la
implementación se ejecutarán las pruebas nuevas y las regresiones completas.
Las rutas concretas de pruebas se asignarán en tasks.md, aún no generado.

## Recorridos de aceptación después de implementar

1. Iniciar una partida con el comando existente, por ejemplo
   `python main.py --cripta <ID> --semilla 2026`. En t=0, usar `ver mapa`:
   inicial explorada, vecinas avistadas y resto sin información. Comparar
   antes/después de precargar: no debe revelar más.
2. Entrar en nuevas salas. Con antorcha encendida, revelar todas las vecinas,
   incluidas las tras puertas cerradas; no mostrar contenido ni activar
   enemigos/trampas remotos. No revelar recursivamente todo el mapa.
3. Observar una puerta abierta y alejarse. Hacer que cierre remotamente:
   el mapa conserva el recuerdo. Volver a observar desde un extremo:
   actualizar dentro de la acción y recalcular la siguiente ruta.
4. Ejecutar `ir a <ID>` y `ir a <Nombre completo>` hacia la misma explorada.
   Distinguir mayúsculas; nombres repetidos requieren ID. Destino avistado o
   desconocido se rechaza sin tiempo; sala actual informa que ya está allí.
5. Contrastar ruta de más pasos pero menor costo y empate de primer salto
   por menor ID. No usar conexiones desconocidas ni abrir puertas con llave.
6. Provocar cada parada: llegada, pérdida de ruta, enemigos al entrar y daño.
   Incluir enemigo que después sale de la sala y daño seguido de regeneración.
   Verificar eventos y costos ordinarios de cada paso.
7. Interrumpir entre pasos y ejecutar `retroceder`: solo último paso revertido,
   conocimiento previo restaurado, consumo de pergamino según P1 y viaje cancelado.
8. Guardar/cargar con recuerdo distinto de la puerta real y con deltas de antorcha.
   Retroceder tras cargar: conservar estados previos y referencias compartidas.
   Guardado anterior al formato 5 recibe rechazo claro.
9. Grabar y reproducir con `python main.py --replay partida.log`: comentario
   de viaje ignorado, movimientos individuales ejecutados, igual estado y
   conocimiento, sin instanciar vista ni sondear teclado.

Estos recorridos requieren escenarios sintéticos controlados y evidencia
automática o log para AC-NV-001 a AC-NV-022; no basta jugar manualmente una vez.

## Mediciones después de implementar

El comando de bench existente, a ampliar por esta capacidad, es:

```powershell
python main.py --bench --cripta <ID-referencia> --semilla 2026 --repeticiones 5
```

Volver a verificar referencia y versiones: cripta-06 solo es identificación
histórica anterior, no excepción en código. Precargar fuera del cronómetro;
comprobar que las mediciones no hagan solicitudes HTTP ni creen vista.

Medir presentes/ausentes en índice, estados de sala, recuerdos y resolución
por nombre. Comparar memoria y construcción de hash según alternativas de
research.md, sin cambiar la elección sin permiso. Para revelación, mantener
igual región afectada y aumentar el resto del mapa; registrar conteos de trabajo.

Medir cada cálculo de paso sobre conocimiento completo de referencia: incluir
preparación de registros y limpieza de heap, distinguir de red, pantalla y
simulación del intervalo. Exigir máximo <5 ms, reportar repeticiones y fallos.
Medir deltas/memoria de cambios e inversión; no confundirlo con memoria total.
Conservar semilla, tamaños, versiones, huellas de código y límites conocidos.

Después de aprobar esas comprobaciones actualizar Documento de Decisiones,
README y trazabilidad con evidencia real. Sigue speckit-tasks y speckit-analyze
antes de implementar, no ejecutar esta guía como si la capacidad estuviera hecha.
