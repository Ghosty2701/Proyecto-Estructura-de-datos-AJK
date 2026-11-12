# Modelo de datos — Terreno y cazadores

**Fecha de diseño**: 2026-11-08. Implementado y verificado el 2026-11-09.
Fuentes: [spec.md](spec.md), [plan.md](plan.md) y [research.md](research.md).

## Estado persistente del juego

| Entidad | Datos pertinentes | Relaciones y validaciones |
| --- | --- | --- |
| SalaRastro | sala_id y lista de salidas existentes | ID estable; destinos pertenecen al esqueleto completo |
| SalidaRastro | destino, puerta, dirección y nuevo costo | costo entero ≥ 1; ausencia en datos equivale a 100; mismo costo en ambos sentidos |
| Puerta | abierta, llave y cierre automático existentes | Apertura/cierre/restauración coherentes en ambas direcciones |
| ActorTurnos cazador | comportamiento cazador y nuevo rango, además de estadísticas y sala | rango entero del catálogo, sin valor inventado por defecto; velocidad positiva |
| MotorEventos | reloj, agenda, historial y azar existentes | Los costos de movimiento alimentan la programación y reajuste de acciones existentes |

Se conserva la lista de salidas de cada sala como adyacencia. No se añade matriz ni
se descargan contenidos para conocer el trayecto. El cazador consulta las puertas vivas,
no los valores iniciales del JSON ni el conocimiento parcial del jugador.

El contrato de puertas exige coherencia de una misma conexión física en ambos sentidos.
El cargador crea hoy objetos por dirección: la integración debe preservar o corregir su
sincronización en apertura, cierre automático y retroceso, sin crear otro índice de grafo.

El costo de una acción en curso ya se expresa en su evento programado: no se reinicia
el movimiento al cambiar velocidad. La fórmula y semántica de intervalos siguen P1,
con costo de salida para moverse. Atacar y esperar mantienen sus costos.

## RegistroBusqueda — temporal, uno por sala alcanzada

| Campo lógico | Significado |
| --- | --- |
| sala_id / sala | Identidad estable y referencia al objeto del modelo |
| distancia | Menor costo encontrado desde el origen |
| primer_salto | Vecina del origen que inicia la mejor ruta; comparación por su ID |
| posicion_heap | Índice actual o -1 si no está en el heap |
| definitivo | Indica que fue extraído con etiqueta mínima |

La etiqueta se compara como `(distancia, primer_salto_id)`. Un costo igual con menor
primer salto también mejora el registro. El heap añade sala_id como desempate técnico
estable; no utiliza secuencia de eventos, orden del JSON ni orden de la tabla hash.
En el origen, de distancia 0, no hay primer salto real; cualquier etiqueta técnica de
raíz queda fuera del resultado observable.

Las salidas tienen costo positivo: todo predecesor de un camino mínimo al objetivo tiene
distancia menor que él. Por eso al extraer el objetivo ya se puede devolver su primer
salto si se respetaron las mejoras de etiqueta. No se devuelve al descubrirlo por primera vez.

## TablaDistancias — doble hashing propio

- Arreglo inicial de 32 casillas, vacía cada casilla al comenzar una búsqueda; no se
  dimensiona con todas las salas de la cripta.
- Claves: IDs enteros de sala. Dos dispersiones enteras propias y deterministas;
  no usar dict, set ni un generador aleatorio para distribuir claves.
- Para capacidad M potencia de dos, inicio `h1(id) & (M - 1)` y salto
  `(h2(id) & (M - 1)) | 1`. El salto es impar, entre 1 y M - 1, y coprimo con M.
- El sondeo visita `(inicio + i * salto) & (M - 1)` y compara IDs, sin confundir una
  colisión con igualdad. Se acota a M intentos para no entrar en un bucle infinito.
- Actualizar un ID existente modifica el registro, sin incrementar cantidad ni ampliar
  por una inserción inexistente.
- Antes de insertar un ID nuevo, si `(cantidad + 1) * 10 > M * 7`, duplicar y redistribuir.
  Reinsertar las mismas referencias a registros; cambiar su casilla no cambia su posición
  en el heap. El umbral y la capacidad inicial son los aprobados por el usuario.
- No necesita borrado por clave ni marcas de borrado para esta capacidad. Los registros
  definitivos siguen disponibles hasta terminar la búsqueda; después se libera el conjunto.

Las dos funciones de mezcla deben dispersar también IDs ordenados y conservar igualdad
de clave aunque haya colisiones. Sus constantes son detalles internos deterministas que
se documentan al implementar y se verifican con claves adversas; no cambian estas estructuras.

## HeapRutas — binario indexado propio

El arreglo contiene referencias a RegistroBusqueda. Como máximo hay una entrada pendiente
por sala. Insertar, extraer mínimo y mejorar prioridad mantienen el orden lexicográfico
por distancia, primer salto e ID de sala.

Cada referencia desplazada actualiza posicion_heap; extraer marca -1 y definitivo.
No se guardan índices de casilla hash como identidad del registro. Al redimensionar la
hash, el heap sigue apuntando a los mismos registros. No se mezcla con AgendaEventos.

## ResultadoRuta — un último resultado por cazador

Ampliación D-TC-09 (2026-11-12): el último resultado por actor se complementa
con `CacheRutas` por motor. La clave es identidad de origen/objetivo, rango y
revisión; el valor es el mismo ResultadoRuta, incluido el resultado sin ruta.
La tabla propia de doble hashing tiene 256 casillas y máximo 179 entradas.
Cuando otra inserción superaría el 70 %, se vacía; no crece ni retiene heap
o tabla de una búsqueda. También se vacía al invalidar conexiones o retroceder.
Es derivada: carga/copia crean una vacía y el esquema binario v6 la excluye.
Los contadores de aciertos/fallos/reinicios son diagnósticos y no son estado
reversible ni se persisten. La equivalencia con recalcular sigue siendo obligatoria.

| Campo lógico | Contenido |
| --- | --- |
| origen / objetivo | Salas de la consulta |
| rango | Rango usado |
| revision_conexiones | Revisión del estado de conexiones y costos usada al buscar |
| primer_paso | Salida o destino del primer paso, o ausencia de paso |
| costo_total | Distancia mínima si se encontró ruta dentro del rango |
| encontrada | Distingue una ruta encontrada de ausencia de ruta dentro del rango |

El caso sin ruta dentro del rango no afirma si hay una ruta más cara fuera de él: ambas
situaciones producen espera. Si comparten sala, se ataca antes de consultar esta búsqueda.

Solo se retiene este registro, no la tabla ni el heap de su búsqueda. Consultas con iguales
origen, objetivo, rango y revisión pueden reutilizarlo, también para esperar. Al moverse
un actor cambia su sala y la consulta deja de coincidir.

## Revisión e invalidación conservadora

Una revisión escalar monotónica del contexto de conexiones cambia al abrir/cerrar puertas
o modificar conexiones/costos. Una puerta lejana también invalida; no hay dependencias
selectivas ni escaneo de todas las puertas para comprobar validez.

Carga y retroceso vacían los últimos resultados o avanzan a una nueva revisión del contexto
restaurado; nunca restauran una revisión antigua y la usan para validar datos de otra
historia. Este metadato es derivado y no consume azar ni tiempo virtual. Velocidad,
movimiento o muerte de otros actores no cambian por sí solos las distancias si la regla
de rutas no los considera obstáculos; se comprueba de todas formas equivalencia con recalcular.

## Persistencia y ciclo de vida

- Añadir costo a la salida y rango al cazador en el esquema explícito, validaciones y
  proyección de lectura selectiva de sala. La versión actual del modelo es 3: el esquema
  ampliado debe usar una versión nueva y rechazar guardados incompatibles anteriores.
- La carga conserva identidad de cripta/catálogo y referencias de salas/puertas/actores.
- Tabla, heap, revisión derivada y ResultadoRuta no son historial del juego ni se
  serializan como campos de la partida. Se reconstruyen/invalidan sin alterar resultados.
- La reversión restaura el estado del juego mediante los deltas existentes e invalida
  decisiones derivadas; no toma snapshots nuevos por turno ni modifica la regla del pergamino.

Los cambios futuros de línea de tiempo pertenecen a su propia especificación; este esquema
debe admitir ampliación posterior sin afirmar que ya conserva una línea de tiempo de P2.
