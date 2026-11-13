"""FR-CI-003/004/009: seguimiento de órdenes reales, sin marcar todo el grafo."""
import pytest

from adaptadores.captura_incremental import CapturadorIncremental, ErrorCobertura
from adaptadores.frontera_incremental import FronteraIncremental
from datos_linea_tiempo import escribir_paquete, crear_partida, ORDENES
from controlador.controlador import Controlador
from vista.vista_consola import VistaConsola


@pytest.mark.parametrize('cada', [1, 5, 10, 25])
def test_ordenes_reales_y_undo_con_marcas_acumuladas(tmp_path, cada):
    p, c = crear_partida(escribir_paquete(tmp_path / 'datos'), tmp_path / 'cache',
                         checkpoint_cada=25)
    ctl = Controlador(p, VistaConsola(salida=lambda _: None))
    with CapturadorIncremental() as captura:
        inicial = captura.capturar((p, c.salas_ordenadas()))
        frontera = FronteraIncremental(captura, p)
        for i, texto in enumerate(ORDENES, 1):
            frontera.ejecutar(lambda: ctl.procesar(texto))
            if i % cada == 0:
                captura.capturar((p, c.salas_ordenadas()))  # oráculo obligatorio
        ultimo = captura.capturar((p, c.salas_ordenadas()))
        assert ultimo.reconstruir()[0].acciones_ejecutadas == p.acciones_ejecutadas
        assert inicial.reconstruir()[0].acciones_ejecutadas == 0
        assert captura.estadisticas['objetos_codificados'] < captura.registrados


def test_navegacion_sin_accion_error_y_escritura_externa_detectada(tmp_path):
    p, c = crear_partida(escribir_paquete(tmp_path / 'datos'), tmp_path / 'cache')
    ctl = Controlador(p, VistaConsola(salida=lambda _: None))
    with CapturadorIncremental() as captura:
        captura.capturar((p, c.salas_ordenadas()))
        frontera = FronteraIncremental(captura, p)
        for texto in ['recoger 1', 'recoger 1']:
            frontera.ejecutar(lambda: ctl.procesar(texto))
        antes = p.acciones_ejecutadas
        frontera.ejecutar(lambda: ctl.procesar('sig'))
        assert antes == p.acciones_ejecutadas
        captura.capturar((p, c.salas_ordenadas()))
        def fallar():
            p.jugador.vida -= 1
            raise RuntimeError('operación abortada')
        with pytest.raises(RuntimeError, match='abortada'):
            frontera.ejecutar(fallar)
        captura.capturar((p, c.salas_ordenadas()))
        # Una escritura fuera del contrato no se acepta silenciosamente.
        p.jugador.vida -= 1
        with pytest.raises(ErrorCobertura):
            captura.capturar((p, c.salas_ordenadas()))


def test_cinco_undo_seguidos_y_ventana_superada(tmp_path):
    carpeta = escribir_paquete(tmp_path / 'datos', objetos_entrada=['pergamino'] * 5)
    p, c = crear_partida(carpeta, tmp_path / 'cache')
    ctl = Controlador(p, VistaConsola(salida=lambda _: None))
    with CapturadorIncremental() as captura:
        captura.capturar((p, c.salas_ordenadas()))
        frontera = FronteraIncremental(captura, p)
        for texto in ['recoger 1'] * 5 + ['esperar'] * 30:
            frontera.ejecutar(lambda: ctl.procesar(texto))
        captura.capturar((p, c.salas_ordenadas()))
        antes = p.acciones_ejecutadas
        for _ in range(5):
            frontera.ejecutar(lambda: ctl.procesar('retroceder'))
            captura.capturar((p, c.salas_ordenadas()))
        assert p.acciones_ejecutadas == antes - 5


def test_navegar_no_reprocesa_deltas_de_acciones_inalteradas(tmp_path, monkeypatch):
    p, c = crear_partida(escribir_paquete(tmp_path / 'datos'), tmp_path / 'cache')
    ctl = Controlador(p, VistaConsola(salida=lambda _: None))
    with CapturadorIncremental() as captura:
        captura.capturar((p, c.salas_ordenadas()))
        frontera = FronteraIncremental(captura, p)
        for texto in ['recoger 1', 'recoger 1', 'esperar']:
            frontera.ejecutar(lambda: ctl.procesar(texto))
        captura.capturar((p, c.salas_ordenadas()))
        def fallar(cambio):
            raise AssertionError('se reprocesó un delta antiguo')
        monkeypatch.setattr(frontera, '_delta', fallar)
        frontera.ejecutar(lambda: ctl.procesar('sig'))
        captura.capturar((p, c.salas_ordenadas()))


def test_reemplazo_de_delta_sin_cambiar_longitud_se_observa(tmp_path):
    p, c = crear_partida(escribir_paquete(tmp_path / 'datos'), tmp_path / 'cache')
    ctl = Controlador(p, VistaConsola(salida=lambda _: None))
    with CapturadorIncremental() as captura:
        captura.capturar((p, c.salas_ordenadas()))
        frontera = FronteraIncremental(captura, p)
        frontera.ejecutar(lambda: ctl.procesar('esperar'))
        captura.capturar((p, c.salas_ordenadas()))
        sala = c.salas_ordenadas()[-1]
        def reemplazar():
            anterior = sala.ultimo_rastro
            sala.ultimo_rastro = 123
            p.motor.historial.acciones[-1].cambios[0] = ('rastro', sala, anterior)
        frontera.ejecutar(reemplazar)
        punto = captura.capturar((p, c.salas_ordenadas()))
        assert punto.reconstruir()[1][-1].ultimo_rastro == 123


