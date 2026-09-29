# Prueba manual: registrar rastros y recuperar el valor anterior.
from modelo.rastro import registrar_rastro
from modelo.rastro import restaurar_rastro

class SalaPrueba:
    # Sala minima con el unico dato que necesitan estas funciones.
    def __init__(self):
        self.ultimo_rastro = None

# Comprueba que registrar devuelve el valor previo, incluso si es 0.
sala = SalaPrueba()
print(registrar_rastro(sala, 0))    # None
print(registrar_rastro(sala, 125))  # 0
print(sala.ultimo_rastro)           # 125

# Comprueba que se puede restaurar un rastro despues de actualizarlo.
sala = SalaPrueba()
sala.ultimo_rastro = 50

anterior = registrar_rastro(sala, 125)
print(sala.ultimo_rastro)  # 125

restaurar_rastro(sala, anterior)
print(sala.ultimo_rastro)  # 50
