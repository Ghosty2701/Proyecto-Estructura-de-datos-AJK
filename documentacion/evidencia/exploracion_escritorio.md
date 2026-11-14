# Revisión interactiva en Windows — 2026-11-14

Aplicación real con Pygame/SDL y paquete sintético lt, sin vídeo dummy.
Herramienta computer-use (`node_repl` + `@oai/sky`), ventana de prueba titulada
«Cripta - Revision final Pygame». Se usaron archivos aislados bajo
`resultados/bench/pygame/escritorio-final/`. La ventana original del usuario
«Cripta · Habitaciones y turnos» permaneció abierta y no se operó sobre ella.

Reproducción manual:

```powershell
.\.venv\Scripts\python.exe -m Pruebas.revisar_escritorio
.\.venv\Scripts\python.exe -m Pruebas.revisar_escritorio --minima
.\.venv\Scripts\python.exe -m Pruebas.revisar_escritorio --minima --muchos
```

## Recorrido observado

| Comprobación | Resultado y evidencia |
|---|---|
| Inicio 1280 × 800 y 1024 × 768 | Catálogo, fila resaltada, resumen y Empezar; [1280](escritorio_1280.png), [1024](escritorio_1024.png). |
| Teclado y foco | La herramienta no entregó eventos de teclado/texto. El usuario probó físicamente WASD/H/Esc y confirmó «Sí, responden correctamente». Registro SDL de W/D/A/S/H y pérdida/recuperación de foco en [eventos](escritorio_eventos_nativos.txt). No se atribuye esa prueba a entradas automatizadas. |
| Turnos/inactividad | Cuatro movimientos físicos dejaron turno 4; selección y paneles no lo incrementaron. El turno siguió estable entre capturas mientras no se actuó. |
| Enemigo y combate | Sabueso con forma canina; selección por sprite, ataque, daño/derrota y desvanecimiento; [combate](escritorio_combate.png). |
| Suelo/inventario | Recoger pergamino y daga; seleccionar daga y equipar; ataque 6 → 9, marca equipado. Ordenar por nombre mantiene turno 8; [inventario](escritorio_inventario.png). |
| Minimap/mapa/viaje | Clic amplía; habitaciones desconocidas siguen con ?, recuerdos remotos tenues. Viaje hacia sala 5 se detiene en sala 2 por daño, con aviso visible; [mapa](escritorio_mapa.png). |
| Guardar/historia | Guardado a t=1000, turno 9; consulta t=0 muestra PASADO y presente t=1000, sin turno; [historia](escritorio_historia.png). |
| Retroceso y carga | Pergamino devuelve t=1000 → 900 y turno 9 → 8; [retroceso](escritorio_retroceso.png). Reanudar recupera sala 2, turno 9 y vida 184, incluido mapa. |
| Selector nativo real | Abrir diálogo, recorrer carpetas, elegir revision.bin; archivo aparece antes de confirmar. Reabrir/cancelar conserva elección; confirmar restaura guardado; [carga](escritorio_carga.png). |
| Redimensionado | Maximizar y restaurar vuelve a distribuir sala, HUD y paneles, con turno 9 estable. Un arrastre hacia fuera fue rechazado por la herramienta; se usó el botón nativo de maximizar/restaurar. La captura intermedia de animación del sistema se descartó y se volvió a observar la ventana correcta. |
| Muchos objetivos | Fixture nativo de 31 enemigos y 19 objetos, 12/8 por página; [vista](escritorio_muchos.png). Hallazgo: selección lejana no cambiaba página. Se corrigió, reabrió y verificó seleccionar número 31; aparece su sprite resaltado y turno 0: [corrección](escritorio_objetivo31.png). |
| Cierre | Todas las ventanas/procesos de prueba cerraron con X. El inventario final de ventanas conservó solo el juego original del usuario. |

## Alcance de la aceptación

Esta revisión cierra la inspección interactiva T020/T047 junto con la regresión
y los renders registrados. Las comprobaciones exhaustivas de antorcha, rechazo,
salto/reducción de efectos, guardados cruzados, pausas y selección caducada
proceden de pruebas automatizadas; no se afirma haber repetido manualmente cada
combinación. El teclado físico se acredita por confirmación expresa del usuario,
con registro SDL complementario. El fallo de inyección de teclado/texto es una
limitación observada de la herramienta, también en el diálogo nativo.

No se usó red real ni se midió latencia de monitor. No se afirma ausencia
universal de fallos en otras criptas/equipos. Las capturas versionadas muestran
solo ventanas del juego; se omitieron capturas transitorias de otras superficies.
Rama preparada para evaluación de integración, sin merge a main.
