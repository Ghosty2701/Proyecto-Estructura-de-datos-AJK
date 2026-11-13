# Reutilización de registros completos (2026-11-13)

Elección explícita del usuario: compartir también registros inmutables iguales
al punto anterior, usando el índice existente. Se conserva el catálogo de tokens,
el formato de tuplas y el guardado v6. K=25 sigue provisional.

La captura acepta un antecesor opcional. Cada posición se reutiliza solo si
coinciden código, datos, tipos exactos y bits de float. Python considera iguales
True/1, 1/1.0 y 0.0/-0.0: estas parejas deben producir registros distintos.
Primero se filtra con igualdad de tuplas y luego se comprueban tipos/bits;
se evita crear la tupla exterior cuando se reutiliza. La primera versión de la
comprobación recursiva resultó más costosa y se sustituyó por esta comprobación
que omite llamadas por cada valor ya idéntico.

Cada punto conserva su arreglo de registros; no guarda un enlace al antecesor.
Los IDs siempre resuelven el contexto actual. Cargar comparte entre puntos
decodificados; las capturas genéricas funcionan sin antecesor. La línea recibe
un capturador que consulta su último punto y mantiene la inyección del modelo.

**697 pruebas pasan**. Casos nuevos: registros iguales/cambiados, independencia
de copias, antecesor liberable, reasignación de IDs, tamaños diferentes, ciclos,
reutilización en línea y carga, mismos bytes v6, y distinción de tipos/bits.
[Regresión](evidencia/pruebas_registros_reutilizados_juan.txt).

## Historias completas

ABBA contra `537db26` (solo tokens compartidos), K=25, 300 salas, 32 cazadores,
5 000 acciones, semilla 2026. Cuatro preparaciones independientes; cada una
mide 5 001 ciclos con registro/puntos y 36 consultas. GC habilitado, sin red
ni vista; resúmenes comprobados contra estados en vivo y partida intacta.

Los ciclos excedidos fueron **9/5/8/9** para A/B/B/A. Cada bloque tuvo 0/36
consultas >=50 ms; los máximos de ciclo siguieron por encima de 20 ms. No se
declara garantía por una mejora de frecuencia en esta muestra.

| Bloque | Registros | Captura mediana (ms) | Ciclo máximo (ms) |
|---|---|---:|---:|
| A1 | propios | 11,778 | 24,478 |
| B1 | reutilizados | 13,578 | 37,577 |
| B2 | reutilizados | 13,324 | 35,134 |
| A2 | propios | 11,845 | 27,888 |

Comparar añade trabajo: las medianas de captura fueron mayores aunque hubo
menos ciclos excedidos en el agregado. Se adopta el ahorro de memoria sin
presentarlo como una aceleración de captura ni como cumplimiento de 20 ms.
[Resumen](evidencia/historias_registros_reutilizados_abba_juan.json).

```powershell
python -X utf8 -u -m modelo.bench_presupuestos --comparar-captura 537db26 --k 25 --salida-json resultado.json
```

La referencia anterior recibe solo la raíz y no reutiliza registros; ambas
variantes usan el mismo reconstruidor vigente. El formato del punto debe ser
compatible para esta comparación. Los presupuestos y K definitivo siguen
pendientes. Avance global estimado: **93 %**.

## Tres K: ciclos sintéticos

Otra corrida con 300 salas, 32 cazadores, 5 000 acciones vigentes, 5 001 ciclos
y 36 consultas por K, GC habilitado y creación del punto incluida:

| K | Ciclo máximo (ms) | Ciclos ≥20 ms | Consulta máxima (ms) | Consultas ≥50 ms |
|---|---:|---:|---:|---:|
| 5 | 49,228 | 94 | 8,933 | 0/36 |
| 10 | 35,344 | 22 | 12,969 | 0/36 |
| 25 | 41,271 | 21 | 24,723 | 0/36 |

[Resumen](evidencia/presupuestos_registros_reutilizados_juan.json).
Reproducir: `python -X utf8 -u -m modelo.bench_presupuestos --salida-json resultado.json`.

## Consultas oficiales y memoria residente

Cripta-06 `f9ed9afa683d`, catálogo `4b9e75a42be5`, 300 salas y 32 cazadores
activos iniciales. Cada proceso ejecuta 5 000 acciones y tres rondas de 12
consultas; semilla 2026. Orden de procesos: 10/5/25, observación externa de
RSS con psutil cada 100 ms. Enemigos originales, vida experimental del jugador,
partida intacta y cero HTTP durante consultas. Versión con comparación exacta
optimizada, posterior a la primera prueba del comparador recursivo.

| K | Mediana (ms) | Máxima (ms) | Consultas ≥50 ms | Pico residente observado (MiB) |
|---|---:|---:|---:|---:|
| 5 | 14,871 | 24,264 | 0/36 | 756,94 |
| 10 | 18,452 | 43,052 | 0/36 | 398,70 |
| 25 | 31,412 | 54,885 | 2/36 | 191,93 |

La corrida previa con solo tokens compartidos observó 1 251,82/651,57/291,04
MiB para K=5/10/25. Se observó aproximadamente 39,5/38,8/34,1 % menos RSS;
incluye todo el proceso y el catálogo fijo, no memoria exclusiva de registros.
Son ejecuciones secuenciales: no se atribuyen todas las diferencias de tiempo
o RSS únicamente al cambio. Las consultas muestreadas con K=5/10 cumplen
50 ms aquí; no se garantiza otra corrida o secuencia.
[Resumen y condiciones](evidencia/k_oficial_registros_reutilizados_memoria_juan.json).

```powershell
python -X utf8 -u -m modelo.bench_k_oficial --valores-k 10 5 25 --salida-json resultado.json
```

K definitivo sigue pendiente porque los ciclos aún incumplen. Se conserva
25 provisional y no se cierra aceptación. Próximo trabajo: reducir picos de
creación/registro antes de decidir K. Avance global estimado: **93 %**.
