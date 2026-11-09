"""Partidas sintéticas para la línea de tiempo (T001; FR-LT-002/003/014, SC-LT-001/002).

Escribe un paquete offline con el contrato oficial en una carpeta temporal y crea
partidas con el cargador real. Los datos son de prueba: no forman parte del código
de la aplicación. El ejecutor captura el estado observable en vivo antes de cada
decisión del jugador y después de cada evento del reloj.
"""
import json

from adaptadores.cache_catalogo import CacheCatalogo
from adaptadores.modo_offline import ModoOffline
from adaptadores.servicio_cripta import ServicioCripta
from controlador.cargar_partida import CargadorPartida
from controlador.controlador import Controlador
from vista.vista_consola import VistaConsola

CRIPTA = "lt"
SEMILLA = 2026

SALAS = [
    {"id": 1, "nombre": "Entrada", "salidas": {"N": {"sala": 2}}},
    {"id": 2, "nombre": "Pasillo", "salidas": {
        "S": {"sala": 1}, "N": {"sala": 3, "costo": 150}, "E": {"sala": 5, "costo": 250}}},
    {"id": 3, "nombre": "Cripta", "salidas": {"S": {"sala": 2, "costo": 150}, "N": {"sala": 4}}},
    {"id": 4, "nombre": "Osario", "salidas": {"S": {"sala": 3}}},
    {"id": 5, "nombre": "Galeria", "salidas": {
        "O": {"sala": 2, "costo": 250},
        "E": {"sala": 6, "cerrada": True, "llave": "llave_salida"}}},
    {"id": 6, "nombre": "Salida", "salidas": {
        "O": {"sala": 5, "cerrada": True, "llave": "llave_salida"}}},
]

CONTENIDO = {
    1: {"enemigos": [], "objetos": ["pergamino", "pergamino", "daga", "antorcha", "pocion"],
        "trampas": []},
    2: {"enemigos": [], "objetos": [], "trampas": [{"instancia": "t-1", "tipo": "dardos"}]},
    3: {"enemigos": [{"instancia": "g-1", "tipo": "guardian", "vida": None}],
        "objetos": [], "trampas": []},
    4: {"enemigos": [{"instancia": "e-1", "tipo": "errante", "vida": None}],
        "objetos": [], "trampas": []},
    5: {"enemigos": [{"instancia": "c-1", "tipo": "sabueso", "vida": None}],
        "objetos": [], "trampas": []},
    6: {"enemigos": [], "objetos": [], "trampas": []},
}

FICHAS = [
    {"id": "pergamino", "clase": "pergamino_retroceso", "nombre": "Pergamino"},
    {"id": "daga", "clase": "arma", "nombre": "Daga", "ataque_bonus": 3},
    {"id": "antorcha", "clase": "antorcha", "nombre": "Antorcha", "duracion": 600},
    {"id": "pocion", "clase": "pocion", "nombre": "Pocion", "cura": 5},
    {"id": "dardos", "clase": "trampa", "nombre": "Dardos", "daño": 3, "rearme": 300},
    {"id": "guardian", "clase": "enemigo", "nombre": "Guardian", "vida_max": 14, "ataque": 3,
     "defensa": 0, "velocidad": 100, "comportamiento": "guardián", "suelta": ["pergamino"]},
    {"id": "errante", "clase": "enemigo", "nombre": "Errante", "vida_max": 9, "ataque": 2,
     "defensa": 0, "velocidad": 80, "comportamiento": "errante", "suelta": []},
    {"id": "sabueso", "clase": "enemigo", "nombre": "Sabueso", "vida_max": 10, "ataque": 1,
     "defensa": 0, "velocidad": 120, "comportamiento": "cazador", "rango": 600, "suelta": []},
]

# Órdenes con movimiento, combate, recogidas, navegación, antorcha y pergamino.
ORDENES = [
    "recoger 1", "recoger 1", "recoger 1", "recoger 1", "sig", "sig", "sig", "usar",
    "w", "esperar", "w", "atacar", "atacar", "s", "d", "esperar", "a", "w", "atacar",
    "retroceder", "esperar", "s", "s", "ant", "equipar", "w", "w", "atacar", "atacar",
    "atacar", "w", "esperar", "esperar", "s",
]


def escribir_paquete(carpeta):
    """Crea el paquete offline sintético y devuelve su carpeta."""
    def escribir(ruta, datos):
        archivo = carpeta / ruta
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")

    escribir("criptas.json", {"criptas": [{"id": CRIPTA, "nombre": "Linea", "salas": len(SALAS)}]})
    escribir("catalogo_version.json", {"version": "cat-lt"})
    escribir(f"criptas/{CRIPTA}/version.json", {"version": "v1"})
    escribir(f"criptas/{CRIPTA}/llaves.json", {"llaves": []})
    escribir(f"criptas/{CRIPTA}/general.json", {
        "id": CRIPTA, "version": "v1", "paginas": 1, "salas_total": len(SALAS),
        "sala_inicial": 1, "sala_salida": 6, "llave_salida": "llave_salida",
        "presupuesto_solicitudes": 40, "inventario_max": 6,
        "jugador": {"vida_max": 200, "ataque": 6, "defensa": 1, "velocidad": 100},
    })
    escribir(f"criptas/{CRIPTA}/salas_1.json", {"pagina": 1, "salas": SALAS})
    for sala, contenido in CONTENIDO.items():
        escribir(f"criptas/{CRIPTA}/contenido/{sala}.json", dict(contenido, sala=sala))
    for ficha in FICHAS:
        escribir(f"catalogo/{ficha['id']}.json", ficha)
    return carpeta


def crear_partida(carpeta, cache_dir, *, checkpoint_cada=None, fuente=None):
    """Partida real con el cargador; devuelve (partida, cargador)."""
    fuente = fuente or ModoOffline(str(carpeta))
    cache = CacheCatalogo(fuente, carpeta=str(cache_dir), tope=25)
    cargador = CargadorPartida(ServicioCripta(fuente, cache))
    opciones = {} if checkpoint_cada is None else {"checkpoint_cada": checkpoint_cada}
    partida = cargador.crear(CRIPTA, SEMILLA, **opciones)
    return partida, cargador


def instantanea(partida):
    """Estado observable comparable (el contenido del resumen histórico, FR-LT-002)."""
    jugador = partida.jugador
    inventario = partida.inventario
    sala = jugador.sala_actual

    def ident(objeto):
        return None if objeto is None else objeto.id

    return (
        partida.motor.reloj, sala.sala_id, jugador.vida, jugador.vida_max,
        jugador.ataque, jugador.defensa,
        tuple(partida.estado().efectos),
        tuple(objeto.id for objeto in inventario.listar()),
        ident(inventario.actual()), ident(inventario.arma_equipada),
        ident(inventario.armadura_equipada),
        tuple((e.actor_id, e.vida, e.vida_max, e.activo) for e in partida.enemigos
              if e.vida > 0 and e.sala_actual is sala),
        repr(partida.mapa()),
        partida.acciones_ejecutadas,
    )


class Grabacion:
    """Resultados en vivo: estado antes de cada decisión y tras cada evento."""

    def __init__(self):
        self.antes_de_accion = []    # (numero_k, reloj, instantanea)
        self.tras_evento = []        # (tiempo, instantanea) del último evento con ese tiempo
        self.decisiones = []         # relojes de decisión vigentes


def jugar(partida, ordenes=ORDENES, *, controlador=None):
    """Ejecuta órdenes por el controlador real y graba el estado en vivo.

    Tras un pergamino, las capturas de la historia revertida se descartan, para
    que la grabación describa la historia vigente como la línea de tiempo.
    """
    grabacion = Grabacion()
    ctl = controlador or Controlador(partida, VistaConsola(salida=lambda texto: None))
    original = partida._ejecutar_evento

    def con_captura(evento):
        original(evento)
        captura = (partida.motor.reloj, instantanea(partida))
        if grabacion.tras_evento and grabacion.tras_evento[-1][0] == captura[0]:
            grabacion.tras_evento[-1] = captura
        else:
            grabacion.tras_evento.append(captura)

    partida._ejecutar_evento = con_captura
    try:
        for texto in ordenes:
            if partida.estado().terminada:
                break
            antes = partida.acciones_ejecutadas
            captura = instantanea(partida)
            ctl.procesar(texto)
            despues = partida.acciones_ejecutadas
            if despues == antes + 1:
                grabacion.antes_de_accion.append((despues, captura[0], captura))
            elif despues == antes - 1:
                restaurado = partida.motor.reloj
                grabacion.antes_de_accion.pop()
                grabacion.tras_evento = [c for c in grabacion.tras_evento if c[0] < restaurado]
    finally:
        del partida._ejecutar_evento
    grabacion.decisiones = [reloj for _, reloj, _ in grabacion.antes_de_accion]
    return grabacion


def instantes_intermedios(grabacion):
    """Instantes de eventos que no coinciden con una decisión vigente."""
    decisiones = grabacion.decisiones
    return [(t, foto) for t, foto in grabacion.tras_evento if t not in decisiones]
