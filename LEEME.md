La fase de efectos temporales ya está integrada en el proyecto. La última verificación, realizada el 15 de octubre de 2026 sobre los archivos del proyecto, aprobó **244 pruebas**: las 204 anteriores y 40 casos nuevos. Es evidencia del estado revisado; no demuestra que la partida completa esté terminada.

**Archivos de esta fase**

- `modelo/efectos.py`: efectos, estados y trampas; aporta los métodos de `MotorEfectos` a `MotorEventos`.
- `modelo/motor_eventos.py`: integra efectos en la ejecución de eventos, activación de enemigos y movimiento.
- `modelo/rastro.py`: incluye la lista de trampas de cada sala.
- `Pruebas/prueba_motor_eventos.py`: contiene las pruebas anteriores y las de esta fase.

**Verificación desde la raíz del proyecto**

Ejecuta en PowerShell:

```powershell
python -m pytest -q
```

Para ejecutar únicamente las pruebas del motor:

```powershell
python -m pytest Pruebas/prueba_motor_eventos.py -v
```

La carpeta temporal de entrega ya fue eliminada. El código necesario está en los archivos del proyecto; no hay que aplicar otro parche. Este documento conserva las decisiones y los pendientes para el DDD y la integración. No sustituye el README general de instalación y ejecución de la aplicación.

**Responsabilidades respetadas**

Esta fase no modificó `modelo/inventario.py`, `comun/ordenamiento.py`, `vista/`, `controlador/`, `adaptadores/` ni sus pruebas. Se usa la función pública de ordenamiento que ya existe. Los efectos utilizan los deltas de atributos y eventos de `modelo/retroceso.py`, sin requerir cambios adicionales en ese archivo para esta fase.

**API del motor incluida**

| Operación | Resultado |
|---|---|
| `aplicar_veneno(actor, dano)` | Programa pulsos cada 80 unidades durante 400. |
| `aplicar_antidoto(actor)` | Cancela el veneno pendiente por referencia directa. |
| `aplicar_velocidad(actor, velocidad_nueva, duracion)` | Cambia a una velocidad final absoluta y reajusta el turno; al expirar recupera la base. |
| `encender_antorcha(actor, duracion)` | Mantiene un estado de antorcha hasta su apagado. |
| `iniciar_regeneracion(actor, cantidad)` | Recupera vida cada 200 unidades sin superar `vida_max`. |
| `detener_regeneracion(actor)` | Cancela el próximo pulso por referencia directa. |
| `curar(actor, cantidad)` | Cura hasta `vida_max`; rechaza curar actores muertos. |
| `aplicar_dano(actor, cantidad)` | Aplica daño fijo de efecto o entorno; cancela los eventos del actor si muere. |

Estas son operaciones internas del modelo. No abren por sí solas un intervalo ni cobran el costo de usar un objeto. Deben integrarse dentro de una acción previamente validada. La operación de ataque conserva su fórmula propia; el daño de efecto no añade azar ni resta defensa.

`ActorTurnos` acepta ahora `vida_max=` y `regeneracion=`. La cantidad de regeneración es configuración; su temporizador comienza automáticamente al activar el enemigo, no al precargarlo.

Una sala dispone de `trampas`. Cada `Trampa` es una instancia del modelo, no una ficha compartida:

```python
from modelo.efectos import Trampa

trampa_dano = Trampa("t-01", "dano", 4)
trampa_veneno = Trampa("t-02", "veneno", 2, rearme=500)
trampa_velocidad = Trampa("t-03", "velocidad", 50, duracion=200)
```

Estos identificadores y valores son ejemplos; los reales se obtienen de los datos de la cripta y el catálogo. La capa que resuelva JSON deberá construir las entidades. No se asume que el JSON tenga exactamente la estructura del constructor.

El movimiento activa las trampas inmediatamente en su sala destino, antes de extraer el siguiente evento. Se programa previamente el turno del jugador para que una trampa de velocidad pueda reajustarlo. Una trampa se desarma y programa un rearme a 300 unidades o al intervalo recibido. Rearmarse no dispara su efecto contra un ocupante: requiere una nueva entrada.

En cualquier escenario con efectos, el callback general debe procesar con:

```python
def ejecutar(evento):
    motor.ejecutar_evento(evento, jugador)
```

Llamar solo a `ejecutar_enemigo` no procesa eventos de efectos ni de entorno.

**Convenciones propuestas donde el enunciado no detalla los casos**

- El veneno tiene cinco pulsos: aplicación +80, +160, +240, +320 y +400; después del último desaparece.
- Reaplicar veneno cancela el pulso pendiente y renueva dosis y duración; no acumula venenos independientes.
- Un nuevo cambio temporal de velocidad reemplaza el anterior, preservando la velocidad base que se restaurará. El motor recibe la velocidad final; no interpreta si `modificador_velocidad` significa suma, factor u otra operación.
- Encender otra antorcha renueva la duración y cancela el apagado anterior.
- Las trampas de una entrada se procesan por ID de instancia ascendente para fijar un orden determinista. Se detiene su procesamiento si el jugador muere.
- La activación automática de trampas corresponde a los movimientos. Debe aclararse el caso de trampas en la sala inicial antes de añadir una activación al inicio; el PDF describe la activación tras completar un movimiento.

Estas convenciones están implementadas y probadas, pero siguen siendo decisiones propuestas para revisar con el equipo, no requisitos adicionales atribuidos al PDF.

**Integración pendiente con tus compañeros**

El consumo reversible de antídotos, pociones y antorchas requiere acordar con Kendall una operación reversible sobre el inventario. Esta fase no elimina objetos ni utiliza campos privados del inventario para simular ese contrato. El efecto de un antídoto y el estado de una antorcha ya están implementados; su consumo y las acciones de uso con costo 50 siguen pendientes.

La lectura de catálogo, normalización de `modificador_velocidad`, persistencia de los nuevos estados y su presentación en consola requieren integración posterior con Juan y Kendall. Los efectos quedan enlazados al actor, por lo que morir cancela sus eventos futuros sin recorrer toda la agenda. El rearme de una trampa pertenece al entorno y puede existir aunque el jugador haya muerto; el bucle de partida se detiene al morir.

Las pruebas cubren reglas de tiempos, curación acotada, renovación y cancelación, efectos al morir, trampas durante movimiento y restauración de atributos, eventos y referencias al deshacer. No demuestran todavía la partida completa ni el límite de 20 ms.

**Siguientes pasos**

1. Acordar con Kendall el contrato reversible para consumir, recoger, soltar y equipar objetos, preservando la excepción de los pergaminos. Los cambios en su inventario deben coordinarse con él.
2. Acordar con Juan cómo entregar entidades y salas completamente resueltas y cómo guardar los nuevos estados. La integración debe respetar la separación del modelo respecto a HTTP y disco.
3. Definir con el equipo la capa de partida que conectará esas interfaces con el motor y el controlador. Completar allí las condiciones de victoria y derrota, las consecuencias de las muertes y los contadores requeridos para el puntaje, según el reparto acordado.
4. Añadir pruebas de integración sobre esos recorridos completos. Los objetos simulados se reservan para las pruebas de interfaces todavía no disponibles.
5. Incorporar las decisiones y mediciones al DDD, mantener la bitácora de prompts y medir el ciclo completo entre decisiones del jugador, excluyendo red y renderizado, para verificar el límite de 20 ms.
