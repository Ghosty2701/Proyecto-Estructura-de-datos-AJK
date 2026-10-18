import json

import pytest

from adaptadores.puntajes import consultar_puntajes, registrar_resultado, ErrorPuntajes


def resultado(nombre, tiempo, acciones, enemigos):
    return {"nombre_jugador": nombre, "id_cripta": "prueba", "version_cripta": "v1",
            "resultado": "victoria", "tiempo_final": tiempo,
            "acciones_jugador": acciones, "enemigos_derrotados": enemigos}


@pytest.mark.parametrize("criterio,nombres", [
    ("tiempo", ["Juan", "Andrey", "Kendall"]),
    ("acciones", ["Kendall", "Andrey", "Juan"]),
    ("enemigos", ["Andrey", "Juan", "Kendall"]),
    ("nombre", ["Andrey", "Juan", "Kendall"]),
])
def test_consulta_ordena_sin_reescribir_el_historial(tmp_path, criterio, nombres):
    ruta = tmp_path / "puntajes.json"
    for fila in (resultado("Kendall", 300, 3, 1), resultado("Juan", 100, 5, 2),
                 resultado("Andrey", 200, 4, 3)):
        registrar_resultado(ruta, fila)
    antes = ruta.read_bytes()
    assert [r["nombre_jugador"] for r in consultar_puntajes(ruta, criterio)] == nombres
    assert ruta.read_bytes() == antes


def test_empates_estables_y_versiones_separadas(tmp_path):
    ruta = tmp_path / "puntajes.json"
    filas = [resultado("Primero", 10, 1, 0), resultado("Segundo", 10, 1, 0),
             resultado("Otra version", 1, 1, 0)]
    filas[-1]["version_cripta"] = "v2"
    ruta.write_text(json.dumps(filas), encoding="utf-8")
    assert consultar_puntajes(ruta) == filas


def test_cli_consulta_local_sin_crear_cliente_http(tmp_path, monkeypatch, capsys):
    import main
    ruta = tmp_path / "puntajes.json"
    registrar_resultado(ruta, resultado("Juan", 100, 2, 3))
    monkeypatch.setattr(main, "ClienteHTTP", lambda **kw: pytest.fail("No debe usar HTTP"))
    assert main.main(["--ver-puntajes", "--puntajes", str(ruta)]) == 0
    assert "Juan" in capsys.readouterr().out


def test_registro_incompleto_da_error_sin_modificar_archivo(tmp_path):
    ruta = tmp_path / "puntajes.json"
    ruta.write_text('[{"nombre_jugador":"Juan"}]', encoding="utf-8")
    antes = ruta.read_bytes()
    with pytest.raises(ErrorPuntajes, match="id_cripta"):
        consultar_puntajes(ruta)
    assert ruta.read_bytes() == antes
