"""Línea de tiempo integrada con la partida real.

T008: re-simulación sin red (FR-LT-006/013).
T011: equivalencia del estado reconstruido con el observado en vivo
(FR-LT-003/013/014, SC-LT-002; AC-LT-001/003/004/005/021).
"""
import pytest

from adaptadores.servicio_cripta import ServicioCripta
from controlador.cargar_partida import ErrorReconstruccion, PreparadorConsulta
from adaptadores.cache_catalogo import ArbolAVL
from datos_linea_tiempo import (
    crear_partida, escribir_paquete, instantanea, instantes_intermedios, jugar,
)


@pytest.fixture
def paquete(tmp_path):
    return escribir_paquete(tmp_path / "datos")


def _sin_red(cargador):
    """Cualquier solicitud posterior falla: la consulta debe usar solo lo descargado."""
    def prohibida(*argumentos, **opciones):
        raise AssertionError("la línea de tiempo no debe pedir datos a la red")

    fuente = cargador.servicio.fuente
    for nombre in ("listar_criptas", "datos_cripta", "pagina_esqueleto", "contenido", "catalogo",
                   "version_cripta", "version_catalogo", "ubicacion_llaves"):
        assert hasattr(fuente, nombre)
        setattr(fuente, nombre, prohibida)


def test_historia_libera_grafo_temporal_sin_esperar_gc(paquete, tmp_path, monkeypatch):
    # FR-LT-006, PR-LT-001/003: el resumen no debe conservar la simulación temporal.
    import gc
    import weakref

    partida, cargador = crear_partida(paquete, tmp_path / 'cache', checkpoint_cada=3)
    jugar(partida, ['recoger 1', 'esperar', 'esperar'])
    crear = cargador.copia_de_trabajo
    observadas = []

    def observar(punto):
        copia = crear(punto)
        observadas.append(weakref.ref(copia))
        return copia

    monkeypatch.setattr(cargador, 'copia_de_trabajo', observar)
    habilitado = gc.isenabled()
    gc.disable()
    try:
        antes = instantanea(partida)
        resumen = partida.historia(('k', 2))
        assert observadas and observadas[0]() is None
        assert resumen.reloj >= 0 and instantanea(partida) == antes
    finally:
        if habilitado:
            gc.enable()
        gc.collect()


@pytest.mark.parametrize("k", [1, 3, 10])
def test_t011_equivalencia_en_decisiones_e_instantes_intermedios(paquete, tmp_path, k):
    # FR-LT-003/013/014, SC-LT-002: tres valores de K, decisiones y eventos intermedios.
    partida, cargador = crear_partida(paquete, tmp_path / "cache", checkpoint_cada=k)
    grabacion = jugar(partida)
    _sin_red(cargador)
    linea = partida.linea_tiempo
    assert linea.cantidad_acciones == len(grabacion.antes_de_accion) >= 20
    assert any(orden.tipo == "pergamino" for orden in linea.ordenes)
    reloj = partida.motor.reloj
    for numero, decision, foto in grabacion.antes_de_accion:
        # AC-LT-001/002/003: #k y el instante de decisión dan el estado antes de decidir.
        assert instantanea(partida.reconstruir(linea.objetivo_por_k(numero))) == foto
        assert instantanea(partida.reconstruir(linea.objetivo_por_t(decision, reloj))) == foto
    intermedios = instantes_intermedios(grabacion)
    assert len(intermedios) >= 10
    for t, foto in intermedios:
        if t == reloj:
            continue
        # AC-LT-004/005: eventos <= t, ninguno posterior. El contador de acciones ya
        # incluye la acción en curso: se compara el resto del estado observable.
        copia = partida.reconstruir(linea.objetivo_por_t(t, reloj))
        assert copia.motor.reloj == t
        assert instantanea(copia)[:-1] == foto[:-1]


def test_t011_reconstruir_no_altera_la_partida(paquete, tmp_path):
    partida, cargador = crear_partida(paquete, tmp_path / "cache", checkpoint_cada=4)
    jugar(partida)
    antes = (instantanea(partida), partida.motor.azar.getstate(),
             len(partida.motor.historial.acciones), len(partida.linea_tiempo.ordenes))
    for numero in range(1, partida.linea_tiempo.cantidad_acciones + 1):
        partida.reconstruir(partida.linea_tiempo.objetivo_por_k(numero))
    despues = (instantanea(partida), partida.motor.azar.getstate(),
               len(partida.motor.historial.acciones), len(partida.linea_tiempo.ordenes))
    assert despues == antes


def test_t008_reconstruir_sin_red_ni_cambios_en_cache(paquete, tmp_path):
    # FR-LT-006, constitución V: ni solicitudes ni cambios en la caché viva.
    partida, cargador = crear_partida(paquete, tmp_path / "cache", checkpoint_cada=50)
    jugar(partida)
    _sin_red(cargador)
    fuente = cargador.servicio.fuente
    cache = cargador.servicio.cache
    lru = []
    nodo = cache.lista.frente
    while nodo is not None:
        lru.append(nodo.id_ficha)
        nodo = nodo.siguiente
    estado_cache = (cache.aciertos, cache.fallos, cache.lecturas_disco,
                    getattr(fuente, "solicitudes_realizadas", None))
    # Con K=50 el único punto es el inicial: se re-simula toda la partida.
    copia = partida.reconstruir(partida.linea_tiempo.objetivo_por_k(partida.linea_tiempo.cantidad_acciones))
    assert copia.jugador.sala_actual.sala_id in (2, 3, 4, 5)
    nodo, despues = cache.lista.frente, []
    while nodo is not None:
        despues.append(nodo.id_ficha)
        nodo = nodo.siguiente
    assert despues == lru
    assert (cache.aciertos, cache.fallos, cache.lecturas_disco,
            getattr(fuente, "solicitudes_realizadas", None)) == estado_cache


def test_t008_contenido_ausente_falla_con_mensaje(paquete, tmp_path):
    partida, cargador = crear_partida(paquete, tmp_path / "cache")
    servicio = cargador.servicio
    vacio = ServicioCripta.__new__(ServicioCripta)
    vacio.contenido = ArbolAVL()
    vacio.cache = servicio.cache
    sala = next(s for s in cargador.salas_ordenadas() if not s.contenido_cargado)
    with pytest.raises(ErrorReconstruccion, match="sin red"):
        PreparadorConsulta(vacio, partida).preparar_sala(sala)
    assert not sala.contenido_cargado


# --- T016: aceptación de US1 por controlador y vista (AC-LT-001 a 006) ---

from controlador.controlador import AccionInvalida, Controlador
from vista.vista_consola import VistaConsola


def _coincide(resumen, foto):
    """El resumen contiene lo mismo que el estado observado en vivo (FR-LT-002)."""
    reloj, sala, vida, vida_max, ataque, defensa, efectos, *_ = foto
    assert (resumen.reloj, resumen.sala_id, resumen.vida, resumen.vida_max,
            resumen.ataque, resumen.defensa, tuple(resumen.efectos)) == (
            reloj, sala, vida, vida_max, ataque, defensa, efectos)
    assert repr(resumen.mapa) == foto[12]


def _consola(partida):
    salida = []
    return Controlador(partida, VistaConsola(salida=salida.append)), salida


def test_ac001_002_003_historia_por_instante_y_numero(paquete, tmp_path):
    # FR-LT-001/002/003/004: resumen completo del estado vivido en ese momento.
    partida, _ = crear_partida(paquete, tmp_path / "cache", checkpoint_cada=5)
    grabacion = jugar(partida)
    for numero, decision, foto in grabacion.antes_de_accion:
        por_k = partida.historia(("k", numero))
        assert por_k.titulo == f"antes de la acción #{numero}"
        _coincide(por_k, foto)
        por_t = partida.historia(("t", decision))   # AC-LT-003: antes de decidir
        _coincide(por_t, foto)
        assert por_t.titulo == f"antes de la acción #{numero}"
    actual = partida.historia(("k", partida.linea_tiempo.cantidad_acciones + 1))
    assert actual.titulo.startswith("estado actual")
    _coincide(actual, instantanea(partida))


def test_ac001_inventario_y_enemigos_del_resumen(paquete, tmp_path):
    # FR-LT-002: inventario en orden real con cursor y equipo; enemigos vivos con estado.
    partida, _ = crear_partida(paquete, tmp_path / "cache", checkpoint_cada=3)
    grabacion = jugar(partida)
    for numero, _, foto in grabacion.antes_de_accion:
        resumen = partida.historia(("k", numero))
        ids_nombres = {"pergamino": "Pergamino", "daga": "Daga", "antorcha": "Antorcha", "pocion": "Pocion"}
        assert [nombre for nombre, _, _ in resumen.inventario] == [ids_nombres[i] for i in foto[7]]
        seleccionados = [nombre for nombre, _, elegido in resumen.inventario if elegido]
        assert seleccionados == ([ids_nombres[foto[8]]] if foto[8] else [])
        assert [(vida, vida_max, dormido) for _, vida, vida_max, dormido in resumen.enemigos] == [
            (vida, vida_max, not activo) for _, vida, vida_max, activo in foto[11]]
    con_cazador = [r for r in (partida.historia(("k", n)) for n, _, _ in grabacion.antes_de_accion)
                   if any("[cazador]" in nombre for nombre, *_ in r.enemigos)]
    assert con_cazador, "la partida sintética debe mostrar al cazador en algún instante"


def test_ac004_005_instantes_intermedios_por_consola(paquete, tmp_path):
    # FR-LT-003: eventos <= t, ninguno posterior; título indica la acción en curso.
    partida, _ = crear_partida(paquete, tmp_path / "cache", checkpoint_cada=4)
    grabacion = jugar(partida)
    t, foto = instantes_intermedios(grabacion)[3]
    resumen = partida.historia(("t", t))
    assert resumen.titulo.startswith("durante la acción #")
    _coincide(resumen, foto)


def test_ac001_historia_0_y_1_muestran_el_estado_inicial(paquete, tmp_path):
    # Casos límite: sala inicial explorada desde el instante 0 (§3.3).
    partida, _ = crear_partida(paquete, tmp_path / "cache")
    jugar(partida)
    for argumento in (("t", 0), ("k", 1)):
        resumen = partida.historia(argumento)
        assert (resumen.reloj, resumen.sala_id, resumen.vida) == (0, 1, 200)
        assert resumen.inventario == []
        explorada = [sala for sala in resumen.mapa if sala[1] == 2]
        assert [sala[0] for sala in explorada] == [1]


def test_partida_sin_acciones_admite_0_y_1_y_rechaza_2(paquete, tmp_path):
    partida, _ = crear_partida(paquete, tmp_path / "cache")
    assert partida.historia(("t", 0)).titulo.startswith("estado actual")
    assert partida.historia(("k", 1)).titulo.startswith("estado actual")
    with pytest.raises(AccionInvalida, match="#k"):
        partida.historia(("k", 2))


def test_ac006_mapa_conocido_de_entonces(paquete, tmp_path):
    # FR-LT-005: el mapa histórico no revela salas exploradas después.
    partida, _ = crear_partida(paquete, tmp_path / "cache", checkpoint_cada=2)
    jugar(partida)
    exploradas_ahora = [s[0] for s in partida.mapa() if s[1] == 2]
    exploradas_k3 = [s[0] for s in partida.historia(("k", 3)).mapa if s[1] == 2]
    assert len(exploradas_k3) < len(exploradas_ahora)
    assert set(exploradas_k3) <= set(exploradas_ahora)


def test_t015_consola_muestra_resumen_y_rechazos(paquete, tmp_path):
    # FR-LT-001/002/007: presentación con el formato del contrato; rechazo con mensaje.
    partida, _ = crear_partida(paquete, tmp_path / "cache")
    controlador, salida = _consola(partida)
    for texto in ("recoger 1", "w", "esperar"):
        controlador.procesar(texto)
    salida.clear()
    controlador.procesar("historia #2")
    texto = "\n".join(salida)
    assert "Historia en t=" in texto and "(antes de la acción #2)" in texto
    assert "Sala 1 - Entrada" in texto and "Inventario (1/6): > Pergamino" in texto
    assert "Enemigos en la sala: ninguno" in texto and "Mapa conocido:" in texto
    controlador.procesar("historia 999999")
    controlador.procesar("historia #x")
    mensajes = controlador.vista.bitacora.mensajes()
    assert any("posterior al reloj actual" in m for m in mensajes)
    assert any(m.startswith("Uso: historia") for m in mensajes)


# --- T017: consultar sin alterar nada (US2; FR-LT-006/007, SC-LT-003) ---

from adaptadores.bitacora_partida import EscritorBitacora, leer_bitacora
from datos_linea_tiempo import CRIPTA, SEMILLA, ORDENES


def _huella(partida, cargador):
    """Todo lo que una consulta no puede cambiar."""
    motor = partida.motor
    linea = partida.linea_tiempo
    cache = cargador.servicio.cache
    lru, nodo = [], cache.lista.frente
    while nodo is not None:
        lru.append(nodo.id_ficha)
        nodo = nodo.siguiente
    return (
        instantanea(partida), motor.reloj, motor.azar.getstate(),
        [(a.reloj_anterior, len(a.cambios)) for a in motor.historial.acciones],
        [(o.texto, o.tipo) for o in linea.ordenes], [(a.reloj, a.posicion) for a in linea.acciones],
        [(p.posicion, p.acciones) for p in linea.puntos], linea.acciones_en_tramo,
        tuple(lru), cache.aciertos, cache.fallos, cache.lecturas_disco,
        cargador.servicio.fuente.solicitudes_realizadas,
    )


CONSULTAS = ["historia 0", "historia #1", "historia #5", "historia 333", "historia 999999",
             "historia #999", "historia", "historia -4", "historia #0", "HISTORIA #3"]


def test_ac007_008_009_consultas_no_cambian_nada_ni_el_log(paquete, tmp_path):
    partida, cargador = crear_partida(paquete, tmp_path / "cache", checkpoint_cada=3)
    ruta = tmp_path / "partida.log"
    with EscritorBitacora(ruta, CRIPTA, "v1", "cat-lt", SEMILLA) as escritor:
        controlador = Controlador(partida, VistaConsola(salida=lambda texto: None),
                                  escritor.registrar_accion)
        jugar(partida, ORDENES[:20], controlador=controlador)
        antes = _huella(partida, cargador)
        for consulta in CONSULTAS:
            controlador.procesar(consulta)
        assert _huella(partida, cargador) == antes
        jugar(partida, ORDENES[20:], controlador=controlador)
    assert not any("historia" in accion for accion in leer_bitacora(ruta)[1])


def test_sc003_continuacion_identica_a_una_partida_sin_consultas(paquete, tmp_path):
    con, cargador_con = crear_partida(paquete, tmp_path / "cache-con", checkpoint_cada=2)
    sin, cargador_sin = crear_partida(paquete, tmp_path / "cache-sin", checkpoint_cada=2)
    ctl_con = Controlador(con, VistaConsola(salida=lambda texto: None))
    ctl_sin = Controlador(sin, VistaConsola(salida=lambda texto: None))
    for numero, texto in enumerate(ORDENES):
        if numero % 3 == 0:
            for consulta in CONSULTAS:
                ctl_con.procesar(consulta)
        ctl_con.procesar(texto)
        ctl_sin.procesar(texto)
    assert _huella(con, cargador_con)[:-1] == _huella(sin, cargador_sin)[:-1]
    assert cargador_con.servicio.fuente.solicitudes_realizadas == cargador_sin.servicio.fuente.solicitudes_realizadas


# --- T019: coherencia con el pergamino (US3; FR-LT-004/007/008/009/014) ---

ORDENES_PERGAMINO = [
    "recoger 1", "recoger 1",       # k1 pA, k2 pB
    "retroceder",                   # revierte k2: pB queda (no se deshace) y se consume pA
    "recoger 1", "recoger 1",       # k2 pC, k3 pD
    "w", "esperar",                 # k4, k5
    "retroceder", "retroceder",     # dos seguidos: revierte k5 y k4
    "recoger 1", "w", "esperar",    # k4 daga, k5, k6
]


@pytest.fixture
def paquete_pergaminos(tmp_path):
    return escribir_paquete(tmp_path / "datos-p",
                            objetos_entrada=["pergamino", "pergamino", "pergamino", "pergamino", "daga"])


@pytest.mark.parametrize("k", [1, 2, 3])
def test_ac011_012_014_historia_vigente_tras_pergaminos(paquete_pergaminos, tmp_path, k):
    # Con K=1 hay un punto creado justo antes de cada pergamino; nunca se invalida.
    partida, _ = crear_partida(paquete_pergaminos, tmp_path / f"cache{k}", checkpoint_cada=k)
    grabacion = jugar(partida, ORDENES_PERGAMINO)
    linea = partida.linea_tiempo
    assert [o.tipo for o in linea.ordenes].count("pergamino") == 3
    assert linea.cantidad_acciones == partida.acciones_ejecutadas == 6 == len(grabacion.antes_de_accion)
    for numero, decision, foto in grabacion.antes_de_accion:
        assert instantanea(partida.reconstruir(linea.objetivo_por_k(numero))) == foto
        assert instantanea(partida.reconstruir(linea.objetivo_por_t(decision, partida.motor.reloj))) == foto
    for t, foto in instantes_intermedios(grabacion):
        if t < partida.motor.reloj:
            assert instantanea(partida.reconstruir(linea.objetivo_por_t(t, partida.motor.reloj)))[:-1] == foto[:-1]


def test_ac011_efectos_que_no_se_deshacen_aparecen_solo_despues(paquete_pergaminos, tmp_path):
    # P1: el pergamino consumido no vuelve y el recogido en la acción revertida se queda.
    partida, _ = crear_partida(paquete_pergaminos, tmp_path / "cache", checkpoint_cada=1)
    jugar(partida, ORDENES_PERGAMINO)
    nombres = lambda k: [nombre for nombre, _, _ in partida.historia(("k", k)).inventario]
    assert nombres(1) == []
    assert nombres(2) == ["Pergamino"]                       # pB conservado, pA consumido
    assert nombres(4) == ["Pergamino"]                       # tras dos pergaminos más: solo pD
    assert nombres(5) == ["Pergamino", "Daga"]


def test_ac011_012_rechazo_posterior_y_numeracion_tras_pergamino(paquete_pergaminos, tmp_path):
    partida, _ = crear_partida(paquete_pergaminos, tmp_path / "cache", checkpoint_cada=2)
    controlador = Controlador(partida, VistaConsola(salida=lambda texto: None))
    for orden in ORDENES_PERGAMINO[:9]:
        controlador.procesar(orden)
    restaurado = partida.motor.reloj
    assert partida.linea_tiempo.cantidad_acciones == 3        # el pergamino no ocupa un k
    with pytest.raises(AccionInvalida, match="posterior"):
        partida.historia(("t", restaurado + 1))
    with pytest.raises(AccionInvalida, match="#k"):
        partida.historia(("k", 5))
    assert partida.historia(("k", 4)).titulo.startswith("estado actual")
    controlador.procesar("recoger 1")
    assert partida.historia(("k", 4)).titulo == "antes de la acción #4"
    assert partida.historia(("k", 5)).titulo.startswith("estado actual")


def test_pr004_recorte_trabaja_solo_sobre_lo_revertido(paquete_pergaminos, tmp_path):
    # PR-LT-004: el recorte depende de las acciones revertidas, no de la historia.
    partida, _ = crear_partida(paquete_pergaminos, tmp_path / "cache", checkpoint_cada=50)
    controlador = Controlador(partida, VistaConsola(salida=lambda texto: None))
    controlador.procesar("recoger 1")
    for _ in range(300):
        controlador.procesar("esperar")
    trabajo = partida.linea_tiempo.trabajo_recorte
    controlador.procesar("retroceder")
    assert partida.linea_tiempo.trabajo_recorte - trabajo == 1
    assert partida.linea_tiempo.cantidad_acciones == 300


# --- T024: configurar los puntos de control (US5; FR-LT-012/013/014, PR-LT-002) ---

from modelo.linea_tiempo import ACCION


def _acciones_resimuladas(linea, objetivo):
    posicion, limite = objetivo
    punto = linea.punto_para(posicion if limite is None else posicion - 1)
    return sum(1 for orden in linea.ordenes_entre(punto.posicion, posicion) if orden.tipo == ACCION)


@pytest.mark.parametrize("k", [1, 2, 5, 25])
def test_ac019_020_un_punto_cada_k_y_consultas_acotadas(paquete_pergaminos, tmp_path, k):
    partida, _ = crear_partida(paquete_pergaminos, tmp_path / f"cache{k}", checkpoint_cada=k)
    grabacion = jugar(partida, ORDENES_PERGAMINO + ["s", "esperar", "w", "esperar", "esperar"])
    linea = partida.linea_tiempo
    puntos = linea.puntos
    for anterior, siguiente in zip(puntos, puntos[1:]):
        # AC-LT-019: exactamente K acciones ejecutadas entre puntos (las revertidas cuentan).
        assert linea.acciones_ejecutadas_entre(anterior.posicion, siguiente.posicion) == k
    reloj = partida.motor.reloj
    objetivos = [linea.objetivo_por_k(n) for n in range(1, linea.cantidad_acciones + 1)]
    objetivos += [linea.objetivo_por_t(t, reloj) for t, _ in grabacion.tras_evento if t < reloj]
    # AC-LT-020: ninguna consulta re-simula más de K acciones.
    assert max(_acciones_resimuladas(linea, o) for o in objetivos if o is not None) <= k


def test_ac021_resumenes_identicos_con_distintos_k(paquete_pergaminos, tmp_path):
    resumenes = []
    for k in (1, 2, 5, 25):
        partida, _ = crear_partida(paquete_pergaminos, tmp_path / f"cache{k}", checkpoint_cada=k)
        jugar(partida, ORDENES_PERGAMINO)
        resumenes.append([partida.historia(("k", n)) for n in range(1, partida.linea_tiempo.cantidad_acciones + 2)]
                         + [partida.historia(("t", t)) for t in range(0, partida.motor.reloj, 37)])
    assert all(r == resumenes[0] for r in resumenes)


@pytest.mark.parametrize("valor", ["0", "-2", "abc", "2.5", "+3"])
def test_ac022_checkpoint_cada_invalido_es_error_de_uso(valor, capsys):
    import main as aplicacion

    with pytest.raises(SystemExit) as salida:
        aplicacion.main(["--cripta", "lt", "--checkpoint-cada", valor])
    assert salida.value.code == 2
    assert "--checkpoint-cada" in capsys.readouterr().err


@pytest.mark.parametrize("modo", [["--listar"], ["--ver-puntajes"], ["--verificar", "lt"]])
def test_ac022_checkpoint_cada_solo_con_modos_de_partida(modo, capsys):
    import main as aplicacion

    with pytest.raises(SystemExit) as salida:
        aplicacion.main(modo + ["--checkpoint-cada", "3"])
    assert salida.value.code == 2


def test_ac019_022_main_aplica_k_y_el_valor_por_defecto(paquete, tmp_path, monkeypatch):
    import main as aplicacion
    from controlador.cargar_partida import CargadorPartida
    from datos_linea_tiempo import CRIPTA, SEMILLA
    from modelo.linea_tiempo import K_POR_DEFECTO

    assert K_POR_DEFECTO == 10  # D-LT-07 elegida por Juan; FR-LT-012.

    usados = []
    original = CargadorPartida.iniciar_linea
    monkeypatch.setattr(CargadorPartida, "iniciar_linea",
                        lambda self, partida, k: (usados.append(k), original(self, partida, k))[1])
    monkeypatch.setattr(aplicacion, "VistaConsola",
                        lambda: VistaConsola(entrada=lambda _: "salir", salida=lambda texto: None))
    base = ["--offline", str(paquete), "--cache-dir", str(tmp_path / "cache"), "--forzar",
            "--puntajes", str(tmp_path / "p.json")]
    assert aplicacion.main(["--cripta", CRIPTA, "--checkpoint-cada", "7"] + base) == 0
    assert aplicacion.main(["--cripta", CRIPTA] + base) == 0
    ruta = tmp_path / "x.log"
    with EscritorBitacora(ruta, CRIPTA, "v1", "cat-lt", SEMILLA) as escritor:
        escritor.registrar_accion("esperar")
    assert aplicacion.main(["--replay", str(ruta), "--checkpoint-cada", "4", "--offline", str(paquete),
                            "--cache-dir", str(tmp_path / "cache")]) == 0
    assert usados == [7, K_POR_DEFECTO, 4]
