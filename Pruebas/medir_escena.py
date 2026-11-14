"""Medición reproducible de presentación y acción; no es presupuesto EX-01.

Ejecutar desde raíz: ./.venv/Scripts/python.exe -m Pruebas.medir_escena
"""
from pathlib import Path
from dataclasses import asdict, replace
from types import SimpleNamespace
from statistics import median
from time import perf_counter, sleep
import os
import platform
import sys


def ejecutar():
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
    import pygame
    from controlador.sesion import ConfiguracionSesion
    from controlador.controlador import Controlador
    from controlador.controlador_grafico import ReceptorValores
    from controlador.proyeccion_grafica import salas_visuales
    from Pruebas.datos_graficos import paquete_grafico, mapa_sintetico
    from vista.pygame_ui.aplicacion import Aplicacion
    carpeta = Path('resultados/bench/pygame/medicion-escena')
    carpeta.mkdir(parents=True, exist_ok=True)
    datos = paquete_grafico(carpeta/'datos')
    config = ConfiguracionSesion(cripta='lt', offline=str(datos), cache_dir=str(carpeta/'cache'), semilla=2026)
    app = Aplicacion(SimpleNamespace(**asdict(config)))
    filas = []
    def medir(nombre, funcion, n=60):
        for _ in range(3): funcion()
        tiempos = []
        for _ in range(n):
            inicio = perf_counter(); funcion(); tiempos.append((perf_counter()-inicio)*1000)
        filas.append(f'| {nombre} | {n} | {min(tiempos):.3f} | {median(tiempos):.3f} | {max(tiempos):.3f} |')
    try:
        assert app.controlador.esperar(5)
        app.animacion.modo = 'sin'; app.actualizar(); app.dibujar()
        p = app.controlador._sesion.partida
        foto = app.controlador.respuesta.presentacion
        antes = (p.motor.reloj, p.acciones_ejecutadas, p.motor.azar.getstate(), len(p.linea_tiempo.ordenes))
        inicio = perf_counter()
        for _ in range(300):
            app.dibujar()
            sleep(0.2)
        pared = perf_counter()-inicio
        assert antes == (p.motor.reloj, p.acciones_ejecutadas, p.motor.azar.getstate(), len(p.linea_tiempo.ordenes))
        for w, h in ((1024, 768), (1280, 800)):
            app.evento(pygame.event.Event(pygame.VIDEORESIZE, w=w, h=h))
            medir(f'Escena + HUD {w}x{h}', app.dibujar)
        app.controlador._respuesta = replace(app.controlador.respuesta, presentacion=replace(
            foto, sala_id=101, salas=salas_visuales(mapa_sintetico(conflicto=True), 101)))
        app.panel_local = 'mapa'; app.dibujar()
        medir('Mapa conocido 300 salas', app.dibujar)
        app.controlador._respuesta = replace(app.controlador.respuesta, presentacion=foto)
        app.panel_local = None
        ctl = Controlador(p, ReceptorValores())
        medir('Accion esperar completa sin dibujo/red', lambda: ctl.procesar('esperar'), 100)
        reporte = '\n'.join([
            '# Mediciones de escena — 2026-11-14', '',
            f'Equipo: {platform.platform()}; {os.environ.get("PROCESSOR_IDENTIFIER", "CPU no informada")}.',
            f'Python {sys.version.split()[0]}; Pygame {pygame.version.ver}; SDL {pygame.get_sdl_version()}.',
            'Video dummy: dibujo de superficies, sin medir GPU, monitor ni percepcion nativa.',
            'Paquete sintetico lt de seis salas; semilla 2026; cache 25; sin HTTP.', '',
            '| Operacion | Muestras | Min ms | Mediana ms | Max ms |',
            '|---|---:|---:|---:|---:|', *filas, '',
            f'Inactividad real: 300 redibujados en {pared:.3f} s, pausas de 0.2 s.',
            'Reloj virtual, acciones, azar y ordenes no cambiaron durante esa inactividad.',
            'Las muestras de dibujo reutilizan recursos escalados; no incluyen carga de PNG ni red.',
            'Accion completa incluye motor y registro/linea compartidos; no es el ciclo oficial K10.',
            'No se afirma EX-01 resuelta ni se extrapola a otras criptas/equipos.',
            'Comando: ./.venv/Scripts/python.exe -m Pruebas.medir_escena', ''])
        Path('documentacion/evidencia/escena_mediciones.md').write_text(reporte, encoding='utf-8')
        print(reporte)
    finally:
        app.controlador.cerrar(esperar=True); pygame.quit()


if __name__ == '__main__':
    ejecutar()
