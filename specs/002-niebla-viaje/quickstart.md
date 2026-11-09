# Guía de validación: Niebla y viaje

**Fecha**: 2026-11-09. Comandos y escenarios implementados; resultados y límites
al final de esta guía. Los datos concretos del servicio pueden cambiar por versión.

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

La línea base fue de 469 pruebas; el cierre tiene 492 aprobadas. Las referencias
por escenario están en [tasks.md](tasks.md). Para aceptación de esta capacidad:

```powershell
python -m pytest -q Pruebas/prueba_conocimiento.py Pruebas/prueba_rutas_conocidas.py Pruebas/prueba_niebla_partida.py Pruebas/prueba_bitacora_partida.py Pruebas/prueba_estado_binario.py Pruebas/prueba_bench_adaptadores.py
```

## Recorridos de aceptación

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

## Mediciones

El comando de bench ampliado por esta capacidad es:

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

## Resultados de cierre

492 pruebas aprobadas. Referencia oficial: 300 salas, 3 000 consultas (1 500
sin ruta con puertas observadas y 1 500 con ruta en estrés de recuerdos abiertos),
máximo 2,1130 ms, cero ≥5 ms. Los recuerdos de estrés no abren puertas físicas.
225 ciclos con 32 cazadores preparados: máximo 18,6757 ms, cero ≥20 ms; 39/63
solicitudes, sin HTTP ni vista medidos. Carga sintética separada: un ciclo de
500 superó 20 ms, máximo 21,7271 ms; conservar ese límite observado.

[Pruebas](../../documentacion/evidencia/pruebas_niebla.txt),
[mediciones finales](../../documentacion/evidencia/mediciones_niebla.json),
[primera corrida sin rutas](../../documentacion/evidencia/mediciones_niebla_inicial.json),
[salidas completas](../../documentacion/evidencia/bench_niebla.txt).
Interrupción verificada mediante callbacks; no se ensayó teclado físico manualmente.
Los presupuestos se verifican para estas cargas/equipo, no para cualquier ejecución.
