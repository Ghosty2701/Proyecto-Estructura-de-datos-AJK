"""Dijkstra individual acotado por rango, sin IO ni cambios en la partida."""
from modelo.tabla_hash import TablaDistancias, RegistroBusqueda
from modelo.heap_rutas import HeapRutas


class ResultadoRuta:
    def __init__(self, origen, objetivo, rango):
        self.origen = origen
        self.objetivo = objetivo
        self.rango = rango
        self.revision_conexiones = None
        self.primer_paso = None
        self.costo_total = None
        self.encontrada = False
        self.salas_examinadas = 0
        self.salidas_examinadas = 0
        self.sondeos = 0
        self.ampliaciones = 0


def buscar_ruta(origen, objetivo, rango):
    if type(rango) is not int:
        raise ValueError("El rango debe ser un entero")
    tabla = TablaDistancias()

    def crear(sala, distancia, primero=None):
        return tabla.insertar(RegistroBusqueda(sala, distancia, primero))

    resultado = _buscar(origen, objetivo, rango,
                        lambda sala: tabla.obtener(sala.sala_id), crear)
    resultado.sondeos, resultado.ampliaciones = tabla.sondeos, tabla.ampliaciones
    return resultado


def buscar_ruta_conocida(conocimiento, origen, objetivo):
    registros = conocimiento.registros
    registros.iniciar()
    if origen.estado != 2 or objetivo.estado != 2:
        return ResultadoRuta(origen, objetivo, None)
    return _buscar(origen, objetivo, None, registros.obtener, registros.crear)


def _buscar(origen, objetivo, rango, obtener, crear):
    """Núcleo compartido: las salas/salidas suministradas definen el conocimiento."""
    resultado = ResultadoRuta(origen, objetivo, rango)
    if origen is objetivo:
        resultado.encontrada, resultado.costo_total = True, 0
        return resultado
    if rango is not None and rango < 1:
        return resultado
    heap = HeapRutas()
    inicio = crear(origen, 0)
    heap.insertar(inicio)
    while heap.datos:
        actual = heap.extraer_minimo()
        resultado.salas_examinadas += 1
        if actual.sala is objetivo:
            resultado.encontrada = True
            resultado.costo_total = actual.distancia
            for salida in origen.salidas:
                if salida.abierta and salida.destino is actual.primer_salto:
                    anterior = resultado.primer_paso
                    if anterior is None or salida.costo < anterior.costo:
                        resultado.primer_paso = salida
            break
        for salida in actual.sala.salidas:
            resultado.salidas_examinadas += 1
            distancia = actual.distancia + salida.costo
            if not salida.abierta or (rango is not None and distancia > rango):
                continue
            primero = salida.destino if actual.sala is origen else actual.primer_salto
            anterior = obtener(salida.destino)
            if anterior is None:
                nuevo = crear(salida.destino, distancia, primero)
                heap.insertar(nuevo)
            elif not anterior.definitivo and (distancia, primero.sala_id) < (
                    anterior.distancia, anterior.primer_salto.sala_id):
                heap.mejorar(anterior, distancia, primero)
    # La liberación de candidatos pendientes ocurre antes de devolver la consulta.
    heap.datos.clear()
    return resultado
