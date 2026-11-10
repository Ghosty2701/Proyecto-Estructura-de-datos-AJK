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


# Reutiliza solo la fabrica de datos sinteticos; no importa pruebas de otro modulo.
from Pruebas.prueba_partida import paquete_oficial_de_prueba, paquete_terreno, crear_cargador


def test_ac017_replay_terreno_cazador_sin_instanciar_vista(paquete_terreno, tmp_path, monkeypatch):
    # FR-TC-013: acciones identicas, azar y reloj; CLI de replay sin interfaz.
    import main as aplicacion
    from adaptadores.bitacora_partida import EscritorBitacora, reproducir_bitacora
    from controlador.controlador import ejecutar_accion_replay
    directa = crear_cargador(paquete_terreno, tmp_path / "directa").crear("prueba", 2026)
    ruta = tmp_path / "terreno.log"
    with EscritorBitacora(ruta, "prueba", "v1", "cat-prueba", 2026) as log:
        log.registrar_accion('# ir a Pasillo')  # FR-NV-014: comentario no ejecutable.
        for comando in ("w", "s", "esperar"):
            # Se conserva la gramatica existente de comandos de partida.
            assert ejecutar_accion_replay(directa, comando) is not False
            log.registrar_accion(comando)
    cargador = crear_cargador(paquete_terreno, tmp_path / "replay")
    repetida = reproducir_bitacora(
        ruta, id_cripta_actual="prueba", version_cripta_actual="v1",
        version_catalogo_actual="cat-prueba",
        crear_partida=lambda h: cargador.crear(h.id_cripta, h.semilla),
        ejecutar_accion=ejecutar_accion_replay)
    assert directa.estado() == repetida.estado()
    assert directa.motor.azar.getstate() == repetida.motor.azar.getstate()
    def prohibida(*args, **kwargs):
        raise AssertionError("Replay no debe instanciar la vista")
    monkeypatch.setattr(aplicacion, "VistaConsola", prohibida)
    assert aplicacion.main(["--replay", str(ruta), "--offline", str(paquete_terreno),
                           "--cache-dir", str(tmp_path / "cli-cache")]) == 0


def test_ac018_022_viaje_registrado_equivale_a_movimientos_y_replay(tmp_path):
    # FR-NV-014/015/017: cada paso individual, comentario conserva nombre original.
    from prueba_niebla_partida import partida_niebla, explorar_todo
    from adaptadores.bitacora_partida import EscritorBitacora, reproducir_bitacora
    from controlador.controlador import ejecutar_accion_replay
    def nueva():
        p, salas = partida_niebla()
        explorar_todo(p, salas)
        return p
    p, manual = nueva(), nueva()
    ruta = tmp_path / 'viaje.log'
    with EscritorBitacora(ruta, 'sintetica', 'v1', 'c1', 2026) as log:
        p.viajar('Sala 4', registrar=log.registrar_accion, comentar=log.registrar_accion)
    for _ in range(4):
        manual.mover('N')
    q = reproducir_bitacora(ruta, id_cripta_actual='sintetica', version_cripta_actual='v1',
                            version_catalogo_actual='c1', crear_partida=lambda h: nueva(),
                            ejecutar_accion=ejecutar_accion_replay)
    assert p.estado() == manual.estado() == q.estado()
    assert p.mapa() == manual.mapa() == q.mapa()
    assert p.motor.azar.getstate() == q.motor.azar.getstate()
    assert ruta.read_text(encoding='utf-8').splitlines()[-5:] == ['# ir a Sala 4'] + ['ir N'] * 4


# --- T021: --replay LOG --hasta T (US4; FR-LT-008/010/011, AC-LT-015 a 018) ---

import pytest as _pytest


@_pytest.fixture
def partida_grabada(tmp_path):
    """Partida sintética grabada con pergaminos, y sus resúmenes en vivo por instante."""
    from controlador.controlador import Controlador
    from datos_linea_tiempo import CRIPTA, SEMILLA, crear_partida, escribir_paquete, jugar
    from vista.vista_consola import VistaConsola, lineas_historia

    carpeta = escribir_paquete(tmp_path / "datos", objetos_entrada=[
        "pergamino", "pergamino", "pergamino", "daga", "antorcha"])
    partida, _ = crear_partida(carpeta, tmp_path / "cache")
    ruta = tmp_path / "partida.log"
    with EscritorBitacora(ruta, CRIPTA, "v1", "cat-lt", SEMILLA) as escritor:
        controlador = Controlador(partida, VistaConsola(salida=lambda texto: None), escritor.registrar_accion)
        grabacion = jugar(partida, ["recoger 1", "recoger 1", "w", "retroceder", "w", "w",
                                    "atacar", "atacar", "retroceder", "s", "d", "esperar"],
                          controlador=controlador)
    instantes = sorted({0, *grabacion.decisiones, *[t for t, _ in grabacion.tras_evento]})
    instantes = [t for t in instantes if t < partida.motor.reloj]
    esperados = {t: lineas_historia(partida.historia(("t", t))) for t in instantes}
    return carpeta, ruta, partida, esperados


def _main(argumentos, monkeypatch, capsys):
    import main as aplicacion

    def sin_vista(*_, **__):
        raise AssertionError("--replay --hasta no debe instanciar la vista")

    monkeypatch.setattr(aplicacion, "VistaConsola", sin_vista)
    codigo = aplicacion.main(argumentos)
    return codigo, capsys.readouterr().out


def test_ac015_017_hasta_igual_a_historia_tambien_con_pergaminos(partida_grabada, tmp_path, monkeypatch, capsys):
    carpeta, ruta, _, esperados = partida_grabada
    assert len(esperados) >= 8
    for t, lineas in esperados.items():
        codigo, salida = _main(["--replay", str(ruta), "--hasta", str(t), "--offline", str(carpeta),
                                "--cache-dir", str(tmp_path / "cache-replay")], monkeypatch, capsys)
        assert codigo == 0
        assert "\n".join(lineas) in salida, t
        assert "terminó" not in salida and "termina en" not in salida


def test_ac016_hasta_posterior_al_final_muestra_estado_final(partida_grabada, tmp_path, monkeypatch, capsys):
    from vista.vista_consola import lineas_historia

    carpeta, ruta, partida, _ = partida_grabada
    final = partida.motor.reloj
    codigo, salida = _main(["--replay", str(ruta), "--hasta", str(final + 5000), "--offline", str(carpeta),
                            "--cache-dir", str(tmp_path / "cache-replay")], monkeypatch, capsys)
    assert codigo == 0
    assert f"El registro termina en t={final}, antes de {final + 5000}" in salida
    actual = lineas_historia(partida.historia(("t", final)))
    assert "\n".join(actual[2:]) in salida   # mismo estado final; el título dice «estado actual»


@_pytest.mark.parametrize("argumentos", [
    ["--hasta", "10"],
    ["--cripta", "lt", "--hasta", "10"],
    ["--replay", "x.log", "--hasta", "-1"],
    ["--replay", "x.log", "--hasta", "abc"],
    ["--replay", "x.log", "--hasta", "+3"],
])
def test_ac018_hasta_invalido_es_error_de_uso(argumentos, capsys):
    import main as aplicacion

    with _pytest.raises(SystemExit) as salida:
        aplicacion.main(argumentos)
    assert salida.value.code == 2
    assert "--hasta" in capsys.readouterr().err


def test_ac016_partida_terminada_antes_de_t(partida_grabada):
    # FR-LT-010: si la partida terminó antes de T se indica, con su estado final.
    from main import informe_hasta

    _, _, partida, esperados = partida_grabada
    final = partida.motor.reloj
    partida.victoria = True            # simula el final; solo afecta al aviso
    texto = informe_hasta(partida, final + 1)
    assert texto.endswith(f"La partida terminó en t={final}, antes de {final + 1}.")
    assert informe_hasta(partida, 0) == "\n".join(esperados[0])
