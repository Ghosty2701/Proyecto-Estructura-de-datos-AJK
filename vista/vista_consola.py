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
  usar | equipar | soltar   actuar sobre el objeto que se esta viendo
  inv | sig | ant        ver inventario / siguiente / anterior
  orden peso|valor|nombre   vista ordenada del inventario
  retroceder             usar un pergamino de retroceso
  guardar | cargar       guardar o cargar la partida
  ayuda | salir"""


def _nombre(objeto):
    return getattr(objeto, "nombre", str(objeto))


class VistaConsola:
    def __init__(self, entrada=input, salida=print, capacidad_bitacora=20):
        self._entrada = entrada
        self._salida = salida
        self.bitacora = BitacoraPantalla(capacidad_bitacora)

    def agregar_mensajes(self, mensajes):
        for mensaje in mensajes:
            self.bitacora.agregar(mensaje)

    def mostrar_estado(self, estado):
        s = self._salida
        s("")
        s("=" * 50)
        s(f"{estado.sala_nombre} (sala {estado.sala_id})   reloj: {estado.reloj}")
        s(f"Vida {estado.vida}/{estado.vida_max}  Ataque {estado.ataque}  Defensa {estado.defensa}")
        presupuesto = getattr(estado, "presupuesto", None)
        if presupuesto is not None:
            s(f"Solicitudes de red: {estado.solicitudes_usadas}/{presupuesto}")
            if getattr(estado, "reserva", 0):
                s(f"Normales: {estado.solicitudes_normales}/{estado.limite_normal}; "
                  f"reserva inicial: {estado.reserva}; reintentos usados: {estado.reintentos}")
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
        mensajes = self.bitacora.mensajes()[-10:]
        for mensaje in mensajes:
            s("  " + mensaje)
        if not mensajes:
            s("  (sin mensajes)")

    def mostrar_inventario(self, objetos, actual=None, arma=None, armadura=None, titulo="Inventario"):
        s = self._salida
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
        self._salida(AYUDA)

    def mostrar_fin(self, estado):
        if estado.resultado == "victoria":
            self._salida("¡Victoria! Escapaste de la cripta.")
        elif estado.resultado == "derrota":
            self._salida("Derrota: tu vida llegó a 0.")
        else:
            self._salida("Partida terminada.")

    def leer_comando(self):
        try:
            return self._entrada("> ")
        except EOFError:
            return "salir"
