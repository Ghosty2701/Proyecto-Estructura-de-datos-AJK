# Referencia visual — Cripta

**Estado**: propuesta de composición; no representa la aplicación implementada.
**Elecciones confirmadas**: vista desde arriba, combate en la misma sala e
ilustración 2D de fantasía oscura.

## Composición

Habitación amplia al centro, con suelo pétreo legible, paredes y decoración
periférica. Personaje y enemigos separados por silueta y escala; objetos
recogibles distinguidos de los elementos de ambientación. Las puertas se
superponen solo donde el conocimiento de la sala indica una salida real.

HUD compacto para vida/estado, minimapa en una esquina y acciones en la zona
inferior. Selección por borde o anillo, nombre y vida observable, sin depender
solo de color. Durante un ataque se conserva esta misma habitación.

La referencia puede contener ejemplos de enemigos y puertas para ilustrar su
composición. Esos ejemplos no son datos de una cripta de producción y no se
copiarán como elementos fijos del fondo jugable.

## Recursos finales previstos

Fondo sin actores ni puertas incrustadas, puertas independientes, personaje,
cuatro familias de enemigos y objetos por clase. Personajes y objetos con
transparencia; nombres y estados del juego se dibujan por código. Se preserva
un recurso genérico para contenido nuevo sin arte específico.

## Generación de la referencia

Herramienta: imagegen incorporado, modo de generación, fondo opaco. La imagen
es una referencia de diseño. La salida se presenta al usuario; no se usa como
una captura de aceptación ni sustituye sprites finales separados.

Prompt completo: `referencia-visual.prompt.txt`.

Referencia generada y revisada: [concepto-sala-v1.png](referencias/concepto-sala-v1.png).
Muestra el lenguaje ilustrado y combate integrado. Sus puertas, cifras y actores
son ejemplos conceptuales; la cámara y distribución definitivas se ajustarán al
render de recursos separados y a la lectura de las acciones reales.
