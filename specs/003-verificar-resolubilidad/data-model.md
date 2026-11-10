# Modelo de datos: Verificación de resolubilidad

**Estado**: diseño, sin implementación. Estructuras aprobadas en [research.md](research.md).
Los nombres describen registros previstos; no amplían reglas de [spec.md](spec.md).

## Entrada validada y normalización

| Registro | Campos y relaciones | Validación |
| --- | --- | --- |
| Datos de cripta | ID, versión, sala inicial, sala de salida, llave de salida; salas y ubicaciones de la misma carga | Identidad y versión coherentes; extremos y ubicaciones referencian salas existentes. |
| Sala compacta | Posición 0..S-1, ID externo entero, lista de salidas y de ubicaciones de llaves | IDs de sala únicos; no indexar por el ID máximo. |
| Salida | Origen, dirección N/S/E/O, destino por posición, coste, registro de puerta | Referencias válidas; coste normalizado según terreno; no perder dirección por compartir puerta. |
| Puerta | Posición local, estado inicial, llave opcional, cierre automático, una o dos salidas identificadas | Compartir solo recíprocas compatibles con emparejamiento único. Costes conservan simetría vigente de terreno; sin emparejamiento no fusionar. |
| Aviso de identidad | Salidas involucradas y motivo del emparejamiento ambiguo | Se informa y conserva separación; no convierte por sí solo un dato válido en error. |
| Llave | Posición compacta, ID textual, lista de ubicaciones | Un ID puede tener varias ubicaciones: no rechazarlo como duplicado de sala. |
| Ubicación | Índice de llave, sala por posición, instancia de enemigo opcional | enemigo puede ser null; sala indica la posición inicial del enemigo según la fuente. |

La respuesta de `/llaves` no requiere un campo versión: se asocia a los datos
generales y se valida la estabilidad de versión de la carga. La entrada
reutilizable conserva datos leídos para iniciar después sin volver a pedirlos.
No hay nueva persistencia de ubicaciones ni cambios del formato binario.

La ausencia/null de llave en una puerta cerrada no crea una llave inventada:
no es transitable bajo los supuestos. No rechazarlo por una restricción ausente
del contrato. Normalizar campos opcionales siguiendo las reglas existentes;
no confundir JSON válido con referencias de sala inválidas.

## Índices aprobados

- Salas: IndiceSalas propio adaptado/reutilizado, entero → posición compacta.
- Llaves: índice propio texto → posición; mezcla reproducible descrita en
  research.md. Capacidad potencia de dos, carga de reserva máxima 70 %, paso
  impar y sondeo acotado. Comparación completa de clave para resolver colisiones.
- Reservar usando cantidad de salas y una cota de IDs de llave en puertas y
  ubicaciones. No crecer durante el cierre; memoria de reserva puede ser O(E+U).
- La posición de casilla hash no decide orden de adquisición o impresión.

## Estado del cierre real

| Campo | Representación aprobada | Transición |
| --- | --- | --- |
| Sala descubierta/procesada | Marcas en arreglo por sala | No descubierta → encolada → procesada, sin volver atrás. |
| Llave obtenida | Marca por posición de llave | Falsa → verdadera al alcanzar cualquiera de sus ubicaciones. |
| Orden de llaves | Lista de posiciones | Agregar solo la primera obtención. |
| Salas pendientes | Lista y cursor FIFO | Agregar al descubrir; avanzar cursor al procesar. |
| Puertas pendientes | Lista agrupada por llave | Registrar desde origen alcanzado; activar una vez al obtener llave. |
| Evidencia de victoria | Registro del acceso válido a la salida | Solo con llave de salida obtenida y una salida habilitada que la requiere. |

El cierre real produce el veredicto y la región alcanzable. No utiliza el
inventario ni estados físicos del juego como almacenamiento auxiliar.

## Diagnóstico privado y certificados

| Registro | Campos y relaciones |
| --- | --- |
| Conectividad física | Marca de sala accesible ignorando cerraduras abribles; marca de llave con alguna ubicación accesible. |
| Cierre diagnóstico | Marcas/cola privadas, sembrando hipotéticamente llaves físicamente aisladas; no altera el cierre real. |
| Regla de desbloqueo | Conclusión, origen, llave requerida si procede, salida/ubicación de procedencia y alternativa correspondiente. |
| Enlace negativo | Regla, antecedente falso elegido y conclusión; índices de incidencias directas e inversas. |
| Imposibilidad estructural | Referencia a origen/ubicación aislada o barrera cerrada sin llave; no etiquetarla como ciclo. |
| Componente | Lista de nodos y marcas de pertenencia; indicación de enlaces externos. |
| Certificado | Grupo cerrado con llave, todas sus alternativas y referencias a puertas/ubicaciones; ciclo concreto que contiene una llave. |

Conservar todas las alternativas de una conclusión, aunque para cada regla
conjunta baste seleccionar un antecedente falso para el enlace negativo.
Una llave residual apunta a todas sus ubicaciones físicamente accesibles;
las aisladas quedan justificadas expresamente, no descartadas silenciosamente.

Kosaraju iterativo usa arreglos de marcas, orden de finalización y pilas propias.
La búsqueda del ciclo se limita a una componente por testigo, sobre componentes
disjuntas. Inicializar marcas una vez. Ninguno de estos registros se incorpora
a guardados, niebla o historial: la verificación es una consulta sobre datos.

## Resultado

- Veredicto, identidad y versión utilizadas.
- Si es resoluble: orden válido reproducible y acceso que acredita la salida.
- Si no: llaves no obtenibles, frontera del cierre real, ubicaciones, avisos
  de identidad de puertas, grupos certificados y ciclos concretos.
- Tablas compartidas con referencias entre registros: no repetir todas las
  ubicaciones de una llave en cada puerta ni sus alternativas en cada línea.
- Error de obtención/validez se propaga como error, no como un resultado negativo.

El controlador/CLI presenta estos datos. El modelo no importa HTTP ni la vista.
