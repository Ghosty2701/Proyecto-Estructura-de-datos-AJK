# Guía de validación: Línea de tiempo

**Estado**: guía planificada; la funcionalidad aún no está implementada.
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

El bench informa, para K = 10/25/50/100 y sin puntos: memoria total, tiempo de
consulta (máximo y percentiles) con ≥ 5 000 acciones, costo de crear un punto y
ciclo máximo. También compara adelante frente a atrás y copia propia frente al
serializador. Con esos datos se elige el K por defecto (D-LT-07) y se registra
en el Documento de Decisiones.
