"""FR-RS-001/002/007/015; AC-RS-007/008/017/020."""
import pytest
from Pruebas.datos_resolubilidad import datos, conectar, ubicaciones
from modelo.verificacion import normalizar, ErrorVerificacion


def test_reciprocas_y_ubicaciones_multiples():
    general, salas = datos(2)
    conectar(salas, 1, 2, 'K')
    mapa = normalizar(general, salas, ubicaciones(('K', 1), ('K', 2)))
    assert len(mapa.puertas) == 1
    assert len(mapa.llaves[0].ubicaciones) == 2
    assert mapa.salas[0].salidas[0].puerta == mapa.salas[1].salidas[0].puerta


def test_ambiguas_no_se_fusionan_y_barrera_sin_llave():
    general, salas = datos(2)
    conectar(salas, 1, 2, 'K')
    conectar(salas, 1, 2, 'K', direccion='N', inversa='S')
    mapa = normalizar(general, salas, ubicaciones(('K', 1)))
    assert len(mapa.puertas) == 4 and mapa.avisos
    salas[0]['salidas']['E']['llave'] = None
    assert normalizar(general, salas, ubicaciones()).salas[0].salidas


@pytest.mark.parametrize('alterar', ['duplicado', 'destino', 'ubicacion', 'costo'])
def test_datos_invalidos(alterar):
    general, salas = datos(2)
    conectar(salas, 1, 2, 'K')
    llaves = ubicaciones(('K', 1))
    if alterar == 'duplicado': salas[1]['id'] = 1
    if alterar == 'destino': salas[0]['salidas']['E']['sala'] = 55
    if alterar == 'ubicacion': llaves['llaves'][0]['sala'] = 55
    if alterar == 'costo': salas[0]['salidas']['E']['costo'] = 0
    with pytest.raises(ErrorVerificacion): normalizar(general, salas, llaves)
