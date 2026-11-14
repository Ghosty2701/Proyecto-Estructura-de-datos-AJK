"""FR-IG-005/006/007: observación presencial y privacidad del recuerdo."""
from Pruebas.datos_graficos import partida_grafica
from controlador.memoria_visual import MemoriaVisual
from controlador.controlador_grafico import ControladorGrafico
from controlador.proyeccion_grafica import IntencionGrafica, proyectar
from types import SimpleNamespace


def test_observacion_vacia_distinta_de_ausente_y_sin_lectura_remota(tmp_path):
    p, _ = partida_grafica(tmp_path)
    memoria = MemoriaVisual(p)
    assert memoria.obtener(1).grupos == ()
    assert memoria.obtener(2) is None and memoria.obtener(3) is None
    assert proyectar(p, 1, 0, memoria=memoria).salas[1].recuerdo is None


def test_recuerdo_remoto_permanece_hasta_reentrar(tmp_path):
    from controlador.controlador import Controlador
    from controlador.controlador_grafico import ReceptorValores
    p, _ = partida_grafica(tmp_path)
    memoria = MemoriaVisual(p)
    ctl = Controlador(p, ReceptorValores())
    for texto in ('w', 'w'):
        ctl.procesar(texto); memoria.observar(p)
    observado = memoria.obtener(3)
    assert observado.grupos == (('guardian', 'Guardian', 1),)
    ctl.procesar('s'); memoria.observar(p)
    guardian = next(e for e in p.enemigos if e.actor_id == 'g-1')
    guardian.vida = 0
    for _ in range(5): proyectar(p, 1, 3, memoria=memoria)
    assert memoria.obtener(3) == observado
    ctl.procesar('w'); memoria.observar(p)
    assert memoria.obtener(3).grupos == ()


def test_coordinador_observa_solo_acciones_aceptadas(tmp_path):
    p, _ = partida_grafica(tmp_path)
    ctl = ControladorGrafico(lambda _: SimpleNamespace(partida=p, registrar_accion=None, cerrar=lambda: None))
    try:
        ctl.iniciar(None); assert ctl.esperar(3)
        inicial = ctl.respuesta.presentacion
        assert inicial.salas[0].recuerdo.grupos == ()
        for operacion, argumento in (('mover', 'N'), ('mover', 'N'), ('mover', 'S')):
            foto = ctl.respuesta.presentacion
            ctl.enviar(IntencionGrafica(foto.generacion, foto.revision, operacion, argumento))
            assert ctl.esperar(3)
        foto = ctl.respuesta.presentacion
        recuerdo = next(s.recuerdo for s in foto.salas if s.sala_id == 3)
        assert recuerdo.grupos == (('guardian', 'Guardian', 1),)
        for operacion in ('ayuda', 'esperar'):
            foto = ctl.respuesta.presentacion
            ctl.enviar(IntencionGrafica(foto.generacion, foto.revision, operacion)); assert ctl.esperar(3)
            assert next(s.recuerdo for s in ctl.respuesta.presentacion.salas if s.sala_id == 3) == recuerdo
    finally:
        ctl.cerrar(esperar=True)


def test_antorcha_revela_mapa_sin_observar_enemigos_remotos(tmp_path):
    from controlador.controlador import Controlador
    from controlador.controlador_grafico import ReceptorValores
    p, _ = partida_grafica(tmp_path)
    memoria = MemoriaVisual(p)
    ctl = Controlador(p, ReceptorValores())
    for orden in ('recoger 4', 'usar', 'w'):
        ctl.procesar(orden)
        assert ctl.ultimo_resultado.aceptada
        memoria.observar(p)
    foto = proyectar(p, 1, 3, memoria=memoria)
    remota = next(s for s in foto.salas if s.sala_id == 3)
    assert remota.estado == 2 and remota.recuerdo is None
    assert foto.enemigos == ()


def test_cinco_deltas_pergamino_usar_rechazo_y_rama_nueva(tmp_path):
    p, _ = partida_grafica(tmp_path, cinco=True)
    from controlador.controlador import Controlador
    from controlador.controlador_grafico import ReceptorValores
    base = Controlador(p, ReceptorValores())
    for _ in range(5): base.procesar('recoger 1')
    ctl = ControladorGrafico(lambda _: SimpleNamespace(partida=p, cerrar=lambda: None))
    def orden(op):
        foto = ctl.respuesta.presentacion
        ctl.enviar(IntencionGrafica(foto.generacion, foto.revision, op)); assert ctl.esperar(3)
        return ctl.respuesta
    try:
        ctl.iniciar(None); assert ctl.esperar(3)
        memoria = ctl._memoria
        for _ in range(5): orden('esperar')
        assert len(memoria.deltas) == 5
        anterior = memoria.deltas[-1]
        orden('usar')
        assert len(memoria.deltas) == 4
        orden('esperar')
        assert len(memoria.deltas) == 5 and memoria.deltas[-1].posicion != anterior.posicion
        assert memoria.deltas[-1].reloj_despues == anterior.reloj_despues
        for _ in range(4): orden('retroceder')
        assert len(memoria.deltas) == 1
        antes = tuple(memoria.observaciones), tuple(memoria.deltas)
        respuesta = orden('retroceder')
        assert not respuesta.resultado.aceptada
        assert (tuple(memoria.observaciones), tuple(memoria.deltas)) == antes
    finally:
        ctl.cerrar(esperar=True)


def test_retroceso_cruza_origen_descarta_recuerdos_inciertos(tmp_path):
    p, _ = partida_grafica(tmp_path)
    from controlador.controlador import Controlador
    from controlador.controlador_grafico import ReceptorValores
    base = Controlador(p, ReceptorValores())
    for texto in ('recoger 1', 'w', 'w', 's'): base.procesar(texto)
    ctl = ControladorGrafico(lambda _: SimpleNamespace(partida=p, cerrar=lambda: None))
    try:
        ctl.iniciar(None); assert ctl.esperar(3)
        memoria = ctl._memoria
        assert memoria.obtener(2) is not None and memoria.obtener(3) is None
        foto = ctl.respuesta.presentacion
        ctl.enviar(IntencionGrafica(foto.generacion, foto.revision, 'retroceder')); assert ctl.esperar(3)
        assert memoria.obtener(2) is None and memoria.obtener(3).grupos
        assert memoria.deltas == []
        assert memoria.origen[1] == p.acciones_ejecutadas
    finally:
        ctl.cerrar(esperar=True)
