"""D-LT-08: FR-LT-013/014, independencia, identidad y ciclos sin grafo retenido."""
import gc
import weakref
import random

import pytest

from adaptadores.instantanea_inmutable import capturar_estado, InstantaneaInmutable
from modelo.rastro import SalaRastro
from modelo.rastro import SalidaRastro
from datos_linea_tiempo import escribir_paquete, crear_partida, jugar, instantanea


def test_captura_con_varios_crecimientos_conserva_ids_alias_y_ciclos(monkeypatch):
    from adaptadores import instantanea_inmutable as modulo
    crecimientos = []

    class TablaContada(modulo.TablaIdentidades):
        def _crecer(self):
            crecimientos.append(self.capacidad)
            super()._crecer()

    monkeypatch.setattr(modulo, 'TablaIdentidades', TablaContada)
    salas = [SalaRastro(i) for i in range(500)]
    salas[0].salidas.append(SalidaRastro(salas[-1]))
    salas[-1].salidas.append(SalidaRastro(salas[0]))
    # Raíz genérica: empieza con 1024 posiciones, sin reserva por salas.
    punto = capturar_estado([salas, salas])
    assert len(crecimientos) >= 2
    copia = punto.reconstruir()
    assert copia[0] is copia[1]
    assert [s.sala_id for s in copia[0]] == list(range(500))
    assert copia[0][0].salidas[0].destino is copia[0][-1]
    assert copia[0][-1].salidas[0].destino is copia[0][0]


def test_valores_primitivos_conservan_tipo_y_subclases_no_se_convierten():
    valores = (None, False, True, 0, -1, 2**100, 1.25, '', 'texto', b'')
    copia = capturar_estado(valores).reconstruir()
    assert copia == valores
    assert tuple(type(v) for v in copia) == tuple(type(v) for v in valores)

    class EnteroConEstado(int):
        pass

    with pytest.raises(TypeError, match='tipo sin esquema'):
        capturar_estado(EnteroConEstado(1))


def test_registros_no_retienen_modelos_y_preservan_ciclos():
    habilitado = gc.isenabled()
    gc.disable()
    try:
        sala = SalaRastro(1)
        ref = weakref.ref(sala)
        lista = [sala]
        lista.append(lista)
        punto = capturar_estado(lista)
        del sala
        lista.clear()
        del lista
        assert ref() is None
        copia = punto.reconstruir()
        assert copia[1] is copia and copia[0].sala_id == 1
    finally:
        if habilitado:
            gc.enable()
        gc.collect()


def test_tuplas_diccionarios_y_alias():
    lista = []
    tupla = (lista,)
    lista.append(tupla)
    p = capturar_estado([lista, lista, {'dato': tupla}])
    copia = p.reconstruir()
    assert copia[0] is copia[1]
    assert copia[0][0][0] is copia[0]
    assert copia[2]['dato'] is copia[0][0]


def test_partida_reconstruida_igual_e_independiente(tmp_path):
    carpeta = escribir_paquete(tmp_path / 'datos')
    p, c = crear_partida(carpeta, tmp_path / 'cache')
    jugar(p)
    punto = capturar_estado((p, c.salas_ordenadas()))
    copia, salas = punto.reconstruir()
    assert instantanea(copia) == instantanea(p)
    assert copia.motor.azar.getstate() == p.motor.azar.getstate()
    copia.jugador.vida = 0
    salas[0].salidas.clear()
    otra, _ = punto.reconstruir()
    assert instantanea(otra) == instantanea(p)


def test_registros_solo_contienen_valores_inmutables_y_azar_independiente():
    azar = random.Random(2026)
    punto = capturar_estado([azar, azar, (1, True, b'dato', None)])
    pendientes = [punto.raiz, punto.registros]
    while pendientes:
        valor = pendientes.pop()
        assert type(valor) in (tuple, type(None), bool, int, float, str, bytes)
        if type(valor) is tuple:
            pendientes.extend(valor)
    copia = punto.reconstruir()
    assert copia[0] is copia[1]
    assert copia[0].random() == azar.random()
    copia[0].random()
    assert punto.reconstruir()[0].getstate() == random.Random(2026).getstate()


def test_rechaza_tipos_fuera_del_esquema():
    with pytest.raises(TypeError, match='tipo sin esquema'):
        capturar_estado([object()])


def test_guardado_v6_identico_al_de_puntos_con_grafo_y_recarga_por_id(tmp_path):
    carpeta = escribir_paquete(tmp_path / 'datos')
    p, c = crear_partida(carpeta, tmp_path / 'cache', checkpoint_cada=3)
    jugar(p)
    datos = c._linea_a_datos(p)
    assert len(p.linea_tiempo.puntos) > 1
    for punto in p.linea_tiempo.puntos:
        assert isinstance(punto.estado, InstantaneaInmutable)
        punto.estado = punto.estado.reconstruir()
    # Mismos bytes por punto que el formato anterior: no solo misma salida visible.
    assert c._linea_a_datos(p) == datos
    linea, _, _ = c._datos_a_linea(datos, c._identidad(p))
    for original, recargado in zip(p.linea_tiempo.puntos, linea.puntos):
        assert isinstance(recargado.estado, InstantaneaInmutable)
        restaurado, _ = recargado.estado.reconstruir()
        assert instantanea(restaurado) == instantanea(original.estado[0])


def test_tokens_compartidos_no_comparten_estado_entre_puntos():
    interior = [1]
    raiz = [interior, interior]
    primero = capturar_estado(raiz)
    interior[0] = 2
    segundo = capturar_estado(raiz)
    assert primero.raiz is segundo.raiz
    assert primero.registros[0][1][0] is segundo.registros[0][1][0]
    assert primero.registros is not segundo.registros
    a, b = primero.reconstruir(), segundo.reconstruir()
    assert a[0] is a[1] and b[0] is b[1]
    assert a == [[1], [1]] and b == [[2], [2]]
    a[0][0] = 99
    assert primero.reconstruir() == [[1], [1]]
    assert segundo.reconstruir() == [[2], [2]]


def test_catalogo_acotado_y_fallback_con_alias_y_ciclo():
    from adaptadores.instantanea_inmutable import _REFERENCIAS_ID
    catalogo = _REFERENCIAS_ID
    raiz = [[] for _ in range(len(catalogo) + 1)]
    raiz.extend((raiz[256], raiz))
    a, b = capturar_estado(raiz), capturar_estado(raiz)
    ultimo = len(catalogo)
    ref_a, ref_b = a.registros[0][1][ultimo], b.registros[0][1][ultimo]
    assert ref_a == ref_b == (ultimo + 1,)
    assert ref_a is not ref_b
    from adaptadores.instantanea_inmutable import _REFERENCIAS_ID as despues
    assert despues is catalogo and len(despues) == 16384
    copia = a.reconstruir()
    assert copia[-1] is copia and copia[-2] is copia[256]
    assert len(copia) == len(raiz)


def test_capturas_concurrentes_conservan_ambito_local_de_ids():
    from concurrent.futures import ThreadPoolExecutor

    def capturar(numero):
        raiz = [numero]
        raiz.append(raiz)
        return capturar_estado(raiz)

    with ThreadPoolExecutor(max_workers=4) as ejecutor:
        puntos = list(ejecutor.map(capturar, range(32)))
    assert all(p.raiz is puntos[0].raiz for p in puntos)
    for numero, punto in enumerate(puntos):
        copia = punto.reconstruir()
        assert copia[0] == numero and copia[1] is copia


def test_registros_iguales_se_reutilizan_y_cambios_se_aislan():
    raiz = [[1], [2]]
    anterior = capturar_estado(raiz)
    raiz[0][0] = 9
    actual = capturar_estado(raiz, anterior)
    assert actual.registros is not anterior.registros
    assert actual.registros[0] is anterior.registros[0]
    assert any(a is b for a, b in zip(actual.registros, anterior.registros))
    assert actual.reconstruir() == [[9], [2]]
    assert anterior.reconstruir() == [[1], [2]]
    copia = actual.reconstruir()
    copia[1].append(99)
    assert actual.reconstruir() == [[9], [2]]
    ref = weakref.ref(anterior)
    del anterior
    assert ref() is None  # los registros compartidos no retienen el punto padre


def test_reuso_con_ids_reasignados_tamanos_distintos_y_ciclos():
    raiz = [[1], [2]]
    anterior = capturar_estado(raiz)
    raiz.insert(0, {'nuevo': [3]})
    raiz.append(raiz)
    actual = capturar_estado(raiz, anterior)
    copia = actual.reconstruir()
    assert copia[:-1] == [{'nuevo': [3]}, [1], [2]] and copia[-1] is copia
    pequeno = capturar_estado([[]], actual)
    assert pequeno.reconstruir() == [[]]
    assert anterior.reconstruir() == [[1], [2]]


@pytest.mark.parametrize('antes,despues', [(True, 1), (1, 1.0), (0.0, -0.0)])
def test_reuso_no_confunde_igualdad_numerica_con_tipo_o_bits(antes, despues):
    import struct
    previo = capturar_estado([antes])
    actual = capturar_estado([despues], previo)
    valor = actual.reconstruir()[0]
    assert type(valor) is type(despues)
    if type(valor) is float:
        assert struct.pack('!d', valor) == struct.pack('!d', despues)
    assert actual.registros[0] is not previo.registros[0]


def test_linea_y_recarga_reutilizan_con_los_mismos_bytes_v6(tmp_path):
    carpeta = escribir_paquete(tmp_path / 'datos')
    p, c = crear_partida(carpeta, tmp_path / 'cache', checkpoint_cada=3)
    jugar(p)
    puntos = p.linea_tiempo.puntos
    assert any(x is y for a, b in zip(puntos, puntos[1:])
               for x, y in zip(a.estado.registros, b.estado.registros))
    datos = c._linea_a_datos(p)
    linea, _, _ = c._datos_a_linea(datos, c._identidad(p))
    assert any(x is y for a, b in zip(linea.puntos, linea.puntos[1:])
               for x, y in zip(a.estado.registros, b.estado.registros))
    for a, b in zip(puntos, linea.puntos):
        assert a.estado.registros == b.estado.registros
    p.linea_tiempo = linea
    assert c._linea_a_datos(p) == datos
