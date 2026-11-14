# Contrato: Aplicación, órdenes y presentación gráfica

**Estado**: diseño para implementación futura. Reglas en [spec.md](../spec.md)
y entidades en [data-model.md](../data-model.md). No contiene código ejecutable.

## Entrada y dependencia opcional

- `python main.py --interfaz pygame` abrirá el menú sin exigir una cripta.
- Se admitirán `--cripta ID` o `--cargar ARCHIVO` para preparar directamente
  una sesión. Los dos siguen siendo mutuamente excluyentes.
- Los argumentos actuales de semilla, nombre, guardado, puntajes, caché, paquete
  offline, bitácora y K mantendrán significado. Sin `--interfaz`, consola conserva
  sus validaciones; `--interfaz consola` las selecciona explícitamente.
- No combinar gráficos con `--listar`, `--verificar`, `--replay`, `--hasta`,
  `--ver-puntajes`, `--sin-interfaz` o `--bench`: error de uso, código 2, antes de importar Pygame
  o crear fuente de datos. Menú y puntajes gráficos son operaciones de la ventana.
- `--forzar` conservará su restricción a una nueva cripta. En el menú, un informe
  no resoluble requerirá una elección explícita equivalente, sin ocultar errores.
- La dependencia gráfica se instalará desde un archivo opcional; no será importada
  por el modelo, la consola, los adaptadores ni los modos sin vista.

## Propiedad de la sesión y resultado compartido

La ventana entrega una `IntencionGrafica` al coordinador. El trabajador valida
generación, revisión y objetivo, llama a la ejecución canónica compartida y
produce un `ResultadoOperacion` y una `PresentacionGrafica` inmutables.

La extracción del resultado debe conservar el contrato booleano de
`Controlador.procesar()` para la consola. Puede exponerse como método compartido
o resultado adicional del controlador; no se deduce de textos de mensajes.
El registro sigue siendo único y usa la misma normalización existente.

Cuando el controlador compartido se ejecute en el trabajador, su `vista` será
un receptor de valores sin Pygame: recopilará mensajes, mapa, inventario e
historia para el resultado de la operación. No se le pasará la vista gráfica
real ni invocará pantalla, fuentes, eventos o superficies desde ese hilo.

| Clase de resultado | Efecto en juego | Efecto en recuerdos |
|---|---|---|
| Acción aceptada | Reglas/costos vigentes; registrar una orden | Un delta y observación actual |
| Retroceso aceptado | Consumir pergamino, contador -1 y registro canónico, tanto por `retroceder` como por `usar` | Restaurar y retirar el delta coincidente, sin añadir otro |
| Navegación de inventario | Sin tiempo; `sig`/`ant` se registran | Sin observación nueva |
| Consulta de mapa, ayuda, orden o historia | Sin tiempo, azar ni orden de simulación | Sin cambios |
| Rechazo | Sin orden inexistente ni tiempo/azar | Sin cambios |
| Guardado | Estado/registro intactos; archivo completo | Exportación opcional en ese archivo |
| Carga correcta | Sustituir con sesión candidata válida | Importar o reiniciar memoria; selección invalidada |
| Salida | No aceptar más órdenes | Liberar sesión sin guardado automático |

## Controles y operaciones canónicas

| Control gráfico | Operación existente | Reglas especiales |
|---|---|---|
| Direcciones y WASD/flechas | `ir N/S/E/O` | Una pulsación inicial aceptada; ignorar repetición automática |
| Abrir salida seleccionada | `abrir DIRECCIÓN` | Revalidar dirección/puerta y aplicar llaves actuales |
| Seleccionar enemigo y atacar | `atacar k` | Resolver índice base 1 de enemigos presentes; no atacar otro por índice obsoleto |
| Esperar / espacio | `esperar` | Una acción, sin temporizador repetitivo |
| Objeto del suelo y recoger | `recoger k` | Índice vigente de suelo y capacidad actual |
| Inventario y selección | `inv`, `sig`, `ant` | Un clic directo emite la navegación necesaria en orden; no asigna el cursor físico |
| Ordenar inventario | `orden peso/valor/nombre` | Solo presentación; mantener correspondencia con posición real |
| Usar, equipar y soltar | Órdenes homónimas | Operar sobre el cursor canónico validado |
| Retroceder / R | `retroceder` | Reglas de pergamino; revertir memoria solo si se aceptó |
| Mapa / M y destino | `ver mapa`, `ir a ID` | Solo destinos explorados; conexiones recordadas |
| Historia / H | `historia t` o `historia #k` | Panel identificado como pasado, sin completar con datos presentes |
| Guardar / F5 y cargar / F9 | `guardar`, `cargar` | No registrar como acciones; cargar no disponible durante grabación |
| Ayuda / F1 | `ayuda` | Sin turno |
| Salir y cierre de ventana | `salir` | Sin guardado automático |

Para un clic de inventario que exige varios `sig`/`ant`, el lote es únicamente
la navegación necesaria para esa selección, sin turnos y sin acciones de combate
en cola. Se publica su cursor final. Usar/equipar requieren una activación
posterior deliberada sobre esa presentación. Si la selección deja de ser válida,
no se la sustituye automáticamente por otro objeto.

La clasificación se obtiene del resultado real de la operación, no del nombre
del botón: `usar` un pergamino también es retroceso. Una carga tiene su propia
clase de resultado y no se clasifica por la diferencia entre el contador de la
partida antigua y el de la cargada.

## Entrada, ocupación y viaje

El trabajador procesa una operación por vez mediante un buzón de capacidad uno,
con sincronización estándar. La ventana no consulta el modelo al dibujar ni
durante una operación. Acciones nuevas mientras está ocupado se rechazan o
ignoran con indicación visual; no se acumulan para ejecutarse más tarde.

Excepción delimitada: durante un viaje se admite **una sola intención
interruptora**, retenida hasta concluir el paso ya aceptado. Detiene/cancela
cualquier paso nuevo, se revalida contra la presentación resultante y se ejecuta
una sola vez. Si su objetivo quedó obsoleto, el viaje permanece detenido y se
informa el rechazo. Las activaciones adicionales se ignoran. Detener no crea
una orden ni tiempo de juego; cerrar tiene prioridad sobre la intención retenida.

Esta intención interruptora puede proceder de la revisión anterior al paso:
se admite en la misma generación y se revalida/rebasa por identidad sobre la
presentación resultante. No se rechaza automáticamente por ese incremento de
revisión ni se reutilizan índices antiguos. Órdenes sin objetivo, como detener
o retroceder, se validan contra las reglas de la sesión resultante. Las demás
intenciones obsoletas siguen rechazándose normalmente.

El paso compartido conserva ruta conocida → movimiento ordinario → registro
`ir DIRECCIÓN` → observación/presentación → parada por llegada, enemigos, daño,
terminación o pérdida de ruta. El comentario `# ir a ...` no es un turno.
La consola consume esos pasos con su política actual; gráficos vuelve al ciclo
de eventos antes del siguiente. No avanza mientras espera un resultado ni
después de perder foco. Perder foco cancela el viaje y la intención interruptora
aún no ejecutada; reanudar requiere una nueva orden de viaje. Una operación ya
aceptada termina de forma segura y no se repite.

## Proyección y privacidad

- Sala actual: estado observable y objetivos con identidad/tipo explícitos;
  el tipo de sprite no se obtiene analizando el nombre formateado del enemigo.
- Salas avistadas: solo datos que permita la proyección del conocimiento, sin
  enemigos, objetos ni etiquetas que revelen su contenido.
- Salas exploradas: conexiones y puertas recordadas. Enemigos remotos: únicamente
  observaciones previas, con marca textual de recuerdo y su instante observado.
- Sin observación no equivale a observada vacía. La antorcha no produce observaciones
  de contenido. La vista nunca recibe `partida.enemigos` ni actores remotos.
- El mapa/cámara se construye solo con la proyección conocida; no reservar
  casillas visibles ni mostrar límites basados en todas las salas físicas.
- Historia: mostrar el resumen y mapa históricos, sin superponer los recuerdos
  remotos actuales. Regresar cierra ese panel y presenta el estado vivo intacto.

## Recursos, fallos y resultados

Preparar una sesión nueva o carga candidata sin modificar la sesión activa.
Solo publicarla cuando concluyan validaciones de juego. Un error conserva la
sesión válida y se presenta en la ventana. Las validaciones visuales opcionales
no convierten una carga de juego válida en un error fatal.

Las operaciones de red y IO pertenecen al trabajador; nunca al dibujo. El cliente
podrá recibir una señal opcional de cancelación para detener esperas 429 o nuevos
intentos al cerrar. No alterar sus defaults, conteo ni reservas. Una solicitud ya
iniciada conserva su timeout; no afirmar cancelación inmediata de `requests.get`.
Una acción ya aceptada termina de forma segura antes de liberar su sesión.

Cerrar invalida generaciones/intenciones, detiene el viaje y no inicia guardados.
Liberar el escritor de bitácora y el trabajador ordenadamente; no matar hilos
durante escrituras. El resultado de victoria/derrota se registra una sola vez por
sesión, al finalizar, y no otra vez al volver al menú o cerrar la ventana.

## Evidencia requerida

Correspondencia con AC-IG-001 a AC-IG-023 en la matriz de [plan.md](../plan.md).
Se probarán registros únicos, igualdad de estado/azar entre interfaces, navegación
de inventario, revisión obsoleta, cierre durante red, interrupción durante viaje,
partidas consecutivas y los modos sin dependencia gráfica. Los controles de vídeo
de prueba no sustituyen la revisión visual ni el teclado físico.
