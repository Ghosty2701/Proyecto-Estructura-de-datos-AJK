## 🔵 Andrey

1. No se si puedas revisar lo que ya llevemos hecho y conectarte con el chat anterior de codex que teniamos para este proyecto

2. no tienes acceso al del web que se llama conffgurar pporyecto edd

3. Te voy a dar contexto de lo que estabamos hacien con este texto, tambien te voy a adjuntar unos archivos que tienen que ver con el proyecto

    1er promt utilizado

    Estoy desarrollando el proyecto universitario Cripta, de Estructuras de Datos II. Soy Andrey y necesito que me ayudes a continuar mi parte como tutor y revisor de código.

    Voy a adjuntar el enunciado original, una guía de roles y el proyecto actualizado. Lee esos documentos y el código antes de proponer cambios. El enunciado original tiene prioridad sobre la guía si existen diferencias.

    Te abri un pdf de igual manera para que lo puedas leer, dice primer pryecto - estructuras de datos ll 2026 

    de igual manera te abri un md que se llama cripta_guia_y_documento_desiciones (2).md



    REPARTO DEL EQUIPO

    - Andrey, yo: motor de simulación, agenda de eventos, retroceso y rastro del jugador.
    - Juan: red, prefetch, caché y persistencia, guardado binario y bitácora/replay.
    - Kendall: inventario, interfaz, bitácora de pantalla y ordenamiento.

    FORMA DE TRABAJAR CONMIGO

    Quiero implementar los cambios personalmente:
    1. Explícame brevemente qué vamos a resolver.
    2. Dime el archivo y la clase exactos donde debo colocar el código.
    3. Indica claramente si debo agregar un método o reemplazarlo.
    4. Dame bloques completos con la sangría correcta.
    5. Pásame pruebas automáticas y los comandos para ejecutarlas.
    6. Avancemos por etapas: espera los resultados antes de introducir otra integración grande.

    Cuando comparta un error, identifica su causa y dame una corrección concreta. Si varios errores se deben a copiar fragmentos incompletos, pásame el método completo.

    No modifiques las partes de mis compañeros sin coordinarlo. Cuando mi código dependa de una interfaz que todavía no existe, acuerda el contrato y usa un objeto simulado únicamente en las pruebas.

    No afirmes que ejecutaste pruebas si no lo hiciste. Distingue entre código revisado, pruebas ejecutadas, funcionamiento parcial e integración pendiente.

    ENTORNO

    Trabajo en Windows, PowerShell y VS Code.
    La última versión utilizada fue Python 3.14.6, con pytest y requests.

    Las pruebas deben ejecutarse desde la raíz del proyecto:
    python -m pytest -q

    Para un archivo concreto:
    python -m pytest Pruebas/nombre_del_archivo.py -v

    No ejecutar directamente los archivos de pruebas con el botón “Ejecutar archivo Python”, porque puede causar errores al importar modelo.

    REPOSITORIO

    https://github.com/Ghosty2701/proyecto-edd
    Rama: main.

    Si puedes acceder a GitHub, revisa el código más reciente y dime el commit que revisaste. Si no puedes acceder, pídeme los archivos necesarios y no supongas que ya viste su contenido.

    ESTADO QUE HABÍAMOS ALCANZADO

    Agenda:
    - Heap binario propio.
    - Prioridad por tiempo y luego secuencia.
    - Cancelación perezosa.
    - Reprogramación mediante un Evento nuevo y una secuencia nueva.
    - Protección contra reutilizar objetos Evento.
    - Funciones para calcular próxima acción y reajustar tiempos por velocidad.

    Motor:
    - ActorTurnos y EventoActor.
    - Referencias a eventos de cada actor mediante enlaces.
    - Programación de turnos, cambios de velocidad y cancelación por muerte.
    - Extracción del siguiente evento válido y avance del reloj.
    - Integración parcial con el historial reversible.

    Retroceso:
    - Historial de hasta cinco intervalos.
    - Deltas de vida, rastro, atributos y operaciones de eventos.
    - Restauración en orden inverso.
    - Restauración de reloj, velocidad, vida, posición y referencias a eventos en los casos probados.
    - No se guardan snapshots completos.

    Rastro:
    - Marca inicial en tiempo 0.
    - Refresco en acciones válidas y al completar movimientos.
    - Restauración al retroceder.
    - Solo es fresco si 0 <= antigüedad < 400.
    - El rastreador considera únicamente salidas abiertas.
    - Elige el rastro más reciente; en empate, menor ID de sala.
    - Si no encuentra destino, la futura lógica del enemigo debe esperar.
    - SalaRastro y SalidaRastro son representaciones mínimas, pendientes de integrar con las entidades completas.

    Pergaminos:
    - Se propuso usar_pergamino(jugador, es_pergamino).
    - Consumir uno queda fuera del historial.
    - Usarlo no crea una acción ni añade tiempo virtual.
    - Se probó con un inventario simulado.
    - El inventario real pertenece a Kendall.
    - El contrato propuesto es consumir_primero(condicion), que consume un objeto coincidente y devuelve True o False.
    - Falta verificar si Kendall ya implementó ese contrato.
    - Recoger y soltar pergaminos tampoco debe deshacerse. Esa excepción necesita pruebas de integración reales.

    ERROR DETECTADO EN UNA REVISIÓN

    En CambiosAccion.reprogramar_evento se cancelaba el original antes de validar el reemplazo. La corrección propuesta fue:

    def reprogramar_evento(self, agenda, anterior, nuevo):
        if anterior is nuevo:
            raise ValueError("La reprogramación requiere un evento nuevo")

        self.programar_evento(agenda, nuevo)
        self.cancelar_evento(agenda, anterior)
        return nuevo

    Verifica si el código actual ya incluye esta corrección.

    PRUEBAS Y BENCHMARKS

    Una revisión anterior del commit 14308a7 ejecutó 108 pruebas y todas pasaron. Esto es evidencia histórica, no garantiza el estado actual.

    Se preparó modelo/bench_modelo.py, ejecutable mediante:
    python -m modelo.bench_modelo

    Compara el heap con una lista ordenada implementada a mano, mide retroceso de vida/rastro y consultas de rastreadores.

    Resultados históricos en mi computadora:
    Python 3.14.6, Windows, semilla 2026, cinco repeticiones, menor tiempo observado.

    Carga inicial:
    - Agenda: 2000 inserciones, 500 cancelaciones, 1500 extracciones activas.
    - Heap: 10.704 ms.
    - Lista ordenada: 198.606 ms.
    - Retroceso: 2000 deltas, 0.317 ms.
    - Memoria parcial del registro: 160528 bytes.
    - Rastro, mapa de 4000 salas y cuatro salidas por sala:
      - 1 rastreador, 100 decisiones: 0.180 ms, 1.801 µs/decisión.
      - 100 rastreadores, 10000 decisiones: 22.248 ms, 2.225 µs/decisión.

    Carga mayor:
    - Agenda: 5000 inserciones, 1250 cancelaciones, 3750 extracciones activas.
    - Heap: 27.003 ms.
    - Lista ordenada: 1015.351 ms.
    - Retroceso: 10000 deltas, 0.955 ms.
    - Memoria parcial del registro: 805520 bytes.
    - Rastro, mapa de 10000 salas y cuatro salidas por sala:
      - 1 rastreador, 100 decisiones: 0.097 ms, 0.966 µs/decisión.
      - 500 rastreadores, 50000 decisiones: 46.476 ms, 0.930 µs/decisión.

    Todas esas cargas pasaron sus comprobaciones funcionales.

    No confundas:
    - El tiempo acumulado de miles de decisiones con un ciclo del juego.
    - La memoria parcial del registro con toda la memoria utilizada.
    - El mínimo de cinco repeticiones con una garantía de rendimiento.
    - Los benchmarks de estructuras con la validación del límite de 20 ms entre decisiones del jugador.

    Se redactó un borrador de mis secciones del DDD con seis puntos: problema, alternativas, decisión, complejidad, evidencia y límites. Verifica si ese borrador ya está incorporado al repositorio.

    PENDIENTES QUE DEBES VERIFICAR

    - Bucle completo de simulación y ejecución de comportamientos.
    - Límites correctos de cada intervalo reversible, incluida la extracción del turno del jugador.
    - Integración real con inventario y pergaminos.
    - Retroceso de los demás cambios: equipamiento, suelo, puertas, trampas y efectos.
    - Manejo del azar reproducible y su interacción con el retroceso según el enunciado.
    - Conexión de los rastreadores con movimiento y espera reales.
    - Medición del procesamiento completo entre decisiones.
    - Documentación y pruebas que todavía falten.

    RESTRICCIONES

    Respeta las restricciones del enunciado sobre estructuras propias. No uses heapq, deque, OrderedDict, sorted(), list.sort() ni dict como sustitutos de las estructuras evaluadas cuando estén prohibidos.

    No inventes resultados, reglas, responsabilidades ni requisitos. Las pruebas que pasan no demuestran por sí solas que el proyecto esté completo.

    EMPIEZA ASÍ

    Revisa los archivos actuales y dime:
    1. Qué está implementado y comprobado de mi parte.
    2. Qué fallas concretas encuentras, con ejemplos reproducibles.
    3. Qué falta y qué depende de mis compañeros.
    4. Cuál es el siguiente paso pequeño que puedo implementar yo.

    Después guíame con código y pruebas, una etapa a la vez.

4. una duda estamos creando un motor desde 0?

5. a todo esto, explicame un poco mas el por que de lo que agregamos esto ultimo con random

6. no crees que estamos haciendo muchos archivos de prueba, o cual es tu opinion con respecto a eso?

7. listo quedo muy chulo. no hay una manera de poder eliminar esos archivos?

8. para esa etapa veo que es todo un poco mas de lo mismo, entonces pasame todo el codigo de esta fase para implementarlo de una sola vez

9. lla siguiente fase de efectos temporales

10. recuerda que no hay que modificar nada de lo que hace juan ni kendall

11. lo de los efectos temporales van incluidos en las instrucciones del proyecto?

12. excelente deberiamos quitar los archivos del parche?

13. puedo eliminar la carpeta de entrega efectos entonces

14. revisa mi parte y busca optimizaciones pero  obviamente teniendo encuenta las instrucciones del proyecto

15. preferiria no cambiar el heap, ya que si es requerido por el proyecto, me gustaria que  en si continuaramos anadiendo funciones para poder terminar el trabajo, ya que tan solo quedan 3 dias

16. revisa bench adaptadores.py

## 🟣 Kendall

1. Actúa como un arquitecto de software y líder técnico experto en Python y Estructuras de Datos.

    Tengo que desarrollar un proyecto universitario llamado "Cripta", un juego de mazmorra dirigido por eventos (sin rondas, basado en un reloj virtual determinista) escrito en Python 3.11+. El objetivo real no es el juego en sí, sino diseñar, implementar y justificar estructuras de datos desde cero bajo restricciones estrictas de rendimiento y concurrencia de red.

    Contexto y Restricciones Principales:

    * Arquitectura: Separación estricta Modelo-Vista-Controlador (MVC). El modelo no debe conocer la vista gráfica/consola ni los detalles HTTP.
    * Red: La topología (esqueleto), contenido de salas y catálogo de entidades se consultan a un API REST. Hay un "presupuesto de solicitudes" máximo por partida que obliga a usar consultas por lotes (hasta 10 ítems) y evitar llamadas redundantes.
    * Prohibiciones Críticas: Está estrictamente prohibido usar `dict` como índice, caché o tabla de búsqueda, y no podemos usar `list.sort()` ni `sorted()` para los ordenamientos evaluados. Toda estructura para resolver los problemas debe ser implementada manualmente.
    * Entregables: Código funcional, interfaz (consola o gráfica), modos `--replay` y `--bench`, bitácora de uso de LLMs, y un "Documento de Decisiones de Diseño" (DDD) con análisis de complejidad y evidencia empírica.

    Los 10 Problemas Estructurales a Resolver:

    1. Agenda de Eventos: El ciclo de juego busca el evento con menor `tiempo_siguiente`. Requiere manejar desempates deterministas por número de secuencia, cancelaciones (ej. muere un actor) y reprogramaciones (cambios de velocidad) sin examinar todos los eventos.
    2. Prefetching de Red: Traer el contenido de salas vecinas antes de que el jugador intente entrar, en lotes, manejando estados pendientes sin que la latencia avance el reloj virtual ni el programa se caiga con HTTP 429.
    3. Caché Persistente y Resolución: Un límite máximo de entidades en memoria (`--cache-size`). Al llenarse, se debe liberar una ficha (que no esté en uso) bajo una política justificada, priorizando recuperar desde persistencia local antes que gastar red.
    4. Inventario: Recorrido bidireccional, capacidad máxima, descartar en cualquier posición en tiempo constante, equipar (mover al frente), y generar vistas ordenadas por atributos (peso, valor) sin alterar el orden real.
    5. Pergaminos de Retroceso (Deshacer): Revertir hasta 5 acciones del jugador hacia atrás (incluyendo efectos, enemigos y estado). Prohibido guardar copias completas del estado de la partida; deben almacenarse deltas/inversiones de cambios.
    6. Rastro del Jugador: Los enemigos "rastreadores" siguen el rastro más fresco (menor a 400 unidades de tiempo). Su decisión debe costar proporcionalmente a las salidas de la sala, no al tamaño total de la cripta.
    7. Bitácora de Pantalla: Interfaz que muestra solo los últimos 20 mensajes con un consumo de memoria constante, donde agregar un mensaje no implique desplazar físicamente los anteriores.
    8. Ordenamiento Dinámico: Implementar al menos 2 algoritmos de ordenamiento distintos. El programa debe seleccionar automáticamente cuál usar evaluando propiedades de los datos (tamaño, nivel de desorden, costo de comparación).
    9. Guardado Binario: Guardar la partida en un formato binario propio que permita leer una sala específica sin cargar todo el archivo en memoria y que detecte versiones incompatibles.
    10. Reproductor (--replay): Guardar acciones del jugador en un archivo de texto append-only (con semilla aleatoria y versiones) para reproducir la partida idéntica sin interacción.

    Tu Tarea:

    1. Explicación General: Explícame de forma clara y accesible (sin jerga innecesaria) de qué trata realmente este proyecto y dónde estarán los cuellos de botella.
    2. División del Trabajo: Somos un equipo de 3 personas. Divide las responsabilidades (los 10 problemas + MVC + API + Documentación) en 3 roles que sean semi-equitativos en cuanto a carga de trabajo y acoplamiento de código.
    3. Sugerencias de Estructuras: Para cada rol asignado, indícame qué estructuras de datos clásicas (ej. Listas Doblemente Enlazadas, Colas de Prioridad, Búferes Circulares, Tablas Hash manuales, Pilas) debe investigar e implementar el encargado para cumplir las reglas sin usar diccionarios integrados.

2. si, en un markdown bien bonito y entendible, tambien quisiera que incluyas todo el software necesario, apps externas, librerias, sitios web, etc(asumiendo que usamos visual studio code),

3. a partir de ahora asume que soy el  integrante C, eso quiere decir que todo lo que conlleve ese rol C tendrás que explicarlo y realizarlo segun lo indique, teniendo cuidado con mis especificaciones y claramente las del proyecto, listo?

4. primero pasa por encima de la explicacion y dame un resumen corto de las deciciones que tomaste para ordenamientos, y almacenamiento, 

    por ejemplo si usaste heap sort en algo, porque lo escogiste y porque es tan eficiente en ese caso, etc

5. como integro estos cambios con los de mis compañeros

6. basandote en las dos recientes adiciones, dime que desiciones de diseño (respecto a estructuras de dato, has escogio para ciertas cosas, para documentarlas)

7. el trabajo ha sido completado desde otra sesion de claude, ocupo que me ayudes a documentar ciertas partes, asi que te avisaré lo que ocupo

8. Hola soy kendall, ocupo proseguir con mi parte dejandome escoger las desiciones importantes de diseño que incluyan estructuras de datos, pero cuando me las enseñes, quiero que me menciones sus pros y contras

9. Añadir enlaces auxiliares para el orden de los objetos reversibles: separa ese orden del de los pergaminos, pero agrega campos a los nodos y más mantenimiento de enlaces.

10. Que falta para que el juego se pueda probar

11. Prosigue con eso, si tienes alguna desicion importante que tomar consultame primero, recuerda, que sea codigo legible sin complejidad innecesaria

12. Reutilizar el AVL existente para localizar salas por ID (recomendado).

    Cripta oficial: usa datos reales, pero requiere conexión y validar el contrato HTTP completo.

13. PS D:\proyrecto edd\proyecto-edd> python main.py --cripta cripta-01 --semilla 2026

    ==================================================
    Entrada derruida (sala 1)   reloj: 0
    Vida 30/30  Ataque 6  Defensa 2
    Salidas: N->2
    En el suelo:
      1. Antorcha
    --------------------------------------------------
      Cripta cripta-01; semilla 2026.
      Prueba inicial: moverse (n/s/e/o), atacar [n], esperar, inv, ayuda y salir.
      Inventario, puertas, retroceso, guardado y victoria aun pendientes de integracion.
    > e   

    ==================================================
    Entrada derruida (sala 1)   reloj: 0
    Vida 30/30  Ataque 6  Defensa 2
    Salidas: N->2
    En el suelo:
      1. Antorcha
    --------------------------------------------------
      Cripta cripta-01; semilla 2026.
      Prueba inicial: moverse (n/s/e/o), atacar [n], esperar, inv, ayuda y salir.
      Inventario, puertas, retroceso, guardado y victoria aun pendientes de integracion.
      No hay una salida hacia E.
    > n

    ==================================================
    Pasillo de las urnas (sala 2)   reloj: 100
    Vida 18/30  Ataque 6  Defensa 2
    Salidas: N->3  S->1  E->5 (cerrada)
    Enemigos:
      1. Rata gigante #e-201  vida 12/12
      2. Rata gigante #e-202  vida 12/12
    En el suelo:
      1. Daga oxidada
    --------------------------------------------------
      Cripta cripta-01; semilla 2026.
      Prueba inicial: moverse (n/s/e/o), atacar [n], esperar, inv, ayuda y salir.
      Inventario, puertas, retroceso, guardado y victoria aun pendientes de integracion.
      No hay una salida hacia E.
      Entras en Pasillo de las urnas.
      Rata gigante #e-201: pierdes 3 de vida.
      Rata gigante #e-202: pierdes 5 de vida.
    > n
    No se pudo continuar la partida: catalogo ids ent_guardian_oseo,itm_llave_negra: presupuesto agotado (9 de 9)
    PS D:\proyrecto edd\proyecto-edd> 

    No se me indican a que salas puedo ir, el presupuesto se agoto demasiado rapido, hay poca informacion de que esta pasando, analiza por quye sucede eso, y luego indicame como proceder para solucionarlos\

14. Completa por lotes de hasta 10 salas y continua con todos los demas arreglos

15. De donde viene el limite de 9 solicitudes

16. Ejecuta una prueba de todas las criptas, necesito que todas las criptas se pueda explorar completas con el presupuesto impuesto por la cripta, si no estariamos limitando al usuario

17. Hay que optimizar el uso de presupuesto para no cargar demasiadas cosas a la vez y volver lento el juego, pero tambien tener al menos un 20% del presupuesto libre para http 429, o otros imprevistos.

    Como podriamos optimizar eso

18. La precarga adaptativa

19. Utiliza mas solicitudes, asi aumentaras la velocidad de respuesta entre solicitudes, sin dejar de priorizar el mantener ese 20% libre

20. Eso aumentara las solicitudes utilizadas para mejorar la eficiencia de carga entre solicitudes?

    Tambien necesito que no se utilicen solicitudes innecesarias, no se puede cargar una gran parte del mapa si no se va a utilizar simplemente para mantenerlo en memoria, por eso hay que optimizar lo que se guarda en memoria con la cantidad de solicitudes

21. Limita la anticipacion a la vecindad inmediata

22. Vecindad por defecto, con una excepción de agrupación más amplia cuando sea necesaria para completar una cripta con su presupuesto.

23. Por que se crea un informe, desde cuando y por que

24. Donde esta eso de auditoria

25. No era necesario un archivo, si ya la estrategia de solicitudes es solida no necesito una funcion que verifique cada vez que el presupuesto alcance.

    Cuales fueron los archivos y funcionalidades extra que aniadiste desde la primera prueba real de la cripta

26. Entonces elimina la auditoria y los informes, evita generar archivos de informacion y documentacion extensos hasta que se te indique, ademas cuando crees una prueba nueva solo implementa casos comunes y necesarios,. cuando la cripta sea funcional se podran extender las pruebas o la documentacion

27. Moverse y atacar usan la misma tecla, mejor asignale wasd al movimiento, ademas limita el tamanio del historial visible por el usuario para que en partidas largas no se complique ver la informacion que se encuentra arriba.

28. ==================================================
    Osario profundo (sala 4)   reloj: 300
    Vida 4/30  Ataque 6  Defensa 2
    Solicitudes de red: 5/9
    Normales: 5/7; reserva inicial: 2; reintentos usados: 0
    Puedes moverte:
      S - Cripta baja, sala 3 (escribe s)
    Puertas cerradas:
      E - Salida, sala 6; requiere itm_llave_negra
    Enemigos:
      1. Rata gigante #e-201  vida 12/12
      2. Rata gigante #e-202  vida 12/12
      3. Guardián óseo #e-401  vida 20/20
    En el suelo:
      1. Llave negra
      2. Poción menor
    --------------------------------------------------
      [t=198] Rata gigante #e-201: pierdes 7 de vida.
      [t=198] Rata gigante #e-202: pierdes 7 de vida.
      [t=200] Entras en Osario profundo.
      [t=264] Rata gigante #e-201 se mueve de Cripta baja a Osario profundo.
      [t=264] Rata gigante #e-202 se mueve de Cripta baja a Osario profundo.
    > 

    Cuando le doy a n, en vez de atacar o recoger, avanza a otra sala, primero separa las funciones de atacar y recoger ademas de corregir eso, tambien aumenta para que se vean los ultimos 10 mensajes

29. Implementa recoger objetos e inventario

30. Cualquier desicion importante indicamela antes de implementar

31. Integrar recogida con deltas e inventario existente (recomendado)

32. Que son los deltasx

33. Se pueden equipar cosas?

34. Implementa equipar cosas, ademas, cuando abro el inventario se ve encima de la partida, mejor cada "pestaña" de informacion nueva colocala debajo de la informacion de la partida

35. Continua con abrir las puertas

36. Implementa usar objetos

37. Como porcentaje sobre la velocidad base: +50 significa un 50 % más; requiere fijar redondeo

38. Hacia abajo: 112,5 → 112 (recomendado)

39. Implementemos ahora victoria y puntuacion

40. No pùedo añadir CSV es muy avanzado, utiliza JSON o algo mas simple

    Finalizar al entrar a la salida (recomendado)

41. Implementa erl soltar objetos

42. Implementa retroceso

43. Marcar la instancia del pergamino como ya recogida (recomendado)

44. El pergamino esta limitado hasta 5 acciones_

45. Se supone que el pergamino deberia poder retroceder hasta cualquier punto pasado de la partida

46. Implementemos bitacora \y replay

47. Como creo la bitacora en primer lugar, el replay de la partida

48. No se reproduce toda la secuencia de acciones de la partida?

49. Implementa eso y que sea la opcion predeterminada, pero que exista una opcion para modo sin interfaz

50. Nada mas has que el replay se pueda avanzar con un enter entre cada bloque de informacion, o si se le da a una tecla especifica complete todo de una vezç

51. A que te refieres con grabacion

52. Entonces mientras exista una repeticion la partida no se podria guardar?

53. Puedo cargar una partida, despues de haberme salido de la partida actual?

54. Despues de cada bloque de informacion, pero antes de bloques como el inventario, vuelve a imprimir los comandos disponibles.

    Tambien si un comando solo esta disponible dentro de otro, por ejemplo sig con el inv, solo colocalo despues de haber usado dicho comando

55. Que parte del enunciado pide Consultar y ordenar puntajes desde la consola

56. Solo lo estrictamente necesario

57. Entonces implementa de nuevo que se muestren los ultimos 20 mensajes y el modo --offline

58. Como funciona offline

59. Eso no significa que empezar una partida descarga toda la cripta?, o que tan limitado esta el modo offline, ademas no entiendo lo del paquete

60. Entonces offline es un requisito pero se podra usar despues?

61. Implementalo junto al bench, si es que no le falta nada complejo

62. Que es LRU

63. Completemos medir los **20 ms del ciclo completo entre decisiones**, tambien quita esa indicacion del ultimo mensaje del bench

64. Usemos al menos dos criptas, la 01 y la 04

    Restaura las conexiones anteriores, fue un error mio y lo pase a un estado anterior, dejalo como estaba antes

65. El benchmark deberia hacer eso? o seria opcionalç

66. Pasame una lista de las estructuras de datos que se usaron en el proyecto

67. Con estructuras de datos tambien cuento metodos de ordenamiento

68. El proyecto respeta TODAS las prohibiciones impuestas? Como la siguiente:

    Deben implementar ustedes las estructuras de datos utilizadas para resolver los problemas de §4. Está prohibido
    sustituirlas por implementaciones equivalentes de bibliotecas.

69. Corrige el replay para que este con sin interfaz por predeterminado y elimina la opcion de darle a enter.

    Soluciona la liberacion de fichas

70. Referencia compartida por ID con AVL (recomendado)

71. El bench mide las alternativas descartadas como exige el enunciado?

72. Hola soy kendall, ocupo que agarres el contexto de los chats "revisar el prefetc" y "revisar avances y chat anterior"

    ocupo proseguir con mi parte dejandome escoger las desiciones importantes de diseño que incluyan estructuras de datos, pero cuando me las enseñes,, quiero que me menciones sus pros y contras

## 🟢 Juan

1. Soy juan (hola) termina el bench de adaptadores

2. Necesito que antes de implementar cuialquier desicion relacionada a una estructura de datos me consultes para analizar las opciones y tomar una desicion

3. Re analiza adaptadores para verificar las funcionalidades faltantes

4. También integración completa

5. Que es el modelo real y que otras opciones hay para guardarlo y restaurarlo

6. Esquema explícito por entidad con IDs y AVL: campos más visibles; requiere más código por cada tipo de entidad

7. Para guardar y restaurar el modelo real, ¿qué representación prefieres? Ambas reutilizan el AVL existente y permiten conservar las referencias que necesita el retroceso.

    Dame todas las opciones disponibles para esto con sus ventajas y desventajas, pero todavia no lo implementes.

    Continua con el resto del codigo

8. Campos visibles, validables y fáciles de explicar; permite organizar bloques por sala.

    Binario propio por campos

9. Que falta en el prefetch

10. Que cambios pequeños le hacen falta a adaptadores que no este trabajando la otra sesion

11. Analiza que tan complejo seria adaptar este proyecto a pygame

12. Necesito que me ayudes a completar lo que se pueda del archivo cache_catalogopy, yo soy el del rol B, aclaro que todo tiene que respetar lo que se indica en el enunciado del proyecto, ademas debe ser un codigo sencillo y legible para principiantes a medida de lo posible, y al igual que en el ejemplo es extremadamente importante que cualquier desicion relacionada a alguna estructura de datos me sea consultada para proceder.

    Concentrate solo en cache_catalogo.py, si hubo algo que no actualize o hay otro error, omitelo y solo haz lo que puedas para completar lo mas posible de cache_catalogo

13. P: ¿Qué tipo de árbol de búsqueda usamos para buscar fichas por id en memoria?
    R: AVL (auto-balanceado)

    P: ¿Cómo guardamos las fichas en disco?
    R: Un archivo JSON por ficha, en una carpeta

    P: Si la caché está llena y todas las fichas están en uso, ¿qué hacemos?
    R: Si en el enunciado del proyecto nunca dice ninguna restriccion con respecto a superar el limite, entonces se supera temporalmente, si no, la segunda opcion, lo mismo para las demas opciones, todo tiene que respetar el enunciado

14. Basandose en la guia y en el enunciado del proyecto, que me falta a mi (el rol B) por terminar, que no dependa de algo que tengan que hacer los compañeros, ademas analiza en profundidad la carpeta de adaptadores (la que me pertenece a mi) y confirma que respete todas las restricciones impuestas en el enunciado del proyecto

15. Vamos con la parte mas facil de lo que me falta, pero esta vez quiero que me enseñes que es lo que estoy haciendo, que cada funcion tenga un contexto y una explicacion que yo pueda entender.

    Por eso no me des un archivo con todo ya hecho, ve paso por paso guiandome entre los metodos que hay que hacer, para que funcionan y por que funcionan, explicalo de manera sencilla asumiendo que no se nada del proyecto, para empezar a comprender de verdad que estoy haciendo y no seguir simplemente copiando y pegando

16. Pregunta, lo que son errores, no estaria bien que fueran como en un .py aparte?, siento que en c++ por ejemplo o java se suele hacer asi, ademas, todo esto si va en adaptadores?, tambien podria crear una carpeta aparte por ejemplo si esto se sale del significado de "adaptadores"

17. ¿Por qué el encabezado va antes de las acciones y no al final? R: Tal vez para poder hacer validaciones antes de leer todo el archivo, como que es el log que busco, la version, etc

    ¿Qué pasaría con el replay si un nombre de acción trajera un salto de línea y no lo validáramos? El controlador lo tomaria como una accion,?

18. ¿De dónde saldrían la versión de la cripta y la del catálogo "de ahora"? Piensa en las dos clases que ya hiciste: `ClienteHTTP` y `CacheCatalogo`. No estoy seguro por que cuando hice esas clases no te pedi que me guiaras tanto

    ¿Qué pide el enunciado si no coinciden?: Que el programa de un aviso de que la reproduccion podria no ser igual a la partida original

    Tambien queria preguntar, por que siempre la primera linea del encabezado es CRIPTA-LOG "1"?, no podrian haber varios log, todos serian log 1

19. La primera prueba que me dijiste que hiciera me puso esto:

    PS C:\Users\pipro\OneDrive\Documentos\proyecto-edd> & C:/Users/pipro/AppData/Local/Programs/Python/Python313/python.exe c:/Users/pipro/OneDrive/Documentos/proyecto-edd/Disco_red/prueba
    Traceback (most recent call last):
      File "c:\Users\pipro\OneDrive\Documentos\proyecto-edd\Disco_red\prueba", line 1, in <module>
        from bitacora import EscritorBitacora, leer_bitacora
    ImportError: cannot import name 'leer_bitacora' from 'bitacora' (c:\Users\pipro\OneDrive\Documentos\proyecto-edd\Disco_red\bitacora.py)
    PS C:\Users\pipro\OneDrive\Documentos\proyecto-edd> 

    (Por si acaso le cambie el nombre de adaptadores a Disco_red, y a bitacora.py)

20. Las pruebas si quieres haslas tu en pytest, que sean sencillas eso si

21. hagamos primero lo del --bench

22. Antes de nada, que se supone que es esta parte, lo que se esta haciendo, que significa el bench y para que es

23. La entrega es en 3 dias, empecemos con lo que falta y que sea sencillo, únicamente haciendo lo estricto y necesario, con poca complejidad de codigo.

24. https://github.com/Ghosty2701/proyecto-edd.git

    Usa el repositorio de git hub para mantenerte al día con los cambios, dime qué procede hacer ahora

25. [adjunto: proyecto-edd_7.zip] El proyecto ya esta casi terminado, revisa que se cumpla todo lo estipulado en el proyecto sin incumplir ninguna regla, ademas indicame cual seria el comando para probar el codigo

26. Las pruebas se pueden simplificar?, son demasiadas, dime si realmente todas son necesarias, o si se pueden acortar, ademas revisa si todas las pruebas estan en pytest
