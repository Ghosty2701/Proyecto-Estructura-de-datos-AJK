"""Abre la aplicación real con datos/archivos aislados para revisión nativa manual."""
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
import os
import json
import sys


def ejecutar():
    os.environ.pop('SDL_VIDEODRIVER', None)
    import pygame
    from Pruebas.datos_graficos import paquete_grafico
    from controlador.sesion import ConfiguracionSesion
    from vista.pygame_ui.aplicacion import Aplicacion
    carpeta = Path('resultados/bench/pygame/escritorio-final')
    muchos = '--muchos' in sys.argv
    if muchos:
        carpeta = carpeta/'muchos'
    datos = paquete_grafico(carpeta/'datos')
    if muchos:
        ruta = datos/'criptas/lt/contenido/1.json'
        contenido = json.loads(ruta.read_text(encoding='utf-8'))
        contenido['enemigos'] = [dict(instancia=f'g-{i}', tipo='guardian', vida=None) for i in range(31)]
        contenido['objetos'] = ['pergamino']*19
        ruta.write_text(json.dumps(contenido), encoding='utf-8')
    config = ConfiguracionSesion(cripta='lt' if muchos else None,
                                 offline=str(datos), cache_dir=str(carpeta/'cache'),
                                 archivo_guardado=str(carpeta/'revision.bin'),
                                 puntajes=str(carpeta/'puntajes.json'))
    registro = carpeta/'eventos_nativos.txt'
    registro.write_text('Eventos nativos de entrada; sin contenido de la partida.\n', encoding='utf-8')
    class AplicacionRevisada(Aplicacion):
        def evento(self, evento):
            if evento.type in (pygame.KEYDOWN, pygame.KEYUP, pygame.TEXTINPUT,
                               pygame.WINDOWFOCUSGAINED, pygame.WINDOWFOCUSLOST):
                with registro.open('a', encoding='utf-8') as archivo:
                    archivo.write(repr(evento)+'\n')
            super().evento(evento)
    app = AplicacionRevisada(SimpleNamespace(**asdict(config)))
    pygame.display.set_caption('Cripta - Revision final Pygame')
    if '--minima' in sys.argv:
        app.evento(pygame.event.Event(pygame.VIDEORESIZE, w=1024, h=768))
    app.ejecutar()


if __name__ == '__main__':
    ejecutar()
