# Auditoría de integridad y actualización

**Fecha**: 2026-11-09, America/Guatemala.
**Estado revisado**: 02284ba, más la aclaración de resolubilidad recibida en esta sesión.
**Alcance**: código local, dependencias, pruebas, documentos, trazabilidad,
versiones de evidencia y estado remoto. No es certificación de capacidades futuras.

## Resultado

No se encontraron fallos en la suite ejecutada ni corrupción de objetos Git.
Se detectaron referencias documentales desactualizadas y se corrigieron sin
modificar código de producción ni elecciones de estructuras.

| Comprobación | Resultado |
| --- | --- |
| Pruebas completas | 492 aprobadas en 5,03 s |
| Sintaxis de producción | 34 archivos analizados mediante AST, sin errores |
| Dependencias | pip check: No broken requirements found |
| CLI existente | main.py --help termina correctamente; no anuncia verificar/forzar aún |
| Enlaces Markdown locales | Ninguno roto en README, constitución, specs y documentación revisada |
| Terreno/cazadores | 38/38 tareas completadas; 14 FR, 3 PR y 19 AC únicos |
| Niebla/viaje | 30/30 tareas completadas; 17 FR, 3 PR y 22 AC únicos |
| Resolubilidad | 15 FR, 3 PR y 20 AC únicos; en aclaración, sin plan/tareas/código |
| Checklist de resolubilidad | 16/16 antes y después; sin cambio de marcadores |
| Código de estructuras nuevas | Sin imports de heapq, bisect, collections o networkx ni uso de sorted/list.sort |
| Datos oficiales en código | No se encontraron IDs/versiones oficiales codificados en producción |
| Evidencia final de niebla | Todas sus huellas SHA256 coinciden con el código actual |
| Git remoto | fetch origin y comparación HEAD...origin/main: 0/0 al comenzar la auditoría |

La auditoría comprueba restricciones según el alcance de cada problema evaluado;
los registros de datos y el despacho de comandos no son índices evaluados. No se
prohíben usos de datos que la constitución no prohíbe.

## Correcciones documentales

- Terreno/cazadores ya no aparece como Draft o con contratos sin implementar.
  Se actualizan estado de pruebas, notas y referencias al cierre ejecutado.
- Niebla ya no dice que sus estructuras, tareas o mediciones estén pendientes.
  Se conservan las explicaciones de alternativas y las cifras históricas.
- Documento de Decisiones: el inventario reversible está integrado; el cierre
  histórico de terreno con esquema 4 se distingue del vigente esquema 5.
- README incorpora la especificación de resolubilidad como trabajo en aclaración;
  no anuncia --verificar ni --forzar como funcionalidades implementadas.
- Se retira el informe temporal de sincronización inicial de la constitución.
  Los principios, versión 1.0.0 y fechas normativas permanecen sin cambios.
- La elección de alcance se registra en la especificación de resolubilidad:
  verificación automática solo al iniciar partidas nuevas; cargar y replay
  conservan sus validaciones existentes y no repiten el análisis.
- El prompt y su respuesta contextual se mantienen en la sesión agrupada 65,
  con texto literal y fecha, según la preferencia editorial del usuario.

## Evidencia, historial y límites

Especificaciones y diseño preceden al código en Git: 290f173 y 1071237 antes de
71b8c9b para terreno; 8c20823, 9a534fd, a1c83c2 y cb7ae25 antes de 257e23a para
niebla. Se verificó la relación de ancestros de esos commits.

Las huellas de las mediciones de terreno difieren del código actual porque son
anteriores a niebla. La primera medición de niebla difiere en bench_conocimiento.py
porque después se amplió su carga. Son evidencias históricas identificadas, no
resultados nuevos del código actual; no se sobrescriben sus huellas.

No se repitieron benchmarks durante esta auditoría: el código medido final no
cambió y sus huellas siguen válidas. Se mantienen sus resultados y límites:
máximo de ruta oficial 2,1130 ms; ciclo oficial 18,6757 ms; un ciclo sintético
alcanzó 21,7271 ms y no cumple 20 ms en esa muestra. No hay garantía para todas
las cargas o equipos.

git fsck --no-reflogs terminó con código 0 y sin corrupción reportada; enumeró
árboles no referenciados del repositorio local. La coincidencia remota se comprobó
antes de crear el commit de esta auditoría; ese commit es una actualización local.

Siguen pendientes la implementación y las mediciones de resolubilidad, y la
capacidad de línea de tiempo. El original de P1 sigue ausente y la interrupción
de teclado físico no se probó manualmente; las pruebas existentes usan entrada
inyectada. Las 492 pruebas verifican los escenarios que ejercitan y no prueban
por sí solas todos los comportamientos posibles.

## Comandos de verificación ejecutados

```powershell
python -m pytest -q -p no:cacheprovider --basetemp=.test_tmp/auditoria_general --tb=short
python -m pip check
python main.py --help
git fsck --no-reflogs
git fetch origin
git rev-list --left-right --count HEAD...origin/main
git diff --check
```

El ejecutable usado fue Python 3.14.6 instalado localmente; las verificaciones de
AST, enlaces, requisitos, tareas y huellas se ejecutaron mediante scripts de lectura.
