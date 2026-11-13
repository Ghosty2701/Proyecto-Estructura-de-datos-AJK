# Índice versionado aislado (2026-11-13)

El usuario eligió hash propio con vector inmutable. Implementado como
`modelo/indice_versionado.py`, todavía **sin conexión al juego**. Una versión
contiene casillas inmutables con (ID, registro); los registros contienen solo
escalares y tuplas. Un lote copia referencias, aplica cambios y congela otra
tupla. Comparte entradas inalteradas y nunca escribe en versiones anteriores.

Claves enteras no negativas; bool no es ID. Doble hashing, salto impar,
potencias de dos, carga activa máxima 70 %. Bajas mediante tumbas; limpieza
preventiva y crecimiento cuando corresponde. IDs grandes no dimensionan el
vector. ELIMINAR es una orden, no un valor almacenado. Una excepción de
validación o del productor del lote descarta el trabajo sin cambiar la versión
original. Actualizar conserva tipos/bits aunque los valores comparen iguales.

## Verificación

**709 pruebas pasan**: diez casos nuevos cubren versiones anteriores,
compartición de registros, colisiones forzadas, bajas, tumbas, actualización sin
duplicar, crecimiento, IDs grandes/inválidos, lotes fallidos y tipos/bits.
Una traza de 300 operaciones verifica todas las versiones retenidas contra
un oráculo de 80 posiciones. [Regresión](evidencia/pruebas_indice_versionado_juan.txt).

## Medición de la estructura

Python 3.13.2, GC habilitado. 6 000 registros activos, 200 publicaciones con
96 cambios por lote (32 actualizaciones, 32 bajas, 32 altas), más la inicial.
Los lotes se preparan antes del cronómetro. El tiempo incluye validación de
registros, copia/publicación y mantenimiento del índice; **no incluye detectar
mutaciones del modelo, asignar IDs ni serializar/reconstruir/replay**.

| Medición | Resultado |
|---|---:|
| Capacidad inicial/final del caso de publicaciones | 16 384 / 16 384 |
| Construcción inicial con crecimiento | 39,630 ms |
| Publicación mediana / p95 / máxima | 0,484 / 0,895 / 3,351 ms |
| Limpieza separada de 9 000 tumbas | 4,098 ms |
| Memoria retenida: inicial + 200 versiones | 29 827 032 bytes |
| Pico de ese caso de memoria | 29 969 996 bytes |

Memoria trazada en otra ejecución sin cronometrar; incluye construir el índice
inicial y sus registros, excluye el caso separado de limpieza. No es RSS. La
construcción inicial supera 20 ms: no se presenta como costo de un ciclo normal
ni se oculta. **Esto no certifica los 20/50 ms del proyecto**; solo muestra el
costo aislado del índice para una carga declarada de 96 cambios.
[Resumen](evidencia/indice_versionado_aislado_juan.json).

```powershell
python -X utf8 -u -m modelo.bench_indice_versionado --salida-json resultado.json
python -m pytest -q
```

## Avance del piloto y pendientes

Este fue el primer paso aislado. Posteriormente se implementaron identidad,
retirada, captura con marcas y observación experimental de órdenes; ver
[piloto completo](CAPTURA_INCREMENTAL_JUAN.md). Las cifras anteriores son del
índice inicial antes de optimizar su primer sondeo; no representan el capturador.
Producción conserva captura completa y K=25 provisional. La integración exige
ventaja demostrada y validación de cobertura/costo completo.

Avance global estimado: **93 %**. El piloto avanzó en infraestructura; los
requisitos de rendimiento y la elección final de K no están cerrados.
