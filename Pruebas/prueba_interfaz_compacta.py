"""FR-EV-015/016: comandos contextuales y paneles de RPG sin nuevos turnos."""
import pytest
pygame = pytest.importorskip('pygame')
from Pruebas.prueba_eventos_pygame import ventana, iniciar, pulsar


@pytest.mark.parametrize('tamano', [(1024, 768), (1280, 800)])
def test_habitacion_tiene_hasta_seis_comandos_y_contexto(ventana, tamano):
    app = ventana; iniciar(app)
    app.evento(pygame.event.Event(pygame.VIDEORESIZE, w=tamano[0], h=tamano[1]))
    app.dibujar()
    assert len(app.ui.botones) <= 6
    assert all(app.ventana.get_rect().contains(b.rect) for b in app.ui.botones)
    assert not any(b.accion == ('juego', 'guardar', None, None) for b in app.ui.botones)
    foto = app.controlador.respuesta.presentacion
    app.accion(('objetivo', foto.objetos[0])); app.dibujar()
    recoger = next(b for b in app.ui.botones if b.texto == 'Recoger')
    assert recoger.accion == ('juego', 'recoger', None, foto.objetos[0])
    app.accion(('puerta', 'N')); app.dibujar()
    entrar = next(b for b in app.ui.botones if b.texto == 'Entrar')
    assert entrar.accion == ('juego', 'mover', 'N', None)
    assert foto.acciones == 0 and foto.reloj == 0


def test_pausa_inventario_y_escape_no_consumen_turnos(ventana):
    app = ventana; iniciar(app)
    antes = app.controlador.respuesta.presentacion
    pulsar(app, 'pausa'); app.dibujar()
    assert app.panel_local == 'pausa'
    assert any(b.texto == 'Guardar partida' for b in app.ui.botones)
    assert any(b.texto == 'Consultar historia' for b in app.ui.botones)
    assert any(b.texto == 'Usar pergamino' for b in app.ui.botones)
    app.evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, repeat=False))
    app.evento(pygame.event.Event(pygame.KEYUP, key=pygame.K_ESCAPE))
    app.dibujar(); assert app.panel_local is None
    pulsar(app, 'inventario_panel'); app.dibujar()
    assert app.panel_local == 'inventario'
    assert app.controlador.respuesta.presentacion is antes


def test_todas_las_puertas_tienen_orientacion_propia(ventana):
    app = ventana; iniciar(app)
    recursos = app.escena.recursos
    assert len(recursos.puertas_fuente) == 8
    recursos.preparar((800, 550))
    cerradas = [recursos.puerta(False, d) for d in ('N', 'S', 'E', 'O')]
    abiertas = [recursos.puerta(True, d) for d in ('N', 'S', 'E', 'O')]
    assert all(a is not b for a, b in zip(cerradas, abiertas))
    assert len({pygame.image.tobytes(s, 'RGBA') for s in cerradas+abiertas}) == 8
