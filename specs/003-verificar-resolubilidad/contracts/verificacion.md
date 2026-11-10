# Contrato: Datos, consulta y comienzo de partida

**Estado**: contrato implementado y verificado; evidencia en [tasks.md](../tasks.md).
Fuentes: [spec.md](../spec.md), [modelo de datos](../data-model.md) y
[evidencia OpenAPI](../../../documentacion/evidencia/contrato_resolubilidad_openapi_2026-11-09.json).
No se modifica el servicio remoto.

## Fuente de ubicaciones

Operación local: `ubicacion_llaves(cripta_id)` en FuenteDatos,
ClienteHTTP y ModoOffline. HTTP: `GET /v1/criptas/{cripta_id}/llaves`, usando
el `_get` existente, con su presupuesto, reintentos y tratamiento de errores.

Forma de respuesta, ejemplo sintético:

```json
{"llaves": [{"id": "llave_ejemplo", "sala": 7, "enemigo": null}]}
```

`id` y `sala` son requeridos; `enemigo` es opcional/nulo e identifica una
instancia, no una ficha de catálogo. Pueden existir varias ubicaciones del mismo
ID. No se exige campo `version` en esta respuesta. Se asocia con identidad y
versión de datos generales y se contrasta la versión de la carga mediante la
consulta existente. Esa solicitud y cualquier reintento también cuentan.

Offline: `criptas/ID/llaves.json` con la misma envoltura; generales y versión
coherentes. Falta, JSON inválido o referencias inválidas producen error. Lecturas
de disco mantienen cero solicitudes de red. No descargar contenidos para inferir
ubicaciones ni suponer el movimiento futuro de un enemigo.

## Preparación reutilizable

El servicio obtiene generales, páginas y ubicaciones una vez; el verificador
normaliza directamente listas con sus índices propios. No requiere construir
el AVL del juego, actores, motor ni conocimiento del jugador.

Al permitir el comienzo de una partida nueva, entregar esos mismos datos
validados al cargador; puede construir las entidades/índices heredados sin
repetir consultas. Una función de normalización compartida impide que el
verificador y el juego interpreten puertas de forma diferente.

Recíprocas compatibles comparten puerta solo si existe un emparejamiento único;
no presuponer direcciones opuestas a partir del Swagger. Compatibilidad de
estado/llave/cierre no sustituye las validaciones vigentes de costes de terreno.
En ambigüedad conservar conexiones separadas y avisar, sin fusionar puertas
distintas ni rechazar automáticamente una cripta válida.

## CLI

| Orden | Comportamiento implementado |
| --- | --- |
| `--verificar ID` | Solo prepara, verifica e imprime; sin VistaConsola, CargadorPartida interactivo, motor o simulación. |
| `--verificar ID --offline CARPETA` | Consulta equivalente sin HTTP. |
| `--cripta ID` | Verifica antes de crear la partida; imprime informe; resultado negativo bloquea inicio. |
| `--cripta ID --forzar` | Permite empezar con resultado negativo; mantiene informe, datos y reglas. |
| `--cargar ARCHIVO` / `--replay LOG` | Conservan sus validaciones; no incorporan consulta nueva de llaves ni bloqueo por resolubilidad. |
| `--bench` | Mide cargas sintéticas sin vista; añade comparación de resolubilidad a las comparaciones vigentes. |
| `--bench --cripta ID` | Añade procesamiento de datos de referencia, separando red y tiempos locales; un diagnóstico negativo puede medirse, no representa inicio interactivo. |

`--verificar` no se combina con otros modos (`--cripta`, `--cargar`, `--replay`,
`--bench`, `--listar`, `--ver-puntajes`) ni `--forzar`; rechazar con explicación
antes de cargar datos. `--forzar` requiere inicio de partida nueva y no permite
ignorar un error de obtención/validez. Opciones de fuente compatibles siguen
disponibles. No ampliar opciones ajenas a esta capacidad.

En `--verificar`, códigos 0 resoluble, 1 no resoluble, 2 error de datos o uso que
impide completar la consulta. El texto también distingue los tres casos. No
reinterpretar los códigos existentes de carga/replay u otros modos.

## Informe y no mutación

El resultado positivo imprime un orden válido determinista. El negativo incluye
llaves no obtenibles y sus ubicaciones, frontera con puertas/llaves y certificados
circulares cuando correspondan. Cada certificado muestra grupo, puertas,
alternativas y un ciclo concreto; no atribuye a cada flecha exclusividad entre
todas las rutas. No basta imprimir «hay un ciclo» ni solo una componente sin
testigo. Las tablas compartidas permiten explicar referencias sin repetición
cuadrática de ubicaciones o alternativas.

Los avisos de identidad física se distinguen del veredicto y del error de datos.
El diagnóstico hipotético nunca se presenta como adquisición real de llaves.
Verificar no consume acciones, reloj o RNG ni altera inventario, actores,
historial o conocimiento. El reporte no concede destinos a `ir a`.

El formato textual puede evolucionar sin alterar el contenido exigido; no se
introduce un modo JSON obligatorio ni un esquema nuevo de partida guardada.
