# Mediciones de escena — 2026-11-14

Equipo: Windows-11-10.0.26200-SP0; Intel64 Family 6 Model 191 Stepping 5, GenuineIntel.
Python 3.13.2; Pygame 2.6.1; SDL (2, 28, 4).
Video dummy: dibujo de superficies, sin medir GPU, monitor ni percepcion nativa.
Paquete sintetico lt de seis salas; semilla 2026; cache 25; sin HTTP.

| Operacion | Muestras | Min ms | Mediana ms | Max ms |
|---|---:|---:|---:|---:|
| Escena + HUD 1024x768 | 60 | 2.084 | 2.258 | 3.317 |
| Escena + HUD 1280x800 | 60 | 2.411 | 2.573 | 3.720 |
| Mapa conocido 300 salas | 60 | 9.906 | 10.619 | 11.746 |
| Accion esperar completa sin dibujo/red | 100 | 0.020 | 0.025 | 1.028 |

Inactividad real: 300 redibujados en 60.993 s, pausas de 0.2 s.
Reloj virtual, acciones, azar y ordenes no cambiaron durante esa inactividad.
Las muestras de dibujo reutilizan recursos escalados; no incluyen carga de PNG ni red.
Accion completa incluye motor y registro/linea compartidos; no es el ciclo oficial K10.
No se afirma EX-01 resuelta ni se extrapola a otras criptas/equipos.
Comando: ./.venv/Scripts/python.exe -m Pruebas.medir_escena
