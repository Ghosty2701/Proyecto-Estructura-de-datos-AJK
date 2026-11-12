from adaptadores.resumen_mediciones import resumir_mediciones


def test_resumen_conserva_picos_fallos_y_configuracion_sin_mutar_origen():
    origen = {'tiempos_ms': [1, 2, 60], 'valores_k': [10, 25, 50],
              'equivalentes': True, 'muestras': [
                  {'tiempo_ms': 60, 'acciones_reaplicadas': 24, 'comparaciones_puntos': 8}]}
    resumen = resumir_mediciones(origen)
    assert resumen['tiempos_ms']['cantidad'] == 3
    assert resumen['tiempos_ms']['maximo_ms'] == 60
    assert resumen['tiempos_ms']['muestras_ge50ms'] == 1
    assert resumen['valores_k'] == [10, 25, 50]
    assert resumen['muestras']['maximo_acciones_reaplicadas'] == 24
    assert origen['tiempos_ms'] == [1, 2, 60]
    assert resumen['equivalentes']


def test_resumen_de_grupos_y_muestras_vacias():
    datos = {'muestras_ms': {'normal': [2, 4]}, 'cargar_ms': [], 'muestras': []}
    resumen = resumir_mediciones(datos)
    assert resumen['muestras_ms']['normal']['mediana_ms'] == 3
    assert resumen['cargar_ms'] == {'cantidad': 0}
    assert resumen['muestras'] == {'cantidad': 0}
