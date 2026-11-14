"""Capturas reproducibles de la interfaz; SDL dummy no acredita revisión nativa."""
from pathlib import Path
from dataclasses import asdict, replace
from types import SimpleNamespace
from threading import Event
import os


def ejecutar():
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    import pygame
    from Pruebas.datos_graficos import paquete_grafico
    from controlador.sesion import ConfiguracionSesion
    from controlador.proyeccion_grafica import ConexionVisual, ObjetivoActual
    from vista.pygame_ui.aplicacion import Aplicacion
    carpeta = Path('resultados/bench/pygame/retro')
    carpeta.mkdir(parents=True, exist_ok=True)
    datos = paquete_grafico(carpeta/'datos')
    config = ConfiguracionSesion(cripta='lt', offline=str(datos), cache_dir=str(carpeta/'cache'),
                                 archivo_guardado=str(carpeta/'aventura.bin'))
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
        while app.controlador.respuesta.presentacion.objetos:
            objetivo = app.controlador.respuesta.presentacion.objetos[0]
            app.accion(('juego', 'recoger', None, objetivo)); assert app.controlador.esperar(5)
            app.actualizar()
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
        app.accion(('juego', 'guardar', None, None)); assert app.controlador.esperar(5)
        app.actualizar()
        foto = app.controlador.respuesta.presentacion
        # Catálogo y carga usan operaciones reales sobre el paquete y bin de prueba.
        app.accion('menu'); app.accion('listar'); assert app.controlador.esperar(5)
        app.actualizar(); app.accion(('cripta', 'lt'))
        for tamano in ((1280, 800), (1024, 768)):
            app.evento(pygame.event.Event(pygame.VIDEORESIZE, w=tamano[0], h=tamano[1]))
            guardar(f'menu-nueva-{tamano[0]}.png')
            if tamano[0] == 1280:
                pygame.image.save(app.ventana, 'documentacion/evidencia/inicio_claro.png')
            app.accion('pantalla_cargar'); app.campo('cargar').valor = config.archivo_guardado
            guardar(f'menu-carga-{tamano[0]}.png')
            if tamano[0] == 1280:
                pygame.image.save(app.ventana, 'documentacion/evidencia/carga_clara.png')
            app.accion('pantalla_nueva')
        app.accion('continuar')
        app.evento(pygame.event.Event(pygame.VIDEORESIZE, w=1280, h=800))
        app.accion('inventario_panel')
        app.accion(('juego', 'orden', 'peso', None)); assert app.controlador.esperar(5)
        app.actualizar(); guardar('inventario-orden.png')
        pygame.image.save(app.ventana, 'documentacion/evidencia/inventario_claro.png')
        app.accion('cerrar_local')
        foto = app.controlador.respuesta.presentacion
        # Muestra de especies en DTO de render; no añade enemigos al motor.
        especies = tuple(ObjetivoActual('enemigo', f'muestra-{i}', i+1, nombre, 'rastreador', 8, 10)
                         for i, nombre in enumerate(('Rata gigante', 'Espectro acechador', 'Sabueso óseo')))
        app.controlador._respuesta = replace(app.controlador.respuesta, presentacion=replace(foto, enemigos=especies))
        app.accion(('objetivo', especies[0])); guardar('criaturas.png')
        pygame.image.save(app.ventana, 'documentacion/evidencia/criaturas_claras.png')
        app.controlador._respuesta = replace(app.controlador.respuesta, presentacion=foto)
        app.objetivo = None
        entrada, liberar = Event(), Event()
        original = app.controlador._ejecutar
        def demorada(*args, **kwargs):
            entrada.set()
            if not liberar.wait(5): raise TimeoutError('Render demorado')
            original(*args, **kwargs)
        app.controlador._ejecutar = demorada
        try:
            app.accion(('juego', 'esperar', None, None)); assert entrada.wait(3)
            pygame.time.wait(170)  # Solo fixture: supera el umbral de dibujo compacto.
            guardar('actividad-juego.png')
            pygame.image.save(app.ventana, 'documentacion/evidencia/actividad_clara.png')
        finally:
            liberar.set()
        assert app.controlador.esperar(5)
        app.controlador._ejecutar = original
        app.actualizar(); foto = app.controlador.respuesta.presentacion
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
