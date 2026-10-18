import struct
from types import SimpleNamespace

import pytest

import adaptadores.guardado_binario as contenedor
import adaptadores.estado_binario as codec
from adaptadores.estado_binario import (
    ErrorGuardado, ObjetoPartida, guardar_partida, cargar_partida,
    leer_identidad_guardada, leer_sala_guardada,
)
from modelo.efectos import Trampa
from modelo.inventario import Inventario
from modelo.motor_eventos import ActorTurnos, MotorEventos
from modelo.rastro import Puerta, SalaRastro, SalidaRastro


def crear_partida(semilla=2026):
    motor = MotorEventos(semilla)
    jugador = ActorTurnos("jugador", 1000, 100, ataque=6, defensa=1)
    jugador.inventario = Inventario(8)
    objetos = [
        ObjetoPartida("llave", "llave", "Llave de bronce"),
        ObjetoPartida("arma", "arma", "Espada", ataque_bonus=3,
                      ficha={"id": "arma", "ataque_bonus": 3, "etiquetas": ["acero"]}),
        ObjetoPartida("armadura", "armadura", "Cota", defensa_bonus=2),
        SimpleNamespace(id="pergamino", clase="pergamino", nombre="Retroceso"),
    ]
    for objeto in objetos:
        jugador.inventario.recoger(objeto)
    jugador.inventario.avanzar()
    jugador.inventario.equipar_actual("arma")
    while jugador.inventario.actual().id != "armadura":
        jugador.inventario.avanzar()
    jugador.inventario.equipar_actual("armadura")

    entrada, destino = SalaRastro(1), SalaRastro(2)
    entrada.nombre, destino.nombre = "Entrada ñ", "Cámara"
    entrada.contenido_cargado = destino.contenido_cargado = True
    entrada.objetos_suelo = [objetos[1]]
    destino.objetos_suelo = []
    puerta = Puerta(False, "llave", cierre_automatico=180)
    norte, sur = SalidaRastro(destino, puerta=puerta), SalidaRastro(entrada, puerta=puerta)
    norte.direccion, sur.direccion = "N", "S"
    entrada.salidas.append(norte)
    destino.salidas.append(sur)
    enemigo = ActorTurnos("e-1", 100, 150, ataque=3, vida_max=150,
                          regeneracion=1, comportamiento="guardian")
    enemigo.sala_actual = entrada
    entrada.enemigos.append(enemigo)
    destino.trampas.append(Trampa("t-1", "veneno", 2))
    motor.iniciar_partida(jugador, entrada)
    motor.encender_antorcha(jugador, 450)
    motor.aplicar_velocidad(enemigo, 200, 250)
    motor.aplicar_veneno(jugador, 1)
    return motor, jugador, [entrada, destino]


def ejecutar_seis_acciones(motor, jugador, salas):
    ejecutar = lambda evento: motor.ejecutar_evento(evento, jugador)
    motor.esperar_jugador(jugador, ejecutar)
    motor.atacar_jugador(jugador, salas[0].enemigos[0], ejecutar)
    motor.abrir_puerta_jugador(jugador, salas[0].salidas[0], ejecutar)
    motor.mover_jugador(jugador, salas[0].salidas[0], ejecutar)
    motor.esperar_jugador(jugador, ejecutar)
    motor.esperar_jugador(jugador, ejecutar)


def guardar(ruta, motor, jugador, salas, **kwargs):
    guardar_partida(ruta, motor, jugador, salas, id_cripta="cripta-prueba",
                    version_cripta="v1", version_catalogo="cat-1", **kwargs)


def firma(motor, jugador, salas):
    inventario = jugador.inventario
    enemigo = salas[0].enemigos[0]
    return (
        motor.reloj, motor.agenda.siguiente_secuencia,
        tuple((e.tiempo, e.secuencia, e.tipo, e.actor_id, e.cancelado) for e in motor.agenda.heap),
        motor.azar.getstate(), jugador.vida, jugador.velocidad, enemigo.vida, enemigo.velocidad,
        jugador.sala_actual.sala_id, tuple(s.ultimo_rastro for s in salas),
        salas[0].salidas[0].abierta, salas[1].trampas[0].armada,
        tuple(o.id for o in inventario.listar()), inventario.actual().id,
        inventario.arma_equipada.id, inventario.armadura_equipada.id,
        len(motor.historial.acciones), jugador.antorcha is not None,
        jugador.veneno.fin if jugador.veneno is not None else None,
    )


@pytest.mark.parametrize("semilla", [2026, 2**130, "semilla-ñ"])
def test_ida_y_vuelta_preserva_modelo_real_y_referencias(tmp_path, semilla):
    motor, jugador, salas = crear_partida(semilla)
    ejecutar_seis_acciones(motor, jugador, salas)
    ruta = tmp_path / "partida.bin"
    guardar(ruta, motor, jugador, list(reversed(salas)), datos_extra={"acciones": 6, "terminada": False})
    cargada = cargar_partida(ruta, id_cripta="cripta-prueba", version_cripta="v1", version_catalogo="cat-1")
    assert firma(cargada.motor, cargada.jugador, cargada.salas) == firma(motor, jugador, salas)
    assert cargada.motor.semilla == semilla
    assert cargada.datos_extra == {"acciones": 6, "terminada": False}
    assert cargada.jugador.proxima_accion in cargada.motor.agenda.heap
    assert cargada.jugador.proxima_accion.actor is cargada.jugador
    assert cargada.salas[0].salidas[0].puerta is cargada.salas[1].salidas[0].puerta
    assert cargada.jugador.inventario.arma_equipada is cargada.salas[0].objetos_suelo[0]
    assert cargada.jugador.inventario.arma_equipada.ficha == jugador.inventario.arma_equipada.ficha
    assert cargada.salas[0].salidas[0].destino is cargada.salas[1]


def test_cinco_retrocesos_despues_de_cargar_y_continuacion_determinista(tmp_path):
    motor, jugador, salas = crear_partida()
    ejecutar_seis_acciones(motor, jugador, salas)
    ruta = tmp_path / "retroceso.bin"
    guardar(ruta, motor, jugador, salas)
    cargada = cargar_partida(ruta)
    for _ in range(5):
        assert cargada.motor.deshacer_ultima_accion() is True
        assert motor.deshacer_ultima_accion() is True
        assert firma(cargada.motor, cargada.jugador, cargada.salas) == firma(motor, jugador, salas)
    assert cargada.motor.deshacer_ultima_accion() is False
    assert motor.deshacer_ultima_accion() is False
    for modelo, actor in ((motor, jugador), (cargada.motor, cargada.jugador)):
        modelo.esperar_jugador(actor, lambda evento: modelo.ejecutar_evento(evento, actor))
    assert firma(cargada.motor, cargada.jugador, cargada.salas) == firma(motor, jugador, salas)


def test_pergamino_real_consumido_no_reaparece_al_retroceder_tras_cargar(tmp_path):
    motor, jugador, salas = crear_partida()
    ejecutar_seis_acciones(motor, jugador, salas)
    ruta = tmp_path / "pergamino.bin"
    guardar(ruta, motor, jugador, salas)
    cargada = cargar_partida(ruta)
    assert cargada.motor.usar_pergamino(cargada.jugador, lambda o: o.clase == "pergamino")
    assert all(o.clase != "pergamino" for o in cargada.jugador.inventario.listar())
    assert cargada.motor.deshacer_ultima_accion()
    assert all(o.clase != "pergamino" for o in cargada.jugador.inventario.listar())


def test_lectura_selectiva_de_sala_no_lee_globales_ni_todo_el_archivo(tmp_path, monkeypatch):
    motor, jugador, salas = crear_partida()
    for numero in range(3, 83):
        sala = SalaRastro(numero)
        sala.nombre = "Nombre " + "x" * 2000
        salas.append(sala)
    ruta = tmp_path / "salas.bin"
    guardar(ruta, motor, jugador, salas)
    leidos = []
    abrir = open

    class ArchivoContado:
        def __init__(self, archivo):
            self.archivo = archivo

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.archivo.close()

        def read(self, cantidad=-1):
            datos = self.archivo.read(cantidad)
            leidos.append(len(datos))
            return datos

        def seek(self, *args):
            return self.archivo.seek(*args)

    monkeypatch.setattr(contenedor, "open", lambda ruta, modo: ArchivoContado(abrir(ruta, modo)), raising=False)
    sala = leer_sala_guardada(ruta, 47)
    assert sala.sala_id == 47
    assert sala.nombre.startswith("Nombre ")
    assert sum(leidos) < ruta.stat().st_size // 10
    assert leer_sala_guardada(ruta, 999) is None


def test_vista_de_sala_refleja_puerta_y_actores_sin_enlaces_incompletos(tmp_path):
    motor, jugador, salas = crear_partida()
    ruta = tmp_path / "vista.bin"
    guardar(ruta, motor, jugador, salas)
    vista = leer_sala_guardada(ruta, 1)
    assert vista.nombre == "Entrada ñ"
    assert vista.salidas == (("N", 2, False, "llave", 180),)
    assert vista.actores[0][0:2] == ("jugador", True)
    assert vista.objetos == (("arma", "arma", "Espada"),)
    assert leer_identidad_guardada(ruta).version_catalogo == "cat-1"


@pytest.mark.parametrize("campo,valor", [("id_cripta", "otra"), ("version_cripta", "v2"),
                                        ("version_catalogo", "cat-2")])
def test_versiones_incompatibles_se_rechazan(tmp_path, campo, valor):
    ruta = tmp_path / "version.bin"
    guardar(ruta, *crear_partida())
    with pytest.raises(ErrorGuardado, match="incompatible"):
        cargar_partida(ruta, **{campo: valor})


def test_version_de_esquema_binario_incompatible(tmp_path):
    ruta = tmp_path / "version_modelo.bin"
    guardar(ruta, *crear_partida())
    globales, salas = contenedor.leer_guardado(ruta)
    datos = bytearray(globales)
    struct.pack_into("<H", datos, 4, codec.VERSION_MODELO + 1)
    contenedor.escribir_guardado(ruta, bytes(datos), salas)
    with pytest.raises(ErrorGuardado, match="version de modelo incompatible"):
        cargar_partida(ruta)


def test_bloque_de_modelo_truncado_se_reporta(tmp_path):
    ruta = tmp_path / "truncado.bin"
    guardar(ruta, *crear_partida())
    globales, salas = contenedor.leer_guardado(ruta)
    contenedor.escribir_guardado(ruta, globales[:-1], salas)
    with pytest.raises(ErrorGuardado, match="truncado|inconsistente"):
        cargar_partida(ruta)


def test_campos_nuevos_no_se_pierden_silenciosamente_ni_pisan_archivo(tmp_path):
    ruta = tmp_path / "previo.bin"
    ruta.write_bytes(b"contenido previo")
    motor, jugador, salas = crear_partida()
    jugador.campo_sin_esquema = 123
    with pytest.raises(ErrorGuardado, match="campo sin esquema.*campo_sin_esquema"):
        guardar(ruta, motor, jugador, salas)
    assert ruta.read_bytes() == b"contenido previo"


def test_fallo_al_publicar_no_destruye_guardado_anterior(tmp_path, monkeypatch):
    ruta = tmp_path / "previo.bin"
    ruta.write_bytes(b"contenido previo")

    def fallar(*args):
        raise OSError("fallo simulado")

    monkeypatch.setattr(codec.os, "replace", fallar)
    with pytest.raises(ErrorGuardado, match="no se pudo guardar"):
        guardar(ruta, *crear_partida())
    assert ruta.read_bytes() == b"contenido previo"
    assert list(tmp_path.iterdir()) == [ruta]


def test_rechaza_salas_duplicadas_o_referenciadas_fuera_del_guardado(tmp_path):
    motor, jugador, salas = crear_partida()
    with pytest.raises(ErrorGuardado, match="duplicada"):
        guardar(tmp_path / "duplicada.bin", motor, jugador, salas + [salas[0]])
    with pytest.raises(ErrorGuardado, match="no fue incluida"):
        guardar(tmp_path / "faltante.bin", motor, jugador, salas[:1])


def test_estado_invalido_del_heap_o_inventario_se_rechaza(tmp_path):
    motor, jugador, salas = crear_partida()
    motor.agenda.siguiente_secuencia = -1
    with pytest.raises(ErrorGuardado, match="secuencia"):
        guardar(tmp_path / "heap.bin", motor, jugador, salas)
    motor, jugador, salas = crear_partida()
    jugador.inventario.cantidad += 1
    with pytest.raises(ErrorGuardado, match="cantidad.*inconsistentes"):
        guardar(tmp_path / "inventario.bin", motor, jugador, salas)


def test_muerte_y_eventos_cancelados_siguen_siendo_reversibles_al_cargar(tmp_path):
    motor, jugador, salas = crear_partida()
    jugador.ataque = 1000
    enemigo = salas[0].enemigos[0]
    motor.atacar_jugador(jugador, enemigo, lambda evento: motor.ejecutar_evento(evento, jugador))
    assert enemigo.vida == 0
    ruta = tmp_path / "muerte.bin"
    guardar(ruta, motor, jugador, salas)
    cargada = cargar_partida(ruta)
    assert cargada.salas[0].enemigos[0].vida == 0
    assert cargada.motor.deshacer_ultima_accion()
    assert motor.deshacer_ultima_accion()
    restaurado = cargada.salas[0].enemigos[0]
    assert restaurado.vida == enemigo.vida == 100
    assert restaurado.proxima_accion.actor is restaurado
    assert restaurado.regeneracion.evento.actor is restaurado
    assert firma(cargada.motor, cargada.jugador, cargada.salas) == firma(motor, jugador, salas)


def test_sala_distinta_con_id_duplicado_no_se_acepta_como_destino(tmp_path):
    motor, jugador, salas = crear_partida()
    salas[0].salidas[0].destino = SalaRastro(2)
    with pytest.raises(ErrorGuardado, match="fuera de las"):
        guardar(tmp_path / "alias.bin", motor, jugador, salas)


def test_referencia_a_entidad_inexistente_se_rechaza(tmp_path):
    ruta = tmp_path / "referencia.bin"
    guardar(ruta, *crear_partida())
    globales, salas = contenedor.leer_guardado(ruta)
    datos = bytearray(globales)
    # Cabecera MDLO + version, seguida por tres textos con etiqueta y longitud.
    posicion = 6
    for texto in ("cripta-prueba", "v1", "cat-1"):
        posicion += 1 + 4 + len(texto.encode("utf-8"))
    struct.pack_into("<I", datos, posicion, 2**32 - 1)
    contenedor.escribir_guardado(ruta, bytes(datos), salas)
    with pytest.raises(ErrorGuardado, match="objeto inexistente"):
        cargar_partida(ruta)
