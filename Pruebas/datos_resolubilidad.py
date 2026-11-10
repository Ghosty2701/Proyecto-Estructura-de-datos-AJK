"""Datos sintéticos externos al modelo: FR-RS-001/002/003/008/009."""


def datos(cantidad, llave='K', salida=None):
    return ({'id': 'sintetica', 'version': 'v1', 'sala_inicial': 1,
             'sala_salida': salida or cantidad, 'llave_salida': llave},
            [{'id': i + 1, 'nombre': str(i + 1), 'salidas': {}}
             for i in range(cantidad)])


def conectar(salas, origen, destino, llave=None, cerrada=None,
             direccion='E', inversa='O', reciproca=True, costo=100):
    entrada = {'sala': destino, 'costo': costo,
               'cerrada': bool(llave) if cerrada is None else cerrada,
               'llave': llave}
    salas[origen - 1]['salidas'][direccion] = entrada
    if reciproca:
        salas[destino - 1]['salidas'][inversa] = dict(entrada, sala=origen)


def ubicaciones(*pares):
    return {'llaves': [{'id': llave, 'sala': sala} for llave, sala in pares]}


class FuenteSintetica:
    def __init__(self, general, salas, llaves):
        self.general = dict(general, paginas=1, presupuesto_solicitudes=100)
        self.salas, self.llaves = salas, llaves
        self.version = general['version']
        self.llamadas = []
        self.solicitudes_realizadas = 0
        self.presupuesto_solicitudes = 100

    def datos_cripta(self, identificador):
        self.llamadas.append('generales')
        return self.general

    def pagina_esqueleto(self, identificador, pagina):
        self.llamadas.append('pagina')
        return {'salas': self.salas}

    def ubicacion_llaves(self, identificador):
        self.llamadas.append('llaves')
        return self.llaves

    def version_cripta(self, identificador):
        self.llamadas.append('version')
        return {'version': self.version}

    def contenido(self, *args):
        raise AssertionError('La verificación no descarga contenido')
