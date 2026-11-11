"""T030/T031: alternativas de reconstrucción y agenda con carga P2."""
from modelo.bench_decisiones import medir_decisiones


def test_alternativas_equivalentes_y_retroceso_restaura_estado():
    d = medir_decisiones(salas=(5,), cazadores=(0, 3), acciones=12, rondas=1)
    assert len(d['escenarios']) == 2
    for f in d['escenarios']:
        assert f['agenda']['equivalentes']
        assert f['agenda']['operaciones'] > 0
        assert f['codec']['equivalentes']
        for bloque in f['retroceso']:
            assert bloque['restaura_estado'] and bloque['deltas'] > 0
            assert bloque['contenedores_deltas_bytes'] > 0
            assert bloque['acciones'] in (1, 3, 5)


def test_integracion_exporta_resultados_nuevos_y_conserva_salida(tmp_path, monkeypatch, capsys):
    import json
    import modelo.bench_cierre as cierre

    def medir(**opciones):
        print('medicion nueva')
        return {'semilla': opciones.get('semilla'), 'equivalentes': True}

    for nombre in ('medir_consultas', 'medir_memoria', 'medir_persistencia', 'medir_decisiones'):
        monkeypatch.setattr(cierre, nombre, medir)
    d = cierre.ejecutar_cierre(carpeta=tmp_path)
    assert json.loads((tmp_path / 'mediciones_linea_tiempo.json').read_text(encoding='utf-8')) == d
    assert 'medicion nueva' in capsys.readouterr().out
    assert 'medicion nueva' in (tmp_path / 'bench_linea_tiempo.txt').read_text(encoding='utf-8')


def test_cli_bench_conjunto_reutiliza_decisiones_y_no_crea_partida(monkeypatch):
    import main
    import modelo.bench_modelo as modelo
    import modelo.bench_cierre as cierre

    decisiones = {'equivalentes': True}
    llamadas = []
    monkeypatch.setattr(modelo, 'ejecutar_bench_completo',
                        lambda *args: {'decisiones_linea_tiempo': decisiones})
    monkeypatch.setattr(cierre, 'ejecutar_cierre', lambda *args, **kw: llamadas.append((args, kw)))
    monkeypatch.setattr(main, 'ClienteHTTP', lambda **kw: (_ for _ in ()).throw(AssertionError('HTTP')))
    assert main.main(['--bench', '--bench-linea-tiempo', '--repeticiones', '1']) == 0
    assert llamadas[0][0] == (1, 2026)
    assert llamadas[0][1]['decisiones'] is decisiones
