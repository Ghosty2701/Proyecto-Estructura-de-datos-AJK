"""PR-IG-002; AC-IG-006/010/011: valores y selección de una sola sesión."""
import pytest
from threading import Event, get_ident
from types import SimpleNamespace

from Pruebas.datos_graficos import partida_grafica
from controlador.proyeccion_grafica import proyectar, IntencionGrafica, validar_intencion
from controlador.controlador_grafico import ControladorGrafico


def test_otras_generaciones_no_actuan_sobre_partida(tmp_path):
    p, _ = partida_grafica(tmp_path)
    foto = proyectar(p, 4, 1)
    with pytest.raises(ValueError, match='sesión'):
        validar_intencion(foto, IntencionGrafica(3, 1, 'esperar'))
    assert p.acciones_ejecutadas == 0 and p.motor.reloj == 0


def test_presentacion_sin_graficos_y_sin_alias_mutables(tmp_path):
    p, _ = partida_grafica(tmp_path)
    mensajes = ['original']
    foto = proyectar(p, 1, 1, mensajes=mensajes)
    mensajes.append('nuevo')
    p.jugador.sala_actual.objetos_suelo.clear()
    assert foto.mensajes == ('original',)
    assert len(foto.objetos) == 6
    assert foto.generacion == 1 and foto.revision == 1


def test_un_trabajador_sin_cola_y_resultados_inmutables(tmp_path):
    # AC-IG-010: mientras prepara no se acumulan órdenes para después.
    p, _ = partida_grafica(tmp_path)
    abrir = Event(); listo = Event(); hilos = []; cierres = []
    def fabrica(_):
        hilos.append(get_ident()); listo.set(); assert abrir.wait(3)
        return SimpleNamespace(partida=p, registrar_accion=None, cerrar=lambda: cierres.append(1))
    ctl = ControladorGrafico(fabrica)
    try:
        assert ctl.iniciar(None)
        assert listo.wait(3)
        assert not ctl.enviar(IntencionGrafica(0, 0, 'esperar'))
        abrir.set(); assert ctl.esperar(3)
        foto = ctl.respuesta.presentacion
        assert hilos == [hilos[0]] and hilos[0] != get_ident()
        assert foto.acciones == 0
        assert ctl.enviar(IntencionGrafica(foto.generacion, foto.revision, 'esperar'))
        assert ctl.esperar(3)
        assert ctl.respuesta.presentacion.acciones == 1 and foto.acciones == 0
        assert ctl.respuesta.resultado.clase == 'accion'
    finally:
        abrir.set(); ctl.cerrar(esperar=True)
    assert cierres == [1]
    assert not ctl.enviar(IntencionGrafica(1, 0, 'guardar'))


def test_error_de_preparacion_conserva_sesion_actual(tmp_path):
    p, _ = partida_grafica(tmp_path)
    def fabrica(config):
        if config == 'error': raise ValueError('Carga inválida')
        return SimpleNamespace(partida=p, registrar_accion=None, cerrar=lambda: None)
    ctl = ControladorGrafico(fabrica)
    try:
        assert ctl.iniciar('valida'); assert ctl.esperar(3)
        foto = ctl.respuesta.presentacion
        assert ctl.iniciar('error'); assert ctl.esperar(3)
        assert ctl.respuesta.presentacion == foto
        assert 'Carga inválida' in ctl.respuesta.error
        assert not ctl.respuesta.resultado.aceptada
        assert ctl.enviar(IntencionGrafica(foto.generacion, foto.revision, 'esperar'))
        assert ctl.esperar(3)
        assert ctl.respuesta.presentacion.acciones == 1
    finally:
        ctl.cerrar(esperar=True)


def test_receptor_historia_no_contiene_graficos_ni_muta_partida(tmp_path):
    p, _ = partida_grafica(tmp_path)
    ctl = ControladorGrafico(lambda _: SimpleNamespace(partida=p, registrar_accion=None, cerrar=lambda: None))
    try:
        ctl.iniciar(None); assert ctl.esperar(3)
        foto = ctl.respuesta.presentacion
        ctl.enviar(IntencionGrafica(foto.generacion, foto.revision, 'historia', '0'))
        assert ctl.esperar(3)
        nueva = ctl.respuesta.presentacion
        assert nueva.historia.reloj == 0 and nueva.panel == 'historia'
        assert nueva.acciones == 0 and nueva.reloj == 0
    finally:
        ctl.cerrar(esperar=True)
