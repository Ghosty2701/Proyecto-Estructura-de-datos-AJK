"""Valores de presentación, sin Pygame ni enlaces al mundo físico (FR-IG-005/009).

Solo el propietario de la sesión llama a proyectar. La ventana recibe tuplas
y registros congelados; nunca consulta una Partida mientras el motor trabaja.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ConexionVisual:
    direccion: str
    destino: int
    nombre: str | None
    costo: int
    observada: bool | None


@dataclass(frozen=True)
class ObservacionEnemigos:
    sala_id: int
    reloj: int
    grupos: tuple  # (comportamiento, nombre, cantidad)


@dataclass(frozen=True)
class SalaVisual:
    sala_id: int
    estado: int
    nombre: str | None
    actual: bool
    salidas: tuple
    recuerdo: ObservacionEnemigos | None = None


@dataclass(frozen=True)
class ObjetivoActual:
    clase: str
    identificador: object
    indice: int
    nombre: str
    comportamiento: str | None = None
    vida: int | None = None
    vida_max: int | None = None
    seleccionado: bool = False
    equipado: bool = False
    clase_objeto: str | None = None


@dataclass(frozen=True)
class IntencionGrafica:
    generacion: int
    revision: int
    operacion: str
    argumento: object = None
    objetivo: ObjetivoActual | None = None


@dataclass(frozen=True)
class ResumenGrafico:
    reloj: int
    titulo: str
    sala_id: int
    sala_nombre: str
    vida: int
    vida_max: int
    ataque: int
    defensa: int
    efectos: tuple
    inventario: tuple
    capacidad: int
    enemigos: tuple
    mapa: tuple


@dataclass(frozen=True)
class PresentacionGrafica:
    generacion: int
    revision: int
    id_cripta: str | None
    nombre_jugador: str
    semilla: int
    sala_id: int
    sala_nombre: str
    reloj: int
    vida: int
    vida_max: int
    ataque: int
    defensa: int
    efectos: tuple
    salas: tuple
    enemigos: tuple
    objetos: tuple
    inventario: tuple
    capacidad: int
    acciones: int
    terminada: bool
    resultado: str | None
    red: tuple
    mensajes: tuple = ()
    panel: str = 'juego'
    historia: ResumenGrafico | None = None
    viaje_activo: bool = False
    permitir_cargar: bool = True


def congelar_mapa(mapa):
    return tuple((ident, estado, nombre,
                  tuple(tuple(salida) for salida in salidas))
                 for ident, estado, nombre, salidas in mapa)


def congelar_historia(resumen):
    if resumen is None:
        return None
    return ResumenGrafico(
        resumen.reloj, resumen.titulo, resumen.sala_id, resumen.sala_nombre,
        resumen.vida, resumen.vida_max, resumen.ataque, resumen.defensa,
        tuple(resumen.efectos), tuple(tuple(o) for o in resumen.inventario),
        resumen.capacidad, tuple(tuple(e) for e in resumen.enemigos),
        congelar_mapa(resumen.mapa),
    )


def salas_visuales(mapa, actual, memoria=None):
    return tuple(SalaVisual(
        ident, estado, nombre if estado == 2 else None, ident == actual,
        tuple(ConexionVisual(*salida) for salida in salidas) if estado == 2 else (),
        memoria.obtener(ident) if memoria is not None and estado == 2 else None,
    ) for ident, estado, nombre, salidas in mapa if estado in (1, 2))


def proyectar(partida, generacion, revision, *, mensajes=(), memoria=None,
              panel='juego', historia=None, orden_inventario=None, viaje_activo=False):
    estado = partida.estado()
    inventario = partida.inventario
    reales = inventario.listar()
    vistos = (inventario.vista_ordenada(lambda o: getattr(o, orden_inventario))
              if orden_inventario else reales)
    objetivos_inv = []
    for objeto in vistos:
        posicion = next(i for i, real in enumerate(reales, 1) if real is objeto)
        objetivos_inv.append(ObjetivoActual(
            'inventario', getattr(objeto, 'id', None), posicion, str(objeto.nombre),
            seleccionado=objeto is inventario.actual(),
            equipado=any(objeto is x for x in (inventario.arma_equipada, inventario.armadura_equipada)),
            clase_objeto=getattr(objeto, 'clase', None),
        ))
    enemigos = tuple(ObjetivoActual(
        'enemigo', e.actor_id, i, str(e.nombre), e.comportamiento, e.vida, e.vida_max,
    ) for i, e in enumerate(partida._enemigos_presentes(), 1))
    suelo = tuple(ObjetivoActual(
        'suelo', getattr(o, 'id', None), i, str(o.nombre),
        clase_objeto=getattr(o, 'clase', None),
    ) for i, o in enumerate(partida.jugador.sala_actual.objetos_suelo, 1))
    return PresentacionGrafica(
        generacion, revision, partida.id_cripta, partida.nombre_jugador,
        partida.motor.semilla, estado.sala_id, estado.sala_nombre,
        estado.reloj, estado.vida, estado.vida_max, estado.ataque, estado.defensa,
        tuple(estado.efectos), salas_visuales(partida.mapa(), estado.sala_id, memoria),
        enemigos, suelo, tuple(objetivos_inv), inventario.capacidad,
        partida.acciones_ejecutadas, estado.terminada, estado.resultado,
        (estado.solicitudes_usadas, estado.presupuesto, estado.solicitudes_normales,
         estado.limite_normal, estado.reserva, estado.reintentos),
        tuple(str(m) for m in mensajes), panel, congelar_historia(historia),
        viaje_activo, not partida.bitacora_activa,
    )


def validar_intencion(presentacion, intencion, *, permitir_rebase=False):
    """Devuelve índice actual de un objetivo; no usa índices de otra revisión."""
    if intencion.generacion != presentacion.generacion:
        raise ValueError('La sesión cambió; selecciona de nuevo.')
    obsoleta = intencion.revision != presentacion.revision
    if obsoleta and not permitir_rebase:
        raise ValueError('La pantalla se actualizó; selecciona de nuevo.')
    objetivo = intencion.objetivo
    if objetivo is None:
        return None
    if obsoleta and objetivo.clase != 'enemigo':
        raise ValueError('El objeto seleccionado cambió; selecciona de nuevo.')
    if objetivo.clase == 'enemigo':
        candidatos = presentacion.enemigos
    elif objetivo.clase == 'inventario':
        candidatos = presentacion.inventario
    elif objetivo.clase == 'suelo':
        candidatos = presentacion.objetos
    else:
        raise ValueError('Objetivo no válido.')
    for actual in candidatos:
        if (actual.identificador == objetivo.identificador and
                (obsoleta or actual.indice == objetivo.indice)):
            return actual.indice
    raise ValueError('El objetivo ya no está disponible.')
