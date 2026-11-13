"""FR-CI-001..009: piloto explícito, sin observador productivo todavía."""
import gc
import random
import struct
import weakref
from types import SimpleNamespace

import pytest

from adaptadores.captura_incremental import CapturadorIncremental, ErrorCobertura
from adaptadores.instantanea_inmutable import capturar_estado
from modelo.rastro import SalaRastro


def test_solo_lee_cambiados_y_nuevos_y_conserva_versiones():
    # FR-CI-001/002/007: alias, sin recorrer atributos del resto del grafo.
    salas = [SalaRastro(i) for i in range(100)]
    raiz = [salas, salas]
    with CapturadorIncremental() as captura:
        a = captura.capturar(raiz)
        salas[50].ultimo_rastro = 10
        captura.marcar(salas[50])
        captura.marcar(salas[50])
        b = captura.capturar(raiz)
        assert captura.estadisticas['objetos_codificados'] == 1
        assert captura.estadisticas['marcas_pendientes'] == 1
        assert b.reconstruir()[0][50].ultimo_rastro == 10
        assert a.reconstruir()[0][50].ultimo_rastro is None
        copia = b.reconstruir()
        assert copia[0] is copia[1]
        copia[0][0].sala_id = -100
        assert b.reconstruir()[0][0].sala_id == 0


def test_ciclos_alias_tuplas_dict_azar_y_tipos_bits():
    # FR-CI-002/005/007: un ciclo que pasa por tupla y lista.
    lista = []
    tupla = (lista,)
    lista.append(tupla)
    azar = random.Random(2026)
    datos = {'uno': lista, 'dos': lista, 'n': True, 'cero': 0.0}
    raiz = [datos, azar, azar]
    with CapturadorIncremental() as captura:
        a = captura.capturar(raiz)
        datos['n'], datos['cero'] = 1, -0.0
        azar.random()
        captura.marcar(datos)
        captura.marcar(azar)
        b = captura.capturar(raiz)
        copia = b.reconstruir()
        assert copia[0]['uno'] is copia[0]['dos']
        assert copia[0]['uno'][0][0] is copia[0]['uno']
        assert type(copia[0]['n']) is int
        assert struct.pack('!d', copia[0]['cero']) == struct.pack('!d', -0.0)
        assert copia[1] is copia[2]
        assert copia[1].getstate() == azar.getstate()
        assert type(a.reconstruir()[0]['n']) is bool


def test_omitir_marca_rechaza_publicacion_y_permite_reintentar():
    # FR-CI-006/009: oráculo antes de publicar, también omisiones dentro de listas.
    interior = [1]
    raiz = [interior]
    with CapturadorIncremental() as captura:
        anterior = captura.capturar(raiz)
        interior.append(2)
        with pytest.raises(ErrorCobertura):
            captura.capturar(raiz)
        assert captura.actual is anterior
        captura.marcar(interior)
        assert captura.capturar(raiz).reconstruir() == [[1, 2]]


def test_fallo_no_borra_marcas_ni_publica_ids_parciales():
    # FR-CI-005/006: error a mitad de descubrimiento y reintento.
    raiz = []
    with CapturadorIncremental() as captura:
        a = captura.capturar(raiz)
        raiz.extend([[1], object()])
        captura.marcar(raiz)
        with pytest.raises(TypeError, match='sin esquema'):
            captura.capturar(raiz)
        assert captura.actual is a
        assert captura.pendientes == 1
        raiz.pop()
        b = captura.capturar(raiz)
        assert b.reconstruir() == [[1]]
        assert captura.pendientes == 0
        assert a.reconstruir() == []


def test_retira_ciclos_y_libera_modelos_aunque_se_conserven_puntos():
    # FR-CI-002/005: índice fuerte acotado al grafo, no a todo lo visto.
    sala = SalaRastro(1)
    sala.enemigos.append(sala)
    referencia = weakref.ref(sala)
    raiz = [sala]
    with CapturadorIncremental() as captura:
        antiguo = captura.capturar(raiz)
        id_maximo = captura.siguiente_id
        raiz.clear()
        captura.marcar(raiz)
        captura.capturar(raiz)
        assert captura.registrados == 1
        assert captura.estadisticas['registros_retirados'] > 0
        del sala
        gc.collect()
        assert referencia() is None
        raiz.append(SalaRastro(2))
        captura.marcar(raiz)
        captura.capturar(raiz)
        assert captura.siguiente_id > id_maximo
        assert antiguo.reconstruir()[0].enemigos[0].sala_id == 1


def test_cerrar_libera_registro_y_los_puntos_siguen_funcionando():
    # FR-CI-005/007: ni puntos ni metadatos públicos retienen modelos.
    sala = SalaRastro(8)
    referencia = weakref.ref(sala)
    captura = CapturadorIncremental()
    punto = captura.capturar(sala)
    del sala
    captura.cerrar()
    assert referencia() is None
    assert captura.registrados == captura.pendientes == 0
    assert punto.reconstruir().sala_id == 8
    with pytest.raises(RuntimeError, match='cerrado'):
        captura.capturar([])


def test_raiz_nueva_no_relee_subgrafo_y_cambio_a_raiz_primitiva_retira_todo():
    # FR-CI-001/005: raíces efímeras de la línea no acumulan IDs vivos.
    interior = [1]
    with CapturadorIncremental() as captura:
        for _ in range(30):
            punto = captura.capturar((interior,))
            assert punto.reconstruir() == ([1],)
            assert captura.registrados == 2
            assert captura.estadisticas['objetos_codificados'] <= 2
        assert captura.capturar(42).reconstruir() == 42
        assert captura.registrados == 0


def test_orden_diccionario_borrado_opcional_y_nan():
    # FR-CI-007: registros cambian orden y presencia, incluso NaN con bits propios.
    objeto = SimpleNamespace(nombre='x', cantidad=1)
    datos = {'a': objeto, 'b': float('nan')}
    with CapturadorIncremental() as captura:
        captura.capturar(datos)
        del objeto.cantidad
        datos['a'] = datos.pop('a')
        captura.marcar(objeto)
        captura.marcar(datos)
        copia = captura.capturar(datos).reconstruir()
        assert list(copia) == ['b', 'a']
        assert not hasattr(copia['a'], 'cantidad')
        assert struct.pack('!d', copia['b']) == struct.pack('!d', datos['b'])


def test_carga_mas_de_cinco_cambios_y_restauraciones():
    # FR-CI-004: las marcas no dependen de la ventana de retroceso.
    objetos = [[i] for i in range(30)]
    with CapturadorIncremental() as captura:
        original = captura.capturar(objetos)
        for i in range(25):
            objetos[i][0] += 100
            captura.marcar(objetos[i])
        for i in range(20, 25):
            objetos[i][0] -= 100
            captura.marcar(objetos[i])
        punto = captura.capturar(objetos)
        assert punto.reconstruir() == objetos
        assert original.reconstruir() == [[i] for i in range(30)]
        assert captura.estadisticas['objetos_codificados'] == 25


def test_colisiones_totales_y_crecimiento(monkeypatch):
    # FR-CI-002/005: el hash de identidad también verifica el objeto, no solo id().
    from adaptadores import captura_incremental as modulo
    monkeypatch.setattr(modulo, '_inicio_identidad', lambda n, m: 0)
    monkeypatch.setattr(modulo, '_mezclar', lambda _: 0)
    raiz = [[i] for i in range(120)]
    with CapturadorIncremental() as captura:
        captura.capturar(raiz)
        for item in raiz[::3]:
            item.append(-1)
            captura.marcar(item)
        assert captura.capturar(raiz).reconstruir() == raiz


def test_marca_primitiva_no_retiene_y_rechaza_tipo_sin_esquema():
    # FR-CI-005/006: el registro no crece con valores inmutables o inválidos.
    with CapturadorIncremental() as captura:
        for valor in (None, True, 1, 'x', b'x', 1.5):
            captura.marcar(valor)
        assert captura.registrados == 0
        with pytest.raises(TypeError):
            captura.marcar(object())
        assert captura.registrados == 0


@pytest.mark.parametrize('frontera', ['_retirar', 'comprobar_equivalencia'])
def test_fallo_de_mantenimiento_u_oraculo_conserva_lote(monkeypatch, frontera):
    # FR-CI-006: también errores posteriores a construir los registros.
    from adaptadores import captura_incremental as modulo
    raiz = [1]
    with CapturadorIncremental() as captura:
        anterior = captura.capturar(raiz)
        raiz.append(2)
        captura.marcar(raiz)
        original = getattr(modulo, frontera)
        def fallar(*args):
            raise RuntimeError('fallo inyectado')
        monkeypatch.setattr(modulo, frontera, fallar)
        with pytest.raises(RuntimeError, match='inyectado'):
            captura.capturar(raiz)
        assert captura.actual is anterior and captura.pendientes == 1
        monkeypatch.setattr(modulo, frontera, original)
        assert captura.capturar(raiz).reconstruir() == [1, 2]


def _marcar_todos_para_probar_codificacion(captura):
    # Arnés conservador de prueba, NO observador incremental ni costo productivo.
    for entrada in captura._identidades.casillas:
        if entrada is not None:
            captura.marcar(entrada.objeto)


@pytest.mark.parametrize('k', [5, 10, 25])
def test_modelo_real_cada_orden_undo_v6_y_continuacion(tmp_path, k):
    # FR-CI-007/008/009: validar representación completa. El arnés marca TODO;
    # no demuestra aún cobertura de fronteras ni mejora de rendimiento del juego.
    from datos_linea_tiempo import escribir_paquete, crear_partida, ORDENES
    from controlador.controlador import Controlador, ejecutar_accion_replay
    from vista.vista_consola import VistaConsola
    from adaptadores.estado_binario import codificar_punto, decodificar_punto

    carpeta = escribir_paquete(tmp_path / 'datos')
    partida, cargador = crear_partida(carpeta, tmp_path / 'cache', checkpoint_cada=k)
    identidad = cargador._identidad(partida)
    ctl = Controlador(partida, VistaConsola(salida=lambda _: None))
    puntos = []
    with CapturadorIncremental() as captura:
        for orden in ['# inicial', *ORDENES]:
            ctl.procesar(orden)
            _marcar_todos_para_probar_codificacion(captura)
            raiz = (partida, cargador.salas_ordenadas())
            punto = captura.capturar(raiz)
            puntos.append(punto)
            copia, salas = punto.reconstruir()
            esperado = codificar_punto(partida.motor, partida.jugador, raiz[1], identidad,
                                       {'partida': partida})
            obtenido = codificar_punto(copia.motor, copia.jugador, salas, identidad,
                                       {'partida': copia})
            assert obtenido == esperado  # bytes completos, también undo/azar
            cargado = decodificar_punto(obtenido, identidad)
            recargada = cargado.datos_extra['partida']
            with CapturadorIncremental() as nueva_sesion:
                restaurado = nueva_sesion.capturar((recargada, cargado.salas))
                assert capturar_estado(restaurado.reconstruir()).registros == capturar_estado(
                    (recargada, cargado.salas)).registros
        # Dos copias independientes del último punto continúan por el preparador
        # de consultas real; se comparan todos los registros, no solo el resumen.
        from modelo.linea_tiempo import PuntoControl
        trabajo = PuntoControl(0, 0, partida.motor.reloj, puntos[-1].a_inmutable(), k)
        a = cargador.copia_de_trabajo(trabajo)
        completo = PuntoControl(0, 0, partida.motor.reloj,
                               capturar_estado((partida, cargador.salas_ordenadas())), k)
        b = cargador.copia_de_trabajo(completo)
        try:
            for orden in ['esperar', 's', 'sig', 'esperar']:
                ejecutar_accion_replay(a, orden)
                ejecutar_accion_replay(b, orden)
                assert capturar_estado(a).registros == capturar_estado(b).registros
        finally:
            a.gestor_guardado.liberar_copia()
            b.gestor_guardado.liberar_copia()
        assert puntos[0].reconstruir()[0].acciones_ejecutadas == 0
