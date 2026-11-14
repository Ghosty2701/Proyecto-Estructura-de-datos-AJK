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
7. Menú → Guardar/Cargar partida y Consultar historia: mismo juego y memoria de 005.
8. Ventana 1024 × 768 y 1280 × 800; muchos enemigos/objetos mediante fixture,
   páginas alcanzables, sprites identificables y texto legible.

Pruebas disponibles: `Pruebas/prueba_sala_visual.py` y
`Pruebas/prueba_animaciones_visuales.py` y `Pruebas/prueba_interfaz_compacta.py`;
regresión completa: 849 con Pygame y 819 sin él (tres módulos omitidos).
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

Medición reproducible: `.\.venv\Scripts\python.exe -m Pruebas.medir_escena`.
Incluye 300 redibujados con pausas de 0,2 s y dura algo más de un minuto.
