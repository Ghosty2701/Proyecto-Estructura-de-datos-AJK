# Contrato: Línea de tiempo

**Estado**: contrato funcional implementado y probado; no certifica los presupuestos de tiempo. Reglas en [spec.md](../spec.md); diseño en
[data-model.md](../data-model.md).

## Orden en partida

| Entrada | Resultado | Efectos |
| --- | --- | --- |
| `historia <t>`, 0 ≤ t ≤ reloj | Resumen histórico del estado en t | Ninguno: no hay tiempo, log, retroceso ni azar. |
| `historia #k`, 1 ≤ k ≤ N + 1 | Resumen justo antes de la acción k; N + 1 = estado actual | Ninguno. |
| `historia <t>` con t > reloj | Rechazo: «el instante t es posterior al reloj actual R» | Ninguno. |
| `historia` sin argumento, t negativo o no entero, `#0`, `#k` con k > N + 1, `#` sin número | Rechazo con el uso: `historia <t>` o `historia #k` | Ninguno. |
| `historia …` durante «ir a» | El viaje se detiene como ante cualquier orden y luego se responde la consulta | Ninguno, aparte de detener el viaje. |

Las palabras `historia` y `#` no distinguen mayúsculas. t y k son enteros en
base 10 sin signo `+`. La orden nunca aparece en `partida.log`.

## Resumen histórico (texto)

```text
Historia en t=<reloj> (antes de la acción #<k>)        ← o «estado actual»
Sala <id> — <nombre>
Vida <v>/<max> · ataque <a> · defensa <d>
Efectos: <lista o «ninguno»>
Inventario (<n>/<capacidad>): <objetos en orden real; [E] equipado; > cursor>
Enemigos en la sala: <nombre [cazador] #id vida v/max (dormido|activo)> | ninguno
Mapa conocido: <mismo formato que «ver mapa» en ese instante>
```

El contenido mínimo es obligatorio (FR-LT-002). El formato exacto puede ajustarse
en la implementación sin quitar campos.

## Línea de comandos

| Opción | Regla |
| --- | --- |
| `--checkpoint-cada K` | Entero ≥ 1. Válida con `--cripta`, `--cargar` y `--replay`. Sin la opción: K por defecto (D-LT-07); al cargar, el K guardado. |
| `--replay LOG --hasta T` | T entero ≥ 0. Imprime el resumen histórico de T sin vista y termina con código 0. Si T es posterior al final del log, imprime el estado final y añade «la partida terminó en t=R, antes de T» (o «el registro termina en t=R» si la partida seguía en curso). |
| `--hasta` sin `--replay`, T inválido, `--checkpoint-cada` inválido | Error de uso de argparse (código 2) con explicación, sin ejecutar ningún modo. Los demás modos (`--cripta`, `--cargar`, `--listar`, `--verificar`, `--bench`, `--ver-puntajes`) ya son excluyentes con `--replay` en el grupo de argparse; combinar `--hasta` con ellos produce ese mismo error. |

Los errores de log (compatibilidad, versión, acción fallida) conservan su
comportamiento actual.

## Guardado

- Versión del modelo **6**. Contiene la línea completa: órdenes, acciones
  vigentes, puntos con su copia y tramos de K.
- Un archivo con versión ≠ 6 (incluidos los de la primera parte y los de versión
  5) se rechaza con «formato de guardado incompatible (versión X; se requiere 6)»
  y no se carga nada.
