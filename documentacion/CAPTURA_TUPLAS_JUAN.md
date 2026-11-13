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

Este ensayo no cierra el presupuesto. Los refinamientos siguientes reducen
generadores y contenedores temporales y verifican ciclos con creación del punto.

## Construcción sin generadores

Se usan comprensiones temporales para construir las tuplas de contenedores,
se evita una tupla de clasificación por registro y se añade la máscara al
vector de campos ya construido, sin otra lista que luego se copie. La lista
temporal se descarta inmediatamente; no se añade una estructura retenida.

Comparación intercalada contra `cce218d`, mismas condiciones y 30 capturas por
variante, con igualdad completa de registros y bytes v6:

| Variante | Mediana (ms) | p95 (ms) | Máximo (ms) | Capturas ≥20 ms |
|---|---:|---:|---:|---:|
| anterior | 19,425 | 28,988 | 51,780 | 14/30 |
| sin generadores | 18,530 | 26,607 | 28,874 | 10/30 |

La mediana baja aproximadamente 4,6 % en este ensayo; quedan diez capturas
fuera del límite. Memoria retenida idéntica (1 405 512 bytes); pico trazado
1 728 368 frente a 1 749 800 bytes. Estos tiempos son de captura aislada,
no de un ciclo completo. [Resumen](evidencia/captura_sin_generadores_juan.json).
Reproducir cambiando `--revision cce218d` en el comando anterior.

## Lectores de campos precalculados

La tabla de esquemas existente conserva un `operator.attrgetter` por tipo con
varios campos requeridos. La captura obtiene esos campos en una llamada; los
opcionales siguen comprobándose individualmente. Tipos con cero/un campo
conservan su lectura previa. No se crea otra tabla de búsqueda ni se retienen
objetos nuevos en los registros; el lector solo forma parte del metadato estático.

Contra `4e82435`, ABBA intercalado con 30 capturas por variante y la misma
comprobación completa de registros/bytes v6:

| Variante | Mediana (ms) | p95 (ms) | Máximo (ms) | Capturas ≥20 ms |
|---|---:|---:|---:|---:|
| anterior | 17,056 | 31,179 | 47,548 | 4/30 |
| lectores precalculados | 16,676 | 22,499 | 53,747 | 3/30 |

La mediana mejora aproximadamente 2,2 % en esta corrida, con picos todavía
fuera del presupuesto. Memoria retenida idéntica; pico trazado 1 728 952 bytes
frente a 1 728 368. No se presenta como solución del límite.
[Resumen](evidencia/captura_lectores_campos_juan.json).
Reproducir cambiando `--revision 4e82435` en el comando anterior.

## Comparación acumulada y ciclos

Los tres cambios juntos se compararon contra `18ffce1` en otro ABBA intercalado,
20 rondas y 40 capturas por variante. Todas produjeron los mismos registros y
bytes v6. Mediana anterior **38,125 ms**, actual **29,979 ms** (21,4 % menos en
este ensayo); máximos 72,164/59,171 ms, respectivamente. Ambas tuvieron 40/40
capturas >=20 ms. Los tiempos absolutos de esta corrida fueron mayores que
los de las comparaciones individuales; no se suman sus porcentajes ni se omite
este resultado. La memoria retenida fue idéntica: **1 405 512 bytes** por punto.
[Comparación acumulada](evidencia/captura_tuplas_acumulada_juan.json).
Reproducir con `--revision 18ffce1 --rondas 20 --exigir-registros-iguales --alternar`.

Corrida completa posterior a los cambios: 300 salas, 32 cazadores, 5 000
acciones vigentes, 5 001 ciclos ejecutados y 36 consultas por K. GC habilitado,
sin tracemalloc, ciclos con registro y creación de punto incluidos:

| K | Punto mediano (ms) | Ciclo máximo (ms) | Ciclos ≥20 ms | Consulta máxima (ms) | Consultas ≥50 ms |
|---|---:|---:|---:|---:|---:|
| 5 | 19,311 | 183,337 | 482 | 14,382 | 0/36 |
| 10 | 14,429 | 50,718 | 101 | 17,427 | 0/36 |
| 25 | 14,600 | 38,761 | 27 | 22,720 | 0/36 |

Con K=25, los 27 excedidos crearon punto; los 4 801 ciclos sin punto tuvieron
máximo 3,779 ms. Con K=5 hubo también un excedido sin punto (22,260 ms).
La corrida anterior con caché compartida tuvo 710/278/166 ciclos excedidos para
K=5/10/25; son corridas secuenciales, con variación del entorno, no una comparación
pareada de ciclos. [Resumen completo](evidencia/presupuestos_captura_tuplas_juan.json).
Reproducir: `python -X utf8 -u -m modelo.bench_presupuestos --salida-json resultado.json`.

Los tres cambios pasaron la regresión completa de **686 pruebas** después
de cada implementación: [contenedores](evidencia/pruebas_captura_contenedores_juan.txt),
[generadores](evidencia/pruebas_captura_generadores_juan.txt),
[lectores](evidencia/pruebas_captura_lectores_juan.txt).
No se certifica 20 ms ni se fija K por una mediana menor de 20 ms.

## Contraste oficial posterior

Cripta-06 `f9ed9afa683d`, catálogo `4b9e75a42be5`, 300 salas, 32 cazadores
activos iniciales, K=25 provisional, 5 000 acciones, semilla 2026 y 36 consultas:
mediana **59,345 ms**, máximo **97,483 ms**, **21/36 >=50 ms**. Partida intacta
y cero HTTP durante consultas; máximo 23 acciones reaplicadas. Se mantiene la
vida experimental del jugador y los enemigos originales del ensayo anterior.
[Resumen](evidencia/consultas_oficial_captura_tuplas_juan.json).

```powershell
python -X utf8 -u -m adaptadores.bench_adaptadores --solo consultas --cripta cripta-06 --acciones 5000 --rondas 3 --muestras 12 --semilla 2026 --checkpoint-cada 25 --salida-json resultado.json
```

La corrida oficial anterior con K=25 tuvo 16/36 excedidos y máximo 65,366 ms.
Estas corridas no son pareadas ni controlan la carga del equipo; no se atribuye
la diferencia exclusivamente al código o al entorno. **No hay mejora oficial
demostrada**, aunque la captura aislada sí reduce trabajo y sus registros son
idénticos. Sigue pendiente reducir los picos de creación y el costo de consultas
antes de fijar K. Se conserva la elección de tuplas. Avance estimado: **93 %**.

## Registro de identidades y primitivos: continuación

Se investigó insertar directamente en una casilla ya localizada, dejando el
método general para crecer. ABBA intercalado contra `a31a869`, 40 capturas por
variante: mediana 21,711 ms anterior y 22,793 ms candidata; máximos 36,694 y
64,954 ms. Registros/bytes iguales y misma memoria. **No mostró beneficio y se
retiró el cambio de producción**. Se conserva una prueba que fuerza varios
crecimientos y comprueba IDs, alias y ciclos.
[Alternativa descartada](evidencia/captura_insercion_directa_juan.json).

Se conserva la inserción de la tabla existente y se optimiza la clasificación
de valores: None vuelve directamente y los otros cinco tipos exactos se
comprueban en una tupla ordenada por su frecuencia en esta carga. No se
aceptan subclases sin esquema ni se convierte bool a int. Una prueba adicional
cubre todos los tipos primitivos, enteros grandes y rechazo de subclases.

ABBA intercalado contra `a31a869`, 40 capturas por variante, registros completos
y bytes v6 idénticos:

| Variante | Mediana (ms) | p95 (ms) | Máximo (ms) | Capturas ≥20 ms |
|---|---:|---:|---:|---:|
| anterior | 18,003 | 34,411 | 173,072 | 10/40 |
| clasificación de primitivos | 17,653 | 28,493 | 39,631 | 11/40 |

La diferencia de mediana es pequeña (1,9 %); no demuestra cumplimiento de
20 ms ni se oculta el aumento de capturas excedidas. Memoria retenida y pico
idénticos: 1 405 512/1 728 952 bytes. El pico anterior de 173,072 ms se conserva.
[Resumen](evidencia/captura_primitivos_juan.json).
Reproducir con `--revision a31a869 --rondas 20 --exigir-registros-iguales --alternar`.

## Reserva de la tabla de identidades

Se comparó reservar 64 posiciones estimadas por sala frente a 32, manteniendo
doble hashing, potencias de dos, crecimiento y carga máxima del 70 %. Para la
carga de 300 salas, la reserva redondea a 32 768 posiciones frente a 16 384.
La raíz genérica sigue empezando en 1 024 y creciendo según necesita.

ABBA intercalado contra `c0050ba`, 40 capturas por variante y registros/bytes
v6 idénticos:

| Reserva estimada | Mediana (ms) | p95 (ms) | Máximo (ms) | Capturas ≥20 ms |
|---|---:|---:|---:|---:|
| 32 por sala | 18,131 | 26,036 | 29,654 | 14/40 |
| 64 por sala | 16,091 | 31,990 | 41,585 | 5/40 |

Se adopta 64: mediana 11,3 % menor y menos excedidos en la muestra, con p95 y
máximo aún desfavorables. Pico trazado 1 991 096 frente a 1 728 952 bytes:
**256 KiB temporales adicionales**, sin incremento de la memoria retenida por
punto (1 405 512 bytes en ambas variantes). No se extrapola a garantía de 20 ms.
[Resumen](evidencia/captura_reserva64_juan.json).
Reproducir con `--revision c0050ba --rondas 20 --exigir-registros-iguales --alternar`.

### Historias completas para decidir la reserva

Primera corrida con K=5/10/25: ciclos máximos 153,695/69,130/64,370 ms y
486/232/83 ciclos >=20 ms; consultas máximas 33,968/20,480/63,581 ms con
0/0/3 excedidos de 50 ms. No cierra los presupuestos ni permite atribuir
diferencias respecto de otra fecha únicamente a la reserva.
[Resumen](evidencia/presupuestos_captura_reserva64_juan.json).

Por eso se añadió una comparación ABBA de **historias completas**, cada una
con 5 000 acciones, K=25, 300 salas, 32 cazadores y semilla 2026. La variante
anterior se carga de `c0050ba`; ambas usan la reconstrucción vigente y la misma
codificación de registros. Cada historia verifica consultas contra capturas
en vivo, partida intacta y cero HTTP. Se restaura el capturador al terminar,
también ante error (comprobado con fallo controlado).

| Bloque | Reserva | Punto mediano (ms) | Ciclo máximo (ms) | Ciclos ≥20 ms | Consulta máxima (ms) |
|---|---:|---:|---:|---:|---:|
| A1 | 32 por sala | 23,671 | 56,875 | 166/5 001 | 26,609 |
| B1 | 64 por sala | 17,326 | 39,628 | 57/5 001 | 30,775 |
| B2 | 64 por sala | 18,372 | 51,198 | 74/5 001 | 28,114 |
| A2 | 32 por sala | 16,062 | 125,552 | 61/5 001 | 14,042 |

Todos los bloques tuvieron 0/36 consultas >=50 ms. La reserva mayor favorece
el conjunto de la muestra (131 ciclos excedidos frente a 227 en dos historias
por variante), pero la variación entre bloques sigue siendo grande: A2 tiene
mejor mediana que ambos B y un pico mayor. No se declara un porcentaje causal
de mejora del ciclo ni se excluye ese pico. Se conserva 64 como ajuste medido,
sin dar por cumplido 20 ms ni elegir K definitivo.
[ABBA completo](evidencia/historias_reserva64_abba_juan.json).

```powershell
python -X utf8 -u -m modelo.bench_presupuestos --comparar-captura c0050ba --k 25 --salida-json resultado.json
```

Primitivos y reserva pasaron **688 pruebas** completas:
[primitivos](evidencia/pruebas_captura_primitivos_juan.txt),
[reserva](evidencia/pruebas_captura_reserva64_juan.txt).
No se repitió el ensayo oficial en esta continuación; no se certifica su límite
de consultas con estos ensayos sintéticos. Avance global estimado: **93 %**.

El siguiente candidato propuesto es un catálogo inmutable y acotado de tuplas
de ID, compartido entre puntos. El usuario lo eligió después y se implementó;
los resultados posteriores están en [catálogo de ID](CATALOGO_ID_JUAN.md).
Se conserva la representación de tuplas, sin empaquetado en bytes.
