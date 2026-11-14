"""Perfil de movimiento/render local, sin red ni presupuesto oficial EX-01."""
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from time import perf_counter
from statistics import median
import cProfile
import io
import os
import pstats
import sys


def ejecutar(destino):
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    from Pruebas.datos_graficos import paquete_grafico
    from controlador.sesion import ConfiguracionSesion
    from controlador.proyeccion_grafica import IntencionGrafica
    from vista.pygame_ui.aplicacion import Aplicacion
    import pygame
    datos = paquete_grafico(Path('resultados/bench/pygame/exploracion/datos'))
    config = ConfiguracionSesion(cripta='lt', offline=str(datos),
                                 cache_dir='resultados/bench/pygame/exploracion/cache')
    app = Aplicacion(SimpleNamespace(**asdict(config)))
    perfil = cProfile.Profile()
    acciones, dibujos = [], []
    try:
        assert app.controlador.esperar(5)
        app.animacion.modo = 'sin'; app.actualizar(); app.dibujar()
        for i in range(40):
            foto = app.controlador.respuesta.presentacion
            orden = IntencionGrafica(foto.generacion, foto.revision, 'mover', 'N' if i%2 == 0 else 'S')
            t = perf_counter(); perfil.runcall(app.controlador._ejecutar, orden)
            acciones.append((perf_counter()-t)*1000)
            app.actualizar()
            t = perf_counter(); app.dibujar(); dibujos.append((perf_counter()-t)*1000)
        salida = io.StringIO()
        pstats.Stats(perfil, stream=salida).sort_stats('cumulative').print_stats(22)
        filas = ['Movimiento local entre salas 1/2; paquete lt, semilla 2026; 40 muestras.',
                 'Python '+sys.version.split()[0]+'; Pygame '+pygame.version.ver+'; SDL dummy.',
                 'Acción medida con cProfile, incluye instrumentación; dibujo separado sin perfil.',
                 'No incluye red, monitor, arranque, PNG ni demora de animación.',
                 f'Acción min/mediana/max ms: {min(acciones):.3f}/{median(acciones):.3f}/{max(acciones):.3f}',
                 f'Dibujo min/mediana/max ms: {min(dibujos):.3f}/{median(dibujos):.3f}/{max(dibujos):.3f}',
                 salida.getvalue()]
        Path(destino).write_text('\n'.join(filas), encoding='utf-8')
        print('\n'.join(filas))
    finally:
        app.controlador.cerrar(esperar=True); pygame.quit()


if __name__ == '__main__':
    ejecutar(sys.argv[1])
