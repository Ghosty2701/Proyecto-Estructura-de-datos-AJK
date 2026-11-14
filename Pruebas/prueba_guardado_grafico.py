"""FR-IG-017/018/024; AC-IG-017/018/023: extensión opcional del binario v6."""
from dataclasses import replace
import pytest
from controlador.controlador_grafico import ControladorGrafico
from controlador.proyeccion_grafica import IntencionGrafica
from controlador.sesion import ConfiguracionSesion
from Pruebas.datos_graficos import paquete_grafico
from adaptadores.estado_grafico import exportar_memoria, importar_memoria


def enviar(ctl, op, arg=None):
    foto = ctl.respuesta.presentacion
    assert ctl.enviar(IntencionGrafica(foto.generacion, foto.revision, op, arg))
    assert ctl.esperar(5)
    return ctl.respuesta


@pytest.fixture
def sesion(tmp_path):
    datos = paquete_grafico(tmp_path/'datos')
    config = ConfiguracionSesion(cripta='lt', offline=str(datos), cache_dir=str(tmp_path/'cache'),
                                 archivo_guardado=str(tmp_path/'partida.bin'))
    ctl = ControladorGrafico()
    assert ctl.iniciar(config) and ctl.esperar(5)
    try:
        for op, arg in (('recoger', '1'), ('mover', 'N'), ('mover', 'N'), ('mover', 'S')):
            assert enviar(ctl, op, arg).resultado.aceptada
        yield ctl
    finally:
        ctl.cerrar(esperar=True)


def test_payload_primitivo_redondo_marca_y_deltas(sesion):
    ctl = sesion; p = ctl._sesion.partida
    datos = exportar_memoria(ctl._memoria, p, ctl._sesion.cache.version)
    memoria, aviso = importar_memoria(datos, p, ctl._sesion.cache.version)
    assert aviso is None
    assert tuple(memoria.observaciones) == tuple(ctl._memoria.observaciones)
    assert memoria.deltas == ctl._memoria.deltas


@pytest.mark.parametrize('mutacion', ['bool', 'version', 'marca', 'huella', 'origen', 'duplicado',
                                    'futuro', 'tipo', 'delta', 'sufijo', 'muchos'])
def test_payload_semanticamente_invalido_reinicia_solo_memoria(sesion, mutacion):
    ctl = sesion; p = ctl._sesion.partida
    datos = list(exportar_memoria(ctl._memoria, p, ctl._sesion.cache.version))
    if mutacion == 'bool': datos[0] = True
    if mutacion == 'version': datos[0] = 999
    if mutacion == 'marca': datos[1] = (*datos[1][:3], 11, *datos[1][4:])
    if mutacion == 'huella': datos[1] = (*datos[1][:-1], '0'*64)
    if mutacion == 'origen': datos[2] = (999999, 0)
    if mutacion == 'duplicado': datos[3] = (*datos[3], datos[3][0])
    if mutacion == 'futuro': datos[3] = ((1, p.motor.reloj+1, ()),)
    if mutacion == 'tipo': datos[3] = ((True, 0, ()),)
    if mutacion == 'delta': datos[4] = ((*datos[4][0][:2], 999, *datos[4][0][3:]), *datos[4][1:])
    if mutacion == 'sufijo': datos[4] = (datos[4][0],)
    if mutacion == 'muchos': datos[4] = datos[4]*2
    antes = p.motor.reloj, p.acciones_ejecutadas, repr(p.mapa()), p.motor.azar.getstate()
    memoria, aviso = importar_memoria(tuple(datos), p, ctl._sesion.cache.version)
    assert aviso and memoria.deltas == []
    assert sum(o is not None for o in memoria.observaciones) == 1
    assert antes == (p.motor.reloj, p.acciones_ejecutadas, repr(p.mapa()), p.motor.azar.getstate())


def test_gui_guarda_carga_v6_con_recuerdos_y_undo(sesion):
    from adaptadores.estado_binario import cargar_partida, VERSION_MODELO
    ctl = sesion; p = ctl._sesion.partida
    memoria = tuple(ctl._memoria.observaciones)
    assert enviar(ctl, 'guardar').resultado.aceptada
    crudo = cargar_partida(p.ruta_guardado)
    assert VERSION_MODELO == 6 and 'interfaz_grafica' in crudo.datos_extra
    enviar(ctl, 'esperar')
    foto = enviar(ctl, 'cargar').presentacion
    assert foto.acciones == 4 and foto.sala_id == 2
    assert tuple(ctl._memoria.observaciones) == memoria
    assert len(ctl._memoria.deltas) == 4
    assert enviar(ctl, 'retroceder').resultado.aceptada
    assert ctl._memoria.obtener(3).grupos and ctl.respuesta.presentacion.sala_id == 3


def test_binario_truncado_conserva_sesion_y_memoria(sesion):
    from pathlib import Path
    ctl = sesion; p = ctl._sesion.partida
    Path(p.ruta_guardado).write_bytes(b'no es un binario')
    antes = ctl.respuesta.presentacion, tuple(ctl._memoria.observaciones), ctl._sesion
    respuesta = enviar(ctl, 'cargar')
    assert not respuesta.resultado.aceptada and respuesta.error
    assert respuesta.presentacion == antes[0] and tuple(ctl._memoria.observaciones) == antes[1]
    assert ctl._sesion is antes[2]


def test_lector_real_main_6107b98_continua_y_reguarda_sin_recuerdos(sesion, tmp_path):
    """SC-IG-007; lector congelado real y proceso separado, sin modificar main."""
    import json
    import os
    import subprocess
    import sys
    import zipfile
    from pathlib import Path
    from Pruebas.datos_linea_tiempo import instantanea
    ctl = sesion
    assert enviar(ctl, 'guardar').resultado.aceptada
    config = ctl._sesion.config
    archivo = Path(config.archivo_guardado)
    copia = tmp_path/'lector.zip'
    base = tmp_path/'main-congelado'
    repo = Path(__file__).resolve().parents[1]
    subprocess.run(['git', 'archive', '--format=zip', '6107b985ec317addff0c122c95c762d940664828',
                    '--output', str(copia)], cwd=repo, check=True, capture_output=True)
    with zipfile.ZipFile(copia) as zip:
        zip.extractall(base)
    script = '''
import json, sys
from adaptadores.modo_offline import ModoOffline
from adaptadores.cache_catalogo import CacheCatalogo
from adaptadores.servicio_cripta import ServicioCripta
from controlador.cargar_partida import CargadorPartida
from controlador.controlador import Controlador
from vista.vista_consola import VistaConsola
from Pruebas.datos_linea_tiempo import instantanea
from adaptadores.estado_binario import cargar_partida
fuente = ModoOffline(sys.argv[1])
cache = CacheCatalogo(fuente, carpeta=sys.argv[4], tope=25)
p = CargadorPartida(ServicioCripta(fuente, cache)).reanudar(sys.argv[2])
antes = instantanea(p)
Controlador(p, VistaConsola(salida=lambda *a: None)).procesar('esperar')
p.ruta_guardado = sys.argv[3]
p.guardar()
assert 'interfaz_grafica' not in cargar_partida(sys.argv[3]).datos_extra
print(json.dumps((antes, instantanea(p))))
'''
    salida_antigua = tmp_path/'reguardado.bin'
    resultado = subprocess.run([sys.executable, '-c', script, config.offline, str(archivo),
                               str(salida_antigua), str(tmp_path/'cache-antigua')], cwd=base,
                              env={**os.environ, 'PYTHONPATH': ''}, text=True, capture_output=True, check=True)
    antes, despues = json.loads(resultado.stdout)
    assert antes == json.loads(json.dumps(instantanea(ctl._sesion.partida)))
    assert enviar(ctl, 'esperar').resultado.aceptada
    assert despues == json.loads(json.dumps(instantanea(ctl._sesion.partida)))
    assert ctl.iniciar(replace(config, cripta=None, cargar=str(salida_antigua))) and ctl.esperar(5)
    assert despues == json.loads(json.dumps(instantanea(ctl._sesion.partida)))
    assert sum(o is not None for o in ctl._memoria.observaciones) == 1
    assert any('no incluye recuerdos' in m for m in ctl.respuesta.presentacion.mensajes)


def test_payload_ausente_o_invalido_en_binario_no_invalida_juego(sesion):
    ctl = sesion
    gestor = ctl._sesion.partida.gestor_guardado
    gestor.exportar_interfaz = lambda p: (999,)
    assert enviar(ctl, 'guardar').resultado.aceptada
    assert enviar(ctl, 'cargar').resultado.aceptada
    assert any('inválidos' in m for m in ctl.respuesta.presentacion.mensajes)
    assert ctl.respuesta.presentacion.acciones == 4
