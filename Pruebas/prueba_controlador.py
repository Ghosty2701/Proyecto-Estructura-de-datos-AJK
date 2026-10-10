from types import SimpleNamespace

from controlador.controlador import AccionInvalida, Controlador
from modelo.inventario import Inventario
from vista.vista_consola import VistaConsola


class Obj:
    def __init__(self, nombre, peso, valor):
        self.nombre, self.peso, self.valor = nombre, peso, valor


class PartidaFalsa:
    # Cumple el contrato documentado en controlador/controlador.py.
    def __init__(self):
        self.inventario = Inventario(capacidad=5)
        self.llamadas = []
        self.terminada = False

    def estado(self):
        return SimpleNamespace(
            sala_id=1, sala_nombre="Entrada", reloj=0, vida=30, vida_max=30,
            ataque=6, defensa=2, efectos=[],
            salidas=[("N", 2, False), ("E", 3, True)],
            enemigos=[("Rata gigante #1", 12, 12)], objetos_suelo=["Daga"],
            terminada=self.terminada, resultado="victoria" if self.terminada else None)

    def _reg(self, nombre, *args):
        self.llamadas.append((nombre,) + args)
        return [f"hecho {nombre}"]

    def mover(self, d): return self._reg("mover", d)
    def abrir(self, d): raise AccionInvalida("No tienes la llave correcta.")
    def atacar(self, i): return self._reg("atacar", i)
    def esperar(self): return self._reg("esperar")
    def recoger(self, i): return self._reg("recoger", i)
    def usar(self): return self._reg("usar")
    def equipar(self): return self._reg("equipar")
    def soltar(self): return self._reg("soltar")
    def retroceder(self): return self._reg("retroceder")
    def guardar(self): return self._reg("guardar")
    def cargar(self): return self._reg("cargar")


def armar(entradas=()):
    salidas = []
    cola = list(entradas)
    vista = VistaConsola(entrada=lambda _: cola.pop(0), salida=salidas.append)
    partida = PartidaFalsa()
    return Controlador(partida, vista), partida, vista, salidas


def test_los_comandos_llegan_a_la_partida_con_sus_argumentos():
    ctl, partida, _, _ = armar()
    for texto in ["n", "atacar 2", "recoger", "esperar", "retroceder"]:
        assert ctl.procesar(texto) is True
    assert partida.llamadas == [
        ("mover", "N"), ("atacar", 2), ("recoger", 1), ("esperar",), ("retroceder",)]


def test_accion_invalida_muestra_mensaje_y_no_tumba_el_juego():
    ctl, _, vista, _ = armar()
    assert ctl.procesar("abrir e") is True
    assert vista.bitacora.mas_reciente() == "No tienes la llave correcta."


def test_comando_desconocido_avisa():
    ctl, _, vista, _ = armar()
    assert ctl.procesar("bailar") is True
    assert "no reconocido" in vista.bitacora.mas_reciente()


def test_salir_devuelve_false():
    ctl, _, _, _ = armar()
    assert ctl.procesar("salir") is False


def test_navegar_inventario_no_llama_a_la_partida():
    ctl, partida, _, salidas = armar()
    partida.inventario.recoger(Obj("daga", 2, 15))
    partida.inventario.recoger(Obj("escudo", 8, 30))
    ctl.procesar("inv")
    ctl.procesar("sig")
    assert partida.inventario.actual().nombre == "escudo"
    assert partida.llamadas == []
    assert any("> escudo" in linea for linea in salidas)


def test_sig_en_el_ultimo_avisa():
    ctl, partida, vista, _ = armar()
    partida.inventario.recoger(Obj("daga", 2, 15))
    ctl.procesar("sig")
    assert "último" in vista.bitacora.mas_reciente()


def test_orden_muestra_vista_ordenada_sin_cambiar_el_orden_real():
    ctl, partida, _, salidas = armar()
    for o in (Obj("escudo", 8, 30), Obj("daga", 2, 15), Obj("pocion", 1, 5)):
        partida.inventario.recoger(o)
    ctl.procesar("orden peso")
    texto = "\n".join(salidas)
    assert texto.index("pocion") < texto.index("daga") < texto.index("escudo")
    assert [o.nombre for o in partida.inventario.listar()] == ["escudo", "daga", "pocion"]


def test_ordenar_por_atributo_inexistente_no_tumba_el_juego():
    ctl, partida, vista, _ = armar()
    partida.inventario.recoger(SimpleNamespace(nombre="raro"))
    partida.inventario.recoger(SimpleNamespace(nombre="otro"))
    assert ctl.procesar("orden peso") is True
    assert "No se puede ordenar" in vista.bitacora.mas_reciente()


def test_bucle_muestra_estado_y_termina_con_salir():
    ctl, _, _, salidas = armar(entradas=["ayuda", "salir"])
    ctl.ejecutar()
    texto = "\n".join(salidas)
    assert "Entrada (sala 1)" in texto
    assert "Rata gigante #1" in texto
    assert "E->3 (cerrada)" in texto
    assert "Comandos:" in texto


def test_bucle_termina_solo_al_acabar_la_partida():
    ctl, partida, _, salidas = armar()
    partida.terminada = True
    ctl.ejecutar()
    assert any("Victoria" in linea for linea in salidas)


def test_bitacora_de_la_vista_solo_muestra_los_ultimos_20():
    ctl, _, vista, salidas = armar()
    for _ in range(30):
        ctl.procesar("esperar")
    vista.mostrar_estado(ctl.partida.estado())
    assert sum(1 for linea in salidas if linea == "  hecho esperar") == 20
