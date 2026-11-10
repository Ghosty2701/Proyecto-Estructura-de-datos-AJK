"""FR-RS-004/006/007/008/009; AC-RS-006..012/016."""
from Pruebas.datos_resolubilidad import datos, conectar, ubicaciones
from modelo.verificacion import normalizar, verificar
import pytest
import random


def comprobar_certificados(resultado):
    n = len(resultado.mapa.salas)
    for certificado in resultado.certificados:
        assert certificado.ciclo[0] == certificado.ciclo[-1]
        assert any(v >= n for v in certificado.ciclo)
        assert all(v in certificado.nodos for v in certificado.ciclo)
        for origen, destino in zip(certificado.ciclo, certificado.ciclo[1:]):
            assert any(r[0] == origen and r[1] == destino for r in certificado.reglas)
        assert all(a in certificado.nodos and b in certificado.nodos
                   for a, b, _ in certificado.reglas)


def test_ac008_009_autobloqueo_concreto_y_frontera_unica():
    general, salas = datos(2)
    conectar(salas, 1, 2, 'K')
    resultado = verificar(normalizar(general, salas, ubicaciones(('K', 2))))
    assert not resultado.resoluble and len(resultado.frontera) == 1
    assert len(resultado.certificados) == 1
    comprobar_certificados(resultado)


def test_ac010_ciclo_dos_llaves_y_orden_determinista():
    general, salas = datos(3, llave='A')
    conectar(salas, 1, 2, 'B')
    conectar(salas, 1, 3, 'A', direccion='N', inversa='S')
    mapa = normalizar(general, salas, ubicaciones(('A', 2), ('B', 3)))
    r = verificar(mapa)
    assert r.certificados and r == verificar(mapa)
    comprobar_certificados(r)
    assert len([v for v in r.certificados[0].ciclo[:-1] if v >= 3]) == 2


def test_ac011_alternativa_obtenible_rompe_ciclo():
    general, salas = datos(2)
    conectar(salas, 1, 2, 'K')
    conectar(salas, 1, 2, direccion='N', inversa='S')
    r = verificar(normalizar(general, salas, ubicaciones(('K', 2))))
    assert r.resoluble and not r.certificados


def test_ac011_grupo_or_conserva_ambas_alternativas():
    general, salas = datos(2, llave='A')
    conectar(salas, 1, 2, 'A')
    conectar(salas, 1, 2, 'B', direccion='N', inversa='S')
    r = verificar(normalizar(general, salas, ubicaciones(('A', 2), ('B', 2))))
    assert len(r.certificados) == 1
    c = r.certificados[0]
    assert 2 in c.nodos and 3 in c.nodos
    comprobar_certificados(r)


def test_ac012_aislamiento_y_pasillos_no_son_ciclos():
    general, salas = datos(4)
    conectar(salas, 1, 2, 'B')
    conectar(salas, 2, 3, 'A')
    # A está ANTES de su puerta; el bloqueo real es B aislada, no A→A.
    r = verificar(normalizar(general, salas, ubicaciones(('A', 2), ('B', 4))))
    assert not r.certificados
    assert r.estructurales


def test_ac011_regresion_b_por_a_no_significa_b_exclusiva():
    general, salas = datos(3, llave='A')
    conectar(salas, 1, 2, 'B')
    conectar(salas, 1, 2, 'A', direccion='N', inversa='S')
    conectar(salas, 1, 3, 'A', direccion='S', inversa='N')
    mapa = normalizar(general, salas, ubicaciones(('B', 2), ('A', 3)))
    r = verificar(mapa)
    comprobar_certificados(r)
    # El grupo terminal justifica A; B depende de ese bloqueo, no es autociclo exclusivo.
    b = len(salas) + mapa.indice_llaves.obtener('B')
    assert all(b not in c.nodos for c in r.certificados)


def test_varias_ubicaciones_conserva_alternativas_y_aisladas():
    general, salas = datos(3)
    conectar(salas, 1, 2, 'K')
    mapa = normalizar(general, salas, ubicaciones(('K', 3), ('K', 2)))
    r = verificar(mapa)
    assert r.certificados
    comprobar_certificados(r)


def cierre_oraculo(mapa, semillas=()):
    """Referencia de pruebas: recorre de nuevo tras cada cambio, sin usar cerrar."""
    llaves = [i in semillas for i in range(len(mapa.llaves))]
    while True:
        salas = [False] * len(mapa.salas)
        salas[mapa.inicial] = True
        cambio = True
        while cambio:
            cambio = False
            for i, sala in enumerate(mapa.salas):
                if not salas[i]: continue
                for salida in sala.salidas:
                    if not salida.cerrada or (salida.llave >= 0 and llaves[salida.llave]):
                        if not salas[salida.destino]:
                            salas[salida.destino], cambio = True, True
        anteriores = list(llaves)
        for k, llave in enumerate(mapa.llaves):
            if any(salas[u.sala] for u in llave.ubicaciones): llaves[k] = True
        if anteriores == llaves: return salas, llaves


@pytest.mark.parametrize('semilla', range(25))
def test_cierre_y_certificado_con_todas_alternativas_contra_oraculo(semilla):
    """FR-RS-002/003/008/009: grafos dirigidos, barreras y múltiples ubicaciones."""
    azar = random.Random(semilla)
    general, salas = datos(7, llave='K0')
    for sala in salas:
        for direccion in ('N', 'S', 'E', 'O'):
            if azar.randrange(3) == 0: continue
            sala['salidas'][direccion] = {
                'sala': azar.randrange(1, 8), 'cerrada': bool(azar.randrange(2)),
                'llave': azar.choice([None, 'K0', 'K1', 'K2'])}
    lugares = {'llaves': [{'id': 'K' + str(k), 'sala': azar.randrange(1, 8)}
                          for k in range(3) for _ in range(azar.randrange(3))]}
    mapa = normalizar(general, salas, lugares)
    resultado = verificar(mapa)
    esperado_salas, esperado_llaves = cierre_oraculo(mapa)
    assert resultado.cierre.salas == esperado_salas
    assert resultado.cierre.llaves == esperado_llaves
    comprobar_certificados(resultado)
    for certificado in resultado.certificados:
        grupo = [v - len(mapa.salas) for v in certificado.nodos if v >= len(mapa.salas)]
        fuera = [k for k in range(len(mapa.llaves)) if k not in grupo]
        _, disponibles = cierre_oraculo(mapa, fuera)
        assert not any(disponibles[k] for k in grupo)
