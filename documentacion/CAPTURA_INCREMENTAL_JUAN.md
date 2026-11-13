# Piloto incremental: resultado y límite (2026-11-13)

Se completaron registro de identidades, retiro, capturador experimental,
materialización, oráculo y seguimiento de órdenes. **No integrar esta variante**:
es correcta en las pruebas ejecutadas, pero empeora los costos del juego.
Producción conserva captura completa con registros compartidos y K=25 provisional.

## Implementación y verificación

- `adaptadores/captura_incremental.py`: IDs monótonos por sesión, hash propio
  por identidad y referencias fuertes verificadas por `is`. List/dict/tuple no
  necesitan weakref; una dirección no puede reutilizarse mientras está registrada.
- Marcas deduplicadas independientes de los cinco undo; codificar solo marcados
  y nuevos. Cada punto usa el hash versionado elegido, sin modelos ni antecesores.
- Retiro por alcanzabilidad de registros inmutables, incluidos ciclos aislados.
  El registro fuerte se recompone con los supervivientes; cerrar libera la sesión.
  Este mantenimiento recorre metadatos O(C + E), aunque no atributos vivos.
- Preparación antes de publicar; errores de codificación, retiro u oráculo
  conservan versión anterior y marcas. Oráculo completo habilitado por defecto,
  con comparación de orden, alias, tipos, NaN y bits de float.
- `adaptadores/frontera_incremental.py`: envoltorio explícito por orden, deltas
  antes/después y fronteras fuera de undo. Recorre inventario y deltas, no todas
  las salas. No intercepta escrituras arbitrarias fuera del envoltorio ni instala
  parches globales. No está conectado a la consola productiva.

**733 pruebas pasan**, 24 más que el índice aislado: independencia, colisiones,
crecimiento, ciclos/retirada, raíces efímeras, fallos con reintento, marcas
omitidas, navegación sin acción, más de 25 órdenes acumuladas y cinco undo.
Se contrastaron registros completos por orden, bytes v6 y continuación contra
captura completa. Hay controles negativos del capturador y del arnés integral.
[Regresión](evidencia/pruebas_captura_incremental_juan.txt).

## Carga controlada: sí mejora la mediana

1 500 salas / 6 007 registros, 200 publicaciones por bloque, GC habilitado.
16 escrituras y sustitución de un objeto con sus contenedores por publicación.
Incluye mutación, marcas, IDs, codificación, mantenimiento, retiro y publicación.
Oráculo final fuera del tiempo. ABBA de historias independientes.

| Variante | Mediana por bloque | Máxima por bloque | Publicaciones ≥20 ms |
|---|---|---|---|
| Completa A/A | 14,432 / 13,682 ms | 22,165 / 34,775 ms | 1 / 5 |
| Incremental B/B | 9,779 / 9,337 ms | 17,824 / 13,963 ms | 0 / 0 |

Incremental codifica 21 objetos y lee 154 campos por punto. Inicio completo:
41,837 / 38,802 ms. Una reconstrucción final: 8,684 / 8,696 ms, frente a
3,859 / 3,374 ms de la captura completa; no es una distribución de consultas.
Memoria Python trazada en ejecución separada, 201 versiones retenidas:
29 569 664 bytes con sesión/modelo; 28 645 288 solo puntos; pico 30 102 152.
No es RSS ni comparación de memoria con producción.
[Resumen reproducible](evidencia/captura_incremental_piloto_juan.json).

## Juego sintético: no demuestra ventaja

300 salas, 32 cazadores, semilla 2026, vida experimental suficiente, contenido
precargado. Seis historias independientes de 5 000 acciones vigentes, con
5 001 ciclos de incremento y un undo por historia. 36 consultas por escenario.
Los ciclos incluyen observar, ejecutar, registrar y crear punto; consultas
incluyen convertir IDs, copiar, replay y resumen. Sin red/vista, GC habilitado.

| Variante | K | Captura mediana | Capturas ≥20 ms | Ciclos ≥20 ms | Consulta máxima / ≥50 ms |
|---|---:|---:|---:|---:|---:|
| Completa A1 | 25 | 13,618 ms | 21/200 | 24/5 001 | 12,965 ms / 0 |
| Incremental | 5 | 50,639 ms | 999/1 000 | 1 001/5 001 | 22,190 ms / 0 |
| Incremental | 10 | 50,841 ms | 500/500 | 501/5 001 | 60,942 ms / 1 |
| Incremental B1 | 25 | 50,527 ms | 200/200 | 200/5 001 | 29,325 ms / 0 |
| Incremental B2 | 25 | 53,773 ms | 200/200 | 201/5 001 | 34,972 ms / 0 |
| Completa A2 | 25 | 13,701 ms | 6/200 | 8/5 001 | 15,332 ms / 0 |

La subsecuencia K25 es A/B/B/A, con K5/10 intercalados antes de B1: no es
ABBA contigua ni control del planificador de Windows. Se conservan máximos y
todos los excedidos en el resumen; no se usa la variación de los controles
para declarar cerrado el límite. El resultado adverso del piloto es consistente.

Fuera del cronómetro se materializaron **todos** los puntos y se calcularon
SHA256 de sus bytes v6. Los cuatro escenarios K25 producen la misma firma
`66cb0b6c48231cfcba743f96b294a352c1a2579993df82d41a1b44c7d94415f2`,
con idénticos metadatos. Consultas equivalentes entre todos los K, a lo sumo
K acciones reaplicadas, partida intacta y cero HTTP. El oráculo final compara
el estado completo, no solo resúmenes. Oráculo por captura deshabilitado solo
en tiempos largos; activado en las pruebas pequeñas. No se mide RSS aquí ni
se certifica la cripta oficial. [Seis escenarios](evidencia/historia_incremental_piloto_juan.json).

## Por qué no basta el caso controlado

En K25 real se codifican 3 472–3 651 objetos / 16 523–20 020 campos por punto,
frente a 21 objetos en el caso controlado. Se crean numerosos registros del
historial, se barren enlaces y se reconstruye el índice de objetos vivos.
La mediana del ciclo sin punto también sube: observar cinco acciones y sus
deltas tiene costo, aunque las marcas estén deduplicadas.

Perfil separado de 500 acciones/K25, solo 21 llamadas a captura sin oráculo:
3,304 s inclusivos bajo cProfile. `retener`: 0,758 s; `_retirar`: 0,645 s;
`con_cambios`: 0,934 s. **Son tiempos inclusivos solapados; no sumarlos**.
722 944 búsquedas del índice, más construcción/validación de registros. El
perfil añade sobrecarga y no sustituye las mediciones sin instrumentar.
[Veinte filas agregadas del perfil](evidencia/perfil_captura_incremental_juan.txt).

## Siguiente decisión de estructura, sin implementar

El registro fuerte actual reconstruye el hash completo para eliminar unos
objetos. Un **índice inverso propio ID → entrada viva**, privado del capturador,
permitiría localizar directamente los IDs retirados y borrar sus casillas por
identidad con tumbas. Es otra aplicación de estructura y AGENTS.md exige elección.

| Alternativa | Trabajo de retiro de identidades | Límite |
|---|---|---|
| Índice inverso hash + bajas con tumbas | O(R) esperado para R bajas, más altas/limpieza ocasional | Otro índice O(N), más costo de inserción y pruebas de atomicidad |
| Conservar barrido/reconstrucción y reducir marcas | O(C + N) por punto para el registro fuerte | Menos código/índices; no elimina el barrido que ya cuesta |

**Recomendación para investigar:** índice inverso hash, comparado antes/después
sobre las mismas trazas y sin activar producción. Solo ataca parte del problema:
la alcanzabilidad O(C + E), los registros nuevos, el observador y la conversión
de consultas siguen costando. No se promete que alcance 20 ms. La elección
anterior de hash versionado no autoriza registrar este índice nuevo como elegido.

## Reproducción y estado

```powershell
python -m pytest -q
python -X utf8 -u -m modelo.bench_captura_incremental --salida-json controlado.json
python -X utf8 -u -m modelo.bench_historia_incremental --salida-json historias.json
```

Avance global estimado: **93 %**. El piloto pasó de índice aislado a capturador
y observador completos para su contrato, con 30 000 acciones vigentes medidas.
No se cerró un requisito de rendimiento; por eso no aumenta la estimación por
escribir infraestructura. Quedan aceptación oficial, mejora de ciclos, RSS y K.
