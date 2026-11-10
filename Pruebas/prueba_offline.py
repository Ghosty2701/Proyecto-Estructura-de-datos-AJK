import json
import os
import tempfile

from adaptadores.fuente_datos import FuenteDatos
from adaptadores.modo_offline import ModoOffline, ErrorOffline


def test_rs_ac007_017_019_020_llaves_offline(tmp_path):
    """FR-RS-001/014/015: ubicaciones sin HTTP ni formato nuevo de caché."""
    import pytest
    from Pruebas.datos_resolubilidad import datos, conectar, ubicaciones
    from adaptadores.servicio_cripta import ServicioCripta, ErrorCripta
    general, salas = datos(2)
    conectar(salas, 1, 2, 'K')
    general.update(paginas=1, presupuesto_solicitudes=20)
    base = ['criptas', 'sintetica']
    escribir(tmp_path, base + ['general.json'], general)
    escribir(tmp_path, base + ['version.json'], {'version': 'v1'})
    escribir(tmp_path, base + ['salas_1.json'], {'salas': salas})
    respuesta = ubicaciones(('K', 1), ('K', 2))
    respuesta['llaves'][0]['enemigo'] = None
    escribir(tmp_path, base + ['llaves.json'], respuesta)
    fuente = ModoOffline(str(tmp_path))
    assert fuente.ubicacion_llaves('sintetica') == respuesta
    servicio = ServicioCripta(fuente, None)
    assert len(servicio.preparar_verificacion('sintetica').llaves[0].ubicaciones) == 2
    assert fuente.solicitudes_realizadas == 0
    escribir(tmp_path, base + ['version.json'], {'version': 'v2'})
    with pytest.raises(ErrorCripta): servicio.preparar_verificacion('sintetica')
    with pytest.raises(ErrorOffline): fuente.ubicacion_llaves('ausente')


def comprobar(descripcion, condicion):
    print(("OK    " if condicion else "FALLO ") + descripcion)
    assert condicion, descripcion


def escribir(carpeta, partes, datos):
    ruta = os.path.join(carpeta, *partes)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False)


def test_contrato_offline_y_presupuesto():
    with tempfile.TemporaryDirectory() as carpeta:
        escribir(carpeta, ["criptas.json"], {"criptas": [{"id": "c1"}]})
        escribir(carpeta, ["catalogo_version.json"], {"version": "cat-1"})
        escribir(carpeta, ["criptas", "c1", "general.json"], {"id": "c1", "presupuesto_solicitudes": 9})
        escribir(carpeta, ["criptas", "c1", "version.json"], {"id": "c1", "version": "v1"})
        escribir(carpeta, ["criptas", "c1", "salas_1.json"], {"pagina": 1, "salas": []})
        escribir(carpeta, ["criptas", "c1", "contenido", "1.json"], {"sala": 1, "enemigos": []})
        escribir(carpeta, ["criptas", "c1", "contenido", "2.json"], {"sala": 2, "enemigos": []})
        escribir(carpeta, ["catalogo", "ent_rata.json"], {"id": "ent_rata", "comportamiento": "guardián"})
        escribir(carpeta, ["catalogo", "itm_daga.json"], {"id": "itm_daga", "clase": "arma"})

        fuente = ModoOffline(carpeta)
        comprobar("cumple el contrato FuenteDatos", isinstance(fuente, FuenteDatos))
        comprobar("listar criptas", fuente.listar_criptas() == {"criptas": [{"id": "c1"}]})
        comprobar("version del catalogo", fuente.version_catalogo() == {"version": "cat-1"})
        comprobar("version de la cripta", fuente.version_cripta("c1")["version"] == "v1")
        comprobar("pagina del esqueleto", fuente.pagina_esqueleto("c1", 1)["pagina"] == 1)

        comprobar("presupuesto desconocido al inicio", fuente.presupuesto_solicitudes is None)
        fuente.datos_cripta("c1")
        comprobar("presupuesto leido = 9", fuente.presupuesto_solicitudes == 9)

        lote = fuente.contenido("c1", [2, 1])
        comprobar("contenido respeta el orden pedido", [e["sala"] for e in lote["contenido"]] == [2, 1])

        fichas = fuente.catalogo(["itm_daga", "ent_rata"])
        comprobar("catalogo respeta el orden pedido", [f["id"] for f in fichas["entidades"]] == ["itm_daga", "ent_rata"])
        comprobar("tildes intactas", fichas["entidades"][1]["comportamiento"] == "guardián")

        comprobar("nada cuenta como solicitud de red", fuente.solicitudes_realizadas == 0)

        try:
            fuente.contenido("c1", [1, 99])
            comprobar("sala inexistente falla", False)
        except ErrorOffline as e:
            comprobar("sala inexistente falla con contexto: " + str(e), "sala 99" in str(e))
