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
    # Estas regresiones comparan activaciones sin demoras; efectos se prueban aparte.
    app.animacion.modo = 'sin'
    try:
        app.actualizar(); app.dibujar()
        yield app
    finally:
        app.controlador.cerrar(esperar=True)
        pygame.quit()


def pulsar(app, accion):
    app.dibujar()
    boton = next((b for b in app.ui.botones if b.accion == accion), None)
    # Recorrer los paneles reales que sustituyen a los antiguos botones permanentes.
    if boton is None:
        if accion == 'cargar':
            app.accion('pantalla_cargar')
        elif accion == 'menu':
            app.accion('pausa')
        elif accion == 'consultar_historia':
            app.accion('abrir_historia')
        elif isinstance(accion, tuple) and accion[0] == 'juego':
            op = accion[1]
            if op in ('mover', 'abrir'):
                app.accion('cerrar_local'); app.accion(('puerta', accion[2]))
            elif op in ('usar', 'equipar', 'soltar', 'orden'):
                app.accion('inventario_panel')
            elif op in ('guardar', 'cargar', 'retroceder', 'ayuda'):
                app.accion('pausa' if op != 'ayuda' else 'opciones_panel')
            elif op in ('atacar', 'recoger') and accion[3] is not None:
                app.accion('cerrar_local'); app.accion(('objetivo', accion[3]))
        app.dibujar()
        boton = next((b for b in app.ui.botones if b.accion == accion), None)
    assert boton is not None, f'Acción no alcanzable: {accion}'
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
    app.campo('cripta').valor = 'lt'
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
    # Una salida inexistente ya no tiene botón; comprobar el rechazo del mismo comando.
    app.accion(('juego', 'abrir', 'E', None)); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar(); respuesta = app.controlador.respuesta
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
    assert app.controlador.respuesta.presentacion == foto
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
    def lento(**opciones):
        entrar.set(); assert liberar.wait(3)
        return original(**opciones)
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


@pytest.mark.parametrize('interrupcion', ['detener', 'foco', 'orden', 'pergamino', 'cerrar'])
def test_interrupcion_durante_paso_no_encola_mas_turnos(tmp_path, interrupcion):
    # FR-IG-010/012/013/022; AC-IG-013/021.
    from threading import Event
    from types import SimpleNamespace
    from Pruebas.datos_graficos import partida_grafica
    from controlador.controlador import Controlador
    from controlador.controlador_grafico import ControladorGrafico, ReceptorValores
    from controlador.proyeccion_grafica import IntencionGrafica
    p, _ = partida_grafica(tmp_path)
    Controlador(p, ReceptorValores()).procesar('recoger 1')
    for conocida in p.motor.conocimiento.salas:
        p.motor.conocimiento.entrar(conocida.sala, False, p.motor._cambiar)
    p.jugador.sala_actual.salidas[0].destino.trampas.clear()
    entrar, liberar = Event(), Event()
    original = p.mover
    def lento(direccion, **opciones):
        entrar.set(); assert liberar.wait(3)
        return original(direccion, **opciones)
    p.mover = lento
    ctl = ControladorGrafico(lambda _: SimpleNamespace(partida=p, cerrar=lambda: None))
    try:
        ctl.iniciar(None); assert ctl.esperar(3)
        foto = ctl.respuesta.presentacion
        assert ctl.enviar(IntencionGrafica(foto.generacion, foto.revision, 'viajar', '4'))
        assert entrar.wait(3)
        if interrupcion == 'cerrar':
            ctl.cerrar()
        elif interrupcion in ('detener', 'foco'):
            assert ctl.detener_viaje(perder_foco=interrupcion == 'foco')
        else:
            op = 'retroceder' if interrupcion == 'pergamino' else 'esperar'
            assert ctl.enviar(IntencionGrafica(foto.generacion, foto.revision, op))
            assert not ctl.enviar(IntencionGrafica(foto.generacion, foto.revision, 'esperar'))
        liberar.set(); assert ctl.esperar(3)
        if interrupcion == 'cerrar':
            ctl.cerrar(esperar=True)
        nueva = ctl.respuesta.presentacion
        assert not nueva.viaje_activo
        assert nueva.acciones == {'pergamino': 1, 'orden': 3}.get(interrupcion, 2)
        assert not ctl.continuar_viaje()
    finally:
        liberar.set(); ctl.cerrar(esperar=True)


def test_viaje_incremental_espera_eventos_y_conserva_paradas(tmp_path):
    from types import SimpleNamespace
    from Pruebas.datos_graficos import partida_grafica
    from controlador.controlador_grafico import ControladorGrafico
    from controlador.proyeccion_grafica import IntencionGrafica
    p, cargador = partida_grafica(tmp_path)
    for conocida in p.motor.conocimiento.salas:
        cargador.preparar_sala(conocida.sala)
        p.motor.conocimiento.entrar(conocida.sala, False, p.motor._cambiar)
        conocida.sala.trampas.clear()
    ctl = ControladorGrafico(lambda _: SimpleNamespace(partida=p, cerrar=lambda: None))
    try:
        ctl.iniciar(None); assert ctl.esperar(3)
        foto = ctl.respuesta.presentacion
        ctl.enviar(IntencionGrafica(foto.generacion, foto.revision, 'viajar', '4')); assert ctl.esperar(3)
        paso1 = ctl.respuesta.presentacion
        assert paso1.sala_id == 2 and paso1.acciones == 1 and paso1.viaje_activo
        assert ctl.esperar(0.01) and ctl.respuesta.presentacion is paso1
        assert ctl.continuar_viaje(); assert ctl.esperar(3)
        paso2 = ctl.respuesta.presentacion
        assert paso2.sala_id == 3 and paso2.acciones == 2 and not paso2.viaje_activo
        assert 'enemigos' in paso2.mensajes[-1] and not ctl.continuar_viaje()
        assert tuple(o.texto for o in p.linea_tiempo.ordenes) == ('ir n', 'ir n')
    finally:
        ctl.cerrar(esperar=True)


def test_historia_panel_separa_pasado_sin_cambiar_juego_memoria_red_azar(ventana):
    from Pruebas.datos_linea_tiempo import instantanea
    app = ventana; iniciar(app)
    turno(app, 'mover', 'N')
    p = app.controlador._sesion.partida
    antes = instantanea(p), p.motor.azar.getstate(), tuple(p.linea_tiempo.ordenes), tuple(app.controlador._memoria.observaciones)
    for valor in ('0', '#1'):
        app.historia.valor = valor
        pulsar(app, 'consultar_historia'); assert app.controlador.esperar(3)
        app.actualizar(); app.dibujar()
        foto = app.controlador.respuesta.presentacion
        assert foto.panel == 'historia' and foto.historia.sala_id == 1
        assert app.mapa_historia.croquis.casilla(3) is None
        assert all(s.recuerdo is None for s in app.foto_historia.salas)
        pulsar(app, ('juego', 'cerrar_panel', None, None)); assert app.controlador.esperar(3)
        app.actualizar(); app.dibujar()
    app.historia.valor = 'invalido'
    pulsar(app, 'consultar_historia'); assert app.controlador.esperar(3)
    app.actualizar(); app.dibujar()
    assert not app.controlador.respuesta.resultado.aceptada
    assert (instantanea(p), p.motor.azar.getstate(), tuple(p.linea_tiempo.ordenes), tuple(app.controlador._memoria.observaciones)) == antes


def test_ventana_minima_camara_300_salas_y_controles_alcanzables(ventana):
    from dataclasses import replace
    from controlador.proyeccion_grafica import salas_visuales
    from Pruebas.datos_graficos import mapa_sintetico
    app = ventana; iniciar(app)
    app.evento(pygame.event.Event(pygame.VIDEORESIZE, w=800, h=600))
    assert app.ventana.get_size() == (1024, 768)
    foto = replace(app.controlador.respuesta.presentacion, sala_id=101,
                   salas=salas_visuales(mapa_sintetico(conflicto=True), 101))
    app.controlador._respuesta = replace(app.controlador.respuesta, presentacion=foto)
    app.dibujar()
    assert len(app.mapa.croquis.casillas) == 300
    ultimo = foto.salas[-1].sala_id
    app.mapa.centrar(ultimo)
    app.mapa.zoom(100)
    app.dibujar()
    assert app.mapa.escala == 1.8
    assert any(ident == ultimo for ident, _ in app.mapa.casillas)
    app.mapa.zoom(0.0001)
    assert app.mapa.escala == 0.45
    for boton in app.ui.botones:
        assert app.ventana.get_rect().contains(boton.rect), boton.texto
    assert not app.controlador.ocupado and foto.acciones == 0
