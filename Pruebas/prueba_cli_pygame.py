"""FR-IG-001/023; AC-IG-001/022: modos opcionales sin importación gráfica accidental."""
import builtins

import pytest

import main as aplicacion
from Pruebas.datos_graficos import paquete_grafico


def test_menu_grafico_no_exige_cripta_y_conserva_opciones(monkeypatch):
    opciones = []
    monkeypatch.setattr(aplicacion, '_iniciar_grafica', lambda o: opciones.append(o) or 0)
    assert aplicacion.main(['--interfaz', 'pygame', '--semilla', '17']) == 0
    assert opciones[0].cripta is None and opciones[0].semilla == 17


@pytest.mark.parametrize('modo', ['--listar', '--verificar', '--replay', '--ver-puntajes', '--bench', '--hasta', '--sin-interfaz'])
def test_modos_incompatibles_rechazados_antes_de_abrir_ventana(modo, monkeypatch, capsys):
    monkeypatch.setattr(aplicacion, '_iniciar_grafica', lambda _: pytest.fail('No abrir ventana'))
    extras = ['x'] if modo in ('--verificar', '--replay') else ['0'] if modo == '--hasta' else []
    with pytest.raises(SystemExit) as error:
        aplicacion.main(['--interfaz', 'pygame', modo, *extras])
    assert error.value.code == 2
    assert 'no se combina' in capsys.readouterr().err


def test_consola_sigue_sin_importar_pygame(tmp_path, monkeypatch):
    paquete = paquete_grafico(tmp_path / 'datos')
    importar = builtins.__import__
    def sin_graficos(nombre, *args, **kwargs):
        if nombre == 'pygame' or nombre.startswith('pygame.'):
            raise AssertionError('La consola no debe importar Pygame')
        return importar(nombre, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', sin_graficos)
    assert aplicacion.main(['--interfaz', 'consola', '--offline', str(paquete), '--listar']) == 0


def test_dependencia_opcional_ausente_informa(monkeypatch, capsys):
    importar = builtins.__import__
    def sin_pygame(nombre, *args, **kwargs):
        if nombre == 'pygame': raise ModuleNotFoundError("No module named 'pygame'", name='pygame')
        return importar(nombre, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', sin_pygame)
    assert aplicacion.main(['--interfaz', 'pygame']) == 1
    error = capsys.readouterr().err
    assert 'requirements-pygame.txt' in error
    # AC-IG-022: el entorno se explica, incluida la versión de Python admitida.
    assert 'Python 3.11 a 3.13' in error and 'py -3.13 -m venv' in error


def test_cripta_y_carga_mutuamente_excluyentes(monkeypatch):
    monkeypatch.setattr(aplicacion, '_iniciar_grafica', lambda _: pytest.fail('No abrir ventana'))
    with pytest.raises(SystemExit) as error:
        aplicacion.main(['--interfaz', 'pygame', '--cripta', 'a', '--cargar', 'b'])
    assert error.value.code == 2
