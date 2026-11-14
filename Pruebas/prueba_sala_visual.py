"""FR-EV-001/002/003/004/005/013/014: recursos y habitación con vídeo de pruebas."""
import pytest
pygame = pytest.importorskip('pygame')
from dataclasses import replace
from Pruebas.datos_graficos import partida_grafica
from controlador.proyeccion_grafica import proyectar, ObjetivoActual
from Pruebas.prueba_eventos_pygame import ventana, iniciar, pulsar


@pytest.fixture
def pantalla(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    pygame.display.init(); pygame.font.init()
    lienzo = pygame.display.set_mode((1024, 768))
    yield lienzo
    pygame.quit()


def test_atlas_locales_transparentes_y_genericos_sin_red(pantalla, monkeypatch):
    import requests
    from vista.pygame_ui.recursos import Recursos
    monkeypatch.setattr(requests, 'get', lambda *a, **k: pytest.fail('Arte no usa red'))
    recursos = Recursos()
    recursos.preparar((700, 500))
    assert len(recursos.actores) == 6 and len(recursos.elementos) == 12
    assert recursos.actor('jugador').get_flags() & pygame.SRCALPHA
    assert recursos.actor('guardian') is not recursos.actor('cazador')
    assert recursos.actor('nuevo_tipo') is recursos.actor('otro')
    assert recursos.objeto('objeto_nuevo') is recursos.objeto('otro')
    assert recursos.objeto('pergamino_retroceso') is not recursos.objeto('pocion')
    fondo = recursos.fondo
    jugador = recursos.actor('jugador')
    recursos.preparar((700, 500))
    assert recursos.fondo is fondo and recursos.actor('jugador') is jugador
    assert fondo.get_size() == (700, 500)


def test_sala_solo_actual_puertas_y_objetivos_vigentes(pantalla, tmp_path):
    from vista.pygame_ui.sala import EscenaSala
    from vista.pygame_ui.componentes import Componentes
    p, _ = partida_grafica(tmp_path)
    foto = proyectar(p, 1, 0)
    escena = EscenaSala()
    escena.dibujar(pantalla, (12, 90, 680, 440), foto, Componentes())
    assert escena.direcciones == ('N',)
    assert not any(r.clase == 'enemigo' for r in escena.regiones)
    objeto = next(r for r in escena.regiones if r.clase == 'suelo')
    assert escena.seleccionar(objeto.rect.center) == ('objetivo', objeto.objetivo)
    puerta = next(r for r in escena.regiones if r.clase == 'puerta')
    assert escena.seleccionar(puerta.rect.center) == ('puerta', 'N')
    assert p.motor.reloj == 0 and p.acciones_ejecutadas == 0


def test_paginacion_12_enemigos_8_objetos_y_nombres_repetidos(pantalla, tmp_path):
    from vista.pygame_ui.sala import EscenaSala
    from vista.pygame_ui.componentes import Componentes
    p, _ = partida_grafica(tmp_path)
    foto = replace(proyectar(p, 1, 0), enemigos=tuple(
        ObjetivoActual('enemigo', f'e-{i}', i+1, 'Guardián', 'guardian', 12, 14) for i in range(31)),
        objetos=tuple(ObjetivoActual('suelo', 'igual', i+1, 'Poción', clase_objeto='pocion') for i in range(19)))
    escena, ui = EscenaSala(), Componentes()
    encontrados, objetos = [], []
    for pagina in range(3):
        escena.pagina_enemigos = pagina
        escena.pagina_objetos = pagina
        escena.dibujar(pantalla, (12, 90, 680, 440), foto, ui)
        enemigos = [r for r in escena.regiones if r.clase == 'enemigo']
        suelo = [r for r in escena.regiones if r.clase == 'suelo']
        assert len(enemigos) <= 12 and len(suelo) <= 8
        assert all(escena.rect.contains(r.rect) for r in escena.regiones)
        for r in enemigos:
            assert escena.seleccionar(r.rect.center) == ('objetivo', r.objetivo)
            encontrados.append(r.objetivo.identificador)
        objetos.extend(r.objetivo.indice for r in suelo)
    assert len(encontrados) == len(set(encontrados)) == 31
    assert objetos == list(range(1, 20))


def test_clic_sprite_y_puerta_sin_turno_y_movimiento_canonico(ventana):
    app = ventana; iniciar(app)
    objeto = next(r for r in app.escena.regiones if r.clase == 'suelo')
    for tipo in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        app.evento(pygame.event.Event(tipo, button=1, pos=objeto.rect.center))
    assert app.objetivo == objeto.objetivo
    assert app.controlador.respuesta.presentacion.acciones == 0
    app.dibujar()
    pulsar(app, ('juego', 'recoger', None, objeto.objetivo)); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    puerta = next(r for r in app.escena.regiones if r.clase == 'puerta')
    for tipo in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        app.evento(pygame.event.Event(tipo, button=1, pos=puerta.rect.center))
    assert app.puerta == 'N'
    pulsar(app, ('juego', 'mover', 'N', None)); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    assert app.controlador.respuesta.presentacion.sala_id == 2
    assert app.controlador.respuesta.resultado.ordenes == ('ir n',)


def test_saltar_animacion_con_espacio_no_ejecuta_esperar(ventana):
    app = ventana; iniciar(app)
    ahora = [0.0]
    app.animacion.modo = 'normal'; app.animacion.reloj = lambda: ahora[0]
    app.accion(('juego', 'mover', 'N', None)); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    foto = app.controlador.respuesta.presentacion
    assert app.animacion.activa
    app.evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, repeat=False))
    assert not app.animacion.activa and app.controlador.respuesta.presentacion is foto
    app.evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, repeat=True))
    assert app.controlador.respuesta.presentacion is foto
    app.evento(pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE))
    app.evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, repeat=False))
    assert app.controlador.esperar(3)
    assert app.controlador.respuesta.presentacion.acciones == foto.acciones+1


def test_foco_cancela_efectos_y_mapa_no_consulta_remoto(ventana):
    app = ventana; iniciar(app)
    app.animacion.modo = 'normal'; app.animacion.reloj = lambda: 0
    app.accion(('juego', 'mover', 'N', None)); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    assert app.animacion.activa
    app.evento(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert not app.animacion.activa
    foto = app.controlador.respuesta.presentacion
    app.accion('mapa'); app.dibujar()
    assert app.controlador.respuesta.presentacion is foto
    assert app.panel_local == 'mapa'


@pytest.mark.parametrize('operacion', ['retroceder', 'cargar'])
def test_carga_o_retroceso_durante_efecto_no_fabrica_curacion(ventana, tmp_path, operacion):
    app = ventana; iniciar(app)
    app.animacion.modo = 'normal'; app.animacion.reloj = lambda: 0
    app.controlador._sesion.partida.ruta_guardado = str(tmp_path/'grafica.bin')
    app.accion(('juego', 'recoger', '1', None)); assert app.controlador.esperar(3)
    app.actualizar()
    app.accion(('juego', 'guardar', None, None)); assert app.controlador.esperar(3)
    app.actualizar()
    app.accion(('juego', 'mover', 'N', None)); assert app.controlador.esperar(3)
    app.actualizar(); assert app.animacion.activa
    app.accion(('juego', operacion, None, None)); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    assert not app.animacion.activa
    assert app.controlador.respuesta.efectos == ()
    assert app.controlador.respuesta.presentacion.sala_id == 1
    assert app.controlador.respuesta.presentacion.vida == 200
