# Guarda cuando ocurre una accion, su tipo y el actor que la realiza.
class Evento:
    def __init__(self, tiempo, tipo, actor_id):
        self.tiempo = tiempo
        self.tipo = tipo
        self.actor_id = actor_id
        # La agenda asigna la secuencia al insertar el evento.
        self.secuencia = None
        # Permite omitir el evento sin quitarlo de inmediato de la agenda.
        self.cancelado = False
