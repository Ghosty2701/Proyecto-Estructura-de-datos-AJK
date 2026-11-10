# Guía de validación: Resolubilidad

**Estado**: guía de la implementación verificada. --verificar y --forzar están
disponibles; 556 pruebas de regresión aprobadas. Evidencia enlazada al final.
Instalación del entorno y dependencias: [README](../../README.md).
Contrato de resultados: [verificacion.md](contracts/verificacion.md).

## Preparación

Desde la raíz, usar Python 3.11+ y dependencias de `documentacion/requirements.txt`.
Preparar datos sintéticos externos al código del juego con generales, páginas,
versión y `criptas/ID/llaves.json`; para iniciar, añadir contenido y catálogo
según el paquete offline existente. Elegir IDs del paquete o catálogo vigente;
ningún ID de ejemplo demuestra el resultado de una cripta oficial.

## Consultas disponibles

```powershell
python main.py --verificar ID --offline CARPETA
$LASTEXITCODE
python main.py --cripta ID --offline CARPETA
python main.py --cripta ID --forzar --offline CARPETA
```

Esperado: consulta soluble 0; no soluble 1; error 2. Una cripta no soluble bloquea
inicio normal y permite inicio explícito con forzar; un error de datos no puede
forzarse como si fuera un diagnóstico negativo. El reporte no marca exploración.

```powershell
python main.py --verificar ID --forzar
python main.py --verificar ID --replay partida.log
```

Esperado: error de uso sin red, creación de vista o inicio de otro modo.
Comprobar cargar/replay con los comandos existentes: sin nueva verificación
automática ni solicitud de ubicaciones de llaves.

## Aceptación y regresión verificadas

| Casos | Evidencia que se debe obtener |
| --- | --- |
| AC-RS-001 a 005 | Victoria completa, cadena de llaves, llave no consumida y supuestos; sala de salida sola no basta. |
| AC-RS-006/007 | Mismo orden/informe repetido; llave de enemigo en sala inicial. |
| AC-RS-008 | Frontera correcta; recíprocas únicas una vez; paralelas ambiguas separadas y aviso. |
| AC-RS-009/010 | Certificado completo y ciclo concreto para autobloqueo y cadena de dos llaves. |
| AC-RS-011 | Alternativa obtenible rompe el ciclo; alternativa dentro de grupo bloqueado se conserva en el certificado. |
| AC-RS-012 | Aislamiento y barreras sin llave no inventan ciclos; varias ubicaciones no se reducen a una arbitraria. |
| AC-RS-013 a 016 | Bloqueo/forzar, consulta sin vista, cero acciones/RNG/exploración y sin cambio en cargar/replay. |
| AC-RS-017 a 020 | Datos nuevos, presupuesto con reintentos, versiones coherentes y errores separados del veredicto. |

Añadir como regresión de diagnóstico el caso S→X(B) con accesos B o A y S→Y(A)
por A: no afirmar que B exige exclusivamente B. Añadir pasillos recíprocos sin
llaves para impedir que se confundan con ciclos de desbloqueo. Sustituir la vista
por un constructor que falle si se instancia en la consulta. Comparar con cierre
repetido de referencia en casos pequeños deterministas. Cada prueba cita FR/AC.

Los archivos y funciones ejecutados están referenciados en [tasks.md](tasks.md).
Ejecución general:

```powershell
python -m pytest -q
```

Revisar partidas, niebla, viajes, terreno/cazadores, guardado/replay y presupuesto
afectados por carga/normalización. No dar por verificada una tarea solo por crear
su archivo de prueba.

## Mediciones ejecutadas

```powershell
python main.py --bench
python main.py --bench --cripta ID
```

La integración conserva opciones vigentes de repeticiones/semilla. Medir
incremental frente a recorridos repetidos en cadenas crecientes, muchos grupos,
alternativas y varias ubicaciones. Registrar preparación, cierre, diagnóstico,
presentación y total local; inicialización una vez, sin ocultar coste por llave
o componente. Excluir red y renderizado, no normalización ni índices.

Para PR-RS-001 identificar la mayor cripta publicada en ese momento, sus versiones
y solicitudes. Registrar equipo, Python, repeticiones, semilla y huellas de
código. Criterio <200 ms; documentar cualquier incumplimiento. Las cifras de
terreno/niebla no sustituyen esta medición.

Resultado de 2026-11-09: cripta-06, 300 salas, versión f9ed9afa683d, 25
repeticiones y máximo 7,5888 ms con texto, sin HTTP/vista en reloj; 10/63
solicitudes y cero ≥200 ms. Cripta-05 devolvió 1 y ciclo concreto.
Sintéticos: 9 cargas, tres repeticiones estructuradas, máximo total 38,1568 ms.
La cadena de 640 salas tuvo cierre incremental máximo 0,5847 ms frente a
110,9633 ms de la referencia repetida; su total incremental fue 18,9840 ms.
La referencia solo calcula cierre/veredicto, no certificados; comparar esas
columnas y el total por separado, sin afirmar una ventaja universal.

Evidencia: [pruebas](../../documentacion/evidencia/pruebas_resolubilidad.txt),
[mediciones](../../documentacion/evidencia/mediciones_resolubilidad.json) y
[salida de bench](../../documentacion/evidencia/bench_resolubilidad.txt).
