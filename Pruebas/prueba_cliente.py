import pytest
import requests

import adaptadores.cliente_http as modulo
from adaptadores.cliente_http import ClienteHTTP, ErrorHTTP, PresupuestoAgotado


class RespuestaFalsa:
    def __init__(self, codigo, cuerpo=None):
        self.status_code = codigo
        self.cuerpo = cuerpo

    def json(self):
        if isinstance(self.cuerpo, Exception):
            raise self.cuerpo
        return self.cuerpo


@pytest.fixture
def preparar(monkeypatch):
    def simular(respuestas):
        llamadas = []
        esperas = []
        pendientes = iter(respuestas)

        def get_falso(url, headers=None, params=None, timeout=None):
            llamadas.append((url, headers, params, timeout))
            respuesta = next(pendientes)
            if isinstance(respuesta, Exception):
                raise respuesta
            return respuesta

        monkeypatch.setattr(modulo.requests, "get", get_falso)
        monkeypatch.setattr(modulo.time, "sleep", esperas.append)
        return llamadas, esperas

    return simular


def test_encabezado_timeout_y_conteo(preparar):
    llamadas, _ = preparar([RespuestaFalsa(200, {}), RespuestaFalsa(200, {})])
    cliente = ClienteHTTP()
    cliente.listar_criptas()
    cliente.version_catalogo()
    assert llamadas[0][1] == llamadas[1][1] == cliente.headers
    assert llamadas[0][1]["X-Cripta-Client-Id"]
    assert llamadas[0][3] == 10
    assert cliente.solicitudes_realizadas == 2


@pytest.mark.parametrize("presupuesto,reserva,normal", [(9, 2, 7), (23, 5, 18), (42, 9, 33), (52, 11, 41)])
def test_reserva_redondea_hacia_arriba_el_veinte_por_ciento(presupuesto, reserva, normal):
    cliente = ClienteHTTP(reservar_imprevistos=True)
    cliente.presupuesto_solicitudes = presupuesto
    assert cliente.reserva_solicitudes == reserva
    assert cliente.limite_normal == normal


def test_reserva_bloquea_nuevas_consultas_pero_permite_reintento_429(preparar):
    llamadas, _ = preparar(
        [RespuestaFalsa(200, {"presupuesto_solicitudes": 9})]
        + [RespuestaFalsa(200, {})] * 5
        + [RespuestaFalsa(429, {"reintentar_en": 0}), RespuestaFalsa(200, {"version": "ok"})]
    )
    cliente = ClienteHTTP(reservar_imprevistos=True)
    cliente.datos_cripta("c1")
    for _ in range(5):
        cliente.version_catalogo()
    assert cliente.version_catalogo() == {"version": "ok"}
    assert cliente.solicitudes_normales == 7 and cliente.solicitudes_reintentos == 1
    assert cliente.solicitudes_realizadas == len(llamadas) == 8
    with pytest.raises(PresupuestoAgotado, match="se reservan 2"):
        cliente.version_catalogo()
    assert len(llamadas) == 8


def test_reintentos_no_pueden_superar_el_presupuesto_total_con_reserva(preparar):
    llamadas, _ = preparar(
        [RespuestaFalsa(200, {"presupuesto_solicitudes": 9})]
        + [RespuestaFalsa(200, {})] * 5
        + [RespuestaFalsa(429, {"reintentar_en": 0})] * 3
    )
    cliente = ClienteHTTP(reservar_imprevistos=True)
    cliente.datos_cripta("c1")
    for _ in range(5):
        cliente.version_catalogo()
    with pytest.raises(PresupuestoAgotado, match="presupuesto agotado"):
        cliente.version_catalogo()
    assert cliente.solicitudes_realizadas == len(llamadas) == 9
    assert cliente.solicitudes_normales == 7 and cliente.solicitudes_reintentos == 2


def test_presupuesto_viene_de_datos_y_no_se_excede(preparar):
    llamadas, _ = preparar([
        RespuestaFalsa(200, {"presupuesto_solicitudes": 2}), RespuestaFalsa(200, {}),
    ])
    cliente = ClienteHTTP()
    cliente.datos_cripta("cripta-01")
    cliente.version_cripta("cripta-01")
    with pytest.raises(PresupuestoAgotado, match="presupuesto agotado"):
        cliente.version_cripta("cripta-01")
    assert len(llamadas) == cliente.solicitudes_realizadas == 2


def test_reintento_429_espera_y_cuenta(preparar):
    llamadas, esperas = preparar([
        RespuestaFalsa(429, {"reintentar_en": 12}),
        RespuestaFalsa(200, {"version": "ok"}),
    ])
    cliente = ClienteHTTP()
    assert cliente.version_catalogo() == {"version": "ok"}
    assert esperas == [12]
    assert len(llamadas) == cliente.solicitudes_realizadas == 2


def test_429_persistente_respeta_maximo_de_reintentos(preparar):
    llamadas, esperas = preparar([RespuestaFalsa(429, {"reintentar_en": 1})] * 3)
    cliente = ClienteHTTP(max_reintentos_429=2)
    with pytest.raises(ErrorHTTP, match="version del catalogo: HTTP 429"):
        cliente.version_catalogo()
    assert esperas == [1, 1]
    assert len(llamadas) == cliente.solicitudes_realizadas == 3


def test_reintentar_tambien_respeta_el_presupuesto(preparar):
    llamadas, _ = preparar([
        RespuestaFalsa(200, {"presupuesto_solicitudes": 2}),
        RespuestaFalsa(429, {"reintentar_en": 1}),
    ])
    cliente = ClienteHTTP()
    cliente.datos_cripta("c1")
    with pytest.raises(PresupuestoAgotado):
        cliente.version_catalogo()
    assert len(llamadas) == cliente.solicitudes_realizadas == 2


@pytest.mark.parametrize("codigo", [400, 404, 500])
def test_errores_http_incluyen_operacion(preparar, codigo):
    preparar([RespuestaFalsa(codigo)])
    with pytest.raises(ErrorHTTP, match=f"version de cripta-99: HTTP {codigo}"):
        ClienteHTTP().version_cripta("cripta-99")


def test_fallo_de_red_tiene_contexto_y_cuenta(preparar):
    preparar([requests.exceptions.Timeout("lento")])
    cliente = ClienteHTTP()
    with pytest.raises(ErrorHTTP, match="listar criptas: fallo de red"):
        cliente.listar_criptas()
    assert cliente.solicitudes_realizadas == 1


@pytest.mark.parametrize("codigo", [200, 429])
def test_json_invalido_tiene_contexto(preparar, codigo):
    preparar([RespuestaFalsa(codigo, ValueError("no es JSON"))])
    with pytest.raises(ErrorHTTP, match="version del catalogo"):
        ClienteHTTP().version_catalogo()


@pytest.mark.parametrize("espera", [-1, "12", None, True, float("nan"), float("inf"), 10**400])
def test_espera_429_invalida_no_duerme_ni_reintenta(preparar, espera):
    llamadas, esperas = preparar([RespuestaFalsa(429, {"reintentar_en": espera})])
    with pytest.raises(ErrorHTTP, match="version del catalogo: HTTP 429 sin 'reintentar_en' valido"):
        ClienteHTTP().version_catalogo()
    assert len(llamadas) == 1
    assert esperas == []


def test_espera_429_ausente(preparar):
    preparar([RespuestaFalsa(429, {})])
    with pytest.raises(ErrorHTTP, match="reintentar_en"):
        ClienteHTTP().version_catalogo()


def test_espera_429_fuera_del_rango_del_sistema(preparar, monkeypatch):
    preparar([RespuestaFalsa(429, {"reintentar_en": 1e30})])

    def fuera_de_rango(segundos):
        raise OverflowError("demasiado grande")

    monkeypatch.setattr(modulo.time, "sleep", fuera_de_rango)
    with pytest.raises(ErrorHTTP, match="version del catalogo: HTTP 429.*fuera de rango"):
        ClienteHTTP().version_catalogo()
