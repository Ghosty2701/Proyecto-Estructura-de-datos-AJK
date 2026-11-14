# Mediciones de Pygame (005, T050) — 2026-11-14

Equipo: Windows-11-10.0.26200-SP0; Intel64 Family 6 Model 142 Stepping 12, GenuineIntel.
Python 3.13.17; Pygame 2.6.1; SDL (2, 28, 4).
Video dummy: dibujo de superficies, sin medir GPU, monitor ni percepcion nativa.
Paquete sintetico lt de seis salas; semilla 2026; cache 25; sin HTTP.

| Operacion | Muestras | Min ms | Mediana ms | Max ms |
|---|---:|---:|---:|---:|
| Escena + HUD 1024x768 | 60 | 3.236 | 3.501 | 6.647 |
| Escena + HUD 1280x800 | 60 | 3.655 | 3.997 | 5.934 |
| Mapa conocido 300 salas | 60 | 14.483 | 15.858 | 17.723 |
| Accion esperar completa sin dibujo/red | 100 | 0.036 | 0.040 | 1.625 |

Inactividad real: 300 redibujados en 61.768 s, pausas de 0.2 s.
Reloj virtual, acciones, azar y ordenes no cambiaron durante esa inactividad.
Las muestras de dibujo reutilizan recursos escalados; no incluyen carga de PNG ni red.
Accion completa incluye motor y registro/linea compartidos; no es el ciclo oficial K10.
No se afirma EX-01 resuelta ni se extrapola a otras criptas/equipos.
Comando: ./.venv/Scripts/python.exe -m Pruebas.medir_escena documentacion/evidencia/pygame_mediciones.md
