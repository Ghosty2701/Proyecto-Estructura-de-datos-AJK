"""AC-IG-004/005/006/008: proyección permitida, sin entidades vivas."""
from dataclasses import FrozenInstanceError

import pytest

from Pruebas.datos_graficos import partida_grafica
from controlador.controlador import Controlador
from vista.vista_consola import VistaConsola
from controlador.proyeccion_grafica import proyectar, IntencionGrafica, validar_intencion


def test_proyeccion_solo_conocido_y_copia_inmutable(tmp_path):
    p, _ = partida_grafica(tmp_path)
    foto = proyectar(p, 7, 3)
    assert tuple(s.sala_id for s in foto.salas) == (1, 2)
    assert foto.salas[1].estado == 1 and foto.salas[1].nombre is None
    assert foto.salas[1].salidas == () and foto.salas[1].recuerdo is None
    assert foto.enemigos == ()
    with pytest.raises(FrozenInstanceError):
        foto.vida = 0
    p.jugador.vida -= 1
    assert foto.vida == 200


def test_objetivos_solo_actual_y_seleccion_obsoleta(tmp_path):
    p, _ = partida_grafica(tmp_path)
    ctl = Controlador(p, VistaConsola(salida=lambda *args: None))
    ctl.procesar('w'); ctl.procesar('w')
    foto = proyectar(p, 1, 2)
    assert len(foto.enemigos) == 1
    enemigo = foto.enemigos[0]
    assert enemigo.identificador == 'g-1' and enemigo.comportamiento == 'guardian'
    intencion = IntencionGrafica(1, 2, 'atacar', objetivo=enemigo)
    assert validar_intencion(foto, intencion) == 1
    with pytest.raises(ValueError, match='actualiz'):
        validar_intencion(proyectar(p, 1, 3), intencion)
    ctl.procesar('s')
    assert proyectar(p, 1, 4).enemigos == ()
    assert len(foto.enemigos) == 1  # no quedó enlazada a la lista física


def test_inventario_ordenado_conserva_posicion_real_y_cursor(tmp_path):
    p, _ = partida_grafica(tmp_path)
    ctl = Controlador(p, VistaConsola(salida=lambda *args: None))
    for _ in range(4): ctl.procesar('recoger 1')
    anterior = p.inventario.actual()
    foto = proyectar(p, 1, 5, orden_inventario='nombre')
    assert p.inventario.actual() is anterior
    assert tuple(o.indice for o in foto.inventario) == (4, 3, 1, 2)
    assert tuple(o.nombre for o in foto.inventario) == ('Antorcha', 'Daga', 'Pergamino', 'Pergamino')
    assert isinstance(foto.inventario, tuple)


def test_croquis_direcciones_niebla_ids_dispersos_y_desconectados():
    from controlador.disposicion_mapa import construir_croquis
    from controlador.proyeccion_grafica import salas_visuales
    mapa = [(101, 2, 'A', [('N', 908, None, 150, False), ('E', 404, None, 100, True)]),
            (908, 1, None, []), (404, 1, None, []), (77, 2, 'Componente', []),
            (999, 0, 'Oculta', [])]
    croquis = construir_croquis(salas_visuales(mapa, 101), 101)
    assert croquis.casilla(101).posicion == (0, 0)
    assert croquis.casilla(908).posicion == (0, -1)
    assert croquis.casilla(404).posicion == (1, 0)
    assert croquis.casilla(999) is None
    assert len(croquis.casillas) == 4 and len(croquis.enlaces) == 2
    assert croquis.enlaces[0].conexion.observada is False
    assert construir_croquis(salas_visuales(mapa[:-1], 101), 101) == croquis


def test_croquis_300_salas_conflictos_sin_solapes_conserva_conexiones():
    from controlador.disposicion_mapa import construir_croquis
    from controlador.proyeccion_grafica import salas_visuales
    from Pruebas.datos_graficos import mapa_sintetico
    mapa = mapa_sintetico(conflicto=True)
    salas = salas_visuales(mapa, 101)
    croquis = construir_croquis(salas, 101)
    assert len(croquis.casillas) == 300
    assert len(croquis.enlaces) == sum(len(s.salidas) for s in salas)
    posiciones = [c.posicion for c in croquis.casillas]
    assert all(posiciones.count(p) == 1 for p in posiciones)
    assert any(e.esquematico for e in croquis.enlaces)
    assert construir_croquis(tuple(reversed(salas)), 101) == croquis
