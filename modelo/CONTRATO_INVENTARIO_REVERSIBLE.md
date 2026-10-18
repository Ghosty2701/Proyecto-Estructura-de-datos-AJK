# Inventario reversible: contrato de integracion

Kendall eligio operaciones inversas y enlaces auxiliares para el orden de los
objetos reversibles. La implementacion esta en `inventario_reversible.py`.

## Estado de esta etapa

`InventarioReversible` extiende `Inventario`. Mantiene la lista real y agrega una
segunda cadena de referencias a los mismos nodos, omitiendo pergaminos. No duplica
objetos ni guarda copias completas del inventario. El inventario anterior sigue
disponible; sus instancias y sus campos persistidos no cambian.

Los metodos heredados tambien mantienen ambos ordenes. Para operaciones que deban
deshacerse se usan las variantes que devuelven un registro. La extension reconoce
`objeto.clase == "pergamino_retroceso"`; los objetos sin `clase` se consideran
ordinarios. La clase del objeto debe permanecer estable mientras esta en la lista.
El catalogo sigue siendo responsabilidad de la capa que crea los objetos.

## API para Andrey y la capa de partida

```python
from modelo.inventario_reversible import InventarioReversible

inventario = InventarioReversible(capacidad=10)
aceptado, cambio = inventario.recoger_reversible(objeto)

# El historial externo conserva cambio solo si no es None.
# Cuando corresponda deshacerlo, en orden inverso:
if cambio is not None:
    inventario.deshacer_cambio(cambio)
```

El ejemplo muestra el contrato; no sustituye la integracion del historial.

| Metodo | Resultado |
| --- | --- |
| `recoger_reversible(objeto)` | `(bool, cambio_o_None)` |
| `soltar_actual_reversible()` | `(objeto_o_None, cambio_o_None)` |
| `consumir_primero_reversible(condicion)` | `(bool, cambio_o_None)` |
| `equipar_actual_reversible(tipo)` | `(objeto_desplazado_o_None, cambio_o_None)` |
| `deshacer_cambio(cambio)` | Restaura el cambio una sola vez. |

Las operaciones rechazadas o sin efecto devuelven registro `None`. Recoger,
soltar o consumir un pergamino tampoco genera registro. Los pergaminos no se
pueden equipar. `consumir_primero` conserva su API anterior para el consumo del
pergamino que ya realiza el motor.

Cada registro guarda un numero constante de referencias: inventario, nodo,
vecinos reales, vecinos reversibles, cursor y equipo anteriores. Recupera el
mismo nodo y objeto. No guarda ni modifica estadisticas del actor, suelo, reloj,
agenda, acciones del jugador ni historial de cinco intervalos.

El consumidor debe conservar solo cambios exitosos y deshacerlos en orden
inverso. No debe mezclar cambios registrados con operaciones ordinarias sin
registro sobre objetos reversibles. Los metodos de navegacion no crean registros.
Al descartar intervalos antiguos se descartan tambien sus referencias a cambios;
la extension no mantiene una segunda coleccion de historial.

## Pergaminos y posiciones

El segundo orden permite recuperar exactamente el orden relativo de los objetos
ordinarios aunque hayan desaparecido pergaminos vecinos. Los pergaminos presentes
conservan su identidad y su orden relativo; ninguno consumido o soltado se vuelve
a insertar al deshacer otra operacion. El cursor antiguo se recupera si su nodo
sigue presente; de lo contrario se conserva un cursor valido o se usa el frente.

Convencion implementada para posiciones excluidas: se aprovecha un vecino real
original que siga dentro del hueco correcto del orden reversible. Si ambos
desaparecieron, se inserta antes del siguiente objeto reversible, o al final si no
existe. Sin cambios excluidos se recupera todo el orden real anterior. Esta
convencion es una decision de implementacion, no una regla adicional del PDF.

## Complejidad

Recoger, soltar el nodo del cursor, equipar y crear sus registros cuestan O(1).
Mantener ambos pares de enlaces requiere una cantidad constante de escrituras.
Consumir por condicion cuesta O(n) por la busqueda; retirar la coincidencia es
O(1). Deshacer cuesta O(n), por validar pertenencia y buscar el hueco real; no se
afirma que el retroceso sea O(1). El espacio es O(n + h), con h registros
conservados por el historial. No se usan indices con `dict` ni ordenamientos
incorporados.

## Integraciones pendientes y limite de capacidad

**Andrey:** incorporar `CambioInventario` como operacion reversible del historial.
La capa de partida debe registrar tambien transferencias al suelo y cambios en
ataque/defensa al equipar, dentro del mismo intervalo. Estas operaciones internas
no abren intervalos ni cobran tiempo por si solas.

**Juan:** agregar esquemas explicitos para `InventarioReversible`, `NodoReversible`
y `CambioInventario`, conservar sus referencias compartidas y validar los enlaces
auxiliares. Los tipos nuevos aun no estan admitidos por `estado_binario.py`.
No reemplazar el inventario de una partida que se guarda hasta completar esa
integracion. No se modificaron los adaptadores ni el historial de Andrey.

**Capacidad:** un objeto ordinario soltado puede necesitar volver cuando su lugar
ya lo ocupa un pergamino recogido posteriormente. Si no hay espacio,
`deshacer_cambio` lanza `ErrorInventario` antes de modificar ese cambio; no elimina
pergaminos ni excede la capacidad. El registro sigue utilizable al liberar espacio.
Esto no define la regla final de la partida: el equipo debe acordarla y validar
todo el intervalo antes de comenzar un retroceso, para evitar aplicarlo a medias.

## Verificacion

Desde la raiz del proyecto:

```powershell
python -m pytest Pruebas/prueba_inventario.py -q
python -m pytest -q
```

Los casos de esta extension estan en el archivo de pruebas existente. Cubren
identidad, enlaces en ambos sentidos y ambos ordenes, ranuras de equipo, cursor,
registros invalidos, capacidad y pergaminos. Incluyen la regresion del vecino
consumido despues de mover otro objeto y secuencias con veinte semillas fijas.
Los consumidores simulados estan solo en las pruebas; no demuestran todavia la
integracion completa con motor, suelo o guardado.
