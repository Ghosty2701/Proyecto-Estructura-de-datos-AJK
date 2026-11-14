"""FR-EV-017–021: especies y recorridos de inicio/carga con respuesta visible."""
from threading import Event
import pytest
pygame = pytest.importorskip('pygame')
from Pruebas.prueba_eventos_pygame import ventana, iniciar, pulsar


def test_especie_visible_prevalece_sobre_comportamiento(ventana):
    recursos = ventana.escena.recursos
    recursos.preparar((800, 550))
    rata = recursos.actor('rastreador', 'Rata gigante')
    assert rata is recursos.actor('guardian', 'RATA GIGANTE')
    assert rata is recursos.actor('errante', 'Rata gigante')
    assert rata is not recursos.actor('rastreador')
    assert recursos.actor('cazador', 'Espectro acechador') is not recursos.actor('cazador', 'Sabueso óseo')
    assert recursos.actor('guardian', 'Bestia desconocida') is recursos.actor('otro', 'Nombre nuevo')
    assert recursos.actor('guardian', 'Esqueleto') is not rata


@pytest.mark.parametrize('tamano', [(1024, 768), (1280, 800)])
def test_seleccion_de_cripta_persistente_y_carga_separada(ventana, tamano):
    app = ventana
    app.evento(pygame.event.Event(pygame.VIDEORESIZE, w=tamano[0], h=tamano[1]))
    pulsar(app, 'listar'); assert app.controlador.esperar(3)
    app.actualizar(); pulsar(app, ('cripta', 'lt')); app.dibujar()
    fila = next(b for b in app.ui.botones if b.accion == ('cripta', 'lt'))
    assert fila.seleccionado
    assert next(b for b in app.ui.botones if b.accion == 'nueva').habilitado
    assert all(app.ventana.get_rect().contains(b.rect) for b in app.ui.botones)
    pulsar(app, 'pantalla_cargar'); app.dibujar()
    assert app.campo('cargar') in app.ui.campos
    assert not any(b.accion == 'nueva' for b in app.ui.botones)
    assert not next(b for b in app.ui.botones if b.accion == 'cargar').habilitado
    assert app.controlador.respuesta.presentacion is None
    app.evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, repeat=False))
    app.evento(pygame.event.Event(pygame.KEYUP, key=pygame.K_ESCAPE))
    app.dibujar()
    assert next(b for b in app.ui.botones if b.accion == ('cripta', 'lt')).seleccionado


def test_buscar_archivo_cancelar_y_cargar_confirmado(ventana, monkeypatch, tmp_path):
    app = ventana
    guardado = tmp_path/'partida con espacios.bin'
    app.campo('archivo_guardado').valor = str(guardado)
    iniciar(app)
    # Guardar mediante el mismo recorrido del juego, sin escribir un bin artificial.
    app.accion(('juego', 'guardar', None, None)); assert app.controlador.esperar(3)
    app.actualizar()
    assert guardado.exists()
    foto = app.controlador.respuesta.presentacion
    app.accion('menu'); pulsar(app, 'pantalla_cargar')
    monkeypatch.setattr('vista.pygame_ui.aplicacion.elegir_archivo_guardado', lambda actual: str(guardado))
    pulsar(app, 'buscar_guardado'); app.dibujar()
    assert app.campo('cargar').valor == str(guardado)
    assert app.controlador.respuesta.presentacion is foto
    monkeypatch.setattr('vista.pygame_ui.aplicacion.elegir_archivo_guardado', lambda actual: '')
    pulsar(app, 'buscar_guardado')
    assert app.campo('cargar').valor == str(guardado)
    pulsar(app, 'cargar'); assert app.controlador.esperar(3)
    app.actualizar()
    assert not app.menu and app.controlador.respuesta.presentacion.sala_id == foto.sala_id


def test_carga_no_depende_de_semilla_para_partida_nueva(ventana, tmp_path):
    app = ventana
    app.campo('semilla').valor = 'no es un número'
    app.campo('checkpoint_cada').valor = 'tampoco'
    app.campo('cargar').valor = str(tmp_path/'ausente.bin')
    pulsar(app, 'pantalla_cargar'); pulsar(app, 'cargar')
    assert app.controlador.esperar(3); app.actualizar(); app.dibujar()
    assert app.menu and app.error
    assert 'ausente.bin' in app.error
    assert app.campo('cargar') in app.ui.campos
    app.evento(pygame.event.Event(pygame.MOUSEWHEEL, y=-1, x=0))
    assert app.informe_scroll == 42


def test_selector_no_disponible_deja_ruta_editable(ventana, monkeypatch):
    app = ventana
    pulsar(app, 'pantalla_cargar')
    app.campo('cargar').valor = 'mi partida.bin'
    def fallo(actual):
        raise OSError('Selector no disponible; escribe la ruta.')
    monkeypatch.setattr('vista.pygame_ui.aplicacion.elegir_archivo_guardado', fallo)
    pulsar(app, 'buscar_guardado'); app.dibujar()
    assert app.error and app.campo('cargar').valor == 'mi partida.bin'
    assert app.campo('cargar') in app.ui.campos
    assert not app.controlador.ocupado


def test_ordenar_explicito_no_crea_turno(ventana):
    app = ventana; iniciar(app)
    antes = app.controlador.respuesta.presentacion
    pulsar(app, 'inventario_panel'); app.dibujar()
    boton = next(b for b in app.ui.botones if b.accion == ('juego', 'orden', 'peso', None))
    assert 'Ordenar' in boton.texto and 'peso' in boton.texto
    pulsar(app, boton.accion); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    despues = app.controlador.respuesta.presentacion
    assert (despues.acciones, despues.reloj) == (antes.acciones, antes.reloj)
    assert next(b for b in app.ui.botones if b.accion == boton.accion).seleccionado
    assert despues.orden_inventario == 'peso'


def test_espera_animada_con_inicio_lento_sin_comandos_duplicados(ventana, monkeypatch):
    app = ventana
    entrada, liberar = Event(), Event()
    preparar = app.controlador._iniciar
    def lento(config):
        entrada.set()
        assert liberar.wait(4)
        preparar(config)
    monkeypatch.setattr(app.controlador, '_iniciar', lento)
    app.campo('cripta').valor = 'lt'
    try:
        pulsar(app, 'nueva'); assert entrada.wait(2)
        app.dibujar(); a = pygame.image.tobytes(app.ventana, 'RGB')
        assert app.controlador.ocupado
        assert any(b.accion == 'salir' and b.habilitado for b in app.ui.botones)
        assert not app.controlador.iniciar(app.config)
        app.ocupado_desde -= 1700
        app.dibujar(); b = pygame.image.tobytes(app.ventana, 'RGB')
        assert a != b
    finally:
        liberar.set()
    assert app.controlador.esperar(3); app.actualizar()
    assert app.controlador.respuesta.presentacion.acciones == 0


def test_actividad_en_juego_y_cierre_durante_operacion(ventana, monkeypatch):
    app = ventana; iniciar(app)
    entrada, liberar = Event(), Event()
    ejecutar = app.controlador._ejecutar
    def lento(*args, **kwargs):
        entrada.set()
        assert liberar.wait(4)
        ejecutar(*args, **kwargs)
    monkeypatch.setattr(app.controlador, '_ejecutar', lento)
    try:
        app.accion(('juego', 'esperar', None, None)); assert entrada.wait(2)
        app.dibujar()
        assert app.controlador.ocupado
        app.evento(pygame.event.Event(pygame.QUIT))
        assert app.saliendo
    finally:
        liberar.set()
    assert app.controlador.esperar(3)
