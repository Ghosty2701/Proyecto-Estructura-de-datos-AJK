"""FR-RS-003/006/007/010..015; AC-RS-008/013..020."""
import json
import pytest
import main as aplicacion
from Pruebas.datos_resolubilidad import datos, conectar, ubicaciones
from Pruebas.prueba_partida import paquete_oficial_de_prueba, crear_cargador


def paquete(tmp_path, soluble=True):
    general, salas = datos(2)
    general.update(paginas=1, presupuesto_solicitudes=20)
    conectar(salas, 1, 2, 'K')
    base = tmp_path / 'criptas' / 'sintetica'
    base.mkdir(parents=True)
    for nombre, valor in [('general', general), ('salas_1', {'salas': salas}),
                          ('llaves', ubicaciones(('K', 1 if soluble else 2))),
                          ('version', {'version': 'v1'})]:
        (base / (nombre + '.json')).write_text(json.dumps(valor), encoding='utf-8')
    return tmp_path


@pytest.mark.parametrize('soluble,codigo', [(True, 0), (False, 1)])
def test_ac015_consulta_sin_vista_motor_ni_cargador(tmp_path, monkeypatch, capsys, soluble, codigo):
    carpeta = paquete(tmp_path, soluble)
    def prohibido(*args, **kwargs): raise AssertionError('No debe instanciarse')
    monkeypatch.setattr(aplicacion, 'VistaConsola', prohibido)
    monkeypatch.setattr(aplicacion, 'CargadorPartida', prohibido)
    assert aplicacion.main(['--verificar', 'sintetica', '--offline', str(carpeta)]) == codigo
    assert 'resoluble' in capsys.readouterr().out


def test_ac020_error_no_es_no_resoluble(tmp_path, capsys):
    assert aplicacion.main(['--verificar', 'sintetica', '--offline', str(tmp_path)]) == 2
    assert 'error' in capsys.readouterr().err.lower()


@pytest.mark.parametrize('extra', [['--forzar'], ['--cripta', 'otra'], ['--bench'],
                                 ['--cargar', 'archivo'], ['--replay', 'log'], ['--listar']])
def test_ac015_combinaciones_invalidas_antes_de_red(monkeypatch, extra):
    def prohibido(*args, **kwargs): raise AssertionError('No debe consultar red')
    monkeypatch.setattr(aplicacion, 'ClienteHTTP', prohibido)
    with pytest.raises(SystemExit) as error: aplicacion.main(['--verificar', 'x'] + extra)
    assert error.value.code == 2


def test_ac013_no_inicia_sin_forzar(tmp_path, monkeypatch):
    carpeta = paquete(tmp_path, False)
    def prohibido(*args, **kwargs): raise AssertionError('No debe crear partida')
    monkeypatch.setattr(aplicacion, 'CargadorPartida', prohibido)
    assert aplicacion.main(['--cripta', 'sintetica', '--offline', str(carpeta),
                            '--cache-dir', str(tmp_path / 'cache')]) == 1


def test_ac014_forzar_llega_al_cargador_pero_no_salta_error(tmp_path, monkeypatch):
    carpeta = paquete(tmp_path, False)
    class InicioObservado(Exception): pass
    def iniciar(*args, **kwargs): raise InicioObservado
    monkeypatch.setattr(aplicacion, 'CargadorPartida', iniciar)
    args = ['--cripta', 'sintetica', '--offline', str(carpeta), '--forzar',
            '--cache-dir', str(tmp_path / 'cache')]
    with pytest.raises(InicioObservado): aplicacion.main(args)
    (tmp_path / 'criptas/sintetica/llaves.json').unlink()
    assert aplicacion.main(args) == 1


def test_ac014_016_inicio_real_no_muta_y_reusa_carga(paquete_oficial_de_prueba, tmp_path, monkeypatch):
    from types import SimpleNamespace
    from adaptadores.modo_offline import ModoOffline
    capturadas, llamadas = [], []
    original = ModoOffline.ubicacion_llaves
    def contar(self, identificador):
        llamadas.append(identificador)
        return original(self, identificador)
    monkeypatch.setattr(ModoOffline, 'ubicacion_llaves', contar)
    monkeypatch.setattr(aplicacion, 'Controlador', lambda partida, *args, **kwargs:
                        SimpleNamespace(ejecutar=lambda: capturadas.append(partida)))
    args = ['--cripta', 'prueba', '--forzar', '--offline', str(paquete_oficial_de_prueba),
            '--cache-dir', str(tmp_path / 'cache-real')]
    assert aplicacion.main(args) == 0 and llamadas == ['prueba']
    partida = capturadas[0]
    base = crear_cargador(paquete_oficial_de_prueba, tmp_path / 'base').crear('prueba', 2026)
    assert partida.estado() == base.estado()
    assert partida.motor.azar.getstate() == base.motor.azar.getstate()
    assert partida.motor.conocimiento.proyeccion() == base.motor.conocimiento.proyeccion()
    assert partida.acciones_ejecutadas == 0 and partida.motor.reloj == 0
    ruta = tmp_path / 'guardada.bin'
    partida.gestor_guardado.guardar_sesion(partida, ruta)
    log = tmp_path / 'vacio.log'
    from adaptadores.bitacora_partida import EscritorBitacora
    with EscritorBitacora(log, partida.id_cripta, partida.version_cripta,
                         partida.gestor_guardado.servicio.cache.version, 2026):
        pass
    def prohibido(*args): raise AssertionError('Cargar/replay no consultan llaves')
    monkeypatch.setattr(ModoOffline, 'ubicacion_llaves', prohibido)
    assert aplicacion.main(['--cargar', str(ruta), '--offline', str(paquete_oficial_de_prueba),
                            '--cache-dir', str(tmp_path / 'cache-carga')]) == 0
    monkeypatch.setattr(aplicacion, 'VistaConsola', lambda: pytest.fail('Replay sin vista'))
    assert aplicacion.main(['--replay', str(log), '--offline', str(paquete_oficial_de_prueba),
                            '--cache-dir', str(tmp_path / 'cache-replay')]) == 0


def test_ac008_puertas_ambiguas_igual_en_modelo_y_juego():
    from types import SimpleNamespace
    from Pruebas.datos_resolubilidad import FuenteSintetica
    from adaptadores.servicio_cripta import ServicioCripta
    from controlador.cargar_partida import CargadorPartida
    general, salas = datos(2)
    conectar(salas, 1, 2, 'K')
    conectar(salas, 1, 2, 'K', direccion='N', inversa='S')
    fuente = FuenteSintetica(general, salas, ubicaciones(('K', 1)))
    servicio = ServicioCripta(fuente, SimpleNamespace())
    mapa = servicio.preparar_verificacion('sintetica')
    servicio.cargar('sintetica', usar_preparada=True)
    cargador = CargadorPartida(servicio)
    cargador._construir_esqueleto()
    assert len(mapa.puertas) == 4 and mapa.avisos
    a, b = cargador.salas.buscar(1), cargador.salas.buscar(2)
    assert all(x.puerta is not y.puerta for x in a.salidas for y in b.salidas)
