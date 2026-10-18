import pytest

from adaptadores.bitacora_partida import (EscritorBitacora,ErrorBitacora,leer_bitacora,verificar_compatibilidad)
from adaptadores.bitacora_partida import reproducir_bitacora

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


def test_bitacora_utf8_y_cierre_por_contexto(tmp_path):
    ruta = tmp_path / "acentos.log"
    with EscritorBitacora(ruta, "cripta-ñ", "v1", "cat-1", 42) as escritor:
        escritor.registrar_accion("usar antídoto")
    encabezado, acciones = leer_bitacora(ruta)
    assert encabezado.id_cripta == "cripta-ñ"
    assert acciones == ["usar antídoto"]
    assert escritor.archivo.closed


def test_rechaza_retorno_de_carro_en_una_accion(tmp_path):
    with EscritorBitacora(tmp_path / "sin_inyeccion.log", "c", "v", "cat", 1) as escritor:
        with pytest.raises(ErrorBitacora, match="saltos de linea"):
            escritor.registrar_accion("esperar\ratacar 1")


def test_codificacion_invalida_se_reporta_con_contexto(tmp_path):
    ruta = tmp_path / "invalida.log"
    ruta.write_bytes(b"\xff")
    with pytest.raises(ErrorBitacora, match="UTF-8 valido"):
        leer_bitacora(ruta)


def reproducir(ruta, crear, ejecutar, version="a3f91c"):
    return reproducir_bitacora(
        ruta, id_cripta_actual="cripta-01", version_cripta_actual=version,
        version_catalogo_actual="cat-1", crear_partida=crear, ejecutar_accion=ejecutar,
    )


def test_replay_valida_version_antes_de_crear_la_partida(tmp_path):
    ruta = crear_bitacora(tmp_path, ["esperar"])

    def no_crear(encabezado):
        pytest.fail("no debe crear una partida con versiones incompatibles")

    with pytest.raises(ErrorBitacora, match="reproduccion fiel"):
        reproducir(ruta, no_crear, lambda partida, accion: None, version="otra")


@pytest.mark.parametrize("resultado", [False, ValueError("objetivo ausente")])
def test_replay_reporta_accion_rechazada_con_numero_y_texto(tmp_path, resultado):
    ruta = crear_bitacora(tmp_path, ["atacar 1"])

    def ejecutar(partida, accion):
        if isinstance(resultado, Exception):
            raise resultado
        return resultado

    with pytest.raises(ErrorBitacora, match="accion 1.*atacar 1"):
        reproducir(ruta, lambda encabezado: None, ejecutar)


def test_replay_rechaza_acciones_vacias(tmp_path):
    ruta = crear_bitacora(tmp_path, [""])
    with pytest.raises(ErrorBitacora, match="accion 1 vacia"):
        reproducir(ruta, lambda encabezado: None, lambda partida, accion: None)


def crear_modelo_replay(encabezado):
    from types import SimpleNamespace
    from modelo.inventario import Inventario
    from modelo.motor_eventos import ActorTurnos, MotorEventos
    from modelo.rastro import Puerta, SalaRastro, SalidaRastro

    motor = MotorEventos(semilla=encabezado.semilla)
    jugador = ActorTurnos("jugador", 1000, 100, ataque=5, defensa=1)
    jugador.inventario = Inventario(3)
    jugador.inventario.recoger(SimpleNamespace(clase="pergamino"))
    entrada, destino = SalaRastro(1), SalaRastro(2)
    entrada.contenido_cargado = destino.contenido_cargado = True
    puerta = Puerta(abierta=True)
    entrada.salidas.append(SalidaRastro(destino, puerta=puerta))
    destino.salidas.append(SalidaRastro(entrada, puerta=puerta))
    enemigo = ActorTurnos("e-1", 100, 150, ataque=3, comportamiento="guardian")
    enemigo.sala_actual = entrada
    entrada.enemigos.append(enemigo)
    motor.iniciar_partida(jugador, entrada)
    motor.aplicar_veneno(jugador, 2)
    return motor, jugador, enemigo


def ejecutar_sobre_modelo(partida, accion):
    motor, jugador, enemigo = partida
    ejecutar = lambda evento: motor.ejecutar_evento(evento, jugador)
    if accion == "esperar":
        return motor.esperar_jugador(jugador, ejecutar)
    if accion == "atacar e-1":
        return motor.atacar_jugador(jugador, enemigo, ejecutar)
    if accion == "mover N":
        return motor.mover_jugador(jugador, jugador.sala_actual.salidas[0], ejecutar)
    if accion == "retroceder":
        return motor.usar_pergamino(jugador, lambda objeto: objeto.clase == "pergamino")
    raise ValueError("accion desconocida")


def test_replay_con_motor_real_reproduce_azar_efectos_y_retroceso(tmp_path):
    acciones = ["esperar", "atacar e-1", "retroceder", "mover N", "esperar"]
    ruta = crear_bitacora(tmp_path, acciones)
    encabezado, _ = leer_bitacora(ruta)
    directa = crear_modelo_replay(encabezado)
    for accion in acciones:
        ejecutar_sobre_modelo(directa, accion)
    repetida = reproducir(ruta, crear_modelo_replay, ejecutar_sobre_modelo)
    ma, ja, ea = directa
    mb, jb, eb = repetida
    assert (ma.reloj, ja.vida, ea.vida, ja.sala_actual.sala_id) == (
        mb.reloj, jb.vida, eb.vida, jb.sala_actual.sala_id)
    assert ma.agenda.siguiente_secuencia == mb.agenda.siguiente_secuencia
    assert [(e.tiempo, e.secuencia, e.tipo, e.cancelado) for e in ma.agenda.heap] == [
        (e.tiempo, e.secuencia, e.tipo, e.cancelado) for e in mb.agenda.heap]
    assert ma.azar.getstate() == mb.azar.getstate()
    assert len(ma.historial.acciones) == len(mb.historial.acciones)
    assert ja.inventario.cantidad == jb.inventario.cantidad == 0
    assert jb.proxima_accion.actor is jb
