# Arte original de Cripta

## Recursos activos — revisión de 16 bits

Por petición explícita del usuario se sustituyó el aspecto ilustrado por pixel
art original inspirado en el lenguaje de RPG clásicos de 16 bits. Generación
con imagegen incorporado el 2026-11-14; prompts exactos en `prompts_16bits.txt`.

- `sala_16bits.png`: fondo opaco 1499 × 1049, sin puertas ni entidades incrustadas.
- `actores_16bits.png`: atlas 3 × 2, 1536 × 1024, mismo orden de seis personajes.
- `elementos_16bits.png`: atlas 4 × 3, 1448 × 1086, mismo orden de doce elementos.
- `puertas_16bits.png`: atlas 4 × 2, 1774 × 887; columnas N/S/E/O, fila cerradas
  y fila abiertas. Orientaciones dibujadas individualmente; no se gira la puerta.

Los atlas tienen transparencia real verificada. El cargador normaliza a tamaños
de pixel art y escala con vecinos próximos. Las puertas incluyen tramos de pared
para encajar en el fondo, con umbral sur bajo y pasos laterales orientados.

### Especies — revisión de claridad

`criaturas_16bits.png`, 1293 × 1217, atlas 3 × 3 con alfa real, generado con
imagegen incorporado el 2026-11-14. Prompt exacto en
`prompts_criaturas_16bits.txt`. Filas: rata gigante / sabueso óseo / espectro;
esqueleto / lobo / araña; goblin / murciélago / símbolo neutral de desconocido.
Se inspeccionaron atlas y render recortado. Los cortes verticales de filas
se ajustan a los huecos transparentes
del PNG (0/390/805/1217), evitando recortar la cabeza del esqueleto o incluirla
como residuo en la rata. La selección usa el nombre observable
normalizado; el comportamiento no determina la especie. Los tipos abstractos
anteriores siguen disponibles; los nombres no reconocidos usan símbolo neutral,
no un mago arbitrario. Nombre y objetivo del motor se conservan.
El arte se carga localmente, sin descargar recursos durante la partida.

## Recursos anteriores conservados como historial

Generado con imagegen incorporado el 2026-11-14, a partir de las elecciones
del usuario: ilustración 2D de fantasía oscura, habitación cenital y combate
integrado. Recursos locales, sin solicitudes HTTP durante el juego.

Archivos finales: `sala.png`, `actores.png` y `elementos.png`. Generados,
inspeccionados y copiados al proyecto. Atlas con alfa real verificado; el color
RGB de píxeles transparentes no se convierte en fondo durante el render.

`actores.png` contiene 3 columnas y 2 filas: jugador, guardián, errante;
rastreador, cazador y enemigo genérico. `elementos.png` contiene 4 columnas y
3 filas: puerta cerrada, abierta, arma, armadura; llave, pergamino, poción,
antídoto; antorcha, amuleto, objeto genérico y contenedor.

El juego recorta celdas al cargar y conserva la transparencia. Ninguna imagen
determina reglas, posiciones de entidades, salidas de una cripta o resultados.
La referencia conceptual de `specs/006-salas-combate-visual/referencias/`
no se usa como fondo jugable.

Prompts originales completos: `prompts.txt`. Modo: generación incorporada,
sin referencias de terceros ni CLI/API alternativo.

Dimensiones: sala 1448 × 1086, actores 1536 × 1024, elementos 1448 × 1086.
Los atlas se segmentan por proporciones exactas, conservando el último píxel
cuando una dimensión no es divisible por el número de columnas.
