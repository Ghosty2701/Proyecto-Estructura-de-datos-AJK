"""Resolubilidad pura: registros compactos e índices propios, sin HTTP ni vista."""
from dataclasses import dataclass, field
from modelo.conocimiento import IndiceSalas
from modelo.indice_llaves import IndiceLlaves

DIRECCIONES = ('N', 'S', 'E', 'O')


class ErrorVerificacion(ValueError):
    pass


@dataclass
class SalaVerificada:
    sala_id: int
    nombre: str
    salidas: list = field(default_factory=list)
    llaves: list = field(default_factory=list)


@dataclass
class LlaveVerificada:
    id: str
    ubicaciones: list = field(default_factory=list)


@dataclass
class Ubicacion:
    llave: int
    sala: int
    enemigo: str | None


@dataclass
class SalidaVerificada:
    origen: int
    destino: int
    direccion: str
    costo: int
    cerrada: bool
    llave: int
    cierre: int | None
    puerta: int = -1


@dataclass
class MapaVerificado:
    id_cripta: str
    version: str
    salas: list
    indice: IndiceSalas
    indice_llaves: IndiceLlaves
    llaves: list
    inicial: int
    salida: int
    llave_salida: int
    puertas: list
    avisos: list


def _entero(valor, nombre, minimo=None):
    if type(valor) is not int or (minimo is not None and valor < minimo):
        raise ErrorVerificacion(f'{nombre}: entero inválido')
    return valor


def normalizar(general, salas, respuesta_llaves):
    """FR-RS-001/002/007/015. No modifica los registros recibidos."""
    try:
        return _normalizar(general, salas, respuesta_llaves)
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        if isinstance(error, ErrorVerificacion):
            raise
        raise ErrorVerificacion(f'Datos de verificación inválidos: {error}') from error


def _normalizar(general, entradas, respuesta):
    if not isinstance(entradas, list) or not entradas:
        raise ErrorVerificacion('El esqueleto debe contener salas')
    ubicaciones = respuesta['llaves']
    if not isinstance(ubicaciones, list):
        raise ErrorVerificacion('llaves debe ser una lista')
    ids = [_entero(s['id'], 'ID de sala') for s in entradas]
    indice = IndiceSalas(ids)
    salas = [SalaVerificada(s['id'], s['nombre']) for s in entradas]
    reserva = 1 + len(ubicaciones) + sum(len(s.get('salidas') or {}) for s in entradas)
    indice_llaves = IndiceLlaves(reserva)
    llaves = []

    def posicion_llave(identificador):
        posicion = indice_llaves.obtener(identificador)
        if posicion is None:
            posicion = len(llaves)
            indice_llaves.insertar(identificador, posicion)
            llaves.append(LlaveVerificada(identificador))
        return posicion

    def posicion_sala(identificador):
        _entero(identificador, 'Referencia de sala')
        posicion = indice.obtener(identificador)
        if posicion is None:
            raise ErrorVerificacion(f'Sala inexistente: {identificador}')
        return posicion

    inicial = posicion_sala(general['sala_inicial'])
    final = posicion_sala(general['sala_salida'])
    llave_salida = posicion_llave(general['llave_salida'])
    version = general['version']
    if not isinstance(version, str) or not version:
        raise ErrorVerificacion('Versión inválida')
    for origen, entrada in enumerate(entradas):
        conexiones = entrada.get('salidas') or {}
        if any(d not in DIRECCIONES for d in conexiones):
            raise ErrorVerificacion('Dirección desconocida')
        for direccion in DIRECCIONES:
            conexion = conexiones.get(direccion)
            if conexion is None:
                continue
            costo = conexion.get('costo')
            costo = 100 if costo is None else _entero(costo, 'Costo', 1)
            cerrada = conexion.get('cerrada')
            if cerrada is not None and type(cerrada) is not bool:
                raise ErrorVerificacion('Estado de puerta inválido')
            clave = conexion.get('llave')
            llave = -1 if clave is None else posicion_llave(clave)
            cierre = conexion.get('cierre_automatico')
            if cierre is not None:
                _entero(cierre, 'Cierre automático', 1)
            salas[origen].salidas.append(SalidaVerificada(
                origen, posicion_sala(conexion['sala']), direccion, costo,
                bool(cerrada), llave, cierre))
    for entrada in ubicaciones:
        llave = posicion_llave(entrada['id'])
        sala = posicion_sala(entrada['sala'])
        enemigo = entrada.get('enemigo')
        if enemigo is not None and not isinstance(enemigo, str):
            raise ErrorVerificacion('Instancia de enemigo inválida')
        ubicacion = Ubicacion(llave, sala, enemigo)
        llaves[llave].ubicaciones.append(ubicacion)
        salas[sala].llaves.append(llave)
    puertas, avisos = emparejar_puertas(salas)
    return MapaVerificado(general.get('id', ''), version, salas, indice,
                         indice_llaves, llaves, inicial, final, llave_salida,
                         puertas, avisos)


def emparejar_puertas(salas):
    """Convenio del equipo: reciprocidad compatible y única, sin asumir geometría."""
    puertas, avisos = agrupar_puertas(
        salas, lambda salida: salas[salida.destino],
        lambda salida: (salida.cerrada, salida.llave, salida.cierre))
    for posicion, grupo in enumerate(puertas):
        for salida in grupo:
            salida.puerta = posicion
    return puertas, avisos


def agrupar_puertas(salas, destino_de, estado_de):
    """Misma regla para registros de verificación y entidades del juego."""
    def compatibles(origen, salida):
        return [inversa for inversa in destino_de(salida).salidas
                if inversa is not salida and destino_de(inversa) is origen
                and estado_de(inversa) == estado_de(salida)]

    puertas, avisos = [], []
    for sala in salas:
        for salida in sala.salidas:
            destino = destino_de(salida)
            candidatas = compatibles(sala, salida)
            pareja = candidatas[0] if len(candidatas) == 1 else None
            if pareja is not None and len(compatibles(destino, pareja)) != 1:
                pareja = None
            grupo = [salida]
            if pareja is not None:
                if salida.costo != pareja.costo:
                    raise ErrorVerificacion('Costos distintos en los sentidos de una salida')
                if (sala.sala_id, salida.direccion) > (destino.sala_id, pareja.direccion):
                    continue
                grupo.append(pareja)
            elif candidatas:
                avisos.append((sala.sala_id, salida.direccion,
                               'Emparejamiento de puerta ambiguo; salidas separadas'))
            puertas.append(grupo)
    return puertas, avisos


@dataclass
class Cierre:
    salas: list
    llaves: list
    orden: list
    operaciones: int


@dataclass
class Certificado:
    nodos: list
    ciclo: list
    reglas: list


@dataclass
class ResultadoVerificacion:
    mapa: MapaVerificado
    cierre: Cierre
    resoluble: bool
    acceso_salida: tuple | None
    frontera: list
    no_obtenibles: list
    certificados: list = field(default_factory=list)
    estructurales: list = field(default_factory=list)


def _habilitada(salida, llaves):
    return not salida.cerrada or (salida.llave >= 0 and llaves[salida.llave])


def cerrar(mapa, semillas=None):
    """Cada sala se procesa una vez; cada espera se reactiva como máximo una vez."""
    alcanzadas = [False] * len(mapa.salas)
    obtenidas = list(semillas) if semillas is not None else [False] * len(mapa.llaves)
    pendientes = [[] for _ in mapa.llaves]
    cola, orden = [mapa.inicial], []
    alcanzadas[mapa.inicial] = True
    cursor = operaciones = 0

    def descubrir(posicion):
        if not alcanzadas[posicion]:
            alcanzadas[posicion] = True
            cola.append(posicion)

    while cursor < len(cola):
        posicion = cola[cursor]
        cursor += 1
        sala = mapa.salas[posicion]
        operaciones += 1
        for llave in sala.llaves:
            operaciones += 1
            if obtenidas[llave]:
                continue
            obtenidas[llave] = True
            orden.append(llave)
            for salida in pendientes[llave]:
                operaciones += 1
                descubrir(salida.destino)
            pendientes[llave].clear()
        for salida in sala.salidas:
            operaciones += 1
            if _habilitada(salida, obtenidas):
                descubrir(salida.destino)
            elif salida.llave >= 0:
                pendientes[salida.llave].append(salida)
    return Cierre(alcanzadas, obtenidas, orden, operaciones)


def resultado_de_cierre(mapa, cierre):
    """FR-RS-003: sala final sola no equivale a victoria."""
    acceso = None
    frontera, vistas = [], [False] * len(mapa.puertas)
    for origen, sala in enumerate(mapa.salas):
        if not cierre.salas[origen]:
            continue
        for salida in sala.salidas:
            if (cierre.llaves[mapa.llave_salida] and salida.destino == mapa.salida
                    and salida.llave == mapa.llave_salida
                    and _habilitada(salida, cierre.llaves) and acceso is None):
                acceso = (origen, salida.direccion)
            if (not cierre.salas[salida.destino] and not _habilitada(salida, cierre.llaves)
                    and not vistas[salida.puerta]):
                vistas[salida.puerta] = True
                frontera.append(salida.puerta)
    resultado = ResultadoVerificacion(
        mapa, cierre, acceso is not None, acceso, frontera,
        [k for k, obtenida in enumerate(cierre.llaves) if not obtenida])
    return resultado


def verificar(mapa):
    resultado = resultado_de_cierre(mapa, cerrar(mapa))
    if not resultado.resoluble:
        _diagnosticar(resultado)
    return resultado


def _componentes(grafo, inversas, activos):
    """Kosaraju iterativo; las aristas guardan destino y procedencia."""
    vistos, orden = [False] * len(grafo), []
    for inicio in range(len(grafo)):
        if not activos[inicio] or vistos[inicio]:
            continue
        vistos[inicio] = True
        pila = [(inicio, 0)]
        while pila:
            nodo, cursor = pila[-1]
            if cursor == len(grafo[nodo]):
                pila.pop()
                orden.append(nodo)
                continue
            pila[-1] = (nodo, cursor + 1)
            destino = grafo[nodo][cursor][0]
            if not vistos[destino]:
                vistos[destino] = True
                pila.append((destino, 0))
    pertenencia, grupos = [-1] * len(grafo), []
    for inicio in reversed(orden):
        if pertenencia[inicio] >= 0:
            continue
        grupo, pila = [], [inicio]
        pertenencia[inicio] = len(grupos)
        while pila:
            nodo = pila.pop()
            grupo.append(nodo)
            for destino in inversas[nodo]:
                if pertenencia[destino] < 0:
                    pertenencia[destino] = len(grupos)
                    pila.append(destino)
        grupos.append(grupo)
    return pertenencia, grupos


def _diagnosticar(resultado):
    mapa = resultado.mapa
    n = len(mapa.salas)
    fisicas, cola = [False] * n, [mapa.inicial]
    fisicas[mapa.inicial] = True
    cursor = 0
    while cursor < len(cola):
        origen = cola[cursor]
        cursor += 1
        for salida in mapa.salas[origen].salidas:
            if salida.cerrada and salida.llave < 0:
                continue
            if not fisicas[salida.destino]:
                fisicas[salida.destino] = True
                cola.append(salida.destino)
    semillas = [not any(fisicas[u.sala] for u in llave.ubicaciones)
                for llave in mapa.llaves]
    diagnostico = cerrar(mapa, semillas)
    activos = [fisicas[i] and not diagnostico.salas[i] for i in range(n)]
    activos += [not valor for valor in diagnostico.llaves]
    grafo, inversas = [[] for _ in activos], [[] for _ in activos]

    def enlazar(conclusion, antecedente, procedencia):
        assert activos[conclusion] and activos[antecedente]
        grafo[conclusion].append((antecedente, procedencia))
        inversas[antecedente].append(conclusion)

    for origen, sala in enumerate(mapa.salas):
        for salida in sala.salidas:
            destino = salida.destino
            if not activos[destino]:
                continue
            procedencia = ('puerta', salida.puerta, origen, salida.direccion)
            if not fisicas[origen] or (salida.cerrada and salida.llave < 0):
                resultado.estructurales.append((destino, procedencia))
                continue
            antecedente = origen if not diagnostico.salas[origen] else n + salida.llave
            enlazar(destino, antecedente, procedencia)
    for k, llave in enumerate(mapa.llaves):
        if semillas[k] and not resultado.cierre.llaves[k]:
            resultado.estructurales.append((n + k, ('llave_aislada', k)))
        if not activos[n + k]:
            continue
        for ubicacion in llave.ubicaciones:
            procedencia = ('ubicacion', k, ubicacion.sala, ubicacion.enemigo)
            if fisicas[ubicacion.sala]:
                enlazar(n + k, ubicacion.sala, procedencia)
            else:
                resultado.estructurales.append((n + k, procedencia))
    pertenencia, grupos = _componentes(grafo, inversas, activos)
    terminales = [True] * len(grupos)
    reglas = [[] for _ in grupos]
    for nodo, aristas in enumerate(grafo):
        for destino, procedencia in aristas:
            if pertenencia[nodo] != pertenencia[destino]:
                terminales[pertenencia[nodo]] = False
            else:
                reglas[pertenencia[nodo]].append((nodo, destino, procedencia))
    # Se inicializan una vez: no hay un arreglo del mapa por cada componente.
    padres = [-1] * len(grafo)
    for i, grupo in enumerate(grupos):
        if not terminales[i]:
            continue
        llave = next((v for v in grupo if v >= n), None)
        if llave is None:
            continue
        inicio = grafo[llave][0][0]
        pila = [inicio]
        padres[inicio] = inicio
        while pila and padres[llave] < 0:
            nodo = pila.pop()
            for destino, _ in grafo[nodo]:
                if pertenencia[destino] == i and padres[destino] < 0:
                    padres[destino] = nodo
                    pila.append(destino)
        assert padres[llave] >= 0
        inverso = [llave]
        while inverso[-1] != inicio:
            inverso.append(padres[inverso[-1]])
        ciclo = [llave] + list(reversed(inverso))
        resultado.certificados.append(Certificado(grupo, ciclo, reglas[i]))
