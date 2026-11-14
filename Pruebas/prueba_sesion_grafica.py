"""PR-IG-002; AC-IG-006/010/011: valores y selección de una sola sesión."""
import pytest
from threading import Event, get_ident
from types import SimpleNamespace

from Pruebas.datos_graficos import partida_grafica
from controlador.proyeccion_grafica import proyectar, IntencionGrafica, validar_intencion
from controlador.controlador_grafico import ControladorGrafico
from controlador.sesion import ConfiguracionSesion, preparar_sesion, CriptaNoResoluble
from Pruebas.datos_graficos import paquete_grafico


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


def test_inicio_verifica_forzado_y_configuracion_offline(tmp_path):
    datos = paquete_grafico(tmp_path / 'datos', resoluble=False)
    config = ConfiguracionSesion(cripta='lt', offline=str(datos),
                                 cache_dir=str(tmp_path/'cache'), nombre='Ana', semilla=88)
    with pytest.raises(CriptaNoResoluble) as error:
        preparar_sesion(config)
    assert 'no resoluble' in error.value.informe
    from dataclasses import replace
    sesion = preparar_sesion(replace(config, forzar=True))
    try:
        assert sesion.partida.nombre_jugador == 'Ana' and sesion.partida.motor.semilla == 88
        assert sesion.fuente.solicitudes_realizadas == 0
    finally:
        sesion.cerrar()


def test_sesion_guardada_y_error_de_candidata_no_afectan_actual(tmp_path):
    datos = paquete_grafico(tmp_path/'datos')
    config = ConfiguracionSesion(cripta='lt', offline=str(datos), cache_dir=str(tmp_path/'cache'),
                                 archivo_guardado=str(tmp_path/'partida.bin'))
    sesion = preparar_sesion(config)
    try:
        sesion.partida.guardar()
        from dataclasses import replace
        with pytest.raises(Exception):
            preparar_sesion(replace(config, cripta=None, cargar=str(tmp_path/'falta.bin')))
        cargada = preparar_sesion(replace(config, cripta=None, cargar=config.archivo_guardado))
        try:
            assert cargada.partida.motor.reloj == 0
            assert sesion.partida.motor.reloj == 0
        finally:
            cargada.cerrar()
    finally:
        sesion.cerrar()


def test_sesion_respeta_k_bitacora_rutas_y_nombre(tmp_path):
    from adaptadores.bitacora_partida import leer_bitacora
    from controlador.controlador import Controlador
    from controlador.controlador_grafico import ReceptorValores
    datos = paquete_grafico(tmp_path/'datos')
    log = str(tmp_path/'partida.log')
    config = ConfiguracionSesion(cripta='lt', offline=str(datos), cache_dir=str(tmp_path/'cache'),
                                 checkpoint_cada=7, nombre=' Ana ', bitacora=log,
                                 archivo_guardado=str(tmp_path/'elegido.bin'))
    sesion = preparar_sesion(config)
    try:
        p = sesion.partida
        assert p.nombre_jugador == 'Ana' and p.ruta_guardado == config.archivo_guardado
        assert p.bitacora_activa and p.linea_tiempo.k == 7
        ctl = Controlador(p, ReceptorValores(), registrar_accion=sesion.registrar_accion)
        ctl.procesar('esperar')
        assert sesion.cache.tope == 25 and sesion.fuente.solicitudes_realizadas == 0
    finally:
        sesion.cerrar(); sesion.cerrar()
    assert not p.bitacora_activa
    encabezado, ordenes = leer_bitacora(log)
    assert encabezado.semilla == 2026 and ordenes == ['esperar']
