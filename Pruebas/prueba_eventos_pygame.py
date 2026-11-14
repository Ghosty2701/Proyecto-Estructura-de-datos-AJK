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
