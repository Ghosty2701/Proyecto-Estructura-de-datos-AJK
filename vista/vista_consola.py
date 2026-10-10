# Vista de consola. Solo presenta datos y lee texto: no conoce reglas del juego.
# Recibe el "estado" como un objeto simple (ver campos en controlador/controlador.py).
# Entrada y salida son inyectables para poder probarla sin teclado ni pantalla.

from vista.bitacora_pantalla import BitacoraPantalla

AYUDA = """Comandos:
  n s e o | ir <dir>     moverse (norte, sur, este, oeste)
  abrir <dir>            abrir una puerta con llave
  atacar [n]             atacar al enemigo n de la sala (por defecto 1)
  esperar                pasar tiempo
  recoger [n]            recoger el objeto n del suelo (por defecto 1)
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
        if estado.efectos:
            s("Efectos: " + ", ".join(estado.efectos))

        if estado.salidas:
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
        mensajes = self.bitacora.mensajes()
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
