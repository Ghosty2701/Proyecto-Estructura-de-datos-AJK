import pytest

from adaptadores.bitacora_partida import (EscritorBitacora,ErrorBitacora,leer_bitacora,verificar_compatibilidad)

def crear_bitacora(carpeta, acciones=()):
    ruta = str(carpeta / "partida.log")
    escritor = EscritorBitacora(ruta, "cripta-01", "a3f91c", "cat-1", 42)
    for accion in acciones:
        escritor.registrar_accion(accion)
    escritor.cerrar()
    return ruta


def escribir_texto(carpeta, texto):
    ruta = str(carpeta / "a_mano.log")
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(texto)
    return ruta


def test_lo_escrito_se_lee_igual(tmp_path):
    ruta = crear_bitacora(tmp_path, ["mover N", "atacar e-201", "esperar"])
    encabezado, acciones = leer_bitacora(ruta)

    assert encabezado.id_cripta == "cripta-01"
    assert encabezado.version_cripta == "a3f91c"
    assert encabezado.version_catalogo == "cat-1"
    assert encabezado.semilla == 42
    assert acciones == ["mover N", "atacar e-201", "esperar"]


def test_la_semilla_se_lee_como_entero(tmp_path):
    ruta = crear_bitacora(tmp_path)
    encabezado, _ = leer_bitacora(ruta)
    assert isinstance(encabezado.semilla, int)


def test_bitacora_sin_acciones_da_lista_vacia(tmp_path):
    ruta = crear_bitacora(tmp_path)
    _, acciones = leer_bitacora(ruta)
    assert acciones == []


def test_lo_registrado_ya_esta_en_disco_sin_cerrar(tmp_path):
    ruta = str(tmp_path / "partida.log")
    escritor = EscritorBitacora(ruta, "cripta-01", "a3f91c", "cat-1", 42)
    escritor.registrar_accion("mover N") 

    _, acciones = leer_bitacora(ruta)
    assert acciones == ["mover N"]
    escritor.cerrar()

def test_no_se_sobrescribe_una_bitacora_existente(tmp_path):
    ruta = crear_bitacora(tmp_path, ["mover N"])
    with pytest.raises(ErrorBitacora, match="ya existe"):
        EscritorBitacora(ruta, "otra", "otra", "otra", 1)

    _, acciones = leer_bitacora(ruta)
    assert acciones == ["mover N"]


def test_un_archivo_no_es_una_bitacora(tmp_path):
    ruta = escribir_texto(tmp_path, "no es una bitacora\n")
    with pytest.raises(ErrorBitacora, match="no es una bitacora"):
        leer_bitacora(ruta)


def test_archivo_vacio(tmp_path):
    ruta = escribir_texto(tmp_path, "")
    with pytest.raises(ErrorBitacora, match="no es una bitacora"):
        leer_bitacora(ruta)


def test_ruta_que_no_existe(tmp_path):
    with pytest.raises(ErrorBitacora, match="no existe"):
        leer_bitacora(str(tmp_path / "no_existe.log"))


def test_encabezado_le_falta_algo(tmp_path):
    ruta = escribir_texto(tmp_path, "CRIPTA-LOG 1\ncripta=x\nversion_catalogo=y\n")
    with pytest.raises(ErrorBitacora, match="encabezado mal formado"):
        leer_bitacora(ruta)


def test_encabezado_sin_la_linea_separadora(tmp_path):
    ruta = escribir_texto(
        tmp_path, "CRIPTA-LOG 1\ncripta=x\nversion_cripta=y\nversion_catalogo=z\nsemilla=1\nmover N\n")
    with pytest.raises(ErrorBitacora, match="encabezado mal formado"):
        leer_bitacora(ruta)


def test_semilla_no_es_un_numero(tmp_path):
    ruta = escribir_texto(
        tmp_path, "CRIPTA-LOG 1\ncripta=x\nversion_cripta=y\nversion_catalogo=z\nsemilla=abc\n---\n")
    with pytest.raises(ErrorBitacora, match="no es un numero entero"):
        leer_bitacora(ruta)


def test_valor_con_el_signo_igual(tmp_path):
    ruta = escribir_texto(
        tmp_path, "CRIPTA-LOG 1\ncripta=a=b\nversion_cripta=y\nversion_catalogo=z\nsemilla=1\n---\n")
    encabezado, _ = leer_bitacora(ruta)
    assert encabezado.id_cripta == "a=b"


def encabezado_de_prueba(tmp_path):
    ruta = crear_bitacora(tmp_path)
    encabezado, _ = leer_bitacora(ruta)
    return encabezado


def test_versiones_iguales(tmp_path):
    encabezado = encabezado_de_prueba(tmp_path)
    verificar_compatibilidad(encabezado, "cripta-01", "a3f91c", "cat-1")


def test_otra_cripta_da_error(tmp_path):
    encabezado = encabezado_de_prueba(tmp_path)
    with pytest.raises(ErrorBitacora, match="se esta usando"):
        verificar_compatibilidad(encabezado, "cripta-02", "a3f91c", "cat-1")


def test_otra_version_de_cripta(tmp_path):
    encabezado = encabezado_de_prueba(tmp_path)
    with pytest.raises(ErrorBitacora, match="de la cripta pero"):
        verificar_compatibilidad(encabezado, "cripta-01", "ZZZ", "cat-1")


def test_otra_version_de_catalogo(tmp_path):
    encabezado = encabezado_de_prueba(tmp_path)
    with pytest.raises(ErrorBitacora, match="del catalogo"):
        verificar_compatibilidad(encabezado, "cripta-01", "a3f91c", "cat-2")


def test_los_erroresque_no_hay_reproduccion_fiel(tmp_path):
    encabezado = encabezado_de_prueba(tmp_path)
    casos = [
        ("cripta-02", "a3f91c", "cat-1"),
        ("cripta-01", "ZZZ", "cat-1"),
        ("cripta-01", "a3f91c", "cat-2"),
    ]
    for caso in casos:
        with pytest.raises(ErrorBitacora, match="reproduccion fiel"):
            verificar_compatibilidad(encabezado, *caso)
