# Guía de validación prevista: Interfaz con Pygame

**Estado**: planificación terminada; interfaz, pruebas y dependencias opcionales
todavía no implementadas. Los comandos de las secciones «después de implementar»
son el contrato previsto de uso, no funcionalidades ya disponibles en esta rama.
Requisitos: [spec.md](spec.md). Contratos: [interfaz](contracts/interfaz-grafica.md)
y [recuerdos v6](contracts/recuerdos-v6.md).

## Comprobaciones disponibles ahora

Desde la raíz de `005-interfaz-pygame`, con Python 3.13.2 como referencia:

```powershell
python -m pytest -q
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec
```

La regresión de referencia conocida tiene 759 pruebas; una ejecución futura
debe registrar su resultado real. La comprobación de spec-kit debe encontrar
la capacidad 005, plan, investigación, modelo de datos, contratos y esta guía.
Encontrar documentos no significa que la interfaz esté implementada.

## Instalación y arranque después de implementar

El archivo opcional previsto incorporará `-r requirements.txt` y `pygame==2.6.1`;
no se añadirá Pygame a los requisitos base.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r documentacion/requirements-pygame.txt
.\.venv\Scripts\python.exe main.py --interfaz pygame
```

Resultado esperado: ventana de inicio con elección de cripta, nombre, semilla,
origen de datos, carga, puntajes y salida; todavía sin turno ni solicitudes
de contenido de una partida no iniciada. Seleccionar una cripta no resoluble
mostrará el informe y exigirá forzar de forma explícita para comenzarla.

## Preparar datos sintéticos reproducibles

El helper de pruebas actual crea un paquete offline de seis salas y datos de
pergaminos, antorcha, enemigo guardián, errante y cazador. Es exclusivamente una
carga de prueba; no modifica las reglas ni los datos de producción. Esa carga
no suministra la llave de salida, por lo que la verificación no la acepta para
un inicio normal: para estos recorridos se elige forzar explícitamente.

```powershell
python -c "from pathlib import Path; from Pruebas.datos_linea_tiempo import escribir_paquete; escribir_paquete(Path('resultados/bench/pygame-datos'))"
```

Después de implementar la entrada gráfica:

```powershell
.\.venv\Scripts\python.exe main.py --interfaz pygame --offline resultados/bench/pygame-datos --cripta lt --semilla 2026 --forzar
```

Para el caso de cinco retrocesos se prepara una segunda carga con cinco
pergaminos en la entrada mediante el parámetro existente del helper:

```powershell
python -c "from pathlib import Path; from Pruebas.datos_linea_tiempo import escribir_paquete; escribir_paquete(Path('resultados/bench/pygame-cinco-pergaminos'), objetos_entrada=['pergamino']*5)"
.\.venv\Scripts\python.exe main.py --interfaz pygame --offline resultados/bench/pygame-cinco-pergaminos --cripta lt --semilla 2026 --forzar
```

Recoger los cinco pergaminos respetando capacidad y costo, ejecutar cinco
esperas y comprobar cinco retrocesos aceptados. Probar tanto el botón de
retroceder como seleccionar un pergamino y pulsar usar. El recorrido con
enemigos y antorcha se realiza por separado con la primera carga.

## Recorrido de aceptación gráfica futuro

1. Verificar sala actual, vecinas avistadas y ausencia de contenido oculto.
   Encender antorcha mediante el inventario: su revelación no crea recuerdos
   de enemigos en salas donde no se entró.
2. Entrar a una sala con enemigos, observar sus sprites y salir. Provocar un
   movimiento remoto: los sprites recordados no lo siguen. Regresar actualiza
   la observación. Distinguir recuerdo, falta de observación y sala observada vacía.
3. Ejecutar cada operación de AC-IG-009 mediante botones, incluidos orden y
   selección de inventario. Comparar reloj, azar, órdenes y continuación con
   una sesión equivalente de consola; no usar el cursor del ratón como regla del juego.
4. Mantener una tecla y repetir entradas durante una operación: no deben
   producir turnos automáticos ni una cola. Dejar inactiva la ventana 60 segundos
   y redibujar 300 veces sin cambiar reloj, azar ni registro.
5. Viajar y detener, cambiar de orden o retroceder entre pasos. Probar también
   una interrupción recibida mientras termina un paso: ejecutar una vez la
   intención válida y no iniciar otro paso. Comprobar daño, enemigos y ruta perdida.
6. Consultar `historia t` y `historia #k` desde el panel, volver al presente y
   confirmar que no se mezclaron recuerdos. En la carga específica, usar cinco pergaminos, generar una
   rama nueva en el mismo instante y comprobar retirada de observaciones futuras.
7. Guardar y cargar; repetir con un v6 sin clave visual, uno con carga visual
   semánticamente inválida y otro re-guardado desde consola. No confundir ese
   caso con un archivo binario físicamente corrupto, que debe rechazarse.
8. Probar un mapa sintético de 300 salas, IDs dispersos, ciclos y posiciones
   cardinales conflictivas. No hay casillas solapadas; los enlaces ajustados
   están marcados y todas las salas/acciones son alcanzables con cámara/paneles.
9. Redimensionar, cambiar foco y cerrar durante viaje/carga de datos. La ventana
   sigue atendiendo eventos, no guarda automáticamente y libera su sesión.
   Victoria/derrota registra un solo resultado incluso al volver al menú.

Guardar capturas y resultados bajo `resultados/bench/pygame/`, junto con versión
de datos, semilla, Python y biblioteca gráfica utilizados. No declarar aprobados
teclado físico, legibilidad o foco solo por una prueba automatizada de vídeo.

## Pruebas automatizadas previstas después de implementar

```powershell
python -m pytest -q Pruebas/prueba_sesion_grafica.py Pruebas/prueba_memoria_visual.py Pruebas/prueba_guardado_grafico.py Pruebas/prueba_mapa_grafico.py Pruebas/prueba_cli_pygame.py
python -c "import os; os.environ['SDL_VIDEODRIVER']='dummy'; import pytest; raise SystemExit(pytest.main(['-q','Pruebas/prueba_eventos_pygame.py']))"
python -m pytest -q
```

La configuración de vídeo de prueba queda limitada a ese proceso. Añadir
pruebas de las primitivas del coordinador: un trabajador, objetivos obsoletos,
error de carga sin reemplazo y cierre sin abandonar una escritura.

## Verificar que gráficos sigue siendo opcional

En otro entorno con solo `documentacion/requirements.txt`, ejecutar las pruebas
base y los modos consola, listar, verificar, replay, puntajes y bench. Deben
funcionar sin importar Pygame ni inicializar vídeo. No es necesario repetir el
benchmark largo por cada edición documental: las pruebas de integración y
modos usan cargas pequeñas, y las mediciones se ejecutarán al implementar la
capacidad afectada. EX-01 se conserva y no certifica rendimiento gráfico.

## Criterio para pasar a implementación

El plan, las decisiones, el modelo de datos y ambos contratos están documentados.
Las 53 tareas están en [tasks.md](tasks.md) y el análisis de consistencia previo
ya se realizó, sin bloqueos críticos/altos identificados. El próximo paso es
`$speckit-implement`, comenzando por T001. Esta guía no afirma que se hayan
ejecutado las pruebas futuras ni sustituye la evidencia por escenario.
