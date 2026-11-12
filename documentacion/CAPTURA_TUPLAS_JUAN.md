# Captura conservando tuplas (2026-11-12)

El usuario eligió conservar las tuplas y optimizar su captura. Se mantiene la
representación D-LT-08, sin empaquetado en bytes ni cambios al guardado v6 o K.
La elección amplía la capacidad 004; no requiere otro spec.

## Búsquedas de esquema de contenedores

Listas, tuplas, diccionarios y Random ya tienen ramas explícitas y no utilizan
los campos del esquema. Se elimina su búsqueda en la tabla de tipos. En el
perfil sintético previo hubo 3 587 búsquedas de esquema; 1 545 correspondían
a estos contenedores. El perfil sirve para localizar trabajo, no para validar
el límite de 20 ms, porque instrumentarlo añade sobrecarga.

Comparación contra `18ffce1`, mismo estado tras 5 000 acciones, 300 salas y
32 cazadores. ABBA intercalado por captura, 15 rondas, 30 capturas por variante.
GC habilitado, sin trazado en tiempos. Se exige igualdad de raíz y **todos los
registros** en cada captura, y los mismos bytes v6 al restaurar.

| Variante | Mediana (ms) | p95 (ms) | Máximo (ms) | Capturas ≥20 ms |
|---|---:|---:|---:|---:|
| anterior | 20,961 | 32,925 | 33,989 | 18/30 |
| sin búsqueda de contenedores | 20,768 | 29,843 | 57,094 | 18/30 |

Ambas retuvieron 1 405 512 bytes por punto y 6 760 registros. La reducción de
trabajo no demuestra una mejora suficiente de latencia: se conserva el pico
de 57,094 ms y no se declara cumplido el límite. La variación del entorno
obliga a comparar de forma intercalada; un ensayo preliminar por bloques tuvo
deriva entre principio y final y no se usa para atribuir porcentajes de mejora.
[Resumen](evidencia/captura_contenedores_alternada_juan.json).

Reproducir:

```powershell
python -X utf8 -u -m modelo.bench_registros --revision 18ffce1 --rondas 15 --exigir-registros-iguales --alternar --salida-json resultado.json
```

Avance global estimado: **93 %**. Próximo: reducir generadores y contenedores
temporales, medir de nuevo y verificar los ciclos incluyendo la creación del punto.
