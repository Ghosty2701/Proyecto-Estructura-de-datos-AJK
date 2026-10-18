import pytest

from adaptadores.bench_adaptadores import ejecutar_bench, medir, microsegundos_por_busqueda


def test_benchmark_detecta_busquedas_incorrectas_antes_de_cronometrar():
    class ArbolRoto:
        def buscar(self, clave):
            return None

    with pytest.raises(AssertionError, match="busqueda incorrecta"):
        microsegundos_por_busqueda(ArbolRoto(), ["ficha_000000"], 1)


@pytest.mark.parametrize("repeticiones,rondas", [(0, 1), (1, 0), (-1, 1)])
def test_medicion_rechaza_cargas_vacias(repeticiones, rondas):
    with pytest.raises(ValueError):
        medir(lambda: None, repeticiones, rondas)


def test_benchmark_completo_valida_cache_y_archivos_reales(capsys):
    ejecutar_bench(rondas=1, tope=2, cantidad_salas=3, tamanos=(3,))
    salida = capsys.readouterr().out
    assert "solicitudes HTTP: 0" in salida
    assert "Tamano binario:" in salida
    assert "Tamano modelo binario:" in salida
    assert "us/operacion" in salida
    assert "Comprobaciones funcionales: OK" in salida
