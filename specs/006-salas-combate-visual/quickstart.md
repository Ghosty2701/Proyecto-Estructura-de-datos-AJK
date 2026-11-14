# Guía de validación prevista — escena ilustrada

**Estado**: escena implementada; regresión automática aprobada. Recorrido nativo
completo pendiente; no presentarlo como aprobado por las capturas con vídeo dummy.

## Preparación

```powershell
.\.venv\Scripts\python.exe -m pip install -r documentacion/requirements-pygame.txt
.\.venv\Scripts\python.exe -c "from pathlib import Path; from Pruebas.datos_graficos import paquete_grafico; paquete_grafico(Path('resultados/bench/pygame/datos'))"
.\.venv\Scripts\python.exe main.py --interfaz pygame --offline resultados/bench/pygame/datos --cripta lt
```

Debe aparecer una habitación pixelada con personaje y puerta N; minimapa
secundario y suelo seleccionable. Este comando ya abre la nueva escena de 006.

## Recorrido de aceptación

1. Seleccionar pergamino y pulsar Recoger; abrir Inventario para equipar arma o usar antorcha.
2. Seleccionar puerta N y mover; comprobar daño visible de trampa confirmado.
3. Volver a mover N: aparece guardián dentro de la misma sala. Seleccionar su
   sprite, atacar y comprobar vida/efectos; derrotarlo produce desvanecimiento.
4. Saltar un efecto y repetir con modo reducido/sin efectos; comparar estado,
   reloj y registro con la secuencia canónica de consola.
5. Abrir mapa, comprobar niebla y recuerdos; no presentar contenido remoto.
6. Viajar y detener, perder foco y retroceder: ningún turno extra o efecto del futuro.
7. Menú → Guardar partida/Reanudar guardado actual y Consultar historia: mismo juego y memoria de 005.
   Cargar otro archivo abre el inicio de carga, con búsqueda y confirmación.
8. Ventana 1024 × 768 y 1280 × 800; muchos enemigos/objetos mediante fixture,
   páginas alcanzables, sprites identificables y texto legible.

Pruebas disponibles: `Pruebas/prueba_sala_visual.py` y
`Pruebas/prueba_animaciones_visuales.py` y `Pruebas/prueba_interfaz_compacta.py`;
regresión completa: 858 con Pygame y 819 sin él (cuatro módulos omitidos).
La comprobación gráfica con vídeo dummy no sustituye pasos 1–8
en escritorio real. Evidencia de render y límites en `documentacion/evidencia/`;
capturas pertinentes en `resultados/bench/pygame/`.

Espacio durante un efecto lo salta sin esperar. Menú → Opciones y ayuda →
Animaciones recorre normal, reducida y sin efectos. Mapa abre su panel; Esc
vuelve a la habitación o abre el menú. Inventario aparece como panel; Objetivos
permite recorrer muchos elementos. Rueda sobre la lista para desplazarse.
La pantalla habitual no muestra botones para todas las direcciones ni operaciones
de guardado: una puerta seleccionada ofrece la acción contextual correspondiente.

Renders reproducibles: `.\.venv\Scripts\python.exe -m Pruebas.renderizar_retro`.
Produce ejemplos de las ocho puertas solo para inspección, sin cambiar el motor.

Revisión de claridad: iniciar sin `--cripta` muestra Nueva partida. Buscar criptas,
elegir una y comprobar fila dorada y resumen antes de Empezar partida. Cargar
partida abre su pantalla; Buscar archivo .bin usa el selector nativo si tkinter
está disponible, o permite escribir la ruta. Cancelar conserva la selección.
Esc vuelve, y una carga fallida permite corregir ruta o volver a la partida.
El guardado conserva su nombre y semilla, aunque los campos de partida nueva
tengan otros valores. Opciones de datos permite elegir una fuente compatible.

Inventario: Ordenar por nombre/peso/valor cambia solo la lista, sin turno;
nombre A–Z, peso/valor de menor a mayor. El criterio queda resaltado y los
objetos muestran peso/valor. Las operaciones demoradas muestran actividad
animada y segundos transcurridos; la ventana conserva su cierre seguro.
Revisar que rata, sabueso óseo y espectro se distinguen independientemente de
su comportamiento. Los nombres desconocidos mantienen nombre y símbolo neutral.
Evidencia y límites: `documentacion/evidencia/claridad_revision.md`.

Medición reproducible: `.\.venv\Scripts\python.exe -m Pruebas.medir_escena`.
Incluye 300 redibujados con pausas de 0,2 s y dura algo más de un minuto.
