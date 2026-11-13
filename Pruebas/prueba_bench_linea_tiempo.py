"""T029: PR-LT-001/002/005, FR-LT-003/006/013/014. Sin umbrales del equipo."""
import pytest

from modelo.bench_linea_tiempo import estadisticas, medir_consultas


def test_estadisticas_conservan_picos_y_percentil_de_rango_mas_cercano():
    datos = estadisticas([60, 2, 4, 1])
    assert datos == {"cantidad": 4, "minimo_ms": 1, "mediana_ms": 3,
                     "p95_ms": 60, "maximo_ms": 60, "excedidos_50ms": 1}


def test_consultas_equivalentes_acotadas_y_aisladas_con_y_sin_cazadores(monkeypatch):
    from vista.vista_consola import VistaConsola

    def prohibida(*args, **kwargs):
        raise AssertionError("el benchmark instancio una vista")

    monkeypatch.setattr(VistaConsola, "__init__", prohibida)
    datos = medir_consultas(acciones=14, cantidad_salas=5, valores_k=(2, 5, 8),
                           cazadores=(0, 3), muestras=6, rondas=1, informar=False)
    assert len(datos["escenarios"]) == 8  # Tres K y solo el punto inicial, por cada carga.
    assert datos["referencia_oficial_verificada"] is False
    for fila in datos["escenarios"]:
        assert fila["acciones_vigentes"] == 14
        assert fila["equivalente_en_vivo"] and fila["equivalente_entre_k"]
        assert fila["partida_intacta"] and fila["http"] == 0 and fila["vista"] is False
        assert fila["cazadores_activos_final"] == fila["cazadores"]
        assert fila["estadisticas"]["cantidad"] == 6
        assert len(fila["muestras"]) == 6
        assert {m["argumento"][0] for m in fila["muestras"]} == {"k", "t"}
        if fila["k"] is None:
            assert fila["puntos"] == 1
        else:
            assert fila["maximo_acciones_reaplicadas"] <= fila["k"]
            assert fila["maximo_comparaciones_puntos"] <= fila["puntos"].bit_length()


def test_bench_detecta_consulta_que_altera_la_partida(monkeypatch):
    from controlador.partida import Partida

    historia = Partida.historia

    def con_efecto(self, argumento):
        resultado = historia(self, argumento)
        self.motor.azar.random()
        return resultado

    monkeypatch.setattr(Partida, "historia", con_efecto)
    with pytest.raises(AssertionError, match="alteraron"):
        medir_consultas(acciones=8, cantidad_salas=3, valores_k=(2,),
                       cazadores=(0,), muestras=6, rondas=1, informar=False)


def test_cli_publica_muestras_de_consultas_y_alternativa_inicial(tmp_path, monkeypatch):
    import json
    import sys
    from adaptadores.bench_adaptadores import main

    salida = tmp_path / "consultas.json"
    monkeypatch.setattr(sys, "argv", ["bench_adaptadores", "--solo", "consultas",
        "--acciones", "8", "--salas", "3", "--rondas", "1", "--muestras", "6",
        "--cazadores", "0", "--valores-k", "2", "4", "--salida-json", str(salida)])
    main()
    datos = json.loads(salida.read_text(encoding="utf-8"))
    assert [f["k"] for f in datos["escenarios"]] == [2, 4, None]
    assert all(f["estadisticas"]["cantidad"] == 6 for f in datos["escenarios"])


@pytest.mark.parametrize('checkpoint_cada', [None, 2, 5])
def test_medicion_de_datos_externos_conserva_versiones_y_presupuesto(tmp_path, capsys, checkpoint_cada):
    # T033, PR-LT-001: usar el cargador real sin depender de un servicio de red en pytest.
    from adaptadores.bench_persistencia import _paquete, _cargador, ID
    from modelo.bench_linea_tiempo import medir_cripta_consultas

    _paquete(tmp_path / "datos", 5, 2026, cazadores=3)
    cargador = _cargador(tmp_path / "datos", tmp_path / "cache")
    partida = cargador.crear(ID, 2026)
    datos = medir_cripta_consultas(cargador, partida, acciones=12, muestras=6, rondas=1,
                                   cazadores_objetivo=3, checkpoint_cada=checkpoint_cada)
    assert datos["version_cripta"] == "v1" and datos["version_catalogo"]
    assert datos["acciones_vigentes"] == 12
    assert datos["cazadores_activos_inicio"] == 3
    assert datos["estadisticas"]["cantidad"] == 6
    assert datos["http_consultas"] == 0 and datos["partida_intacta"]
    assert datos["maximo_acciones_reaplicadas"] <= datos["k"]
    assert datos['k'] == (10 if checkpoint_cada is None else checkpoint_cada)  # D-LT-07.


@pytest.mark.parametrize("opciones", [
    {"acciones": 2}, {"cantidad_salas": 2}, {"valores_k": ()}, {"valores_k": (0,)},
    {"rondas": 0}, {"muestras": 5}, {"cazadores": ()}, {"cazadores": (-1,)},
])
def test_consultas_rechazan_cargas_invalidas(opciones):
    with pytest.raises(ValueError):
        medir_consultas(informar=False, **opciones)
