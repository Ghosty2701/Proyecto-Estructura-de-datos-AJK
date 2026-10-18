import pytest
from types import SimpleNamespace

from controlador.controlador import AccionInvalida, Controlador
from controlador.partida import Partida
from modelo.inventario_reversible import InventarioReversible
from modelo.motor_eventos import ActorTurnos, MotorEventos
from modelo.rastro import SalaRastro, SalidaRastro
from vista.vista_consola import VistaConsola


def preparar_partida(vida=30, enemigo=False):
    entrada, pasillo = SalaRastro(1), SalaRastro(2)
    for sala, nombre in ((entrada, "Entrada"), (pasillo, "Pasillo")):
        sala.nombre = nombre
        sala.contenido_cargado = True
        sala.objetos_suelo = []
    salida = SalidaRastro(pasillo)
    salida.direccion = "N"
    entrada.salidas.append(salida)
    regreso = SalidaRastro(entrada)
    regreso.direccion = "S"
    pasillo.salidas.append(regreso)
    enemigos = []
    if enemigo:
        guardian = ActorTurnos("g-1", 12, 150, ataque=3, comportamiento="guardian")
        guardian.nombre = "Guardian"
        guardian.sala_actual = pasillo
        pasillo.enemigos.append(guardian)
        enemigos.append(guardian)
    jugador = ActorTurnos("jugador", vida, 100, ataque=5)
    jugador.inventario = InventarioReversible(4)
    motor = MotorEventos(semilla=2026)
    motor.iniciar_partida(jugador, entrada)
    return Partida(motor, jugador, enemigos, lambda sala: None)


def test_partida_inicial_y_espera_usan_reloj_real_del_motor():
    partida = preparar_partida()
    inicial = partida.estado()
    assert inicial.sala_id == 1 and inicial.reloj == 0 and not inicial.terminada
    assert inicial.salidas == [("N", 2, False)]
    partida.esperar()
    assert partida.estado().reloj == 100
    assert len(partida.motor.historial.acciones) == 1


def test_victoria_inmediata_exige_abrir_puerta_y_detiene_las_acciones():
    partida = preparar_partida(enemigo=True)
    partida.sala_salida = 2
    partida.llave_salida = "llave-1"
    salida = partida.jugador.sala_actual.salidas[0]
    # Llegar a una salida que nunca se abrio con llave no es victoria.
    partida.mover("N")
    assert not partida.estado().terminada
    partida.mover("S")
    salida.abierta = False
    salida.puerta.llave = "llave-1"
    partida.inventario.recoger(SimpleNamespace(nombre="Llave", clase="llave", id="llave-1"))
    partida.abrir("N")
    reloj = partida.motor.reloj
    vida = partida.jugador.vida
    partida.mover("N")
    assert partida.estado().resultado == "victoria"
    assert partida.motor.reloj == reloj and partida.jugador.vida == vida
    assert partida.resultado_final()["acciones_jugador"] == 4
    with pytest.raises(AccionInvalida, match="escapaste"):
        partida.esperar()
    partida.motor.deshacer_ultima_accion()
    assert not partida.victoria and partida.acciones_ejecutadas == 3


def test_resultado_derrota_cuenta_acciones_validas_y_enemigos_derrotados():
    partida = preparar_partida(vida=1, enemigo=True)
    assert partida.resultado_final() is None
    with pytest.raises(AccionInvalida):
        partida.atacar(1)
    partida.mover("N")
    resumen = partida.resultado_final()
    assert resumen["resultado"] == "derrota"
    assert resumen["acciones_jugador"] == 1
    assert resumen["enemigos_derrotados"] == 0 and resumen["tiempo_final"] == 66


def test_tabla_json_conserva_resultados_y_rechaza_archivo_invalido(tmp_path):
    import json
    from adaptadores.puntajes import ErrorPuntajes, registrar_resultado

    ruta = tmp_path / "puntajes.json"
    partida = preparar_partida(vida=1, enemigo=True)
    partida.mover("N")
    resultado = partida.resultado_final()
    registrar_resultado(ruta, resultado)
    registrar_resultado(ruta, resultado)
    assert json.loads(ruta.read_text(encoding="utf-8")) == [resultado, resultado]
    ruta.write_text("contenido invalido", encoding="utf-8")
    with pytest.raises(ErrorPuntajes):
        registrar_resultado(ruta, resultado)
    assert ruta.read_text(encoding="utf-8") == "contenido invalido"


def test_main_gana_muestra_resumen_y_guarda_identidad_en_json(tmp_path, monkeypatch):
    import json
    import main as aplicacion

    partida = preparar_partida(enemigo=True)
    partida.sala_salida = 2
    partida.llave_salida = "llave-1"
    partida.id_cripta = "prueba"
    partida.version_cripta = "v1"
    salida = partida.jugador.sala_actual.salidas[0]
    salida.abierta = False
    salida.puerta.llave = "llave-1"
    partida.inventario.recoger(SimpleNamespace(nombre="Llave", clase="llave", id="llave-1"))
    monkeypatch.setattr(aplicacion, "CargadorPartida", lambda servicio: SimpleNamespace(
        crear=lambda cripta, semilla: partida,
    ))
    comandos = iter(["abrir n", "w"])
    lineas = []
    monkeypatch.setattr(aplicacion, "VistaConsola", lambda: VistaConsola(
        entrada=lambda _: next(comandos), salida=lineas.append,
    ))
    ruta = tmp_path / "puntajes.json"
    assert aplicacion.main(["--cripta", "prueba", "--nombre", "Kendall",
                            "--puntajes", str(ruta), "--cache-dir", str(tmp_path / "cache")]) == 0
    registro = json.loads(ruta.read_text(encoding="utf-8"))[0]
    assert registro == {
        "nombre_jugador": "Kendall", "id_cripta": "prueba", "version_cripta": "v1",
        "resultado": "victoria", "acciones_jugador": 2,
        "enemigos_derrotados": 0, "tiempo_final": 50,
    }
    assert any("Victoria" in linea for linea in lineas)
    assert any("Acciones: 2" in linea for linea in lineas)


def test_recoger_y_consultar_inventario_sin_consumir_tiempo_extra():
    partida = preparar_partida()
    objeto = SimpleNamespace(nombre="Llave", clase="llave")
    partida.jugador.sala_actual.objetos_suelo.append(objeto)
    lineas = []
    vista = VistaConsola(salida=lineas.append)
    controlador = Controlador(partida, vista)
    controlador.procesar("recoger 1")
    assert partida.motor.reloj == 25
    assert partida.jugador.sala_actual.objetos_suelo == []
    assert partida.inventario.actual() is objeto
    controlador.procesar("inv")
    assert any("Llave" in linea for linea in lineas)
    assert partida.motor.reloj == 25
    assert partida.motor.deshacer_ultima_accion()
    assert partida.motor.reloj == 0
    assert partida.inventario.esta_vacio()
    assert partida.jugador.sala_actual.objetos_suelo[0] is objeto


def test_recoger_rechaza_indice_invalido_e_inventario_lleno_sin_tiempo():
    partida = preparar_partida()
    objeto = SimpleNamespace(nombre="Antorcha", clase="antorcha")
    partida.jugador.sala_actual.objetos_suelo.append(objeto)
    with pytest.raises(AccionInvalida):
        partida.recoger(2)
    for _ in range(partida.inventario.capacidad):
        partida.inventario.recoger(SimpleNamespace(nombre="Objeto"))
    with pytest.raises(AccionInvalida, match="lleno"):
        partida.recoger(1)
    assert partida.motor.reloj == 0
    assert partida.motor.historial.acciones == []
    assert partida.jugador.sala_actual.objetos_suelo[0] is objeto


def test_recogidas_deshacen_objetos_normales_sin_restaurar_pergaminos():
    partida = preparar_partida()
    primero = SimpleNamespace(nombre="Llave", clase="llave")
    pergamino = SimpleNamespace(nombre="Pergamino", clase="pergamino_retroceso")
    ultimo = SimpleNamespace(nombre="Pocion", clase="pocion")
    suelo = partida.jugador.sala_actual.objetos_suelo
    suelo.extend([primero, pergamino, ultimo])
    partida.recoger(1)
    partida.recoger(1)
    partida.motor.deshacer_ultima_accion()
    partida.motor.deshacer_ultima_accion()
    assert len(suelo) == 2 and suelo[0] is primero and suelo[1] is ultimo
    assert partida.inventario.listar() == [pergamino]


def test_usar_pocion_cura_sin_superar_maximo_y_retroceso_la_restaura():
    partida = preparar_partida()
    pocion = SimpleNamespace(nombre="Pocion", clase="pocion", ficha={"cura": 8})
    partida.inventario.recoger(pocion)
    partida.jugador.vida = 27
    mensajes = partida.usar()
    assert partida.jugador.vida == 30 and partida.motor.reloj == 50
    assert partida.inventario.esta_vacio()
    assert any("recuperas 3 de vida" in mensaje for mensaje in mensajes)
    partida.motor.deshacer_ultima_accion()
    assert partida.jugador.vida == 27 and partida.motor.reloj == 0
    assert partida.inventario.actual() is pocion


def test_usar_antidoto_cancela_veneno_y_retroceso_recupera_su_evento():
    partida = preparar_partida()
    antidoto = SimpleNamespace(nombre="Antidoto", clase="antidoto")
    partida.inventario.recoger(antidoto)
    veneno = partida.motor.aplicar_veneno(partida.jugador, 2)
    evento = veneno.evento
    partida.usar()
    assert partida.jugador.veneno is None and partida.inventario.esta_vacio()
    assert evento.cancelado
    partida.motor.deshacer_ultima_accion()
    assert partida.jugador.veneno is veneno and not evento.cancelado
    assert partida.inventario.actual() is antidoto


def test_usar_antorcha_consume_objeto_y_programa_apagado():
    partida = preparar_partida()
    antorcha = SimpleNamespace(nombre="Antorcha", clase="antorcha", ficha={"duracion": 80})
    partida.inventario.recoger(antorcha)
    partida.usar()
    assert partida.jugador.antorcha.fin == 80
    assert partida.inventario.esta_vacio() and partida.motor.reloj == 50
    mensajes = partida.esperar()
    assert partida.jugador.antorcha is None
    assert any("[t=80] Se apaga" in mensaje for mensaje in mensajes)
    partida.motor.deshacer_ultima_accion()
    partida.motor.deshacer_ultima_accion()
    assert partida.jugador.antorcha is None
    assert partida.inventario.actual() is antorcha


def test_pocion_velocidad_redondea_y_renueva_sobre_base_sin_acumular():
    partida = preparar_partida()
    partida.jugador.velocidad = 75
    primera = SimpleNamespace(nombre="Rapidez", clase="pocion",
                              ficha={"modificador_velocidad": 50, "duracion": 200})
    segunda = SimpleNamespace(nombre="Rapidez", clase="pocion", ficha=primera.ficha)
    partida.inventario.recoger(primera)
    partida.inventario.recoger(segunda)
    partida.usar()
    previo = partida.jugador.efecto_velocidad
    evento_previo = previo.evento
    assert partida.jugador.velocidad == 112 and previo.anterior == 75
    assert partida.motor.reloj == 44
    partida.usar()
    assert partida.jugador.velocidad == 112
    assert partida.jugador.efecto_velocidad.fin == 244
    assert evento_previo.cancelado
    partida.motor.deshacer_ultima_accion()
    assert partida.jugador.efecto_velocidad is previo
    assert previo.evento is evento_previo and not evento_previo.cancelado
    assert partida.inventario.actual() is segunda
    partida.motor.deshacer_ultima_accion()
    assert partida.jugador.velocidad == 75 and partida.jugador.efecto_velocidad is None
    assert partida.inventario.listar() == [primera, segunda]


def test_pocion_velocidad_expira_y_reajusta_turno_pendiente():
    partida = preparar_partida()
    partida.jugador.velocidad = 75
    partida.inventario.recoger(SimpleNamespace(
        nombre="Rapidez breve", clase="pocion",
        ficha={"modificador_velocidad": 50, "duracion": 20},
    ))
    mensajes = partida.usar()
    assert partida.jugador.velocidad == 75 and partida.jugador.efecto_velocidad is None
    assert partida.motor.reloj == 55
    assert partida.jugador.proxima_accion.tiempo == 55
    assert any("[t=20] Termina el cambio de velocidad" in mensaje for mensaje in mensajes)


def test_pocion_velocidad_invalida_no_se_consume():
    partida = preparar_partida()
    objeto = SimpleNamespace(nombre="Pocion", clase="pocion",
                             ficha={"modificador_velocidad": -100, "duracion": 200})
    partida.inventario.recoger(objeto)
    with pytest.raises(AccionInvalida, match="menor que 1"):
        partida.usar()
    assert partida.inventario.actual() is objeto
    assert partida.motor.reloj == 0 and partida.motor.historial.acciones == []


def test_usar_objeto_invalido_no_consume_objeto_tiempo_ni_historial():
    partida = preparar_partida()
    with pytest.raises(AccionInvalida, match="vacio"):
        partida.usar()
    llave = SimpleNamespace(nombre="Llave", clase="llave")
    partida.inventario.recoger(llave)
    with pytest.raises(AccionInvalida, match="no se puede consumir"):
        partida.usar()
    assert partida.inventario.actual() is llave
    assert partida.motor.reloj == 0 and partida.motor.historial.acciones == []


def test_equipar_sustituye_bonos_y_retroceso_restaura_equipo_y_orden():
    partida = preparar_partida()
    arma = SimpleNamespace(nombre="Daga", clase="arma", ataque_bonus=2)
    otra = SimpleNamespace(nombre="Espada", clase="arma", ataque_bonus=4)
    armadura = SimpleNamespace(nombre="Coraza", clase="armadura", defensa_bonus=3)
    for objeto in (arma, otra, armadura):
        partida.inventario.recoger(objeto)
    partida.equipar()
    assert partida.jugador.ataque == 7 and partida.motor.reloj == 50
    partida.inventario.avanzar()
    partida.equipar()
    assert partida.jugador.ataque == 9 and partida.motor.reloj == 100
    assert partida.inventario.arma_equipada is otra
    assert partida.inventario.listar() == [otra, arma, armadura]
    partida.inventario.avanzar()
    partida.inventario.avanzar()
    partida.equipar()
    assert partida.jugador.defensa == 3 and partida.motor.reloj == 150
    assert partida.inventario.armadura_equipada is armadura
    partida.motor.deshacer_ultima_accion()
    assert partida.jugador.defensa == 0
    assert partida.inventario.armadura_equipada is None
    partida.motor.deshacer_ultima_accion()
    assert partida.jugador.ataque == 7
    assert partida.inventario.arma_equipada is arma
    assert partida.inventario.listar() == [arma, otra, armadura]


def test_equipar_rechaza_vacio_objeto_inadecuado_y_equipo_repetido():
    partida = preparar_partida()
    with pytest.raises(AccionInvalida, match="vacio"):
        partida.equipar()
    partida.inventario.recoger(SimpleNamespace(nombre="Llave", clase="llave"))
    with pytest.raises(AccionInvalida, match="armas y armaduras"):
        partida.equipar()
    assert partida.motor.reloj == 0 and partida.motor.historial.acciones == []
    partida.inventario.recoger(SimpleNamespace(nombre="Daga", clase="arma", ataque_bonus=2))
    partida.inventario.avanzar()
    partida.equipar()
    with pytest.raises(AccionInvalida, match="ya esta equipado"):
        partida.equipar()
    assert partida.motor.reloj == 50 and len(partida.motor.historial.acciones) == 1


def test_retroceder_restaura_movimiento_enemigos_reloj_y_azar_sin_restaurar_pergamino():
    partida = preparar_partida(enemigo=True)
    pergamino = SimpleNamespace(nombre="Pergamino", clase="pergamino_retroceso")
    partida.inventario.recoger(pergamino)
    with pytest.raises(AccionInvalida, match="No hay acciones"):
        partida.retroceder()
    assert partida.inventario.actual() is pergamino
    turno = partida.jugador.proxima_accion
    azar = partida.motor.azar.getstate()
    partida.mover("N")
    partida.retroceder()
    assert partida.jugador.sala_actual.sala_id == 1
    assert partida.jugador.vida == 30 and partida.motor.reloj == 0
    assert partida.jugador.proxima_accion is turno
    assert partida.motor.consultar_siguiente_evento() is turno
    assert partida.motor.azar.getstate() == azar
    assert not partida.enemigos[0].activo
    assert partida.inventario.esta_vacio() and partida.acciones_ejecutadas == 0
    partida.mover("N")
    with pytest.raises(AccionInvalida, match="No tienes un pergamino"):
        partida.retroceder()
    assert partida.motor.reloj == 100


def test_usar_pergamino_consume_el_seleccionado():
    partida = preparar_partida()
    primero = SimpleNamespace(nombre="Primero", clase="pergamino_retroceso")
    segundo = SimpleNamespace(nombre="Segundo", clase="pergamino_retroceso")
    partida.inventario.recoger(primero)
    partida.inventario.recoger(segundo)
    partida.esperar()
    partida.inventario.avanzar()
    partida.usar()
    assert partida.inventario.listar() == [primero]
    assert partida.motor.reloj == 0 and partida.motor.historial.acciones == []


def test_retroceso_se_limita_a_cinco_intervalos():
    partida = preparar_partida()
    partida.inventario.capacidad = 6
    for _ in range(6):
        partida.inventario.recoger(SimpleNamespace(nombre="Pergamino", clase="pergamino_retroceso"))
        partida.esperar()
    for _ in range(5):
        partida.retroceder()
    assert partida.motor.reloj == 100 and partida.acciones_ejecutadas == 1
    assert partida.inventario.cantidad == 1
    with pytest.raises(AccionInvalida, match="No hay acciones"):
        partida.retroceder()
    assert partida.inventario.cantidad == 1


def test_retroceso_inventario_lleno_aprovecha_el_espacio_del_pergamino_consumido():
    partida = preparar_partida()
    partida.inventario.capacidad = 2
    pergamino = SimpleNamespace(nombre="Pergamino", clase="pergamino_retroceso")
    pocion = SimpleNamespace(nombre="Pocion", clase="pocion", ficha={"cura": 8})
    partida.inventario.recoger(pergamino)
    partida.inventario.recoger(pocion)
    partida.inventario.avanzar()
    partida.usar()
    partida.jugador.sala_actual.objetos_suelo.append(SimpleNamespace(
        nombre="Otro pergamino", clase="pergamino_retroceso",
    ))
    partida.recoger(1)
    assert partida.inventario.esta_lleno()
    partida.retroceder()
    partida.retroceder()
    assert partida.inventario.listar() == [pocion]
    assert partida.motor.reloj == 0 and partida.acciones_ejecutadas == 0


def test_pergamino_de_botin_recogido_y_consumido_no_se_duplica_al_repetir_muerte():
    partida = preparar_partida(enemigo=True)
    enemigo = partida.enemigos[0]
    enemigo.vida = 1
    botin = SimpleNamespace(nombre="Botin", clase="pergamino_retroceso")
    enemigo.suelta = [botin]
    partida.inventario.recoger(SimpleNamespace(nombre="Inicial", clase="pergamino_retroceso"))
    partida.mover("N")
    partida.atacar(1)
    suelo = partida.jugador.sala_actual.objetos_suelo
    assert suelo == [botin]
    partida.recoger(1)
    partida.retroceder()
    assert partida.inventario.actual() is botin and suelo == []
    partida.usar()
    assert enemigo.vida == 1 and partida.inventario.esta_vacio()
    partida.atacar(1)
    assert enemigo.vida == 0 and suelo == []


def test_soltar_objeto_seleccionado_y_deshacer_restauran_orden_y_cursor():
    partida = preparar_partida()
    objetos = [SimpleNamespace(nombre=nombre, clase="llave") for nombre in ("A", "B", "C")]
    for objeto in objetos:
        partida.inventario.recoger(objeto)
    partida.inventario.avanzar()
    suelo = partida.jugador.sala_actual.objetos_suelo
    mensajes = partida.soltar()
    assert len(suelo) == 1 and suelo[0] is objetos[1]
    assert partida.inventario.listar() == [objetos[0], objetos[2]]
    assert partida.motor.reloj == 25 and partida.acciones_ejecutadas == 1
    assert any("Sueltas B" in mensaje for mensaje in mensajes)
    partida.motor.deshacer_ultima_accion()
    assert suelo == [] and partida.inventario.listar() == objetos
    assert partida.inventario.actual() is objetos[1]
    assert partida.motor.reloj == 0 and partida.acciones_ejecutadas == 0


def test_soltar_equipo_retira_bonos_y_deshacer_los_recupera():
    partida = preparar_partida()
    arma = SimpleNamespace(nombre="Daga", clase="arma", ataque_bonus=3)
    partida.inventario.recoger(arma)
    partida.equipar()
    assert partida.jugador.ataque == 8
    partida.soltar()
    assert partida.jugador.ataque == 5 and partida.inventario.arma_equipada is None
    assert partida.jugador.sala_actual.objetos_suelo[0] is arma
    partida.motor.deshacer_ultima_accion()
    assert partida.jugador.ataque == 8 and partida.inventario.arma_equipada is arma
    assert partida.jugador.sala_actual.objetos_suelo == []


def test_soltar_pergamino_no_se_deshace():
    partida = preparar_partida()
    pergamino = SimpleNamespace(nombre="Pergamino", clase="pergamino_retroceso")
    partida.inventario.recoger(pergamino)
    partida.soltar()
    partida.motor.deshacer_ultima_accion()
    assert partida.inventario.esta_vacio()
    assert partida.jugador.sala_actual.objetos_suelo[0] is pergamino
    assert partida.motor.reloj == 0


def test_soltar_inventario_vacio_no_consume_tiempo():
    partida = preparar_partida()
    with pytest.raises(AccionInvalida, match="vacio"):
        partida.soltar()
    assert partida.motor.reloj == 0 and partida.motor.historial.acciones == []


def test_recoger_procesa_turnos_enemigos_dentro_del_intervalo():
    partida = preparar_partida(enemigo=True)
    partida.mover("N")
    partida.jugador.sala_actual.objetos_suelo.extend([
        SimpleNamespace(nombre="Objeto", clase="llave") for _ in range(2)
    ])
    partida.recoger(1)
    vida_anterior = partida.jugador.vida
    partida.recoger(1)
    assert partida.motor.reloj == 150
    assert partida.jugador.vida < vida_anterior


def test_partida_movimiento_carga_destino_antes_de_confirmarse():
    partida = preparar_partida()
    llamados = []

    def cargar(sala):
        llamados.append((sala.sala_id, partida.motor.reloj, partida.jugador.sala_actual.sala_id))

    partida.preparar_sala = cargar
    partida.mover("n")
    assert llamados == [(2, 0, 1)]
    assert partida.estado().sala_id == 2 and partida.estado().reloj == 100
    partida.mover("S")
    assert partida.estado().sala_id == 1 and partida.estado().reloj == 200


@pytest.mark.parametrize("accion", [lambda p: p.mover("E"), lambda p: p.atacar(1), lambda p: p.atacar(0)])
def test_partida_acciones_invalidas_no_avanzan_reloj_ni_historial(accion):
    partida = preparar_partida()
    with pytest.raises(AccionInvalida):
        accion(partida)
    assert partida.motor.reloj == 0 and partida.motor.historial.acciones == []


def test_abrir_con_llave_permite_moverse_y_puede_deshacerse():
    partida = preparar_partida()
    salida = partida.jugador.sala_actual.salidas[0]
    salida.abierta = False
    salida.puerta.llave = "llave-1"
    llave = SimpleNamespace(nombre="Llave", clase="llave", id="llave-1")
    partida.jugador.sala_actual.objetos_suelo.append(llave)
    partida.recoger(1)
    mensajes = partida.abrir("n")
    assert salida.abierta and partida.motor.reloj == 75
    assert partida.inventario.actual() is llave
    assert any("Abres la puerta" in mensaje for mensaje in mensajes)
    partida.motor.deshacer_ultima_accion()
    assert not salida.abierta and partida.motor.reloj == 25
    partida.abrir("N")
    partida.mover("N")
    assert partida.jugador.sala_actual is salida.destino


def test_abrir_rechaza_sin_llave_y_ya_abierta_sin_tiempo():
    partida = preparar_partida()
    salida = partida.jugador.sala_actual.salidas[0]
    with pytest.raises(AccionInvalida, match="ya esta abierta"):
        partida.abrir("N")
    salida.abierta = False
    salida.puerta.llave = "llave-1"
    partida.inventario.recoger(SimpleNamespace(nombre="Otra llave", clase="llave", id="llave-2"))
    with pytest.raises(AccionInvalida, match="llave correcta"):
        partida.abrir("N")
    assert partida.motor.reloj == 0 and partida.motor.historial.acciones == []
    assert not salida.abierta


def test_abrir_respeta_cierre_automatico_y_lo_informa():
    partida = preparar_partida()
    salida = partida.jugador.sala_actual.salidas[0]
    salida.abierta = False
    salida.puerta.llave = "llave-1"
    salida.puerta.cierre_automatico = 30
    partida.inventario.recoger(SimpleNamespace(nombre="Llave", clase="llave", id="llave-1"))
    mensajes = partida.abrir("N")
    assert partida.motor.reloj == 50 and not salida.abierta
    assert any("[t=30] Se cierra la puerta" in mensaje for mensaje in mensajes)


def test_partida_puerta_cerrada_no_carga_ni_mueve():
    partida = preparar_partida()
    partida.jugador.sala_actual.salidas[0].abierta = False
    with pytest.raises(AccionInvalida, match="cerrada"):
        partida.mover("N")
    assert partida.estado().sala_id == 1 and partida.estado().reloj == 0


def test_partida_enemigo_rapido_ataca_entre_decisiones_y_puede_morir():
    partida = preparar_partida(enemigo=True)
    mensajes = partida.mover("N")
    assert partida.estado().vida < 30
    assert any("pierdes" in mensaje for mensaje in mensajes)
    assert partida.estado().enemigos[0][0] == "Guardian #g-1"
    for _ in range(4):
        if not partida.estado().enemigos:
            break
        partida.atacar(1)
    assert partida.enemigos[0].vida == 0
    assert partida.estado().enemigos == []
    assert partida.enemigos[0].proxima_accion is None


def test_partida_derrota_detiene_controlador_sin_pedir_otro_comando():
    partida = preparar_partida(vida=1, enemigo=True)
    salida = []
    comandos = iter(["w"])
    vista = VistaConsola(entrada=lambda _: next(comandos), salida=salida.append)
    Controlador(partida, vista).ejecutar()
    assert partida.estado().resultado == "derrota"
    assert partida.estado().terminada and partida.estado().reloj == 66
    assert any("Derrota" in linea for linea in salida)


def test_partida_controlador_real_navega_espera_y_sale():
    partida = preparar_partida()
    salida = []
    comandos = iter(["inv", "atacar", "w", "esperar", "s", "guardar", "salir"])
    vista = VistaConsola(entrada=lambda _: next(comandos), salida=salida.append)
    Controlador(partida, vista).ejecutar()
    assert partida.estado().sala_id == 1 and partida.estado().reloj == 300
    assert any("No hay un gestor de guardado" in m for m in vista.bitacora.mensajes())


def test_partida_misma_semilla_y_acciones_producen_mismo_estado():
    primera, segunda = preparar_partida(enemigo=True), preparar_partida(enemigo=True)
    for partida in (primera, segunda):
        partida.mover("N")
        partida.atacar(1)
        partida.esperar()
    assert primera.estado() == segunda.estado()


@pytest.fixture
def paquete_oficial_de_prueba(tmp_path):
    """Respuestas sinteticas con el contrato oficial; no se usan en produccion."""
    import json

    carpeta = tmp_path / "datos"

    def escribir(ruta, datos):
        archivo = carpeta / ruta
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")

    escribir("criptas.json", {"criptas": [{"id": "prueba", "nombre": "Cripta de prueba", "salas": 2}]})
    escribir("catalogo_version.json", {"version": "cat-prueba"})
    escribir("criptas/prueba/general.json", {
        "id": "prueba", "version": "v1", "paginas": 1, "salas_total": 2,
        "sala_inicial": 1, "sala_salida": 2, "llave_salida": "llave",
        "presupuesto_solicitudes": 10, "inventario_max": 4,
        "jugador": {"vida_max": 30, "ataque": 20, "defensa": 2, "velocidad": 100},
    })
    escribir("criptas/prueba/salas_1.json", {"pagina": 1, "salas": [
        {"id": 1, "nombre": "Entrada", "salidas": {"N": {"sala": 2}}},
        {"id": 2, "nombre": "Pasillo", "salidas": {"S": {"sala": 1}}},
    ]})
    escribir("criptas/prueba/contenido/1.json", {
        "sala": 1, "enemigos": [], "objetos": ["daga", "daga"], "trampas": [],
    })
    escribir("criptas/prueba/contenido/2.json", {
        "sala": 2, "enemigos": [{"instancia": "g-1", "tipo": "guardian", "vida": None}],
        "objetos": [], "trampas": [{"instancia": "t-1", "tipo": "dardos"}],
    })
    escribir("catalogo/daga.json", {"id": "daga", "clase": "arma", "nombre": "Daga", "ataque_bonus": 3})
    escribir("catalogo/guardian.json", {
        "id": "guardian", "clase": "enemigo", "nombre": "Guardian", "vida_max": 12,
        "ataque": 3, "defensa": 0, "velocidad": 100, "comportamiento": "guardián",
        "suelta": ["daga"],
    })
    escribir("catalogo/dardos.json", {
        "id": "dardos", "clase": "trampa", "nombre": "Dardos", "daño": 4, "rearme": None,
    })
    return carpeta


def crear_cargador(carpeta, tmp_path):
    from adaptadores.cache_catalogo import CacheCatalogo
    from adaptadores.modo_offline import ModoOffline
    from adaptadores.servicio_cripta import ServicioCripta
    from controlador.cargar_partida import CargadorPartida

    fuente = ModoOffline(str(carpeta))
    cache = CacheCatalogo(fuente, carpeta=str(tmp_path / "cache"), tope=25)
    return CargadorPartida(ServicioCripta(fuente, cache))


def test_bitacora_y_replay_reproducen_seleccion_equipo_combate_y_pergamino(paquete_oficial_de_prueba, tmp_path):
    import json
    from adaptadores.bitacora_partida import EscritorBitacora, leer_bitacora, reproducir_bitacora
    from controlador.controlador import ejecutar_accion_replay

    archivo = paquete_oficial_de_prueba / "criptas/prueba/contenido/1.json"
    contenido = json.loads(archivo.read_text(encoding="utf-8"))
    contenido["objetos"] = ["daga", "coraza", "pergamino"]
    archivo.write_text(json.dumps(contenido), encoding="utf-8")
    for id_objeto, ficha in (
        ("coraza", {"id": "coraza", "nombre": "Coraza", "clase": "armadura", "defensa_bonus": 4}),
        ("pergamino", {"id": "pergamino", "nombre": "Pergamino", "clase": "pergamino_retroceso"}),
    ):
        (paquete_oficial_de_prueba / f"catalogo/{id_objeto}.json").write_text(json.dumps(ficha), encoding="utf-8")
    directa = crear_cargador(paquete_oficial_de_prueba, tmp_path / "directa").crear("prueba", 2026)
    ruta = tmp_path / "partida.log"
    with EscritorBitacora(ruta, "prueba", "v1", "cat-prueba", 2026) as escritor:
        ctl = Controlador(directa, VistaConsola(salida=lambda texto: None), escritor.registrar_accion)
        for texto in (
            "inv", "atacar", "recoger 1", "recoger 1", "recoger 1", "sig", "equipar",
            "sig", "equipar", "ayuda", "w", "atacar", "retroceder", "atacar", "s", "esperar",
        ):
            ctl.procesar(texto)
    encabezado, acciones = leer_bitacora(ruta)
    assert acciones[:3] == ["recoger 1"] * 3
    assert "sig" in acciones and "retroceder" in acciones
    assert "inv" not in acciones and "ayuda" not in acciones
    cargador = crear_cargador(paquete_oficial_de_prueba, tmp_path / "replay")
    repetida = reproducir_bitacora(
        ruta, id_cripta_actual="prueba", version_cripta_actual="v1", version_catalogo_actual="cat-prueba",
        crear_partida=lambda h: cargador.crear(h.id_cripta, h.semilla, encabezado_log=h),
        ejecutar_accion=ejecutar_accion_replay,
    )
    assert repetida.estado() == directa.estado()
    assert repetida.acciones_ejecutadas == directa.acciones_ejecutadas
    assert repetida.motor.azar.getstate() == directa.motor.azar.getstate()
    assert [objeto.id for objeto in repetida.inventario.listar()] == [objeto.id for objeto in directa.inventario.listar()]
    assert repetida.inventario.arma_equipada.id == "daga"
    assert repetida.inventario.armadura_equipada.id == "coraza"
    assert [(e.tiempo, e.secuencia, e.tipo, e.cancelado) for e in repetida.motor.agenda.heap] == [
        (e.tiempo, e.secuencia, e.tipo, e.cancelado) for e in directa.motor.agenda.heap
    ]


def test_main_registra_y_reproduce_sin_vista_ni_puntaje_adicional(paquete_oficial_de_prueba, tmp_path, monkeypatch, capsys):
    import main as aplicacion
    from adaptadores.modo_offline import ModoOffline

    monkeypatch.setattr(aplicacion, "ClienteHTTP", lambda **opciones: ModoOffline(str(paquete_oficial_de_prueba)))
    comandos = iter(["recoger", "esperar", "salir"])
    monkeypatch.setattr(aplicacion, "VistaConsola", lambda: VistaConsola(
        entrada=lambda _: next(comandos), salida=lambda texto: None,
    ))
    ruta = tmp_path / "partida.log"
    puntajes = tmp_path / "puntajes.json"
    assert aplicacion.main(["--cripta", "prueba", "--bitacora", str(ruta),
                            "--puntajes", str(puntajes), "--cache-dir", str(tmp_path / "cache")]) == 0
    monkeypatch.setattr(aplicacion, "VistaConsola", lambda: pytest.fail("El replay no debe crear una vista"))
    assert aplicacion.main(["--replay", str(ruta), "--sin-interfaz", "--puntajes", str(puntajes),
                            "--cache-dir", str(tmp_path / "cache-replay")]) == 0
    assert "Replay completado: sala 1, vida 30, reloj 125" in capsys.readouterr().out
    assert not puntajes.exists()


@pytest.mark.parametrize("pasos", [("", ""), ("t",)])
def test_replay_avanza_con_enter_o_completa_con_t(paquete_oficial_de_prueba, tmp_path, monkeypatch, pasos):
    import main as aplicacion
    from adaptadores.bitacora_partida import EscritorBitacora
    from adaptadores.modo_offline import ModoOffline

    ruta = tmp_path / "partida.log"
    with EscritorBitacora(ruta, "prueba", "v1", "cat-prueba", 2026) as escritor:
        for accion in ("recoger 1", "esperar"):
            escritor.registrar_accion(accion)
    monkeypatch.setattr(aplicacion, "ClienteHTTP", lambda **opciones: ModoOffline(str(paquete_oficial_de_prueba)))
    lineas = []
    entradas = iter(pasos)
    consultas = []

    def entrada(mensaje):
        consultas.append(mensaje)
        return next(entradas)

    monkeypatch.setattr(aplicacion, "VistaConsola", lambda: VistaConsola(
        entrada=entrada, salida=lineas.append,
    ))
    assert aplicacion.main(["--replay", str(ruta), "--cache-dir", str(tmp_path / "cache")]) == 0
    estados = [linea for linea in lineas if "Entrada (sala 1)" in linea]
    assert len(estados) == 3
    assert "reloj: 0" in estados[0] and "reloj: 25" in estados[1] and "reloj: 125" in estados[2]
    assert any("Replay > recoger 1" in linea for linea in lineas)
    assert any("Recoges Daga" in linea for linea in lineas)
    assert any("Replay > esperar" in linea for linea in lineas)
    assert len(consultas) == len(pasos)


def test_replay_rechaza_version_incompatible_antes_de_construir_entidades(paquete_oficial_de_prueba, tmp_path):
    from adaptadores.bitacora_partida import EncabezadoLog, ErrorBitacora

    cargador = crear_cargador(paquete_oficial_de_prueba, tmp_path)
    with pytest.raises(ErrorBitacora, match="reproduccion fiel"):
        cargador.crear("prueba", 2026, encabezado_log=EncabezadoLog("prueba", "otra", "cat-prueba", 2026))
    assert cargador.jugador is None and cargador.salas.cantidad == 0


def test_guardado_binario_de_sesion_conserva_equipo_deltas_y_referencias(paquete_oficial_de_prueba, tmp_path):
    cargador = crear_cargador(paquete_oficial_de_prueba, tmp_path / "original")
    partida = cargador.crear("prueba", 2026)
    partida.recoger(1)
    partida.recoger(1)
    partida.inventario.avanzar()
    partida.equipar()
    partida.mover("N")
    partida.atacar(1)
    ruta = tmp_path / "partida.bin"
    cargador.guardar_sesion(partida, ruta)
    otro = crear_cargador(paquete_oficial_de_prueba, tmp_path / "nueva")
    restaurada = otro.reanudar(ruta)
    assert restaurada.estado() == partida.estado()
    assert restaurada.acciones_ejecutadas == partida.acciones_ejecutadas == 5
    assert restaurada.motor.azar.getstate() == partida.motor.azar.getstate()
    assert restaurada.inventario.arma_equipada is restaurada.inventario.frente.objeto
    assert otro.salas.buscar(2) is restaurada.jugador.sala_actual
    restaurada.motor.deshacer_ultima_accion()
    assert restaurada.acciones_ejecutadas == 4
    assert restaurada.enemigos[0].vida == 12
    assert restaurada.jugador.sala_actual.objetos_suelo == []
    restaurada.atacar(1)
    assert restaurada.estado() == partida.estado()


def test_reanudar_reutiliza_contenido_guardado_sin_recrear_instancias(paquete_oficial_de_prueba, tmp_path, monkeypatch):
    cargador = crear_cargador(paquete_oficial_de_prueba, tmp_path / "original")
    partida = cargador.crear("prueba", 2026)
    partida.recoger(1)
    ruta = tmp_path / "partida.bin"
    cargador.guardar_sesion(partida, ruta)
    otro = crear_cargador(paquete_oficial_de_prueba, tmp_path / "nueva")
    restaurada = otro.reanudar(ruta)
    monkeypatch.setattr(otro.servicio.fuente, "contenido", lambda *args: pytest.fail("El contenido ya estaba guardado"))
    restaurada.mover("N")
    enemigo = restaurada.enemigos[0]
    otro.preparar_sala(restaurada.jugador.sala_actual)
    assert restaurada.enemigos == [enemigo]
    assert restaurada.jugador.sala_actual.enemigos[0] is enemigo


def test_comandos_guardar_cargar_no_consumen_tiempo_y_reconectan_retroceso(paquete_oficial_de_prueba, tmp_path):
    cargador = crear_cargador(paquete_oficial_de_prueba, tmp_path)
    partida = cargador.crear("prueba", 2026)
    partida.ruta_guardado = str(tmp_path / "partida.bin")
    partida.recoger(1)
    partida.guardar()
    assert partida.motor.reloj == 25 and partida.acciones_ejecutadas == 1
    partida.esperar()
    solicitudes = partida.fuente.solicitudes_realizadas
    partida.cargar()
    assert partida.motor.reloj == 25 and partida.acciones_ejecutadas == 1
    assert partida.fuente.solicitudes_realizadas == solicitudes
    assert cargador.jugador is partida.jugador
    partida.motor.deshacer_ultima_accion()
    assert partida.motor.reloj == 0 and partida.acciones_ejecutadas == 0
    assert partida.inventario.esta_vacio()
    partida.esperar()
    anterior = partida.motor
    (tmp_path / "partida.bin").write_bytes(b"guardado truncado")
    with pytest.raises(AccionInvalida, match="No se pudo cargar"):
        partida.cargar()
    assert partida.motor is anterior and partida.motor.reloj == 100


def test_guardado_conserva_efectos_y_excepcion_de_pergaminos(paquete_oficial_de_prueba, tmp_path):
    from adaptadores.estado_binario import ObjetoPartida

    cargador = crear_cargador(paquete_oficial_de_prueba, tmp_path / "original")
    partida = cargador.crear("prueba", 2026)
    suelo = partida.jugador.sala_actual.objetos_suelo
    suelo.append(ObjetoPartida("perg", "pergamino_retroceso", "Pergamino"))
    partida.recoger(3)
    suelo.append(ObjetoPartida("rapidez", "pocion", "Rapidez", ficha={
        "id": "rapidez", "modificador_velocidad": 50, "duracion": 200,
    }))
    partida.recoger(3)
    partida.inventario.avanzar()
    partida.usar()
    ruta = tmp_path / "partida.bin"
    cargador.guardar_sesion(partida, ruta)
    nueva = crear_cargador(paquete_oficial_de_prueba, tmp_path / "nueva").reanudar(ruta)
    assert nueva.jugador.velocidad == 150
    assert nueva.jugador.efecto_velocidad.fin == 250
    assert nueva.inventario.actual().recogido_fuera_historial
    nueva.retroceder()
    assert nueva.jugador.velocidad == 100 and nueva.jugador.efecto_velocidad is None
    assert nueva.inventario.actual().id == "rapidez"
    assert nueva.motor.reloj == 50 and nueva.acciones_ejecutadas == 2


def test_main_permite_guardar_con_bitacora_y_reanudar_en_otra_ejecucion(paquete_oficial_de_prueba, tmp_path, monkeypatch):
    import main as aplicacion
    from adaptadores.modo_offline import ModoOffline
    from adaptadores.bitacora_partida import leer_bitacora

    monkeypatch.setattr(aplicacion, "ClienteHTTP", lambda **opciones: ModoOffline(str(paquete_oficial_de_prueba)))
    ruta = tmp_path / "partida.bin"
    log = tmp_path / "partida.log"
    lineas = []
    comandos = iter(["recoger", "guardar", "esperar", "cargar", "salir"])
    monkeypatch.setattr(aplicacion, "VistaConsola", lambda: VistaConsola(
        entrada=lambda _: next(comandos), salida=lineas.append,
    ))
    assert aplicacion.main(["--cripta", "prueba", "--nombre", "Kendall", "--bitacora", str(log),
                            "--archivo-guardado", str(ruta), "--cache-dir", str(tmp_path / "cache")]) == 0
    assert ruta.exists()
    assert any("No puedes cargar mientras registras una bitacora" in linea for linea in lineas)
    assert leer_bitacora(log)[1] == ["recoger", "esperar"]
    comandos = iter(["esperar", "salir"])
    lineas.clear()
    assert aplicacion.main(["--cargar", str(ruta), "--cache-dir", str(tmp_path / "otra-cache")]) == 0
    assert any("reloj: 25" in linea for linea in lineas)
    assert any("reloj: 125" in linea for linea in lineas)
    assert any("--- Resumen de red y cache ---" in linea for linea in lineas)
    assert any("Solicitudes HTTP: 0/10" in linea for linea in lineas)
    assert any("Aciertos de cache:" in linea for linea in lineas)
    assert any("Fallos de cache:" in linea for linea in lineas)


def test_medicion_ciclos_usa_partida_real_precargada_y_repite_el_estado(paquete_oficial_de_prueba, tmp_path, monkeypatch, capsys):
    from modelo.bench_modelo import medir_cripta_cargada

    cargador = crear_cargador(paquete_oficial_de_prueba, tmp_path)
    partida = cargador.crear("prueba", 2026)
    cargador.preparar_sala(cargador.salas.buscar(2))
    monkeypatch.setattr(cargador.servicio.fuente, "contenido", lambda *args: pytest.fail("Los datos ya estan precargados"))
    monkeypatch.setattr(cargador.servicio.fuente, "catalogo", lambda *args: pytest.fail("Las fichas ya estan precargadas"))
    resultado = medir_cripta_cargada(cargador, partida, repeticiones=2, ciclos=6)
    assert resultado["ciclos"] == 12
    assert resultado["maximo_ms"] >= 0
    salida = capsys.readouterr().out
    assert "maximo:" in salida and "Ciclos con tiempo >= 20 ms:" in salida
    assert partida.acciones_ejecutadas == 6


def test_medicion_ciclos_rechaza_una_solicitud_dentro_del_cronometro():
    from modelo.bench_modelo import medir_ciclos_partida

    partida = preparar_partida()
    partida.fuente = SimpleNamespace(solicitudes_realizadas=0)
    original = partida.mover

    def mover_con_solicitud(direccion):
        mensajes = original(direccion)
        partida.fuente.solicitudes_realizadas += 1
        return mensajes

    partida.mover = mover_con_solicitud
    with pytest.raises(RuntimeError, match="HTTP durante un ciclo"):
        medir_ciclos_partida(partida, 1)


def test_cargador_comparte_fichas_y_salidas_pero_no_instancias(paquete_oficial_de_prueba, tmp_path):
    cargador = crear_cargador(paquete_oficial_de_prueba, tmp_path)
    partida = cargador.crear("prueba", 2026)
    entrada, pasillo = cargador.salas.buscar(1), cargador.salas.buscar(2)
    assert entrada.salidas[0].destino is pasillo
    assert pasillo.salidas[0].destino is entrada
    a, b = entrada.objetos_suelo
    assert a is not b and a.ficha is b.ficha
    assert partida.inventario.capacidad == 4
    assert partida.jugador.ataque == 20 and partida.jugador.defensa == 2
    assert partida.motor.reloj == 0
    assert cargador.servicio.fuente.solicitudes_realizadas == 0
    assert cargador.ficha_en_uso("daga")


def test_cargador_precargar_no_activa_ni_duplica_enemigos(paquete_oficial_de_prueba, tmp_path):
    cargador = crear_cargador(paquete_oficial_de_prueba, tmp_path)
    partida = cargador.crear("prueba", 2026)
    pasillo = cargador.salas.buscar(2)
    assert not pasillo.contenido_cargado
    assert cargador.servicio.contenido.buscar(2) is not None
    cargador.preparar_sala(pasillo)
    enemigo = pasillo.enemigos[0]
    assert enemigo.vida == enemigo.vida_max == 12
    assert enemigo.comportamiento == "guardian"
    assert not enemigo.activo and enemigo.proxima_accion is None
    assert pasillo.trampas[0].rearme == 300
    cargador.preparar_sala(pasillo)
    assert cargador.enemigos == [enemigo]
    partida.mover("N")
    assert enemigo.activo and partida.motor.reloj == 100
    assert partida.jugador.vida == 26  # Trampa inmediata, antes del turno enemigo.
    assert cargador.ficha_en_uso("dardos") and cargador.ficha_en_uso("guardian")


def test_cargador_y_combate_dejan_botin_en_suelo_una_sola_vez(paquete_oficial_de_prueba, tmp_path):
    cargador = crear_cargador(paquete_oficial_de_prueba, tmp_path)
    partida = cargador.crear("prueba", 2026)
    partida.mover("N")
    enemigo = partida.enemigos[0]
    partida.atacar(1)
    suelo = partida.jugador.sala_actual.objetos_suelo
    assert len(suelo) == 1 and suelo[0] is enemigo.suelta[0]
    assert not cargador.ficha_en_uso("guardian") and cargador.ficha_en_uso("daga")
    with pytest.raises(AccionInvalida):
        partida.atacar(1)
    assert len(suelo) == 1
    pergamino = SimpleNamespace(nombre="Pergamino", clase="pergamino_retroceso")
    partida.inventario.recoger(pergamino)
    assert partida.motor.usar_pergamino(
        partida.jugador, lambda objeto: objeto.clase == "pergamino_retroceso",
    )
    assert enemigo.vida == 12 and suelo == []
    assert partida.inventario.esta_vacio() and partida.motor.reloj == 100
    partida.atacar(1)
    assert len(suelo) == 1 and suelo[0] is enemigo.suelta[0]


def test_cargador_no_publica_contenido_si_falla_una_entidad(paquete_oficial_de_prueba, tmp_path):
    import json

    archivo = paquete_oficial_de_prueba / "catalogo/dardos.json"
    ficha = json.loads(archivo.read_text(encoding="utf-8"))
    ficha["daño"] = 0
    archivo.write_text(json.dumps(ficha), encoding="utf-8")
    cargador = crear_cargador(paquete_oficial_de_prueba, tmp_path)
    partida = cargador.crear("prueba", 2026)
    with pytest.raises(AccionInvalida, match="Sala 2"):
        partida.mover("N")
    assert partida.motor.reloj == 0 and partida.jugador.sala_actual.sala_id == 1
    assert partida.motor.historial.acciones == []
    assert cargador.enemigos == []
    assert not cargador.salas.buscar(2).contenido_cargado


def test_cargador_rechaza_destino_inexistente(paquete_oficial_de_prueba, tmp_path):
    import json
    from controlador.cargar_partida import ErrorDatosPartida

    archivo = paquete_oficial_de_prueba / "criptas/prueba/salas_1.json"
    pagina = json.loads(archivo.read_text(encoding="utf-8"))
    pagina["salas"][0]["salidas"]["N"]["sala"] = 999
    archivo.write_text(json.dumps(pagina), encoding="utf-8")
    cargador = crear_cargador(paquete_oficial_de_prueba, tmp_path)
    with pytest.raises(ErrorDatosPartida, match="destino inexistente"):
        cargador.crear("prueba", 2026)


def test_main_lista_y_juega_con_componentes_reales(paquete_oficial_de_prueba, tmp_path, monkeypatch, capsys):
    import main as aplicacion
    from adaptadores.modo_offline import ModoOffline

    monkeypatch.setattr(aplicacion, "ClienteHTTP", lambda **opciones: ModoOffline(str(paquete_oficial_de_prueba)))
    assert aplicacion.main(["--listar"]) == 0
    assert "prueba: Cripta de prueba (2 salas)" in capsys.readouterr().out
    comandos = iter(["w", "atacar", "esperar", "s", "salir"])
    salida = []
    monkeypatch.setattr(aplicacion, "VistaConsola", lambda: VistaConsola(
        entrada=lambda _: next(comandos), salida=salida.append,
    ))
    assert aplicacion.main(["--cripta", "prueba", "--cache-dir", str(tmp_path / "cache")]) == 0
    assert any("reloj: 400" in linea for linea in salida)
    assert any("Derrotaste" in linea for linea in salida)


def test_main_offline_lista_juega_y_reproduce_sin_crear_cliente_http(paquete_oficial_de_prueba, tmp_path, monkeypatch, capsys):
    import main as aplicacion

    monkeypatch.setattr(aplicacion, "ClienteHTTP", lambda **opciones: pytest.fail("Offline no debe crear un cliente HTTP"))
    carpeta = str(paquete_oficial_de_prueba)
    assert aplicacion.main(["--offline", carpeta, "--listar"]) == 0
    assert "prueba: Cripta de prueba" in capsys.readouterr().out
    comandos = iter(["recoger", "esperar", "salir"])
    lineas = []
    monkeypatch.setattr(aplicacion, "VistaConsola", lambda: VistaConsola(
        entrada=lambda _: next(comandos), salida=lineas.append,
    ))
    ruta_log = str(tmp_path / "partida.log")
    cache = str(tmp_path / "cache")
    assert aplicacion.main(["--offline", carpeta, "--cripta", "prueba",
                            "--cache-dir", cache, "--bitacora", ruta_log]) == 0
    assert any("Solicitudes de red: 0/10" in linea for linea in lineas)
    assert any("reloj: 125" in linea for linea in lineas)
    assert aplicacion.main(["--offline", carpeta, "--replay", ruta_log,
                            "--sin-interfaz", "--cache-dir", cache]) == 0
    assert "Replay completado: sala 1, vida 30, reloj 125" in capsys.readouterr().out


def test_main_bench_no_crea_cliente_http(monkeypatch):
    import main as aplicacion
    from modelo import bench_modelo

    llamadas = []
    monkeypatch.setattr(aplicacion, "ClienteHTTP", lambda **opciones: pytest.fail("Bench no debe crear un cliente HTTP"))
    monkeypatch.setattr(bench_modelo, "ejecutar_bench_completo", lambda *args: llamadas.append(args))
    assert aplicacion.main(["--bench", "--repeticiones", "1", "--semilla", "2026"]) == 0
    assert llamadas == [(1, 2026, 25)]


def test_main_bench_cripta_conecta_medicion_real_sin_vista(paquete_oficial_de_prueba, tmp_path, monkeypatch, capsys):
    import main as aplicacion
    from modelo import bench_modelo

    monkeypatch.setattr(bench_modelo, "ejecutar_bench_completo", lambda *args: None)
    monkeypatch.setattr(aplicacion, "ClienteHTTP", lambda **opciones: pytest.fail("Se pidio modo offline"))
    monkeypatch.setattr(aplicacion, "VistaConsola", lambda: pytest.fail("La medicion excluye la vista"))
    codigo = aplicacion.main([
        "--bench", "--cripta", "prueba", "--offline", str(paquete_oficial_de_prueba),
        "--repeticiones", "1", "--cache-dir", str(tmp_path / "cache"),
    ])
    salida = capsys.readouterr().out
    assert "CICLO COMPLETO: cripta prueba" in salida
    assert "Ciclos entre decisiones:" in salida and "maximo:" in salida
    assert codigo == (1 if "NO CUMPLE" in salida else 0)


def test_main_offline_informa_paquete_ausente(tmp_path, capsys):
    import main as aplicacion

    assert aplicacion.main(["--offline", str(tmp_path / "ausente"), "--listar"]) == 1
    error = capsys.readouterr().err
    assert "no existe" in error and "criptas.json" in error and "Traceback" not in error


def test_main_error_http_se_informa_sin_traceback(monkeypatch, capsys):
    import main as aplicacion
    from adaptadores.cliente_http import ErrorHTTP

    def cliente_sin_conexion():
        raise ErrorHTTP("listar criptas: fallo de red")

    # La creacion normalmente no hace red; se simula el fallo de la consulta.
    class FuenteSinConexion:
        listar_criptas = staticmethod(cliente_sin_conexion)

    monkeypatch.setattr(aplicacion, "ClienteHTTP", lambda **opciones: FuenteSinConexion())
    assert aplicacion.main(["--listar"]) == 1
    error = capsys.readouterr().err
    assert "fallo de red" in error and "Traceback" not in error


def test_main_rechaza_cache_size_cero_antes_de_conectar():
    import main as aplicacion

    with pytest.raises(SystemExit) as error:
        aplicacion.main(["--cripta", "prueba", "--cache-size", "0"])
    assert error.value.code == 2


def test_mensajes_explican_trampa_y_ataques_en_orden_temporal(paquete_oficial_de_prueba, tmp_path):
    cargador = crear_cargador(paquete_oficial_de_prueba, tmp_path)
    partida = cargador.crear("prueba", 2026)
    partida.jugador.sala_actual.salidas[0].destino.nombre = "Pasillo de prueba"
    mensajes = partida.mover("N")
    assert mensajes[0] == "[t=0] Entras en Pasillo de prueba."
    assert mensajes[1] == "[t=0] Trampas de entrada: pierdes 4 de vida."
    mensajes = partida.atacar(1)
    assert any("[t=100]" in m and "pierde 12 de vida" in m for m in mensajes)
    assert any("[t=100] Derrotaste" in m for m in mensajes)
    assert all("[t=100]" in m for m in mensajes)


def test_ataque_se_informa_antes_de_regeneracion_enemiga():
    partida = preparar_partida(enemigo=True)
    enemigo = partida.enemigos[0]
    enemigo.regeneracion_cantidad = 3
    partida.mover("N")
    mensajes = partida.atacar(1)
    dano = next(m for m in mensajes if "pierde" in m and "queda en" in m)
    regeneracion = next(m for m in mensajes if "recupera" in m)
    assert "[t=100]" in dano and "[t=200]" in regeneracion
    assert mensajes.index(dano) < mensajes.index(regeneracion)


def test_trampa_letal_se_informa_aunque_no_se_ejecute_ningun_evento(
    paquete_oficial_de_prueba, tmp_path
):
    partida = crear_cargador(paquete_oficial_de_prueba, tmp_path).crear("prueba", 2026)
    partida.jugador.vida = 1
    mensajes = partida.mover("N")
    assert "[t=0] Trampas de entrada: pierdes 1 de vida." in mensajes
    assert partida.estado().resultado == "derrota" and partida.motor.reloj == 0


def test_rastreador_que_llega_a_la_sala_aparece_en_mensajes_y_objetivos():
    partida = preparar_partida(enemigo=True)
    partida.enemigos[0].comportamiento = "rastreador"
    partida.mover("N")
    mensajes = partida.mover("S")
    assert any("se mueve de Pasillo a Entrada" in m for m in mensajes)
    assert partida.estado().enemigos[0][0] == "Guardian #g-1"


def test_estado_y_vista_muestran_destinos_abiertos_cerrados_y_presupuesto(paquete_oficial_de_prueba, tmp_path):
    cargador = crear_cargador(paquete_oficial_de_prueba, tmp_path)
    partida = cargador.crear("prueba", 2026)
    fuente = cargador.servicio.fuente
    fuente.solicitudes_realizadas = 5
    fuente.presupuesto_solicitudes = 9
    salida = partida.jugador.sala_actual.salidas[0]
    salida.abierta = False
    salida.puerta.llave = "llave-prueba"
    lineas = []
    vista = VistaConsola(salida=lineas.append)
    vista.mostrar_estado(partida.estado())
    assert "Solicitudes de red: 5/9" in lineas
    assert any("Ninguna salida abierta" in linea for linea in lineas)
    assert any("N - Pasillo, sala 2; requiere llave-prueba" in linea for linea in lineas)
    salida.abierta = True
    lineas.clear()
    vista.mostrar_estado(partida.estado())
    assert any("N - Pasillo, sala 2 (escribe w)" in linea for linea in lineas)
    assert not any("Puertas cerradas" in linea for linea in lineas)


@pytest.mark.parametrize("tipo_error", ["presupuesto", "red"])
def test_fallo_de_carga_no_cierra_consola_ni_modifica_simulacion(
    paquete_oficial_de_prueba, tmp_path, monkeypatch, tipo_error
):
    from adaptadores.cliente_http import ErrorHTTP, PresupuestoAgotado

    cargador = crear_cargador(paquete_oficial_de_prueba, tmp_path)
    partida = cargador.crear("prueba", 2026)
    turno = partida.jugador.proxima_accion
    estado_azar = partida.motor.azar.getstate()
    def falla(sala):
        if tipo_error == "presupuesto":
            raise PresupuestoAgotado("9 de 9")
        raise ErrorHTTP("sin conexion")
    monkeypatch.setattr(cargador, "preparar_sala", falla)
    comandos = iter(["w", "esperar", "salir"])
    lineas = []
    vista = VistaConsola(entrada=lambda _: next(comandos), salida=lineas.append)
    controlador = Controlador(partida, vista)
    assert controlador.procesar("w")
    assert partida.motor.reloj == 0 and partida.jugador.sala_actual.sala_id == 1
    assert partida.jugador.proxima_accion is turno
    assert partida.motor.azar.getstate() == estado_azar and partida.motor.historial.acciones == []
    assert "No se confirmo el movimiento" in vista.bitacora.mas_reciente()
    Controlador(partida, vista).ejecutar()
    assert partida.motor.reloj == 100
    assert partida.jugador.sala_actual.sala_id == 1
