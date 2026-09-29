from modelo.retroceso import HistorialRetroceso


class SalaPrueba:
    def __init__(self):
        self.ultimo_rastro = 20


class ActorPrueba:
    def __init__(self):
        self.vida = 12


sala = SalaPrueba()
rata = ActorPrueba()
historial = HistorialRetroceso()

historial.iniciar_accion(50)
historial.registrar_rastro(sala, 50)
historial.registrar_vida(rata)
rata.vida -= 7

print(sala.ultimo_rastro, rata.vida)  # 50 5

reloj = historial.deshacer_ultima()
print(sala.ultimo_rastro, rata.vida, reloj)  # 20 12 50