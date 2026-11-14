"""FR-EV-022–025: exploración sin ventanas invasivas ni trabajo visual repetido."""
from dataclasses import replace
from types import SimpleNamespace
import pytest
pygame = pytest.importorskip('pygame')
from Pruebas.prueba_eventos_pygame import ventana, iniciar, pulsar, turno


@pytest.mark.parametrize('tamano', [(1024, 768), (1280, 800)])
def test_minimapa_alto_y_ayuda_sin_turnos(ventana, tamano):
    app = ventana; iniciar(app)
    app.evento(pygame.event.Event(pygame.VIDEORESIZE, w=tamano[0], h=tamano[1]))
    app.dibujar()
    assert app.mapa.rect.h >= 230 and app.mapa.escala >= 0.6
    assert len(app.ui.botones) <= 6
    foto = app.controlador.respuesta.presentacion
    app.evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h, repeat=False))
    app.evento(pygame.event.Event(pygame.KEYUP, key=pygame.K_h))
    assert app.controlador.esperar(3); app.actualizar(); app.dibujar()
    assert app.panel_local == 'ayuda'
    pulsar(app, ('juego', 'cerrar_panel', None, None)); assert app.controlador.esperar(3)
    app.actualizar()
    nueva = app.controlador.respuesta.presentacion
    assert (foto.acciones, foto.reloj) == (nueva.acciones, nueva.reloj)


def test_movimiento_no_recarga_arte_y_mapa_no_recompara_snapshot(ventana, monkeypatch):
    app = ventana; iniciar(app)
    monkeypatch.setattr(pygame.image, 'load', lambda *a, **k: pytest.fail('No cargar PNG al mover'))
    turno(app, 'mover', 'N')
    app.dibujar()
    croquis = app.mapa.croquis
    # Una segunda llamada con el mismo snapshot no recorre de nuevo las salas.
    foto = app.controlador.respuesta.presentacion
    class SalasContadas(tuple):
        recorridos = 0
        def __iter__(self):
            self.recorridos += 1
            return super().__iter__()
    salas = SalasContadas(foto.salas)
    prueba = replace(foto, salas=salas)
    app.mapa.actualizar(prueba)
    antes = salas.recorridos
    for _ in range(20): app.mapa.actualizar(prueba)
    assert salas.recorridos == antes
    assert app.mapa.croquis is croquis
    # Snapshot nuevo con topología distinta invalida la clave.
    nueva = replace(prueba, salas=tuple(replace(s, estado=2) for s in foto.salas))
    app.mapa.actualizar(nueva)
    assert app.mapa.croquis is not croquis


def test_actividad_en_juego_es_compacta_y_no_agrega_botones(ventana):
    app = ventana; iniciar(app)
    app.ocupado_desde = pygame.time.get_ticks()-1600
    app.ui.comenzar()
    app.dibujar_actividad()
    assert app.ui.botones == []
    app.accion('menu'); app.ui.comenzar()
    app.dibujar_actividad()
    assert any(b.accion == 'salir' for b in app.ui.botones)


@pytest.mark.parametrize('clase,cantidad', [('enemigo', 31), ('suelo', 19)])
def test_lista_numerada_muestra_pagina_del_objetivo_elegido(ventana, clase, cantidad):
    from controlador.proyeccion_grafica import ObjetivoActual
    app = ventana; iniciar(app)
    foto = app.controlador.respuesta.presentacion
    objetivos = tuple(ObjetivoActual(clase, f'e-{i}', i+1, 'Repetido', 'guardian', 10, 10)
                      for i in range(cantidad))
    nueva = replace(foto, enemigos=objetivos if clase == 'enemigo' else (),
                    objetos=objetivos if clase == 'suelo' else ())
    app.controlador._respuesta = replace(app.controlador.respuesta, presentacion=nueva)
    app.accion('objetivos_panel'); app.lista_inicio = cantidad
    app.dibujar()
    boton = next(b for b in app.ui.botones if b.accion == ('elegir_objetivo', objetivos[-1]))
    assert boton.texto.startswith(str(cantidad)+'.')
    pulsar(app, boton.accion); app.dibujar()
    assert app.objetivo == objetivos[-1]
    assert any(r.objetivo == objetivos[-1] for r in app.escena.regiones)
    assert app.controlador.respuesta.presentacion.acciones == 0


@pytest.mark.parametrize('modo,limite', [('normal', .16), ('reducida', .08)])
def test_transicion_de_movimiento_breve_y_combate_conservado(modo, limite):
    from vista.pygame_ui.animaciones import Animaciones
    animacion = Animaciones(reloj=lambda: 0)
    animacion.modo = modo
    foto = SimpleNamespace(generacion=1, revision=1)
    def respuesta(tipo):
        return SimpleNamespace(presentacion=foto, efectos=(SimpleNamespace(tipo=tipo),),
                               resultado=SimpleNamespace(clase='accion', aceptada=True))
    animacion.incorporar(respuesta('movimiento'), foto)
    assert animacion.actual.duracion <= limite
    animacion.incorporar(respuesta('ataque'), foto)
    assert animacion.actual.duracion == (.5 if modo == 'normal' else .18)
