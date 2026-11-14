# Revisión visual de Pygame (005, T051) — consolidada 2026-11-14

Alcance personal de la rama `005-interfaz-pygame`; no forma parte de la nota de
Parte II ni reabre EX-01.

## Historial de la revisión

1. **Primer intento (2026-11-14, sesión de Juan):** con control de aplicaciones de
   Windows. La primera captura no correspondió a la aplicación y el usuario detuvo
   el control con Escape. No se aprobó nada con ese intento.
2. **Revisión real de escritorio (2026-11-14, sesión de Juan, capacidad 006):**
   aplicación real con Pygame/SDL, sin vídeo dummy, a 1280 × 800 y 1024 × 768. Es la
   misma aplicación que entrega 005, con la presentación ampliada de 006. Detalle,
   capturas y registro de eventos SDL en [exploracion_escritorio.md](exploracion_escritorio.md).
   El teclado físico (WASD/H/Esc) lo confirmó el usuario expresamente
   («Sí, responden correctamente»), con el [registro de eventos](escritorio_eventos_nativos.txt)
   como respaldo. La herramienta automatizada no pudo inyectar teclado.
3. **Consolidación (esta revisión):** se contrasta esa revisión real con cada paso
   de [quickstart.md](../../specs/005-interfaz-pygame/quickstart.md). Se separa lo
   observado en la ventana real de lo que solo cubren pruebas automatizadas. No se
   repitió una sesión manual nueva.

## Cobertura por paso del recorrido de aceptación

| Paso de quickstart | Observado en ventana real | Cubierto por pruebas automatizadas | Estado |
|---|---|---|---|
| 1. Sala actual, avistadas, contenido oculto; antorcha sin recuerdos | Salas desconocidas con «?», recuerdos remotos tenues ([mapa](escritorio_mapa.png)) | Antorcha y conocimiento: `prueba_memoria_visual.py`, `prueba_mapa_grafico.py` | Parcial manual; antorcha solo automatizada |
| 2. Sprites observados, recuerdo remoto, regreso actualiza | Sprites del sabueso, recuerdos tenues | Movimiento remoto no revelado: `prueba_memoria_visual.py` | Parcial manual |
| 3. Cada operación de AC-IG-009 por botones | Mover, atacar, recoger, seleccionar, equipar (ataque 6 → 9), ordenar, viajar, historia, guardar, cargar, retroceder, ayuda, cerrar ([combate](escritorio_combate.png), [inventario](escritorio_inventario.png)) | Comparación con consola: `prueba_eventos_pygame.py` | Verificado |
| 4. Tecla mantenida, sin cola; 60 s y 300 redibujados | Turno estable entre capturas sin actuar; paneles y selección sin turno | Repetición sin cola: `prueba_eventos_pygame.py`; inactividad 300 redibujados/61,8 s sin cambios ([mediciones](pygame_mediciones.md)) | Verificado (inactividad medida con vídeo dummy) |
| 5. Viaje, parada, interrupción entre pasos | Viaje a sala 5 detenido en sala 2 por daño, aviso visible | Interrupción única, cambio de orden y retroceso: `prueba_eventos_pygame.py` | Parcial manual |
| 6. Historia t y #k, presente, cinco pergaminos y rama nueva | Historia t=0 como PASADO y presente t=1000 sin turno ([historia](escritorio_historia.png)); pergamino t=1000 → 900 ([retroceso](escritorio_retroceso.png)) | Cinco retrocesos y retiro de observaciones futuras: `prueba_memoria_visual.py` | Parcial manual |
| 7. Guardar/cargar; v6 sin clave, clave inválida, re-guardado de consola | Guardar, reanudar con mapa, selector nativo real ([carga](escritorio_carga.png)) | Matriz v6 y lector congelado de `main`: `prueba_guardado_grafico.py` ([compatibilidad](pygame_compatibilidad_v6.txt)) | Parcial manual |
| 8. Mapa de 300 salas, IDs dispersos, conflictos | 31 enemigos y 19 objetos paginados; hallazgo de página corregido ([muchos](escritorio_muchos.png), [objetivo 31](escritorio_objetivo31.png)) | 300 salas sin solapes y enlaces marcados: `prueba_mapa_grafico.py`; dibujo 15,9 ms de mediana ([mediciones](pygame_mediciones.md)) | Mapa grande solo automatizado |
| 9. Redimensionar, foco, cierre; resultado único | Maximizar/restaurar redistribuye paneles; pérdida y recuperación de foco (SDL); cierre con X sin procesos huérfanos | Cierre durante viaje o carga y resultado único: `prueba_sesion_grafica.py` | Parcial manual |

## Escenarios con verificación real en ventana

AC-IG-001 (inicio y selección), AC-IG-009 (acciones por botones), AC-IG-020
(legibilidad a 1024 × 768 y 1280 × 800 con muchos objetivos) y AC-IG-021 (cierre
sin pérdida de sesión ni procesos abiertos). El resto de escenarios se acredita
con pruebas automatizadas, listadas en la matriz de la especificación.

## Límites declarados

- Antorcha, movimiento remoto provocado, cinco pergaminos con rama nueva, archivos
  v6 cruzados y cierre durante viaje o carga **no se repitieron manualmente**;
  solo los cubren pruebas con vídeo dummy.
- Sin red real, sin latencia de monitor ni GPU. Las mediciones usan vídeo dummy.
- No se afirma ausencia de fallos en otras criptas o equipos.

Las capturas versionadas están en `documentacion/evidencia/escritorio_*.png`;
`resultados/bench/pygame/` (ignorado por Git) contiene los archivos de trabajo.
