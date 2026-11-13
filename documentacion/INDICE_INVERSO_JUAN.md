# Índice inverso: implementación y decisión (2026-11-13)

El usuario eligió investigar hash inverso por ID y bajas con tumbas. Está
implementado y verificado, pero **no aporta ventaja suficiente para activar el
piloto**. Tras los ajustes empata aproximadamente con el capturador incremental
anterior, consume más espacio y todas las capturas largas siguen superando
20 ms. Producción mantiene captura completa y K=25 provisional.

## Trabajo completado

`adaptadores/captura_incremental.py` mantiene dos hashes privados sincronizados:
identidad → entrada e ID estable → la misma entrada. Ninguno entra en los
puntos ni retiene versiones anteriores. La alcanzabilidad devuelve IDs retirados;
se borran de ambos hashes con tumbas, sin reconstruir todos los supervivientes.
La carga activa máxima es 70 %; las altas limpian tumbas o crecen. Por debajo
del 17,5 % se reduce capacidad, respetando el mínimo de sesión.

Se copian ambos vectores antes de preparar altas/bajas. Un fallo conserva
versión, IDs, índices y marcas originales. Los IDs no se reciclan; la memoria
del índice depende de objetos activos/reserva, no del mayor ID asignado.
Las tumbas no contienen objetos vivos. Cerrar libera también el índice inverso.

También se completaron, sin cambiar estructuras:

- Retorno inmediato al acertar la primera casilla de los hashes.
- Observación de los sufijos de deltas modificados por identidad. Una lista
  del mismo tamaño con un delta reemplazado se detecta. Undo conserva y procesa
  los deltas anteriores; expulsar una acción intacta no los reprocesa.
- Reserva privada de 64 casillas por sala, redondeada a potencia de dos, en
  raíces de partida. Es un mínimo de sesión que evita limpieza/reducción
  excesiva; no agranda los puntos. Casos genéricos conservan mínimo 8.

El retiro de referencias fuertes cuesta O(R) esperado para R bajas, salvo
limpieza/reducción. **La captura completa del piloto sigue incluyendo barrido
O(C + E), altas, codificación, validación y copias de vectores**: no es O(D).

## Verificación

**744 pruebas pasan**, 11 más que la etapa anterior. Nuevos casos cubren
colisiones en ambos índices, buscar tras tumbas, crecimiento/limpieza/reducción,
1 530 IDs con cardinalidad acotada, claves mayores que 2^80, liberación de
modelos, fallos a mitad de altas/bajas, reserva privada y observador sin repetir
deltas intactos. Continúan alias/ciclos, cinco undo, carga v6, continuación y
controles negativos. El arnés ABBA restaura sus sustituciones aun si falla.
[Regresión completa](evidencia/pruebas_indice_inverso_juan.txt).

## Primer ensayo: la estructura sola empeora

ABBA contigua, K25, cuatro historias de 5 000 acciones vigentes, 300 salas,
32 cazadores, semilla 2026. Referencia del capturador: `5ab4c78`. Ambos lados
usan el mismo observador e índice de versiones vigentes en esa ejecución.
GC habilitado, sin perfilador/tracemalloc en tiempos. Todas las altas, bajas,
limpiezas y copias están dentro del ciclo/captura.

| Variante | Captura mediana | Captura máxima | Capturas ≥20 ms |
|---|---:|---:|---:|
| Anterior A1 | 51,658 ms | 91,569 ms | 200/200 |
| Inverso B1 | 64,395 ms | 123,514 ms | 200/200 |
| Inverso B2 | 62,209 ms | 100,662 ms | 200/200 |
| Anterior A2 | 50,889 ms | 97,677 ms | 200/200 |

Había 195–196 recomposiciones del hash por identidad y 207 del inverso.
La captura de la carga controlada sí bajó a 3,908/3,968 ms, pero este caso
codifica solo 21 objetos: no representa el historial real. Memoria trazada
en otra ejecución genérica, 201 versiones: 30 037 596 bytes con sesión/modelo,
28 645 980 solo puntos y pico 30 701 540; no es RSS ni incluye reserva por salas
porque esa carga tiene raíz genérica. [ABBA adversa](evidencia/indice_inverso_abba_juan.json),
[carga controlada](evidencia/indice_inverso_controlado_juan.json).

## Segundo ensayo: ajustes, sin ventaja clara frente al control

Otras cuatro historias independientes con la misma carga. Ambos lados comparten
ahora observador optimizado, primer sondeo del índice de versiones y reconstructor.
El capturador anterior sigue siendo el de `5ab4c78`; el nuevo incorpora índice
inverso, primer sondeo por identidad y reserva privada. No atribuir la diferencia
entre ejecuciones exclusivamente a la reserva: cambió también el observador
común. La comparación dentro de cada ABBA es la relevante.

| Variante | Captura mediana | Captura máxima | Ciclo mediano | Consulta máxima |
|---|---:|---:|---:|---:|
| Anterior A1 | 45,541 ms | 82,258 ms | 0,785 ms | 34,016 ms |
| Ajustado B1 | 47,236 ms | 103,046 ms | 0,901 ms | 33,947 ms |
| Ajustado B2 | 45,899 ms | 77,613 ms | 0,879 ms | 37,214 ms |
| Anterior A2 | 46,374 ms | 102,444 ms | 0,819 ms | 27,651 ms |

Cada escenario tuvo **200/200 capturas y 200/5 001 ciclos ≥20 ms**; 0/36
consultas ≥50 ms. Las consultas incluyen conversión de IDs, copia, replay y
resumen. Máximos y excedidos quedan en el resumen, sin descartar picos.
[ABBA ajustada](evidencia/indice_inverso_ajustado_abba_juan.json).

La reserva redujo las recomposiciones a 18 por identidad y 41 por ID, con
32 768 casillas por hash privado frente a 16 384 del hash anterior. Al final
había 6 760 registros activos y el índice de cada punto conservaba 16 384
casillas. Vectores privados: 524 400 bytes; pares inversos: 378 560 bytes.
El control usa 131 128 bytes de vector y ningún par inverso. Diferencia
superficial: **771 832 bytes adicionales (~754 KiB)**, excluyendo entradas de
identidad compartidas, modelos, enteros, temporales y RSS del proceso.

En ambas ABBA se materializaron los **201 puntos de cada historia**, se
codificaron en v6 y coincidió su SHA256 completo:
`66cb0b6c48231cfcba743f96b294a352c1a2579993df82d41a1b44c7d94415f2`.
Consultas equivalentes a capturas en vivo, partida intacta, cero HTTP y replay
≤K. Oráculo completo final fuera del cronómetro; habilitado por defecto en
pruebas pequeñas, deshabilitado explícitamente para las capturas cronometradas.
Son **40 000 acciones vigentes** entre los ocho ensayos largos de este bloque.
No se certifica la cripta oficial ni el presupuesto de producción con estos datos.

## Perfil y cierre del ensayo

Perfil separado de 500 acciones/K25: 21 capturas sin oráculo, 2,876 s bajo
cProfile. Ya no aparece `retener`; `borrar_ids` consume 0,256 s inclusivos.
Persisten referencia/codificación (1,001 s), `con_cambios` (0,787 s) y
alcanzabilidad (0,607 s). **No sumar tiempos inclusivos solapados** ni usar
el perfil para certificar latencia. [Veinte filas agregadas](evidencia/perfil_indice_inverso_juan.txt).

Se cierra la investigación del índice elegido con resultado negativo para
integración. No repetir RSS/oficial de esta variante como si hubiera superado
el criterio previo de costo. Quedan abiertos los límites de producción, la
decisión final de K y la aceptación. Antes de otra modificación de arquitectura
debe usarse este diagnóstico, sin presentar mejoras aisladas como mejoras del juego.

```powershell
python -m pytest -q
python -X utf8 -u -m modelo.bench_historia_incremental --comparar-indice 5ab4c78 --salida-json resultado.json
```

Este comando reproduce la segunda variante con el código vigente; la primera
usó núcleo `cb5fc3c` y arnés `ae29141`. El segundo núcleo es `18affe2` y el
arnés `43b5f9d`. La evidencia mantiene ambas etapas, sin arrays crudos de ciclos.
Avance global estimado: **93 %**; el ensayo quedó implementado, probado y medido,
pero no cerró un requisito de rendimiento.
