"""FR-NV-005/009/010/012/015: Dijkstra usa conocimiento y generaciones."""
from prueba_niebla_partida import partida_niebla


def test_ac010_011_costos_empate_y_atajos_ocultos():
    p, salas = partida_niebla()
    k = p.motor.conocimiento
    for sala in salas:
        k.entrar(sala, False, p.motor._cambiar)
    resultado = k.ruta(salas[0], k.salas[-1])
    assert resultado.encontrada and resultado.costo_total == 400
    assert resultado.primer_paso.destino is k.salas[1]
    # Cambio real remoto no altera la ruta conocida.
    salas[2].salidas[-1].abierta = False
    assert k.ruta(salas[0], k.salas[-1]).encontrada
    k.observar(salas[2], p.motor._cambiar)
    assert not k.ruta(salas[0], k.salas[-1]).encontrada


def test_ac009_012_generaciones_y_salas_no_exploradas():
    p, salas = partida_niebla()
    k = p.motor.conocimiento
    assert not k.ruta(salas[0], k.salas[1]).encontrada
    k.entrar(salas[1], False, p.motor._cambiar)
    a = k.ruta(salas[0], k.salas[1])
    assert a.encontrada and a.costo_total == 100
    b = k.ruta(salas[1], k.salas[0])
    assert b.encontrada and b.primer_paso.destino is k.salas[0]
    assert k.registros.generacion == 3
    assert k.ruta(salas[0], k.salas[0]).costo_total == 0


def test_ac010_011_ponderacion_y_mejora_de_primer_salto():
    # FR-NV-009/010: camino más largo y mejora de etiqueta con igual costo.
    from prueba_conocimiento import mapa
    from modelo.conocimiento import ConocimientoMapa
    from modelo.motor_eventos import MotorEventos
    from modelo.rastro import Puerta, SalidaRastro
    salas = mapa(5)
    for sala, identificador in zip(salas, (1, 3, 8, 10, 20)):
        sala.sala_id, sala.salidas = identificador, []
    def unir(a, b, costo):
        puerta = Puerta()
        for origen, destino in ((a, b), (b, a)):
            salida = SalidaRastro(destino, costo=costo, puerta=puerta)
            salida.direccion = 'N'
            origen.salidas.append(salida)
    a, menor, mayor, puente, objetivo = salas
    unir(a, mayor, 1)
    unir(mayor, puente, 9)
    unir(a, menor, 5)
    unir(menor, puente, 5)
    unir(puente, objetivo, 1)
    unir(a, objetivo, 50)  # Menos pasos pero más caro.
    k, motor = ConocimientoMapa(salas), MotorEventos()
    for sala in salas:
        k.entrar(sala, False, motor._cambiar)
    ruta = k.ruta(a, k.salas[-1])
    assert ruta.costo_total == 11 and ruta.primer_paso.destino.sala_id == 3
    k.salas[0].salidas.reverse()
    assert k.ruta(a, k.salas[-1]).primer_paso.destino.sala_id == 3
