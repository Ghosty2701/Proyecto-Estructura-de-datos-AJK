# Guía de validación: Línea de tiempo

**Estado**: funcionalidad implementada; mediciones de memoria, consultas,
persistencia y decisiones ejecutables desde el modo conjunto. Quedan pendientes
los presupuestos de tiempo y K. Estado consolidado en
[revisión de entrega](../../documentacion/ESTADO_ENTREGA_P2.md).
Instalación: [README](../../README.md). Contrato: [linea-tiempo.md](contracts/linea-tiempo.md).

## Preparación

Desde la raíz, con Python 3.11+ y `documentacion/requirements.txt` instalados.
Usar una cripta del servicio (`--listar`) o un paquete `--offline`. Ningún ID de
ejemplo forma parte del código.

## Consultas en partida

```powershell
python main.py --cripta ID --semilla 2026 --bitacora prueba.log --checkpoint-cada 10
```

Durante la partida:

1. Hacer varias acciones; escribir `historia 0` y `historia #1`: se ve el estado
   inicial con la sala inicial explorada.
2. `historia <reloj actual>`: coincide con el estado mostrado ahora.
3. `historia <reloj + 1>`: rechazo y nada cambia.
4. Usar un pergamino; repetir una consulta posterior al reloj restaurado: rechazo.
   Hacer otra acción y consultar `#k`: refleja la acción nueva.
5. Comprobar que `prueba.log` no contiene ninguna línea `historia`.

## Reproducción hasta un instante

```powershell
python main.py --replay prueba.log --hasta 250
python main.py --replay prueba.log --hasta 999999
python main.py --hasta 10
```

Esperado: el primer resumen coincide con `historia 250` de la partida original;
el segundo muestra el estado final e indica que la partida terminó antes; el
tercero es un error de uso.

## Guardado

```powershell
python main.py --cargar partida.bin --checkpoint-cada 25
```

Tras guardar en la partida anterior y cargar, las consultas a instantes previos
dan los mismos resúmenes; un guardado de versión anterior se rechaza.

## Pruebas y mediciones

```powershell
python -m pytest -q Pruebas/prueba_linea_tiempo.py Pruebas/prueba_copia_estado.py Pruebas/prueba_historia_partida.py
python -m pytest -q
python main.py --bench
```

El bench completo se ejecuta con `python main.py --bench --bench-linea-tiempo --repeticiones 1`.
Informa para K = 10/25/50/100 y solo punto inicial: asignaciones Python, tiempo de
consulta (máximo y percentiles) con ≥ 5 000 acciones, costo de crear un punto y
ciclo máximo. También compara adelante frente a atrás y copia propia frente al
serializador. Con esos datos se elige el K por defecto (D-LT-07) y se registra
en el Documento de Decisiones.

Tramo ejecutable de Juan (persistencia y comparación de copias, sin cazadores):

```powershell
python -m adaptadores.bench_adaptadores --solo persistencia --acciones 5000 --salas 200 --rondas 3 --semilla 2026 --salida-json documentacion/evidencia/mediciones_persistencia_juan.json
python -m pytest -q Pruebas/prueba_bench_persistencia.py Pruebas/prueba_estado_binario.py Pruebas/prueba_bitacora_partida.py
```

Mide tamaño, guardado/carga completos y copia propia frente a ida y vuelta
binaria. No mide memoria total ni certifica los límites del motor/historia.

Consultas (T029) y ensayo con datos externos (T033):

```powershell
python -m adaptadores.bench_adaptadores --solo consultas --acciones 5000 --salas 200 --rondas 3 --semilla 2026 --muestras 12 --cazadores 0 32 --salida-json documentacion/evidencia/mediciones_consultas_juan.json
python -m adaptadores.bench_adaptadores --solo consultas --cripta cripta-06 --acciones 5000 --rondas 3 --semilla 2026 --muestras 12 --salida-json documentacion/evidencia/mediciones_consultas_referencia_juan.json
python -m pytest -q Pruebas/prueba_bench_linea_tiempo.py
```

Compara consultas completas, con mínimo/mediana/p95/máximo y muestras ≥50 ms.
Incluye estado actual, decisiones e intermedios. El ensayo sintético valida
decisiones contra resúmenes en vivo y todos los destinos entre K y contra solo
el punto inicial; verifica partida intacta y no más de K acciones por consulta.
La referencia usa el K provisional y activa hasta 32 cazadores con sus datos
originales. Aumenta la vida del jugador como preparación experimental. No se
cambia K ni se declara un cumplimiento general a partir de las muestras.


Memoria y creación de puntos (T029 medida):

```powershell
python -m adaptadores.bench_adaptadores --solo memoria --acciones 5000 --salas 200 --rondas 1 --semilla 2026 --cazadores 0 32 --salida-json documentacion/evidencia/mediciones_memoria_juan.json
```

Tracemalloc y tiempos se ejecutan por separado y se verifica equivalencia.
Asignaciones Python, no RSS; punto inicial excluido de los tiempos de copia.
Los incumplimientos de 20 ms están publicados; K permanece provisional.
