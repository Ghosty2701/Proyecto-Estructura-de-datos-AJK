"""Preparación de sesiones independiente de la interfaz y de sus hilos."""
from dataclasses import dataclass, fields

from adaptadores.bitacora_partida import EscritorBitacora
from adaptadores.cache_catalogo import CacheCatalogo
from adaptadores.cliente_http import ClienteHTTP
from adaptadores.modo_offline import ModoOffline
from adaptadores.puntajes import registrar_resultado
from adaptadores.servicio_cripta import ServicioCripta
from controlador.cargar_partida import CargadorPartida
from modelo.verificacion import verificar
from vista.informes import informe_verificacion


@dataclass(frozen=True)
class ConfiguracionSesion:
    cripta: str | None = None
    cargar: str | None = None
    nombre: str | None = None
    semilla: int = 2026
    offline: str | None = None
    cache_dir: str = '.cache_cripta'
    cache_size: int = 25
    archivo_guardado: str | None = None
    checkpoint_cada: int | None = None
    bitacora: str | None = None
    puntajes: str = 'puntajes.json'
    forzar: bool = False

    @classmethod
    def desde_opciones(cls, opciones):
        return cls(**{f.name: getattr(opciones, f.name) for f in fields(cls)})

    def validar(self):
        if bool(self.cripta) == bool(self.cargar):
            raise ValueError('Elige una cripta nueva o un archivo de carga.')
        if self.nombre is not None and not self.nombre.strip():
            raise ValueError('El nombre del jugador no puede estar vacío.')
        if type(self.semilla) is not int or self.cache_size < 1:
            raise ValueError('Semilla o tamaño de caché inválido.')
        if self.checkpoint_cada is not None and self.checkpoint_cada < 1:
            raise ValueError('K debe ser mayor o igual que 1.')
        if self.cargar and (self.bitacora or self.forzar):
            raise ValueError('Cargar no admite bitácora nueva ni forzado.')


class CriptaNoResoluble(ValueError):
    def __init__(self, informe):
        super().__init__(informe)
        self.informe = informe


def abrir_partida(cargador, config, mapa=None):
    """Una misma entrada al cargador para consola y ventana."""
    if config.cargar:
        partida = cargador.reanudar(config.cargar, checkpoint_cada=config.checkpoint_cada)
    else:
        partida = cargador.crear(config.cripta, config.semilla, datos_verificados=mapa,
                                 checkpoint_cada=config.checkpoint_cada)
    if config.nombre is not None:
        partida.nombre_jugador = config.nombre.strip()
    if config.archivo_guardado is not None:
        partida.ruta_guardado = config.archivo_guardado
    return partida


def guardar_resultado(partida, ruta, registrar=registrar_resultado):
    resultado = partida.resultado_final()
    if resultado is None:
        return False
    registrar(ruta, resultado)
    return True


class Sesion:
    def __init__(self, partida, fuente, cache, config, escritor=None, mensajes=()):
        self.partida, self.fuente, self.cache = partida, fuente, cache
        self.config, self.escritor, self.mensajes = config, escritor, tuple(mensajes)
        self.registrar_accion = escritor.registrar_accion if escritor else None
        self._cerrada = False
        self._resultado_intentado = False

    def finalizar(self):
        # Un fallo se informa una vez; no provoca escrituras por cada frame.
        if self._resultado_intentado or self.partida.resultado_final() is None:
            return False
        self._resultado_intentado = True
        try:
            return guardar_resultado(self.partida, self.config.puntajes)
        finally:
            self.cerrar()

    def cerrar(self):
        if self._cerrada:
            return
        self._cerrada = True
        self.partida.bitacora_activa = False
        if self.escritor:
            self.escritor.cerrar()


def crear_fuente(config, cancelar=None):
    return (ModoOffline(config.offline) if config.offline is not None
            else ClienteHTTP(reservar_imprevistos=True, cancelar=cancelar))


def listar_criptas(config, cancelar=None):
    if cancelar is not None and cancelar.is_set():
        raise ValueError('Preparación cancelada.')
    datos = crear_fuente(config, cancelar).listar_criptas()['criptas']
    return tuple((str(c['id']), str(c['nombre']), c['salas']) for c in datos)


def preparar_sesion(config, *, cancelar=None):
    config.validar()
    if cancelar is not None and cancelar.is_set():
        raise ValueError('Preparación cancelada.')
    fuente = crear_fuente(config, cancelar)
    cache = CacheCatalogo(fuente, carpeta=config.cache_dir, tope=config.cache_size)
    servicio = ServicioCripta(fuente, cache)
    mapa, mensajes = None, []
    if config.cripta:
        mapa = servicio.preparar_verificacion(config.cripta)
        resultado = verificar(mapa)
        informe = informe_verificacion(resultado)
        if not resultado.resoluble and not config.forzar:
            raise CriptaNoResoluble(informe)
        mensajes.append(informe)
    if cancelar is not None and cancelar.is_set():
        raise ValueError('Preparación cancelada.')
    partida = abrir_partida(CargadorPartida(servicio), config, mapa)
    escritor = None
    if config.bitacora:
        cache.obtener_varias(())
        escritor = EscritorBitacora(config.bitacora, partida.id_cripta,
                                   partida.version_cripta, cache.version, config.semilla)
    partida.bitacora_activa = escritor is not None
    return Sesion(partida, fuente, cache, config, escritor, mensajes)


