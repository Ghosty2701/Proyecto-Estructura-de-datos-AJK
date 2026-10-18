import json
import os
import tempfile

from adaptadores.fuente_datos import FuenteDatos
from adaptadores.modo_offline import ModoOffline, ErrorOffline


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