"""T004 — Estructura de la línea de tiempo sin partida.

FR-LT-004/008/012/013, PR-LT-002/004; AC-LT-012/013/019/020.
"""
import pytest

from modelo.linea_tiempo import ACCION, NAVEGACION, PERGAMINO, ErrorHistoria, LineaTiempo


class Estado:
    """Raíz ficticia: la copia solo registra qué se copió."""

    def __init__(self):
        self.valor = 0


def copiar(estado):
    copia = Estado()
    copia.valor = estado.valor
    return copia


class Simulador:
    """Conduce la línea como lo haría la partida: un reloj y un contador de acciones."""

    def __init__(self, k=3):
        self.estado = Estado()
        self.reloj = 0
        self.vigentes = 0
        self.linea = LineaTiempo(k, copiar)
        self.linea.iniciar(lambda: self.estado, self.reloj)
        self.pila = []  # relojes de decisión de las acciones vigentes

    def accion(self, costo=100):
        decision = self.reloj
        self.pila.append(decision)
        self.reloj += costo
        self.vigentes += 1
        self.estado.valor += 1
        self.linea.registrar('esperar', ACCION, decision, self.reloj, self.vigentes)

    def navegar(self):
        self.linea.registrar('sig', NAVEGACION, self.reloj, self.reloj, self.vigentes)

    def pergamino(self):
        self.reloj = self.pila.pop()
        self.vigentes -= 1
        self.linea.registrar('retroceder', PERGAMINO, self.reloj, self.reloj, self.vigentes)


def test_registro_clasifica_y_numera_acciones():
    # FR-LT-004: k numera solo acciones vigentes; navegación solo queda como orden.
    s = Simulador(k=100)
    s.accion(); s.navegar(); s.accion()
    linea = s.linea
    assert [o.tipo for o in linea.ordenes] == [ACCION, NAVEGACION, ACCION]
    assert linea.cantidad_acciones == 2
    assert [(a.reloj, a.posicion) for a in linea.acciones] == [(0, 0), (100, 2)]


def test_pergamino_recorta_sin_tocar_ordenes_y_no_suma_al_tramo():
    # FR-LT-008/013 y aclaración: el pergamino no cuenta; las revertidas sí.
    s = Simulador(k=3)
    s.accion(); s.accion()
    s.pergamino()
    assert s.linea.cantidad_acciones == 1
    assert len(s.linea.ordenes) == 3          # la orden revertida permanece
    assert s.linea.acciones_en_tramo == 2     # 2 acciones ejecutadas, el pergamino no suma
    s.accion()                                # tercera acción ejecutada → punto
    assert len(s.linea.puntos) == 2
    assert s.linea.puntos[1].posicion == 4 and s.linea.puntos[1].acciones == 2
    # La nueva acción toma el número siguiente a las vigentes.
    assert [a.reloj for a in s.linea.acciones] == [0, 100]


def test_recorte_no_depende_de_la_longitud_de_la_historia():
    # PR-LT-004: el recorte trabaja solo sobre las acciones revertidas.
    s = Simulador(k=10)
    for _ in range(2000):
        s.accion()
    trabajo_antes = s.linea.trabajo_recorte
    s.pergamino()
    assert s.linea.trabajo_recorte - trabajo_antes == 1


def test_puntos_cada_k_acciones_ejecutadas_y_nunca_se_borran():
    # FR-LT-013, AC-LT-019: no más de un punto cada K acciones; los puntos permanecen.
    s = Simulador(k=3)
    for _ in range(7):
        s.accion()
    assert [p.acciones for p in s.linea.puntos] == [0, 3, 6]
    s.pergamino()
    assert [p.acciones for p in s.linea.puntos] == [0, 3, 6]
    assert [p.estado.valor for p in s.linea.puntos] == [0, 3, 6]
    assert s.linea.puntos[0].reloj == 0 and s.linea.puntos[1].reloj == 300


def test_busqueda_binaria_de_puntos_por_posicion():
    # PR-LT-002: localizar el último punto con posición ≤ objetivo.
    s = Simulador(k=2)
    for _ in range(9):
        s.accion()
    posiciones = [p.posicion for p in s.linea.puntos]
    assert posiciones == [0, 2, 4, 6, 8]
    for objetivo, esperado in ((0, 0), (1, 0), (2, 2), (3, 2), (8, 8), (9, 8)):
        assert s.linea.punto_para(objetivo).posicion == esperado
    assert s.linea.busquedas_puntos > 0


def test_objetivo_por_numero_de_accion():
    # FR-LT-004: #k → posición exclusiva de la acción k; k = N + 1 es el estado actual.
    s = Simulador(k=100)
    s.accion(); s.navegar(); s.accion()
    assert s.linea.objetivo_por_k(1) == (0, None)
    assert s.linea.objetivo_por_k(2) == (2, None)
    assert s.linea.objetivo_por_k(3) is None
    for invalido in (0, -1, 4):
        with pytest.raises(ErrorHistoria):
            s.linea.objetivo_por_k(invalido)


def test_objetivo_por_instante():
    # FR-LT-003: decisión exacta → antes de la acción; intermedio → acción con límite t.
    s = Simulador(k=100)
    s.accion(100); s.accion(250); s.accion(50)   # decisiones en 0, 100, 350; reloj 400
    linea = s.linea
    assert linea.objetivo_por_t(0, s.reloj) == (0, None)
    assert linea.objetivo_por_t(100, s.reloj) == (1, None)
    assert linea.objetivo_por_t(99, s.reloj) == (1, 99)
    assert linea.objetivo_por_t(349, s.reloj) == (2, 349)
    assert linea.objetivo_por_t(399, s.reloj) == (3, 399)
    assert linea.objetivo_por_t(400, s.reloj) is None
    with pytest.raises(ErrorHistoria, match='posterior'):
        linea.objetivo_por_t(401, s.reloj)
    with pytest.raises(ErrorHistoria):
        linea.objetivo_por_t(-1, s.reloj)


def test_partida_sin_acciones_solo_admite_el_estado_inicial():
    s = Simulador(k=5)
    assert s.linea.objetivo_por_t(0, 0) is None
    assert s.linea.objetivo_por_k(1) is None
    with pytest.raises(ErrorHistoria):
        s.linea.objetivo_por_k(2)


def test_ninguna_consulta_supera_k_acciones():
    # AC-LT-020: entre el punto elegido y el objetivo hay a lo sumo K acciones ejecutadas.
    for k in (1, 2, 5):
        s = Simulador(k=k)
        for paso in range(23):
            s.accion()
            if paso % 7 == 6:
                s.pergamino()
        linea = s.linea
        for numero in range(1, linea.cantidad_acciones + 2):
            objetivo = linea.objetivo_por_k(numero)
            if objetivo is None:
                continue
            punto = linea.punto_para(objetivo[0])
            assert linea.acciones_ejecutadas_entre(punto.posicion, objetivo[0]) <= k


def test_cambio_de_k_empieza_un_tramo_y_respeta_ambos_limites():
    # AC-LT-025: los puntos previos se conservan y el nuevo K rige desde el cambio.
    s = Simulador(k=4)
    for _ in range(6):
        s.accion()                     # puntos en 0 y 4; dos acciones en el tramo
    s.linea.cambiar_k(2, s.reloj)  # ya hay 2 ≥ 2 acciones: punto inmediato
    assert [p.acciones for p in s.linea.puntos] == [0, 4, 6]
    assert [t.k for t in s.linea.tramos] == [4, 2]
    s.accion(); s.accion()
    assert [p.acciones for p in s.linea.puntos] == [0, 4, 6, 8]
    s.linea.cambiar_k(2, s.reloj)  # mismo K: sin tramo nuevo
    assert len(s.linea.tramos) == 2
    with pytest.raises(ValueError):
        s.linea.cambiar_k(0, s.reloj)


def test_k_invalido_se_rechaza():
    for k in (0, -3, 2.5, '3', True):
        with pytest.raises(ValueError):
            LineaTiempo(k, copiar)
