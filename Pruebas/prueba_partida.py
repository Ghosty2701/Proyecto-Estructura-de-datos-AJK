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
    assert any("todavia no esta integrado" in m for m in vista.bitacora.mensajes())


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
