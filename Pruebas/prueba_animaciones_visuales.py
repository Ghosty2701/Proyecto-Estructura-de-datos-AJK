"""FR-EV-006/007/008/009/011: hechos confirmados, sin estado gráfico persistido."""
from Pruebas.datos_graficos import partida_grafica
from Pruebas.datos_linea_tiempo import instantanea
from controlador.controlador import Controlador
from controlador.controlador_grafico import ReceptorValores, ControladorGrafico
from controlador.proyeccion_grafica import IntencionGrafica
from types import SimpleNamespace


def test_efectos_conservan_secuencia_consola_y_guardado(tmp_path):
    p, _ = partida_grafica(tmp_path/'visual')
    q, _ = partida_grafica(tmp_path/'consola')
    efectos = []
    visual = Controlador(p, ReceptorValores(), observar=efectos.append)
    consola = Controlador(q, ReceptorValores())
    derrotas = []
    for orden in ('recoger 5', 'w', 'usar', 'w', 'atacar 1', 'atacar 1', 'atacar 1'):
        efectos.clear(); visual.procesar(orden); consola.procesar(orden)
        assert instantanea(p) == instantanea(q)
        assert p.motor.azar.getstate() == q.motor.azar.getstate()
        assert tuple(p.__dict__) == tuple(q.__dict__)
        derrotas.extend(e for e in efectos if e.tipo == 'derrota')
    assert any(e.actor_id == 'g-1' and e.cantidad == 0 for e in derrotas)
    visual.procesar('abrir E')
    assert not visual.ultimo_resultado.aceptada
    p.ruta_guardado = str(tmp_path/'visual.bin')
    visual.procesar('guardar')
    assert visual.ultimo_resultado.aceptada  # callback no se guardó en Partida.


def test_dano_y_curacion_no_se_pierden_por_variacion_neta_cero(tmp_path):
    p, _ = partida_grafica(tmp_path)
    efectos = []
    ctl = Controlador(p, ReceptorValores(), observar=efectos.append)
    ctl.procesar('recoger 5'); ctl.procesar('w')
    assert any(e.tipo == 'dano' and e.actor_id == 'jugador' for e in efectos)
    efectos.clear(); ctl.procesar('usar')
    assert any(e.tipo == 'curacion' and e.actor_id == 'jugador' for e in efectos)


def test_hechos_separados_aunque_la_vida_final_sea_igual(tmp_path, monkeypatch):
    p, _ = partida_grafica(tmp_path)
    efectos = []
    p._iniciar_mensajes('Prueba de observación')
    inicial = p.jugador.vida
    cambios = iter([-7, 7])
    monkeypatch.setattr(p.motor, 'ejecutar_evento', lambda *args: setattr(p.jugador, 'vida', p.jugador.vida+next(cambios)))
    for _ in range(2):
        p._ejecutar_evento(SimpleNamespace(actor=None, tipo='pulso_veneno'), efectos.append)
    assert p.jugador.vida == inicial
    assert [(e.tipo, e.cantidad) for e in efectos] == [('dano', 7), ('curacion', 7)]


def test_worker_publica_efectos_solo_de_accion_aceptada(tmp_path):
    p, _ = partida_grafica(tmp_path)
    ctl = ControladorGrafico(lambda _: SimpleNamespace(partida=p, cerrar=lambda: None))
    try:
        ctl.iniciar(None); assert ctl.esperar(3)
        for op, arg in (('mover', 'N'), ('ayuda', None), ('abrir', 'O')):
            foto = ctl.respuesta.presentacion
            ctl.enviar(IntencionGrafica(foto.generacion, foto.revision, op, arg)); assert ctl.esperar(3)
            if op == 'mover':
                assert any(e.tipo == 'movimiento' for e in ctl.respuesta.efectos)
            else:
                assert ctl.respuesta.efectos == ()
    finally:
        ctl.cerrar(esperar=True)


def test_una_animacion_reloj_real_salto_y_modos_sin_turnos(tmp_path):
    from vista.pygame_ui.animaciones import Animaciones
    from controlador.efectos_visuales import EfectoVisual
    from controlador.controlador import ResultadoOperacion
    from controlador.controlador_grafico import RespuestaGrafica
    from dataclasses import replace
    from controlador.proyeccion_grafica import proyectar
    p, _ = partida_grafica(tmp_path)
    anterior = proyectar(p, 1, 0)
    siguiente = replace(anterior, revision=1)
    respuesta = RespuestaGrafica(ResultadoOperacion('accion', True), siguiente,
                                efectos=(EfectoVisual('dano', 'jugador', 1, 100, 7),))
    ahora = [0.0]
    animacion = Animaciones(reloj=lambda: ahora[0])
    for modo, duracion in (('normal', 0.5), ('reducida', 0.18), ('sin', 0)):
        animacion.modo = modo
        animacion.incorporar(respuesta, anterior)
        assert animacion.activa == bool(duracion)
        ahora[0] += duracion+0.001
        assert not animacion.activa
    animacion.modo = 'normal'; animacion.incorporar(respuesta, anterior)
    assert animacion.activa
    animacion.saltar(); assert not animacion.activa
    for _ in range(300):
        ahora[0] += 0.2
        assert not animacion.activa
    assert p.motor.reloj == 0 and p.acciones_ejecutadas == 0


def test_enemigo_que_sale_no_se_notifica_como_derrota(tmp_path, monkeypatch):
    p, _ = partida_grafica(tmp_path)
    ctl = Controlador(p, ReceptorValores())
    ctl.procesar('w'); ctl.procesar('w')
    enemigo = p._enemigos_presentes()[0]
    destino = p.jugador.sala_actual.salidas[0].destino
    monkeypatch.setattr(p.motor, 'ejecutar_evento', lambda *a: setattr(enemigo, 'sala_actual', destino))
    efectos = []
    p._ejecutar_evento(SimpleNamespace(actor=enemigo, tipo='accion'), efectos.append)
    assert [e.tipo for e in efectos] == ['salida']
    assert all(e.sala_id == p.jugador.sala_actual.sala_id for e in efectos)
