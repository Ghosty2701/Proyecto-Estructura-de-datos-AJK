"""Aceptación FR-NV: integración con eventos y presentación de conocimiento."""
from types import SimpleNamespace

import pytest

from prueba_conocimiento import mapa
from modelo.conocimiento import ConocimientoMapa
from modelo.motor_eventos import ActorTurnos, MotorEventos
from modelo.inventario_reversible import InventarioReversible
from controlador.partida import Partida


def partida_niebla(cantidad=5):
    salas = mapa(cantidad)
    jugador = ActorTurnos('jugador', 100, 100)
    jugador.inventario = InventarioReversible(6)
    motor = MotorEventos(2026)
    motor.conocimiento = ConocimientoMapa(salas)
    motor.iniciar_partida(jugador, salas[0])
    return Partida(motor, jugador, [], lambda s: None), salas


def test_ac001_003_005_proyeccion_no_revela_ni_observa():
    # FR-NV-001/002/003/004/005/015
    p, salas = partida_niebla()
    azar = p.motor.azar.getstate()
    assert p.estado().rutas[0].nombre == 'Sala avistada'
    mapa_inicial = p.mapa()
    assert mapa_inicial[0][2] == 'Sala 0'
    assert len(mapa_inicial) == 2 and mapa_inicial[1][2] is None
    salas[0].salidas[0].abierta = False  # cambio no observado por el motor
    assert not p.estado().rutas[0].cerrada
    assert p.mapa() == mapa_inicial
    assert p.motor.reloj == 0 and not p.motor.historial.acciones
    assert p.motor.azar.getstate() == azar


def test_ac002_004_observacion_dentro_de_accion_y_ambos_extremos():
    # FR-NV-001/002/003
    p, salas = partida_niebla()
    p.mover('N')
    assert [s.estado for s in p.motor.conocimiento.salas] == [2, 2, 1, 0, 0]
    p.motor.iniciar_accion()
    p.motor._cambiar(salas[1].salidas[-1].puerta, 'abierta', False)
    assert p.motor.conocimiento.salas[1].salidas[-1].puerta.observada is False
    assert p.motor.historial.acciones[-1].cambios


def test_ac006_007_antorcha_no_carga_ni_activa():
    # FR-NV-006/007
    p, salas = partida_niebla()
    salas[2].contenido_cargado = False
    salas[2].enemigos.append(SimpleNamespace(vida=10, activo=False))
    p.jugador.antorcha = SimpleNamespace()
    p.mover('N')
    assert [s.estado for s in p.motor.conocimiento.salas] == [2, 2, 2, 1, 0]
    assert not salas[2].contenido_cargado and not salas[2].enemigos[0].activo


def explorar_todo(p, salas):
    for sala in salas:
        p.motor.conocimiento.entrar(sala, False, p.motor._cambiar)


def test_ac009_012_017_viaje_y_destino_actual_sin_accion():
    # FR-NV-008/011/012/013
    from controlador.controlador import AccionInvalida
    p, salas = partida_niebla()
    with pytest.raises(AccionInvalida, match='explorada'):
        p.resolver_viaje(str(salas[1].sala_id))
    explorar_todo(p, salas)
    pasos = []
    mensajes = p.viajar('Sala 4', registrar=pasos.append)
    assert 'llegaste al destino' in mensajes[-1]
    assert p.jugador.sala_actual is salas[-1]
    assert p.motor.reloj == 400 and p.acciones_ejecutadas == 4
    assert pasos == ['ir N'] * 4
    assert p.viajar(str(salas[-1].sala_id)) == ['Ya estás en esa sala.']
    assert p.motor.reloj == 400 and p.acciones_ejecutadas == 4


def test_paso_compartido_equivale_al_viaje_completo_y_registra_una_orden():
    # FR-IG-012/014; AC-IG-012/014.
    a, salas_a = partida_niebla()
    b, salas_b = partida_niebla()
    explorar_todo(a, salas_a); explorar_todo(b, salas_b)
    ordenes_a, ordenes_b, cuadros = [], [], []
    mensajes_a = a.viajar('Sala 4', registrar=ordenes_a.append)
    destino = b.resolver_viaje('Sala 4')
    mensajes_b = []
    while True:
        paso = b.paso_viaje(destino, registrar=ordenes_b.append,
                            mostrar_paso=lambda: cuadros.append(b.acciones_ejecutadas))
        mensajes_b.extend(paso.mensajes)
        if not paso.continuar: break
    assert ordenes_a == ordenes_b == ['ir N'] * 4
    assert mensajes_a == mensajes_b and cuadros == [1, 2, 3, 4]
    assert a.motor.reloj == b.motor.reloj == 400
    assert a.motor.azar.getstate() == b.motor.azar.getstate()
    assert b.mapa() == a.mapa()


def test_ac014_015_enemigos_al_entrar_y_dano_aunque_cure():
    # FR-NV-007/011/013
    from modelo.efectos import Trampa
    p, salas = partida_niebla()
    explorar_todo(p, salas)
    enemigo = ActorTurnos('g', 10, 100, comportamiento='guardian')
    enemigo.nombre = 'Guardian'
    enemigo.sala_actual = salas[1]
    salas[1].enemigos.append(enemigo)
    p.enemigos.append(enemigo)
    assert 'enemigos' in p.viajar('Sala 4')[-1]
    assert enemigo.activo and p.jugador.sala_actual is salas[1]
    assert p.acciones_ejecutadas == 1 and p.motor.enemigos_entrada
    p, salas = partida_niebla()
    explorar_todo(p, salas)
    salas[1].trampas.append(Trampa('t', 'dano', 1))
    ejecutar = p._ejecutar_evento
    def con_cura(evento):
        ejecutar(evento)
        p.motor._cambiar(p.jugador, 'vida', p.jugador.vida_max)
    p._ejecutar_evento = con_cura
    assert 'daño' in p.viajar('Sala 4')[-1]
    assert p.jugador.sala_actual is salas[1] and p.motor.hubo_dano


def test_ac013_016_no_abre_puertas_y_recalcula():
    # FR-NV-003/009/012/013
    p, salas = partida_niebla()
    explorar_todo(p, salas)
    salas[1].salidas[-1].abierta = False  # remoto: recuerdo sigue abierto
    from adaptadores.estado_binario import ObjetoPartida
    salas[1].salidas[-1].puerta.llave = 'llave'
    p.jugador.inventario.recoger(ObjetoPartida('llave', 'llave', 'Llave'))
    assert 'no hay ruta conocida' in p.viajar('Sala 4')[-1]
    assert p.jugador.sala_actual is salas[1]
    assert p.motor.reloj == 100 and p.acciones_ejecutadas == 1
    assert not salas[1].salidas[-1].abierta


def test_ac014_enemigo_presente_al_entrar_aunque_despues_salga():
    # FR-NV-013: la parada depende de entrada, no solo de enemigos al final.
    p, salas = partida_niebla()
    explorar_todo(p, salas)
    enemigo = ActorTurnos('g', 10, 200, comportamiento='guardian')
    enemigo.nombre, enemigo.sala_actual = 'Guardian', salas[1]
    salas[1].enemigos.append(enemigo)
    p.enemigos.append(enemigo)
    ejecutar = p._ejecutar_evento
    def salida_posterior(evento):
        ejecutar(evento)
        if evento.actor is enemigo:
            p.motor._cambiar(enemigo, 'sala_actual', salas[2])
    p._ejecutar_evento = salida_posterior
    p.viajar('Sala 4')
    assert enemigo.sala_actual is salas[2]
    assert p.jugador.sala_actual is salas[1] and p.acciones_ejecutadas == 1


def test_ver_mapa_y_parser_preservan_nombre():
    # FR-NV-004/005/008/015
    from controlador.comandos import parsear
    from controlador.controlador import Controlador
    from vista.vista_consola import VistaConsola
    assert parsear('ir a Biblioteca Grande').argumento == 'Biblioteca Grande'
    p, _ = partida_niebla()
    lineas, acciones = [], []
    ctl = Controlador(p, VistaConsola(entrada=lambda _: '', salida=lineas.append), acciones.append)
    ctl.procesar('ver mapa')
    assert any('Mapa conocido' in l for l in lineas)
    assert not acciones and not p.motor.historial.acciones


def test_ac019_020_interrumpir_retrocede_ultimo_paso_y_no_continua():
    # FR-NV-011/016: pergamino real y antorcha, mediante controlador.
    from adaptadores.estado_binario import ObjetoPartida
    from modelo.efectos import EstadoEfecto
    from controlador.controlador import Controlador
    from vista.vista_consola import VistaConsola
    p, salas = partida_niebla()
    explorar_todo(p, salas)
    p.jugador.inventario.recoger(ObjetoPartida('perg', 'pergamino_retroceso', 'Pergamino'))
    llamadas = iter([False, False, True])
    acciones = []
    vista = VistaConsola(entrada=lambda _: 'retroceder', salida=lambda _: None,
                         interrupcion=lambda: next(llamadas))
    Controlador(p, vista, acciones.append).procesar('ir a Sala 4')
    assert p.jugador.sala_actual is salas[1] and p.motor.reloj == 100
    assert p.acciones_ejecutadas == 1
    assert acciones == ['# ir a Sala 4', 'ir n', 'ir n', 'retroceder']
    assert not any(o.clase == 'pergamino_retroceso' for o in p.inventario.listar())
    # Una entrada con antorcha revierte también la exploración remota.
    p, salas = partida_niebla()
    p.jugador.inventario.recoger(ObjetoPartida('perg', 'pergamino_retroceso', 'Pergamino'))
    p.jugador.antorcha = EstadoEfecto('antorcha', fin=1000)
    anterior = p.mapa()
    p.mover('N')
    p.retroceder()
    assert p.mapa() == anterior and p.motor.reloj == 0


def test_ac018_021_022_guardado_y_retroceso_restauran_memoria(tmp_path):
    # FR-NV-003/016/017
    from adaptadores.estado_binario import guardar_partida, cargar_partida
    p, salas = partida_niebla()
    p.mover('N')
    p.mover('N')
    recuerdo = salas[0].salidas[0].puerta.recuerdo
    salas[0].salidas[0].abierta = False  # cambio remoto sin observación
    assert recuerdo.observada is True
    ruta = tmp_path / 'niebla.bin'
    guardar_partida(ruta, p.motor, p.jugador, salas,
                    id_cripta='sintetica', version_cripta='v1', version_catalogo='c1')
    q = cargar_partida(ruta)
    k = q.motor.conocimiento
    assert k.proyeccion() == p.mapa()
    assert k.salas[0].salidas[0].puerta is k.salas[1].salidas[0].puerta
    assert not q.salas[0].salidas[0].abierta and k.salas[0].salidas[0].puerta.observada
    assert k.registros.generacion == 0
    p.motor.deshacer_ultima_accion()
    q.motor.deshacer_ultima_accion()
    assert k.proyeccion() == p.mapa()


@pytest.mark.parametrize('corromper', ['estado', 'posicion', 'recuerdo'])
def test_guardado_rechaza_conocimiento_inconsistente(tmp_path, corromper):
    # FR-NV-017
    from adaptadores.estado_binario import guardar_partida
    from adaptadores.guardado_binario import ErrorGuardado
    from modelo.conocimiento import RecuerdoPuerta
    p, salas = partida_niebla()
    k = p.motor.conocimiento
    if corromper == 'estado':
        k.salas[1].estado = 8
    elif corromper == 'posicion':
        k.salas[1].posicion = 0
    else:
        k.salas[0].salidas[0].puerta = RecuerdoPuerta()
    with pytest.raises(ErrorGuardado):
        guardar_partida(tmp_path / 'malo.bin', p.motor, p.jugador, salas,
                        id_cripta='x', version_cripta='v', version_catalogo='c')


def test_ac_lt_010_historia_durante_ir_a_detiene_el_viaje_sin_tiempo(tmp_path):
    # FR-LT-006, AC-LT-010: escribir historia interrumpe el viaje como cualquier orden;
    # la consulta no consume tiempo y el viaje no se reanuda solo.
    from controlador.controlador import Controlador
    from datos_linea_tiempo import crear_partida, escribir_paquete
    from vista.vista_consola import VistaConsola

    partida, _ = crear_partida(escribir_paquete(tmp_path / "datos"), tmp_path / "cache")
    llamadas = []
    salida = []
    comandos = iter(["historia 0"])
    vista = VistaConsola(entrada=lambda _: next(comandos), salida=salida.append,
                         interrupcion=lambda: llamadas.append(1) or len(llamadas) >= 2)
    controlador = Controlador(partida, vista)
    # La antorcha explora la Galería sin visitarla; volver a la Entrada deja el viaje listo.
    for orden in ("recoger 1", "recoger 1", "recoger 1", "recoger 1", "sig", "sig", "sig",
                  "usar", "w", "s"):
        controlador.procesar(orden)
    llamadas.clear()
    controlador.procesar("ir a Galeria")
    # Un paso hasta el Pasillo; luego la interrupción y la consulta escrita.
    assert partida.jugador.sala_actual.sala_id == 2
    reloj, acciones = partida.motor.reloj, partida.acciones_ejecutadas
    assert "Viaje interrumpido por el jugador." in vista.bitacora.mensajes()
    assert any("Historia en t=0" in linea for linea in salida)
    assert (partida.motor.reloj, partida.acciones_ejecutadas) == (reloj, acciones)
    assert [o.texto for o in partida.linea_tiempo.ordenes][-1] == "ir n"
