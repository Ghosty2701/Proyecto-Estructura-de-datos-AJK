# Reutilización de registros completos (2026-11-12)

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
[Resumen](evidencia/historias_registros_reutilizados_abba_juan.json).

```powershell
python -X utf8 -u -m modelo.bench_presupuestos --comparar-captura 537db26 --k 25 --salida-json resultado.json
```

La referencia anterior recibe solo la raíz y no reutiliza registros; ambas
variantes usan el mismo reconstruidor vigente. El formato del punto debe ser
compatible para esta comparación. Los presupuestos y K definitivo siguen
pendientes. Avance global estimado: **93 %**.
