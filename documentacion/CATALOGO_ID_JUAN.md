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

## Historias completas y ciclos

ABBA contra `ed4b505`: cuatro historias sintéticas independientes, K=25,
5 000 acciones, 300 salas, 32 cazadores, semilla 2026 y GC habilitado. Cada
historia mide 5 001 ciclos incluyendo registro/punto y 36 consultas completas.
Usan la reconstrucción vigente y comprueban estado en vivo, partida intacta
y cero HTTP. [Resumen](evidencia/historias_catalogo_id_abba_juan.json).

| Bloque | Tokens | Punto mediano (ms) | Ciclo máximo (ms) | Ciclos ≥20 ms |
|---|---|---:|---:|---:|
| A1 | propios | 13,397 | 29,409 | 16 |
| B1 | catálogo | 13,447 | 28,786 | 9 |
| B2 | catálogo | 13,785 | 42,691 | 12 |
| A2 | propios | 14,740 | 32,731 | 15 |

Todos los bloques tuvieron 0/36 consultas >=50 ms. El catálogo reduce los
excedidos agregados en esta muestra (21 frente a 31), con máximos aún fuera
del presupuesto y sin mejora consistente de mediana. No se declara garantía.
Reproducir: `python -X utf8 -u -m modelo.bench_presupuestos --comparar-captura ed4b505 --k 25 --salida-json resultado.json`.

Otra corrida con tres K produjo:

| K | Ciclo máximo (ms) | Ciclos ≥20 ms | Consulta máxima (ms) | Consultas ≥50 ms |
|---|---:|---:|---:|---:|
| 5 | 75,873 | 219 | 12,081 | 0/36 |
| 10 | 39,789 | 40 | 19,988 | 0/36 |
| 25 | 31,863 | 11 | 18,328 | 0/36 |

[Resumen](evidencia/presupuestos_catalogo_id_juan.json).
Reproducir: `python -X utf8 -u -m modelo.bench_presupuestos --salida-json resultado.json`.

## Cripta oficial y memoria residente

Cripta-06 `f9ed9afa683d`, catálogo `4b9e75a42be5`, 300 salas, 32 cazadores
activos iniciales, 5 000 acciones por K, semilla 2026 y tres rondas de 12
consultas. Procesos independientes en orden 10/5/25; observador externo psutil
7.2.2 cada 100 ms. Los enemigos conservan estadísticas/posiciones, con vida
experimental del jugador. Partida intacta y cero HTTP durante consultas.

| K | Mediana (ms) | Máxima (ms) | Consultas ≥50 ms | Pico residente observado (MiB) |
|---|---:|---:|---:|---:|
| 5 | 76,159 | 259,838 | 24/36 | 1 251,82 |
| 10 | 20,774 | 44,224 | 0/36 | 651,57 |
| 25 | 42,323 | 79,257 | 9/36 | 291,04 |

La memoria residente incluye **todo el proceso y el catálogo fijo**, a
diferencia de la medición marginal del punto. La corrida anterior observó
1 833,22/941,14/407,10 MiB para K=5/10/25. Las reducciones de RSS son observadas
en ejecuciones secuenciales; no sustituyen la medida de asignaciones ni se
atribuyen diferencias de latencia exclusivamente al catálogo o al entorno.
En particular, K=5 fue mucho más lento en esta corrida, pese al menor pico de
memoria; ese resultado desfavorable se conserva.
[Resumen y condiciones](evidencia/k_oficial_catalogo_id_memoria_juan.json).
Reproducir: `python -X utf8 -u -m modelo.bench_k_oficial --valores-k 10 5 25 --salida-json resultado.json`.

K=10 es un candidato para la siguiente evaluación: las consultas **muestreadas**
cumplen 50 ms aquí, pero los ciclos sintéticos aún incumplen 20 ms. No se fija
K definitivo; 25 sigue provisional y no se cierran PR-LT-001/007 ni aceptación.

## Diagnóstico del siguiente candidato

Un análisis de solo lectura de 201 puntos sintéticos encontró **827 257 de
1 352 296 registros (61,2 %)** completamente iguales al del punto anterior
en el mismo ID. La fracción por punto varió de 44,7 % a 91,2 %. No es una
medición de memoria ahorrada ni demuestra que compararlos mejore la latencia.
[Diagnóstico](evidencia/diagnostico_registros_iguales_juan.json).
Reproducir: `python -X utf8 -u -m modelo.bench_registros --diagnosticar-registros --salida-json resultado.json`.

Se propuso reutilizar también esos registros inmutables mediante el índice de
ID existente, frente a compartir solo los tokens actuales. Amplía lo que se
comparte y está **pendiente de elección explícita**; no está implementado.
Avance global estimado: **93 %**.
