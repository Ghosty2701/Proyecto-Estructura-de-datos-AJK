"""Mediciones de Juan: T029/T030, FR-LT-015 y PR-LT-005/006.

Las pruebas comprueban equivalencia y aislamiento; los tiempos dependen del equipo.
"""
import pytest

from adaptadores.bench_persistencia import medir_persistencia


def test_bench_conserva_historia_y_compara_copias_sin_red_ni_vista():
    resultado = medir_persistencia(acciones=12, cantidad_salas=4, valores_k=(2, 4, 8),
                                   rondas=1, semilla=2026, informar=False)
    assert resultado["http"] == 0 and resultado["vista"] is False
    assert resultado["cazadores"] == 0  # Carga aislada de persistencia, no de rendimiento del motor.
    assert resultado["acciones_vigentes"] == 12
    assert [f["k"] for f in resultado["filas"]] == [2, 4, 8]
    for fila in resultado["filas"]:
        assert fila["historia_equivalente"] and fila["continuacion_equivalente"]
        assert fila["acciones_ejecutadas"] == 13  # Incluye una acción luego revertida.
        assert fila["ordenes"] == 14            # Incluye la orden retroceder.
        assert fila["puntos"] == 1 + 13 // fila["k"]
        assert fila["archivo_bytes"] > 0
        assert len(fila["guardar_ms"]) == len(fila["cargar_ms"]) == 1
        assert fila["copias_equivalentes"]
        assert fila["copiador_ms"][0] >= 0 and fila["codec_ida_vuelta_ms"][0] >= 0


def test_bench_reproduce_la_misma_carga_para_cada_k():
    resultado = medir_persistencia(acciones=8, cantidad_salas=3, valores_k=(2, 5),
                                   rondas=1, semilla=71, informar=False)
    assert resultado["carga_equivalente_entre_k"]


def test_cli_persistencia_publica_resultados_verificados(tmp_path, monkeypatch):
    # FR-LT-015, PR-LT-005/006: salida reproducible y utilizable por el bench del equipo.
    import json
    import sys
    from adaptadores.bench_adaptadores import main

    salida = tmp_path / "mediciones.json"
    monkeypatch.setattr(sys, "argv", ["bench_adaptadores", "--solo", "persistencia",
                                      "--acciones", "6", "--salas", "3", "--rondas", "1",
                                      "--valores-k", "2", "3", "--salida-json", str(salida)])
    main()
    datos = json.loads(salida.read_text(encoding="utf-8"))
    assert datos["acciones_vigentes"] == 6
    assert [fila["k"] for fila in datos["filas"]] == [2, 3]
    assert all(fila["historia_equivalente"] for fila in datos["filas"])


def test_bench_detecta_perdida_del_registro_al_cargar(monkeypatch):
    # FR-LT-015: el benchmark debe fallar si solo restaura el estado final.
    from controlador.cargar_partida import CargadorPartida

    aplicar = CargadorPartida.aplicar_sesion

    def carga_incompleta(self, partida, datos):
        aplicar(self, partida, datos)
        partida.linea_tiempo.ordenes.pop()

    monkeypatch.setattr(CargadorPartida, "aplicar_sesion", carga_incompleta)
    with pytest.raises(AssertionError, match="el guardado cambio ordenes"):
        medir_persistencia(acciones=6, cantidad_salas=3, valores_k=(2,),
                           rondas=1, informar=False)


@pytest.mark.parametrize("opciones", [
    {"acciones": 0}, {"acciones": 2}, {"cantidad_salas": 2}, {"rondas": 0},
    {"valores_k": ()}, {"valores_k": (0, 10)}, {"valores_k": (True,)},
])
def test_bench_rechaza_cargas_invalidas(opciones):
    with pytest.raises(ValueError):
        medir_persistencia(informar=False, **opciones)
