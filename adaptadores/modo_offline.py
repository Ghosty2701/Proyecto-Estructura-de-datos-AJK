import json
import os

from adaptadores.fuente_datos import FuenteDatos

class ErrorOffline(Exception):
    # Falta un archivo del paquete; indica la operacion y la ruta buscada.
    pass

class ModoOffline(FuenteDatos):
    def __init__(self, carpeta="datos_offline"):
        self.carpeta = carpeta
        # Leer de disco es una solicitud de red
        self.solicitudes_realizadas = 0
        self.presupuesto_solicitudes = None

    def listar_criptas(self):
        return self._leer("listar criptas", "criptas.json")

    def datos_cripta(self, cripta_id):
        datos = self._leer(f"datos generales de {cripta_id}", "criptas", cripta_id, "general.json")
        self.presupuesto_solicitudes = datos["presupuesto_solicitudes"]
        return datos

    def pagina_esqueleto(self, cripta_id, pagina):
        return self._leer(f"esqueleto de {cripta_id} pagina {pagina}","criptas", cripta_id, f"salas_{pagina}.json")

    def contenido(self, cripta_id, salas):
        # Arma la misma respuesta de un lote juntando el contenido de cada sala pedida.
        entradas = []
        for sala in salas:
            entradas.append(self._leer(f"contenido de {cripta_id} sala {sala}","criptas", cripta_id, "contenido", f"{sala}.json"))
        return {"contenido": entradas}

    def catalogo(self, ids):
        # Arma la misma respuesta de un lote juntando la ficha de cada id pedido.
        entidades = []
        for id_ficha in ids:
            entidades.append(self._leer(f"catalogo id {id_ficha}", "catalogo", f"{id_ficha}.json"))
        return {"entidades": entidades}

    def version_cripta(self, cripta_id):
        return self._leer(f"version de {cripta_id}", "criptas", cripta_id, "version.json")

    def version_catalogo(self):
        return self._leer("version del catalogo", "catalogo_version.json")

    def _leer(self, operacion, *partes):
        ruta = os.path.join(self.carpeta, *partes)
        try:
            with open(ruta, encoding="utf-8") as archivo:
                return json.load(archivo)
        except FileNotFoundError as error:
            raise ErrorOffline(f"{operacion}: no existe {ruta}") from error