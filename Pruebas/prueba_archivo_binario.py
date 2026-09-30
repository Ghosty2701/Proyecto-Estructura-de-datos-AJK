import struct

import pytest

import adaptadores.guardado_binario as modulo
from adaptadores.guardado_binario import (
    ErrorGuardado, escribir_guardado, leer_globales, leer_sala)


class ArchivoContador:
    # Envuelve un archivo real y cuenta cuantos bytes se piden leer.
    def __init__(self, archivo, contador):
        self.archivo = archivo
        self.contador = contador

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.archivo.close()

    def read(self, n=-1):
        datos = self.archivo.read(n)
        self.contador.append(len(datos))
        return datos

    def seek(self, *args):
        return self.archivo.seek(*args)

    def tell(self):
        return self.archivo.tell()


@pytest.fixture
def ruta(tmp_path):
    return str(tmp_path / "partida.bin")


def test_ida_y_vuelta_con_bloques_de_distinto_tamano(ruta):
    salas = [(1, b"a"), (3, b""), (4, b"x" * 500), (10, b"hola"), (42, b"z" * 7)]
    escribir_guardado(ruta, b"globales", salas)

    assert leer_globales(ruta) == b"globales"
    for id_sala, datos in salas:
        assert leer_sala(ruta, id_sala) == datos


def test_sala_ausente_devuelve_none(ruta):
    escribir_guardado(ruta, b"g", [(5, b"a"), (9, b"b")])
    assert leer_sala(ruta, 1) is None     # antes de la primera
    assert leer_sala(ruta, 7) is None     # entre dos salas
    assert leer_sala(ruta, 100) is None   # despues de la ultima


def test_archivo_sin_salas(ruta):
    escribir_guardado(ruta, b"g", [])
    assert leer_globales(ruta) == b"g"
    assert leer_sala(ruta, 1) is None


def test_leer_una_sala_no_lee_el_archivo_completo(ruta, monkeypatch):
    salas = [(i, bytes(1000)) for i in range(1, 201)]
    escribir_guardado(ruta, b"g", salas)
    tamano = 200 * 1000

    leidos = []
    abrir = open
    monkeypatch.setattr(modulo, "open", lambda r, m: ArchivoContador(abrir(r, m), leidos), raising=False)

    assert leer_sala(ruta, 137) == bytes(1000)
    assert sum(leidos) < tamano // 10


def test_version_de_formato_distinta_se_detecta(ruta):
    escribir_guardado(ruta, b"g", [(1, b"a")])
    with open(ruta, "r+b") as archivo:
        archivo.seek(4)   # justo despues del magic
        archivo.write(struct.pack("<H", modulo.VERSION_FORMATO + 1))

    with pytest.raises(ErrorGuardado, match="version de formato incompatible"):
        leer_sala(ruta, 1)
    with pytest.raises(ErrorGuardado, match="version de formato incompatible"):
        leer_globales(ruta)


def test_archivo_ajeno_se_rechaza(ruta):
    with open(ruta, "wb") as archivo:
        archivo.write(b"esto no es un guardado de cripta")
    with pytest.raises(ErrorGuardado, match="no es un archivo de guardado"):
        leer_sala(ruta, 1)


def test_archivo_truncado_se_reporta(ruta):
    escribir_guardado(ruta, b"g", [(1, b"a" * 100)])
    with open(ruta, "r+b") as archivo:
        archivo.truncate(modulo.TAM_CABECERA + 6)
    with pytest.raises(ErrorGuardado, match="truncado"):
        leer_sala(ruta, 1)


@pytest.mark.parametrize("salas", [[(2, b"a"), (1, b"b")], [(1, b"a"), (1, b"b")]])
def test_salas_desordenadas_o_repetidas_se_rechazan(ruta, salas):
    with pytest.raises(ValueError, match="ordenadas"):
        escribir_guardado(ruta, b"g", salas)