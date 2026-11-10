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
