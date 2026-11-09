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
