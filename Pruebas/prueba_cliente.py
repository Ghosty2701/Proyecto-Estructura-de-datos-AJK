import sys

import requests
import Disco_red.cliente_http as modulo
from Disco_red.cliente_http import ClienteHTTP, ErrorHTTP, PresupuestoAgotado


class RespuestaFalsa:
    def __init__(self, codigo, cuerpo=None):
        self.status_code = codigo
        self.cuerpo = cuerpo

    def json(self):
        return self.cuerpo


def comprobar(descripcion, condicion):
    print(("OK    " if condicion else "FALLO ") + descripcion)


if len(sys.argv) > 1 and sys.argv[1] == "real":
    c = ClienteHTTP()
    print(c.listar_criptas())
    print("solicitudes:", c.solicitudes_realizadas)
    sys.exit()

llamadas = []
esperas = []


def preparar(respuestas):
    # Respuestas en orden; una excepcion en la lista se lanza como fallo de red.
    llamadas.clear()
    esperas.clear()
    pendientes = list(respuestas)

    def get_falso(url, headers=None, params=None, timeout=None):
        llamadas.append((url, headers, params, timeout))
        actual = pendientes.pop(0)
        if isinstance(actual, Exception):
            raise actual
        return actual

    modulo.requests.get = get_falso
    modulo.time.sleep = esperas.append

# 1. Encabezado con el mismo id en todas las solicitudes, timeout y conteo.
preparar([RespuestaFalsa(200, {}), RespuestaFalsa(200, {})])
c = ClienteHTTP()
c.listar_criptas()
c.version_catalogo()
comprobar("mismo client id en ambas", llamadas[0][1] == llamadas[1][1] == c.headers)
comprobar("timeout enviado", llamadas[0][3] == 10)
comprobar("2 solicitudes contadas", c.solicitudes_realizadas == 2)

# 2. El presupuesto sale de los datos generales y la solicitud sobrante no se hace.
preparar([RespuestaFalsa(200, {"presupuesto_solicitudes": 2}), RespuestaFalsa(200, {})])
c = ClienteHTTP()
c.datos_cripta("cripta-01")
c.version_cripta("cripta-01")
try:
    c.version_cripta("cripta-01")
    comprobar("tercera solicitud rechazada", False)
except PresupuestoAgotado:
    comprobar("tercera solicitud rechazada", True)
comprobar("solo 2 llamadas reales", len(llamadas) == 2)

# 3. Un 429 espera reintentar_en y el reintento cuenta como solicitud.
preparar([RespuestaFalsa(429, {"reintentar_en": 12}), RespuestaFalsa(200, {"version": "ok"})])
c = ClienteHTTP()
comprobar("429 y luego exito", c.version_catalogo() == {"version": "ok"})
comprobar("espero 12 segundos", esperas == [12])
comprobar("el reintento cuenta (2)", c.solicitudes_realizadas == 2)

# 4. 429 persistente se detiene en el maximo de reintentos.
preparar([RespuestaFalsa(429, {"reintentar_en": 1})] * 3)
c = ClienteHTTP(max_reintentos_429=2)
try:
    c.version_catalogo()
    comprobar("429 persistente falla", False)
except ErrorHTTP as e:
    comprobar("429 persistente falla con contexto: " + str(e), "version del catalogo" in str(e))
comprobar("2 esperas y 3 solicitudes", len(esperas) == 2 and c.solicitudes_realizadas == 3)

# 5. Otros codigos y fallos de red se reportan con la operacion.
preparar([RespuestaFalsa(500)])
try:
    ClienteHTTP().version_cripta("cripta-99")
except ErrorHTTP as e:
    comprobar("HTTP 500 con contexto: " + str(e), "version de cripta-99" in str(e))

preparar([requests.exceptions.Timeout("lento")])
try:
    ClienteHTTP().listar_criptas()
except ErrorHTTP as e:
    comprobar("timeout con contexto: " + str(e), "listar criptas" in str(e))