"""FR-CI-002/005/006: dos índices sincronizados, tumbas y transacciones."""
import gc
import weakref

import pytest

from adaptadores.captura_incremental import CapturadorIncremental, _Identidades
from modelo.rastro import SalaRastro


def test_bajas_con_colisiones_no_ocultan_supervivientes(monkeypatch):
    from adaptadores import captura_incremental as modulo
    monkeypatch.setattr(modulo, '_inicio_identidad', lambda n, m: 0)
    monkeypatch.setattr(modulo, '_mezclar', lambda n: 0)
    monkeypatch.setattr('modelo.indice_versionado._inicio', lambda n, m: 0)
    monkeypatch.setattr('modelo.indice_versionado._mezclar', lambda n: 0)
    registro = _Identidades()
    objetos = [[] for _ in range(12)]
    entradas = [registro.registrar(o) for o in objetos]
    registro.borrar_ids([entradas[0].referencia[0], entradas[5].referencia[0]])
    assert registro.obtener(objetos[0]) is None
    assert registro.obtener(objetos[5]) is None
    for i in (1, 4, 6, 11):
        assert registro.obtener(objetos[i]) is entradas[i]
        assert registro.por_id.obtener(entradas[i].referencia[0]) is entradas[i]
    nueva = registro.registrar([])
    assert nueva.referencia[0] == 12
    assert registro.cantidad == registro.por_id.cantidad == 11


def test_copia_de_vectores_borrado_y_reduccion_no_alteran_original():
    registro = _Identidades()
    objetos = [[] for _ in range(100)]
    entradas = [registro.registrar(o) for o in objetos]
    copia = registro.copiar()
    copia.borrar_ids([e.referencia[0] for e in entradas[:-2]])
    assert copia.cantidad == copia.por_id.cantidad == 2
    assert len(copia.casillas) <= 16 and len(copia.por_id.casillas) <= 16
    assert registro.cantidad == 100
    assert all(registro.obtener(o) is e for o, e in zip(objetos, entradas))
    assert registro.siguiente == copia.siguiente == 100


def test_churn_usa_capacidad_activa_no_numero_de_ids_y_limpia_tumbas():
    registro = _Identidades()
    grupo = [registro.registrar([]) for _ in range(30)]
    for _ in range(100):
        bajas, grupo = grupo[:15], grupo[15:]
        registro.borrar_ids([e.referencia[0] for e in bajas])
        grupo.extend(registro.registrar([]) for _ in range(15))
        assert registro.cantidad == registro.por_id.cantidad == 30
        assert len(registro.casillas) <= 128
        assert len(registro.por_id.casillas) <= 128
        assert all(registro.por_id.obtener(e.referencia[0]) is e for e in grupo)
    assert registro.siguiente == 1530
    assert registro.recomposiciones > 0 and registro.por_id.recomposiciones > 0


def test_fallo_despues_de_primera_baja_no_cambia_indices_publicados(monkeypatch):
    raiz = [SalaRastro(1), SalaRastro(2)]
    with CapturadorIncremental() as captura:
        anterior = captura.capturar(raiz)
        registro = captura._identidades
        cantidad, siguiente = registro.cantidad, registro.siguiente
        raiz.clear()
        captura.marcar(raiz)
        original = _Identidades.borrar_ids
        def fallar(self, ids):
            original(self, ids[:1])
            raise RuntimeError('baja interrumpida')
        monkeypatch.setattr(_Identidades, 'borrar_ids', fallar)
        with pytest.raises(RuntimeError, match='interrumpida'):
            captura.capturar(raiz)
        assert captura.actual is anterior and captura._identidades is registro
        assert registro.cantidad == registro.por_id.cantidad == cantidad
        assert registro.siguiente == siguiente and captura.pendientes == 1
        monkeypatch.setattr(_Identidades, 'borrar_ids', original)
        captura.capturar(raiz)
        assert captura.registrados == captura._identidades.por_id.cantidad == 1


def test_tumbas_no_retienen_objetos_y_puntos_no_retienen_indice_inverso():
    sala = SalaRastro(7)
    ref = weakref.ref(sala)
    raiz = [sala]
    with CapturadorIncremental() as captura:
        punto = captura.capturar(raiz)
        raiz.clear()
        captura.marcar(raiz)
        captura.capturar(raiz)
        del sala
        gc.collect()
        assert ref() is None
        assert punto.reconstruir()[0].sala_id == 7
        assert captura._identidades.por_id.cantidad == 1


def test_ids_dispersos_y_fallo_de_alta_no_publican_indices_parciales(monkeypatch):
    from adaptadores import captura_incremental as modulo
    raiz = []
    with CapturadorIncremental() as captura:
        captura._identidades.siguiente = 2**80
        anterior = captura.capturar(raiz)
        registro = captura._identidades
        raiz.append([])
        captura.marcar(raiz)
        original = modulo._IndicePorId.insertar
        def fallar(self, entrada):
            original(self, entrada)
            raise RuntimeError('alta interrumpida')
        monkeypatch.setattr(modulo._IndicePorId, 'insertar', fallar)
        with pytest.raises(RuntimeError, match='interrumpida'):
            captura.capturar(raiz)
        assert captura.actual is anterior and captura._identidades is registro
        assert registro.cantidad == registro.por_id.cantidad == 1
        assert registro.siguiente == 2**80 + 1
        monkeypatch.setattr(modulo._IndicePorId, 'insertar', original)
        assert captura.capturar(raiz).reconstruir() == [[]]
        assert len(captura._identidades.por_id.casillas) <= 32


def test_reserva_por_salas_es_privada_y_no_agranda_puntos():
    salas = [SalaRastro(i) for i in range(30)]
    with CapturadorIncremental() as captura:
        punto = captura.capturar((salas,))
        assert len(captura._identidades.casillas) == 2048
        assert len(captura._identidades.por_id.casillas) == 2048
        assert len(punto.version.casillas) < 2048
        assert captura._identidades.minima == 2048
        captura.capturar((salas,))
        assert captura.estadisticas['recomposiciones_identidades'] == 0
        assert captura.estadisticas['recomposiciones_inverso'] == 0
    assert captura.registrados == 0
    assert len(captura._identidades.casillas) == 32
