# Revisión del render de 16 bits — 2026-11-14

La prueba previa registró 30 botones en la habitación anterior a 1024 × 768
y 1280 × 800. La nueva vista muestra cuatro comandos sin selección, cinco al
seleccionar un enemigo/objeto/puerta y como máximo seis con un control temporal.
Las demás funciones están en inventario, mapa y menú; sus recorridos conservan
las comprobaciones de acciones, reloj, azar y registro.

## Capturas inspeccionadas

Comando reproducible: `.\.venv\Scripts\python.exe -m Pruebas.renderizar_retro`.
Paquete sintético lt, semilla 2026, vídeo dummy.

- `documentacion/evidencia/retro_jugable.png`: captura versionada del juego en
  combate, con los cinco comandos normales y paneles de RPG.
- `resultados/bench/pygame/retro/inicio.png`, `objeto.png`, `combate.png`:
  habitación, sprites, contexto, escala y selección.
- `pausa.png`, `inventario.png`: paneles agrupados y retorno sin turno.
- `minima.png`: render a 1024 × 768, texto y acciones alcanzables.
- `puertas-abiertas.png`, `puertas-cerradas.png`: ocho orientaciones inspeccionadas.
  Esos dos renders usan conexiones de un DTO sintético para mostrar las cuatro
  paredes a la vez; no modifican el motor ni son datos de una cripta real.

Se comprobó que sur no está invertida y que este/oeste usan puertas de pared
lateral, sin girar una ilustración frontal. Marcos, fuente, escala de sprites y
pixel art comparten el estilo retro. No se usó un mockup como fondo jugable.

## Límites

No se acredita con estas imágenes una revisión interactiva nativa completa.
T020 y su cierre dependiente continúan pendientes. No se repitieron acciones de
control de escritorio tras los problemas de captura descritos en la revisión
anterior. La ejecución con vídeo dummy sí permite reproducir todos estos renders
y las pruebas de eventos, pero no prueba foco/teclado físicos ni latencia del monitor.
