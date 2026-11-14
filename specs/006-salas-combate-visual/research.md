# Investigación: Habitación y animaciones

**Fecha**: 2026-11-14. **Estado**: Investigación de integración completada;
D-EV-04 confirmada por el usuario. No contiene elecciones de estructuras inferidas.

## D-EV-01 — Vista principal

**Elección del usuario**: sala desde arriba con minimapa.
**Razón**: el personaje habita una habitación y el mapa ayuda a orientarse.
**Alternativa consultada**: otra perspectiva. No fue elegida.

## D-EV-02 — Presentación del combate

**Elección del usuario**: dentro de la misma sala, con animaciones por turno.
**Razón**: continuidad visual entre explorar y atacar.
**Alternativa consultada**: escena separada inspirada en RPG Maker. No fue elegida.

## D-EV-03 — Dirección artística

**Elección del usuario**: ilustración 2D de fantasía oscura.
**Alternativa consultada**: pixel art oscuro y legible. No fue elegida.
Arte original, con siluetas claras y selección complementada por nombre y borde;
ilustración oscura no significa ocultar objetos o controles por falta de contraste.

## D-EV-04 — Organización de elementos y efectos: confirmada

Nueva necesidad: organizar recursos y sprites de la habitación, sus regiones de
clic y los efectos de un turno. AGENTS.md exige presentar alternativas y esperar
la elección, incluso cuando existe una estructura heredada reutilizable.

| Alternativa consultada | Ventaja | Costo/límite |
|---|---|---|
| Vectores por sala y un registro de animación activa | Simples, recorrido predecible, fáciles de invalidar por revisión; sin cola de turnos | Selección por recorrido lineal; paginar contenido numeroso |
| Índice espacial propio para sprites/clics | Reduce candidatos cuando hay muchos elementos | Construir, mantener e invalidar el índice; más complejidad para una sola sala |

**Recomendación**: primera opción. **Elección explícita**: vectores por sala y una animación activa; todavía no implementada.
La consulta incluye sprites, regiones de clic y efectos. No se añadirá una
estructura auxiliar no aprobada bajo la apariencia de un detalle estándar.

## D-EV-05 — Integración y privacidad

Investigación de lectura realizada siguiendo la fase 0 de `$speckit-plan`, con
un revisor de integración y sin cambios de archivos por su parte.

- `controlador/proyeccion_grafica.py:76,132`: datos suficientes para habitación,
  personaje, objetos y enemigos actuales. Las salidas salen de `SalaVisual.actual`.
- `vista/pygame_ui/aplicacion.py:186`: punto para reemplazar mapa central por sala.
- `vista/pygame_ui/aplicacion.py:135`: nueva respuesta confirmada, distinguiendo
  acciones aceptadas de consultas. El número de revisión no basta.
- `controlador/controlador_grafico.py:284`: frontera del trabajador para entregar
  efectos estructurados sin transmitir modelos vivos.
- `vista/pygame_ui/aplicacion.py:364`: coordinación de pasos del viaje con la
  transición visual y el ciclo de eventos.

Las posiciones interiores son escénicas: no hay coordenadas jugables, alcance
ni colisiones en el modelo. Se conserva el costo de ir entre salas.

## D-EV-06 — Hechos confirmados frente a inferencias

Antes/después ofrece variación neta de vida de actores que siguen observables.
No ofrece secuencia de golpes, daño+curación cancelados ni distingue muerte y
abandono de la sala. No se usará desaparición como prueba de derrota, ni se
analizarán mensajes textuales para decidir resultados.

Los puntos `_informar_inicio` y `_ejecutar_evento` en `controlador/partida.py`
conocen el daño, ataque inicial, derrota y eventos observables cuando suceden.
Se propone callback opcional pasado por parámetros, sin guardarlo en objetos
persistidos. Así se pueden emitir hechos estructurados sin cambiar las reglas.
La forma de agrupar dichos hechos depende de D-EV-04.

**Alternativa considerada**: solo comparar snapshots y mostrar cambios agregados.
Es suficiente para cifras netas, pero no para todas las animaciones de derrota
solicitadas en el spec. No se atribuirán golpes precisos usando esa inferencia.

## D-EV-07 — Reutilización y pruebas

La nueva vista entrega los `ObjetivoActual` existentes a la validación por
generación y revisión. Suelo/inventario conservan posiciones vigentes; nombres
repetidos no se convierten en identificadores.

Regresiones a reutilizar: mapa, memoria, sesión, guardado, CLI y eventos de 005.
Casos adicionales: daño y curación neta cero; enemigo que sale sin morir;
rechazo sin éxito visual; salto/reducción de efectos; carga/retroceso durante
animación; muchos objetivos y selección desde sus sprites.

No añadir atributos gráficos ni métodos enlazados por instancia a Partida o
MotorEventos: el esquema v6 es cerrado. Guardado y checkpoints deben seguir
pasando con las mismas raíces y campos.

## Fuentes y límites

Código local en `61ef64a`, spec aclarado y constitución. No se han ejecutado
pruebas ni medido rendimiento para esta capacidad; las afirmaciones anteriores
son hallazgos de lectura y propuestas de integración. D-EV-04 quedó resuelta explícitamente por el usuario; la investigación de diseño está cerrada.
