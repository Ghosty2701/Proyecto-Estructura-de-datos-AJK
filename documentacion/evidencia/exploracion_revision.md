# Exploración ligera — cierre 2026-11-14

Spec previo en `205610e`, rama `005-interfaz-pygame`. Alcance personal Pygame;
sin cambios al motor, esquema v6, presupuesto HTTP o excepción académica EX-01.

## Cambios verificados

- FR-EV-022 / AC-EV-024: marco del minimapa de 156 a 286 px; área útil de
  140 a 234 px de alto, escala inicial 0,45 → 0,60. Estado debajo, sala visible.
- FR-EV-023 / AC-EV-025: inicio/cierre conserva actividad detallada; juego usa
  indicador de 160 × 30 en una esquina, después de 150 ms. Las operaciones
  rápidas no muestran el indicador. Sin botón extra ni espera añadida al motor.
- FR-EV-024 / AC-EV-026: leyenda tenue WASD/H permanente; H abre ayuda existente.
  Ayuda/cierre de panel no cambia acciones ni reloj.
- FR-EV-025 / AC-EV-027: mismo snapshot inmutable evita recorrer topología cada
  cuadro; croquis/índice existentes se invalidan cuando cambian sus datos.
  Prueba cuenta iteraciones: cero recorridos adicionales en veinte llamadas
  sobre el mismo snapshot. No se recargan PNG al moverse.
- Movimiento: transición normal 500 → 160 ms, reducida 180 → 80 ms; el combate
  conserva 500/180 ms. Son duraciones de presentación, no latencia de red.
- La revisión nativa descubrió una selección de objetivos fuera de página:
  ahora la lista numera enemigos/objetos y elegir uno muestra su página y sprite.
  Casos nuevos con 31 enemigos y 19 objetos; selección sin turno.

## Medidas reproducibles y límites

```powershell
.\.venv\Scripts\python.exe -m Pruebas.medir_exploracion documentacion/evidencia/exploracion_perfil_despues.txt
```

Paquete sintético lt de seis salas, semilla 2026, 40 movimientos N/S entre
salas 1/2, Python 3.13.2/Pygame 2.6.1, vídeo dummy. Acción con cProfile y
dibujo sin perfil, separados. Fuente local y caché de catálogo reutilizada.

| Mediana observada | Antes | Después |
|---|---:|---:|
| Acción instrumentada | 0,513 ms | 0,475 ms |
| Dibujo | 3,385 ms | 3,045 ms |

Salidas íntegras: [antes](exploracion_perfil_antes.txt) y
[después](exploracion_perfil_despues.txt), con mínimos/máximos y perfil.
La variación de muestras no demuestra una mejora de red o un porcentaje estable
de rendimiento. La reducción garantizada es la duración configurada de transición
y la eliminación del recorrido repetido. El servicio ya anticipa vecinas y
omite consultas nuevas de contenido para destinos anticipados; no se cambió
su política ni se añadieron estructuras/cachés de biblioteca.
No incluye monitor, HTTP real o cargas publicadas grandes; EX-01 no se reabre.

## Regresión y revisión visual

**866 pruebas con Pygame**, [salida](exploracion_regresion_grafica.txt).
**819 sin Pygame y cinco módulos gráficos omitidos**,
[salida](exploracion_regresion_sin_pygame.txt). Incluye matriz v6, equivalencia
de estados/azar/registro, niebla, memoria y animaciones existentes.
Ocho casos nuevos en `Pruebas/prueba_exploracion_ligera.py`; se observaron fallos
antes de implementar y antes de corregir el hallazgo de paginación.

Renders reproducibles: `.\.venv\Scripts\python.exe -m Pruebas.renderizar_retro`.
[Actividad discreta](actividad_clara.png), [render actual](retro_jugable.png).
No se confunden esas capturas dummy con la
[revisión interactiva de escritorio](exploracion_escritorio.md).

Alcance actual de 006 terminado: 25 FR, 27 AC, 12 SC y tareas T001–T048
auditadas. Estimación de avance de Pygame: 100 % del alcance acordado,
no del proyecto académico ni de futuras mejoras. Rama lista para evaluar
integración; no se fusiona main y no se afirma latencia de red universal.
