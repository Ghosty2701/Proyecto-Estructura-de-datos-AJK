# Revisión de claridad — 2026-11-14

Rama `005-interfaz-pygame`. Ampliación personal, independiente de Parte II.
Python 3.13.2, pygame 2.6.1 y pytest 9. Especificación confirmada en `c245b8b`
antes del código de esta revisión. Sin hooks de extensión registrados.

## Resultado y comprobaciones

- FR-EV-017 / AC-EV-018 / SC-EV-009: el código anterior elegía el sprite por
  comportamiento. La ficha local de Rata gigante es rastreador, por lo que usaba
  un encapuchado. Ahora nombre observable normalizado determina la especie;
  rata, espectro y sabueso óseo tienen recursos propios. Prueba con rata guardiana
  y rastreadora, y nombres desconocidos con símbolo neutral.
- FR-EV-018 / AC-EV-019: inventario muestra peso/valor, controles «Ordenar por…»,
  criterio/sentido y explicación de que solo cambia la lista, sin turno.
  Metadatos simples en los mismos registros congelados; ninguna raíz v6 cambia.
- FR-EV-019 / AC-EV-020/021: inicio separado en Nueva partida y Cargar partida;
  fila elegida resaltada, resumen nombre/ID/salas y botón Empezar. Carga con ruta,
  búsqueda de .bin y confirmación; cancelar conserva archivo. Carga válida real
  del bin escrito por el propio juego, error recuperable, fuente configurable.
  Campos inválidos de semilla/K de partida nueva no impiden cargar ni sustituyen
  el nombre/semilla del guardado. Pausa distingue guardado actual y otro archivo.
- FR-EV-020 / AC-EV-022: operaciones de inicio y juego deliberadamente demoradas
  con barreras; indicador cambia con tiempo real, cierre atendido y solicitud
  duplicada rechazada. Barra indeterminada y descripción/segundos, sin porcentaje
  inventado. No se alteró timeout ni presupuesto HTTP del motor.
- FR-EV-021 / AC-EV-023 / SC-EV-010: botones con gradiente, bisel, sombra, aristas
  iluminadas y selección dorada; ventanas con remates. Inspección de tamaños
  1024 × 768 y 1280 × 800. Controles de inicio/carga contenidos en ventana.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short
python -m pytest -q --tb=short
.\.venv\Scripts\python.exe -m Pruebas.renderizar_retro
```

Regresión gráfica: **858 aprobadas**, salida íntegra en
[claridad_regresion_grafica.txt](claridad_regresion_grafica.txt).
Sin Pygame instalado: **819 aprobadas y cuatro módulos omitidos**, salida en
[claridad_regresion_sin_pygame.txt](claridad_regresion_sin_pygame.txt).
Incluye matriz v6 y comparación de reglas/modos existentes. Nueve casos nuevos
en `Pruebas/prueba_claridad_pygame.py`; los recorridos anteriores se mantienen.
La ejecución dirigida previa de cuatro módulos pasó 39 casos.
Antes de implementar se observaron ausencias de selección, especies, carga
separada, explicación e indicador; no se eliminaron esas comprobaciones.

## Capturas inspeccionadas

- [Inicio con cripta elegida](inicio_claro.png).
- [Carga con archivo confirmado](carga_clara.png).
- [Inventario y orden explicado](inventario_claro.png).
- [Rata, espectro y sabueso](criaturas_claras.png).
- [Actividad durante operación demorada](actividad_clara.png).

Los renders usan paquete sintético lt, semilla 2026 y vídeo dummy. Nueva partida,
catálogo, inventario y archivo guardado proceden de operaciones del juego.
La muestra de tres especies usa un DTO solo para render, sin añadir esas
criaturas al motor. La actividad se captura durante una operación real retenida
con una barrera de prueba; no es una medición de latencia de red o monitor.
El script también genera versiones mínimas de inicio/carga y las ocho puertas
en `resultados/bench/pygame/retro/`, reproducibles y no versionadas.

## Límites y estado

tkinter 8.6 está disponible localmente, pero el diálogo se prueba con sustituto
controlado; no se acredita interacción nativa del selector. Si no está disponible,
queda la edición de ruta y un error explicativo. Las imágenes y eventos dummy
no acreditan el recorrido completo en escritorio de T020, foco o teclado físicos.
T020 y cierre dependiente T023/T024 permanecen pendientes. Avance visual exclusivo
~90 % estimado. No hay medición nueva de rendimiento ni cambio a EX-01.
`main` no se fusiona ni se modifica por esta revisión.
