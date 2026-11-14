# Revisión visual de la escena — 2026-11-14

## Render de la aplicación inspeccionado

Se generaron e inspeccionaron capturas de la aplicación a 1280 × 800 y
1024 × 768, con el paquete sintético lt, semilla 2026, y vídeo dummy.
Se comprobaron habitación, personaje, puertas, objetos, guardián seleccionado,
cifras y corte de combate, minimapa, botones e historia/inventario accesibles.
Se corrigieron el solape lateral y el centrado del minimapa tras cambiar de sala.

Captura versionada: [escena_jugable.png](escena_jugable.png). Es render de código
jugable con efectos confirmados, no el concepto generado con imagegen. El reloj
de presentación se fijó a 220 ms para capturar un efecto; el estado ya había
sido ejecutado y confirmado por el trabajador.

Capturas locales adicionales en `resultados/bench/pygame/escena/`:
`inicio-final.png`, `combate-final.png` y `minima-final.png`.

## Intento nativo y límite

Se lanzó la aplicación en una ventana nativa titulada «Cripta · Revision visual
006». El servicio de control devolvió correctamente su vista inicial a
1280 × 800: personaje, seis objetos, puerta N, minimapa y controles legibles.
El primer clic posterior fue bloqueado con «user input was detected in this
window; call get_window_state before continuing». Al reobservar, la captura ya
no correspondía al juego. No se utilizaron esas coordenadas ni se enviaron
acciones sobre la otra aplicación. Se cerró el proceso de prueba.

No se considera completada T020. Queda revisar de forma interactiva el recorrido
de quickstart, teclado/foco físicos, resize nativo y cierre desde la interfaz.
Los tests y capturas dummy no se presentan como aprobación de esos escenarios.
