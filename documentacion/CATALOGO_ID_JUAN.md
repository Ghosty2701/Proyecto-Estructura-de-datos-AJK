# Catálogo acotado de tuplas de ID (2026-11-12)

Elección explícita del usuario: compartir las tuplas de ID mediante un catálogo
acotado. Se amplía D-LT-08 en la capacidad 004; no se empaqueta en bytes ni se
cambia el guardado v6 o K provisional.

## Representación e independencia

Catálogo estático de **16 384 tuplas `(ID,)`**, indexado por arreglo inmutable.
Se construye una vez al importar el módulo, no crece y solo contiene números.
Cada punto sigue teniendo sus propios registros. Los IDs se interpretan dentro
de ese punto, aunque el token sea el mismo objeto que en otro punto. Los IDs
fuera del catálogo crean tokens propios como antes. La captura reutiliza
también el entero del token en su pila temporal.

El catálogo no tiene escrituras durante capturas y permite su uso concurrente.
La reconstrucción crea su propia tabla de objetos, conservando alias y ciclos
dentro del punto sin compartir estado mutable entre reconstrucciones.

**691 pruebas aprobadas**. Casos nuevos comprueban dos estados distintos con
los mismos tokens, reconstrucciones independientes, capturas concurrentes y
fallback con alias/ciclo por encima del límite. Las pruebas previas cubren
liberación de modelos con GC deshabilitado y compatibilidad exacta de bytes v6.
[Regresión](evidencia/pruebas_catalogo_id_juan.txt).

## Captura y memoria marginal

Contra `ed4b505`: mismo estado tras 5 000 acciones sintéticas, 300 salas,
32 cazadores, semilla 2026, Python 3.13.2/Windows. ABBA intercalado, 40 capturas
por variante. Se exige igualdad de raíz, todos los registros y bytes v6.
GC habilitado; tiempos sin tracemalloc y memoria en mediciones separadas.

| Variante | Captura mediana (ms) | Máxima (ms) | Capturas ≥20 ms | Memoria marginal por punto (bytes) |
|---|---:|---:|---:|---:|
| tokens propios | 13,275 | 36,728 | 1/40 | 1 405 512 |
| catálogo compartido | 13,227 | 19,261 | 0/40 | 898 948 |

Ahorro marginal **506 564 bytes por punto (36,0 %)** en este estado. La
diferencia de mediana es mínima y no demuestra una aceleración importante.
La muestra sin excedidos no garantiza 20 ms en otros estados o corridas.
[Comparación y costo fijo](evidencia/captura_catalogo_id_juan.json).

El catálogo ya existía al trazar cada punto: **su costo se suma aparte**.
Una réplica de la construcción, medida por separado con tracemalloc, asigna
**1 433 608 bytes (1,37 MiB)**, con pico 1 458 384 bytes. Es un costo fijo del
proceso, incluso en partidas pequeñas. No es RSS. Para puntos del tamaño del
ensayo, el ahorro acumulado compensa ese costo a partir de tres puntos; no se
extrapola ese umbral a partidas pequeñas ni se cuenta como memoria exclusiva
del punto una tupla ya compartida con el catálogo.

```powershell
python -X utf8 -u -m modelo.bench_registros --revision ed4b505 --rondas 20 --exigir-registros-iguales --alternar --salida-json resultado.json
```

Avance global estimado: **93 %**. Pendientes: presupuestos completos y K
definitivo; el ahorro de memoria no declara cumplidos 20/50 ms.
