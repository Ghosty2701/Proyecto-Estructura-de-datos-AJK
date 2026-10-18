import math
import time
import uuid
import requests

URL_BASE = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"

class ErrorHTTP(Exception):
    pass


class PresupuestoAgotado(Exception):
    pass

class ClienteHTTP:
    def __init__(self, timeout=10, max_reintentos_429=3, *, reservar_imprevistos=False):
        # El id se genera una sola vez por ejecucion y se reutiliza en todas las solicitudes.
        self.headers = {"X-Cripta-Client-Id": str(uuid.uuid4())}
        self.timeout = timeout
        self.max_reintentos_429 = max_reintentos_429
        self.solicitudes_realizadas = 0
        self.solicitudes_normales = 0
        self.solicitudes_reintentos = 0
        self.reservar_imprevistos = reservar_imprevistos
        # Se conoce hasta leer los datos generales de la cripta.
        self.presupuesto_solicitudes = None

    def listar_criptas(self):
        return self._get("listar criptas", "/criptas")

    def datos_cripta(self, cripta_id):
        datos = self._get(f"datos generales de {cripta_id}", f"/criptas/{cripta_id}")
        self.presupuesto_solicitudes = datos["presupuesto_solicitudes"]
        return datos

    def pagina_esqueleto(self, cripta_id, pagina):
        return self._get(f"esqueleto de {cripta_id} pagina {pagina}", f"/criptas/{cripta_id}/salas", {"pagina": pagina})

    def contenido(self, cripta_id, salas):
        texto = ",".join(str(s) for s in salas)
        return self._get(f"contenido de {cripta_id} salas {texto}", f"/criptas/{cripta_id}/contenido", {"salas": texto})

    def catalogo(self, ids):
        texto = ",".join(ids)
        return self._get(f"catalogo ids {texto}", "/catalogo", {"ids": texto})

    def version_cripta(self, cripta_id):
        return self._get(f"version de {cripta_id}", f"/criptas/{cripta_id}/version")

    def version_catalogo(self):
        return self._get("version del catalogo", "/catalogo/version")

    @property
    def reserva_solicitudes(self):
        if not self.reservar_imprevistos or self.presupuesto_solicitudes is None:
            return 0
        return (self.presupuesto_solicitudes + 4) // 5

    @property
    def limite_normal(self):
        # Umbral de planificacion de la precarga, no un segundo presupuesto.
        if self.presupuesto_solicitudes is None:
            return None
        return self.presupuesto_solicitudes - self.reserva_solicitudes

    def _verificar_presupuesto(self, operacion, es_reintento=False):
        # Con presupuesto conocido, la solicitud presupuesto++ no se realiza.
        if (self.presupuesto_solicitudes is not None
                and self.solicitudes_realizadas >= self.presupuesto_solicitudes):
            raise PresupuestoAgotado(
                f"{operacion}: presupuesto agotado "
                f"({self.solicitudes_realizadas} de {self.presupuesto_solicitudes})")

    def _get(self, operacion, ruta, parametros=None):
        reintentos = 0

        while True:
            self._verificar_presupuesto(operacion, es_reintento=reintentos > 0)
            # Cada intento cuenta, tambien los reintentos por 429.
            self.solicitudes_realizadas += 1
            if reintentos:
                self.solicitudes_reintentos += 1
            else:
                self.solicitudes_normales += 1

            try:
                respuesta = requests.get(URL_BASE + ruta, headers=self.headers, params=parametros, timeout=self.timeout)
            except requests.exceptions.RequestException as error:
                raise ErrorHTTP(f"{operacion}: fallo de red ({error})") from error

            if respuesta.status_code == 200:
                try:
                    return respuesta.json()
                except ValueError as error:
                    raise ErrorHTTP(f"{operacion}: la respuesta no es un JSON") from error

            if respuesta.status_code == 429 and reintentos < self.max_reintentos_429:
                try:
                    espera = respuesta.json()["reintentar_en"]
                    if type(espera) not in (int, float) or not math.isfinite(espera) or espera < 0:
                        raise ValueError("la espera debe ser un numero finito no negativo")
                except (ValueError, KeyError, TypeError, OverflowError) as error:
                    raise ErrorHTTP(f"{operacion}: HTTP 429 sin 'reintentar_en' valido") from error
                try:
                    time.sleep(espera)
                except (ValueError, OverflowError) as error:
                    raise ErrorHTTP(f"{operacion}: HTTP 429 con 'reintentar_en' fuera de rango") from error
                reintentos += 1
                continue

            raise ErrorHTTP(f"{operacion}: HTTP {respuesta.status_code}")
