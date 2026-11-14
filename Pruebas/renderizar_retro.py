"""Capturas reproducibles de la interfaz; SDL dummy no acredita revisión nativa."""
from pathlib import Path
from dataclasses import asdict, replace
from types import SimpleNamespace
import os


def ejecutar():
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    import pygame
    from Pruebas.datos_graficos import paquete_grafico
    from controlador.sesion import ConfiguracionSesion
    from controlador.proyeccion_grafica import ConexionVisual
    from vista.pygame_ui.aplicacion import Aplicacion
    carpeta = Path('resultados/bench/pygame/retro')
    carpeta.mkdir(parents=True, exist_ok=True)
    datos = paquete_grafico(carpeta/'datos')
    config = ConfiguracionSesion(cripta='lt', offline=str(datos), cache_dir=str(carpeta/'cache'))
    app = Aplicacion(SimpleNamespace(**asdict(config)))
    def guardar(nombre):
        app.dibujar()
        pygame.image.save(app.ventana, carpeta/nombre)
    try:
        assert app.controlador.esperar(5)
        app.animacion.modo = 'sin'; app.actualizar()
        guardar('inicio.png')
        app.accion(('objetivo', app.controlador.respuesta.presentacion.objetos[0]))
        guardar('objeto.png')
        app.accion('inventario_panel'); guardar('inventario.png')
        app.accion('cerrar_local')
        for d in ('N', 'N'):
            app.accion(('juego', 'mover', d, None)); assert app.controlador.esperar(5)
            app.actualizar()
        foto = app.controlador.respuesta.presentacion
        app.accion(('objetivo', foto.enemigos[0])); guardar('combate.png')
        pygame.image.save(app.ventana, 'documentacion/evidencia/retro_jugable.png')
        app.accion('pausa'); guardar('pausa.png')
        app.accion('cerrar_local')
        app.evento(pygame.event.Event(pygame.VIDEORESIZE, w=1024, h=768))
        guardar('minima.png')
        for abierta in (False, True):
            # DTO sintético para inspeccionar las cuatro orientaciones; no cambia el motor.
            actual = next(s for s in foto.salas if s.actual)
            sala = replace(actual, salidas=tuple(ConexionVisual(d, 1, 'Prueba', 100, abierta) for d in ('N', 'S', 'E', 'O')))
            visual = replace(foto, salas=tuple(sala if s.actual else s for s in foto.salas))
            app.controlador._respuesta = replace(app.controlador.respuesta, presentacion=visual)
            guardar('puertas-abiertas.png' if abierta else 'puertas-cerradas.png')
        print('Capturas:', carpeta.resolve())
    finally:
        app.controlador.cerrar(esperar=True); pygame.quit()


if __name__ == '__main__':
    ejecutar()
