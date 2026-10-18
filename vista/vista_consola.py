# Vista de consola. Solo presenta datos y lee texto: no conoce reglas del juego.
# Recibe el "estado" como un objeto simple (ver campos en controlador/controlador.py).
# Entrada y salida son inyectables para poder probarla sin teclado ni pantalla.

from vista.bitacora_pantalla import BitacoraPantalla

AYUDA = """Comandos:
  w a s d               moverse (norte, oeste, sur, este)
  ir <n/s/e/o>           moverse por direccion cardinal
  abrir <dir>            abrir una puerta con llave
  atacar [numero]        ejemplo: atacar 1 (primer enemigo)
  esperar                pasar tiempo
  recoger [numero]       ejemplo: recoger 1 (primer objeto del suelo)
  inv                    abrir el inventario y ver sus comandos
  retroceder             usar un pergamino de retroceso
  guardar | cargar       guardar o cargar la partida
  ayuda | salir"""

AYUDA_INVENTARIO = """Comandos de inventario:
  sig | ant              seleccionar el siguiente objeto o el anterior
  orden peso|valor|nombre   consultar una vista ordenada
  usar | equipar | soltar   actuar sobre el objeto seleccionado"""


def _nombre(objeto):
    return getattr(objeto, "nombre", str(objeto))


class VistaConsola:
    def __init__(self, entrada=input, salida=print, capacidad_bitacora=20):
        self._entrada = entrada
        self._salida = salida
        self.bitacora = BitacoraPantalla(capacidad_bitacora)
        self._inventario_visible = False
        self.permitir_cargar = True

    def mostrar_comandos(self):
        cargar = " | cargar" if self.permitir_cargar else ""
        self._salida("Comandos: w/a/s/d | atacar [numero] | recoger [numero] | abrir <n/s/e/o> | "
                     f"esperar | inv | retroceder | guardar{cargar} | ayuda | salir")
        if self._inventario_visible:
            self._salida("Inventario: sig | ant | orden peso/valor/nombre | usar | equipar | soltar")

    def agregar_mensajes(self, mensajes):
        for mensaje in mensajes:
            self.bitacora.agregar(mensaje)

    def mostrar_estado(self, estado):
        self._inventario_visible = False
        s = self._salida
        s("")
        s("=" * 50)
        s(f"{estado.sala_nombre} (sala {estado.sala_id})   reloj: {estado.reloj}")
        s(f"Vida {estado.vida}/{estado.vida_max}  Ataque {estado.ataque}  Defensa {estado.defensa}")
        presupuesto = getattr(estado, "presupuesto", None)
        if presupuesto is not None:
            s(f"Solicitudes de red: {estado.solicitudes_usadas}/{presupuesto}")
            if getattr(estado, "reserva", 0):
                s(f"Consultas normales: {estado.solicitudes_normales}; "
                  f"margen preventivo: {estado.reserva}; reintentos usados: {estado.reintentos}")
        if estado.efectos:
            s("Efectos: " + ", ".join(estado.efectos))

        rutas = getattr(estado, "rutas", None)
        if rutas:
            s("Puedes moverte:")
            abiertas = [ruta for ruta in rutas if not ruta.cerrada]
            if not abiertas:
                s("  Ninguna salida abierta.")
            for ruta in abiertas:
                if ruta.direccion == "N":
                    tecla = "w"
                elif ruta.direccion == "O":
                    tecla = "a"
                elif ruta.direccion == "E":
                    tecla = "d"
                else:
                    tecla = "s"
                s(f"  {ruta.direccion} - {ruta.nombre}, sala {ruta.sala_id} (escribe {tecla})")
            cerradas = [ruta for ruta in rutas if ruta.cerrada]
            if cerradas:
                s("Puertas cerradas:")
                for ruta in cerradas:
                    llave = f"; requiere {ruta.llave}" if ruta.llave else ""
                    s(f"  {ruta.direccion} - {ruta.nombre}, sala {ruta.sala_id}{llave} (abrir {ruta.direccion.lower()})")
        elif estado.salidas:
            partes = []
            for direccion, destino, cerrada in estado.salidas:
                partes.append(f"{direccion}->{destino}" + (" (cerrada)" if cerrada else ""))
            s("Salidas: " + "  ".join(partes))
        else:
            s("Salidas: ninguna")

        if estado.enemigos:
            s("Enemigos:")
            for numero, (nombre, vida, vida_max) in enumerate(estado.enemigos, start=1):
                s(f"  {numero}. {nombre}  vida {vida}/{vida_max}")
        if estado.objetos_suelo:
            s("En el suelo:")
            for numero, nombre in enumerate(estado.objetos_suelo, start=1):
                s(f"  {numero}. {nombre}")

        s("-" * 50)
        mensajes = self.bitacora.mensajes()[-20:]
        for mensaje in mensajes:
            s("  " + mensaje)
        if not mensajes:
            s("  (sin mensajes)")
        if not estado.terminada:
            self.mostrar_comandos()

    def mostrar_inventario(self, objetos, actual=None, arma=None, armadura=None, titulo="Inventario"):
        s = self._salida
        self._inventario_visible = True
        self.mostrar_comandos()
        s(f"--- {titulo} ({len(objetos)}) ---")
        if not objetos:
            s("  (vacio)")
        for objeto in objetos:
            marca = ">" if objeto is actual else " "
            equipo = ""
            if objeto is arma:
                equipo = " [arma]"
            elif objeto is armadura:
                equipo = " [armadura]"
            extra = ""
            if hasattr(objeto, "peso") and hasattr(objeto, "valor"):
                extra = f"  (peso {objeto.peso}, valor {objeto.valor})"
            s(f" {marca} {_nombre(objeto)}{equipo}{extra}")

    def mostrar_ayuda(self):
        ayuda = AYUDA if self.permitir_cargar else AYUDA.replace("guardar | cargar", "guardar")
        self._salida(ayuda)
        if self._inventario_visible:
            self._salida(AYUDA_INVENTARIO)
        self.mostrar_comandos()

    def mostrar_fin(self, estado):
        if estado.resultado == "victoria":
            self._salida("¡Victoria! Escapaste de la cripta.")
        elif estado.resultado == "derrota":
            self._salida("Derrota: tu vida llegó a 0.")
        else:
            self._salida("Partida terminada.")
        resumen = getattr(estado, "resumen", None)
        if resumen is not None:
            self._salida(f"Jugador: {resumen['nombre_jugador']}; "
                         f"cripta: {resumen['id_cripta']} (version {resumen['version_cripta']})")
            self._salida(f"Acciones: {resumen['acciones_jugador']}; "
                         f"enemigos derrotados: {resumen['enemigos_derrotados']}; "
                         f"tiempo final: {resumen['tiempo_final']}")

    def mostrar_resumen_red(self, solicitudes, presupuesto, aciertos, fallos):
        self._salida("--- Resumen de red y cache ---")
        self._salida(f"Solicitudes HTTP: {solicitudes}/{presupuesto}")
        self._salida(f"Aciertos de cache: {aciertos}")
        self._salida(f"Fallos de cache: {fallos}")

    def leer_comando(self, mensaje="> "):
        try:
            return self._entrada(mensaje)
        except EOFError:
            return "salir"
