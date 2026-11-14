"""FR-IG-002/003/020/024: inicio real con vídeo de pruebas; no acredita QA visual."""
import os
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')

import pytest
pygame = pytest.importorskip('pygame')

from controlador.sesion import ConfiguracionSesion
from Pruebas.datos_graficos import paquete_grafico


@pytest.fixture
def ventana(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from dataclasses import asdict
    from vista.pygame_ui.aplicacion import Aplicacion
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    datos = paquete_grafico(tmp_path/'datos')
    config = ConfiguracionSesion(offline=str(datos), cache_dir=str(tmp_path/'cache'))
    app = Aplicacion(SimpleNamespace(**asdict(config)))
    try:
        app.actualizar(); app.dibujar()
        yield app
    finally:
        app.controlador.cerrar(esperar=True)
        pygame.quit()


def pulsar(app, accion):
    boton = next(b for b in app.ui.botones if b.accion == accion)
    app.evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=boton.rect.center))
    app.evento(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=boton.rect.center))


def test_menu_lista_elige_e_inicia_sin_ordenes_consola(ventana):
    app = ventana
    pulsar(app, 'listar'); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    assert len(app.catalogo) == 1
    pulsar(app, ('cripta', 'lt'))
    pulsar(app, 'nueva'); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    foto = app.controlador.respuesta.presentacion
    assert not app.menu and foto.id_cripta == 'lt' and foto.acciones == 0


def test_campos_foco_texto_y_error_local(ventana):
    app = ventana
    campo = app.campo('semilla')
    app.evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=campo.rect.center))
    app.evento(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=campo.rect.center))
    app.evento(pygame.event.Event(pygame.TEXTINPUT, text='x'))
    pulsar(app, 'nueva')
    assert app.error and not app.controlador.ocupado


def test_verificacion_y_forzado_explicito_desde_menu(ventana, tmp_path):
    app = ventana
    datos = paquete_grafico(tmp_path/'sin_salida', resoluble=False)
    app.campo('offline').valor = str(datos)
    app.campo('cripta').valor = 'lt'
    pulsar(app, 'nueva'); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    assert app.controlador.respuesta.presentacion is None
    assert 'no resoluble' in app.error
    pulsar(app, 'forzar'); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    assert app.controlador.respuesta.presentacion is not None and not app.menu


def test_carga_fallida_mantiene_partida_y_menu_recuperable(ventana, tmp_path):
    app = ventana
    app.campo('cripta').valor = 'lt'
    pulsar(app, 'nueva'); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    foto = app.controlador.respuesta.presentacion
    pulsar(app, 'menu'); app.dibujar()
    app.campo('cargar').valor = str(tmp_path/'inexistente.bin')
    pulsar(app, 'cargar'); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    assert app.menu and app.error
    assert app.controlador.respuesta.presentacion == foto
    pulsar(app, 'continuar'); app.dibujar()
    assert not app.menu


def test_mapa_redibujado_no_observa_ni_reconstruye(ventana):
    app = ventana
    app.campo('cripta').valor = 'lt'
    pulsar(app, 'nueva'); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    foto = app.controlador.respuesta.presentacion
    croquis = app.mapa.croquis
    memoria = app.controlador._memoria
    observaciones = tuple(memoria.observaciones)
    for _ in range(20): app.dibujar()
    assert app.mapa.croquis is croquis
    assert tuple(memoria.observaciones) == observaciones
    assert app.controlador.respuesta.presentacion is foto
    assert foto.acciones == 0 and foto.reloj == 0


def iniciar(app):
    app.campo('cripta').valor = 'lt'
    pulsar(app, 'nueva'); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()


def turno(app, op, arg=None, objetivo=None):
    accion = ('juego', op, arg, objetivo)
    pulsar(app, accion)
    assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    return app.controlador.respuesta


def test_botones_mover_esperar_abrir_rechazar_y_recoger(ventana):
    app = ventana; iniciar(app)
    foto = app.controlador.respuesta.presentacion
    app.accion(('objetivo', foto.objetos[0])); app.dibujar()
    respuesta = turno(app, 'recoger', objetivo=foto.objetos[0])
    assert respuesta.resultado.ordenes == ('recoger 1',)
    assert respuesta.presentacion.acciones == 1
    respuesta = turno(app, 'abrir', 'E')
    assert not respuesta.resultado.aceptada and respuesta.presentacion.acciones == 1
    respuesta = turno(app, 'esperar')
    assert respuesta.presentacion.acciones == 2
    respuesta = turno(app, 'mover', 'N')
    assert respuesta.presentacion.sala_id == 2 and respuesta.presentacion.acciones == 3


def test_inventario_ordenado_seleccion_emite_navegacion_sin_turno(ventana):
    app = ventana; iniciar(app)
    for _ in range(4):
        foto = app.controlador.respuesta.presentacion
        app.accion(('objetivo', foto.objetos[0])); app.dibujar()
        turno(app, 'recoger', objetivo=foto.objetos[0])
    app.accion(('tab', 'inventario')); app.dibujar()
    turno(app, 'orden', 'nombre')
    foto = app.controlador.respuesta.presentacion
    assert foto.inventario[0].nombre == 'Antorcha' and foto.inventario[0].indice == 4
    app.accion(('seleccionar', foto.inventario[0])); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    respuesta = app.controlador.respuesta
    assert respuesta.resultado.ordenes == ('sig', 'sig', 'sig')
    assert respuesta.presentacion.reloj == foto.reloj and respuesta.presentacion.acciones == 4
    assert next(o for o in respuesta.presentacion.inventario if o.seleccionado).indice == 4
    respuesta = turno(app, 'usar')
    assert respuesta.resultado.ordenes == ('usar',) and respuesta.presentacion.acciones == 5


def test_tecla_sostenida_foco_e_inactividad_no_crean_turnos(ventana):
    app = ventana; iniciar(app)
    evento = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, repeat=False)
    app.evento(evento); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    foto = app.controlador.respuesta.presentacion
    assert foto.acciones == 1
    for _ in range(5):
        app.evento(evento)
        app.evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, repeat=True))
    assert app.controlador.esperar(3)
    app.actualizar()
    assert app.controlador.respuesta.presentacion is foto
    app.evento(pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE))
    for _ in range(300): app.dibujar()
    assert app.controlador.respuesta.presentacion is foto
    app.accion('menu'); app.dibujar()
    app.ui.foco = app.campo('nombre')
    app.evento(evento)
    assert app.controlador.respuesta.presentacion is foto


def test_reloj_presentacion_60_segundos_300_frames_sin_simulacion(ventana):
    app = ventana; iniciar(app)
    foto = app.controlador.respuesta.presentacion
    p = app.controlador._sesion.partida
    azar = p.motor.azar.getstate()
    ordenes = tuple(p.linea_tiempo.ordenes)
    class RelojPresentacion:
        frames = 0
        transcurrido = 0
        def tick(self, fps):
            assert fps == 60
            self.frames += 1
            self.transcurrido += 200
            if self.frames == 300:
                app.accion('salir')
                app.controlador.cerrar(esperar=True)
    reloj = RelojPresentacion()
    assert app.ejecutar(reloj) == 0
    assert reloj.frames == 300 and reloj.transcurrido == 60_000
    assert app.controlador.respuesta.presentacion is foto
    assert p.motor.azar.getstate() == azar and tuple(p.linea_tiempo.ordenes) == ordenes


def test_ataque_equipar_soltar_y_entrada_ocupada(ventana):
    from threading import Event
    app = ventana; iniciar(app)
    foto = app.controlador.respuesta.presentacion
    app.accion(('objetivo', foto.objetos[2])); app.dibujar()
    turno(app, 'recoger', objetivo=foto.objetos[2])
    app.accion(('tab', 'inventario')); app.dibujar()
    assert turno(app, 'equipar').resultado.ordenes == ('equipar',)
    assert turno(app, 'soltar').resultado.ordenes == ('soltar',)
    turno(app, 'mover', 'N'); turno(app, 'mover', 'N')
    foto = app.controlador.respuesta.presentacion
    app.accion(('objetivo', foto.enemigos[0])); app.dibujar()
    assert turno(app, 'atacar', objetivo=foto.enemigos[0]).resultado.ordenes == ('atacar 1',)
    p = app.controlador._sesion.partida
    entrar, liberar = Event(), Event()
    original = p.esperar
    def lento():
        entrar.set(); assert liberar.wait(3)
        return original()
    p.esperar = lento
    try:
        app.accion(('juego', 'esperar', None, None))
        assert entrar.wait(3)
        app.evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s, repeat=False))
        assert not app.controlador.enviar(__import__('controlador.proyeccion_grafica', fromlist=['IntencionGrafica']).IntencionGrafica(foto.generacion, foto.revision, 'esperar'))
        liberar.set(); assert app.controlador.esperar(3)
        assert app.controlador.respuesta.presentacion.sala_id == 3
    finally:
        liberar.set()
