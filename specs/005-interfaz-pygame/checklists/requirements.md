# Lista de calidad: Interfaz gráfica de Cripta con Pygame

**Propósito**: Revisar la especificación antes de planificar la implementación.
**Creación y revisión**: 2026-11-13.
**Especificación**: [spec.md](../spec.md).
**Semántica**: Una casilla marcada acredita calidad del requisito revisado; no implementación, prueba gráfica ni cumplimiento funcional del producto futuro.

## Calidad del contenido

- [x] CHK001 No se eligen estructuras, algoritmos, módulos ni mecanismos de almacenamiento.
- [x] CHK002 Las historias describen valor para el jugador y conservan el juego por turnos.
- [x] CHK003 El comportamiento se entiende sin conocer el código de presentación.
- [x] CHK004 Están completas las secciones de escenarios, requisitos, entidades, criterios y supuestos.

## Completitud de requisitos

- [x] CHK005 No quedan marcadores de aclaración ni texto de plantilla pendiente.
- [x] CHK006 Los 24 requisitos funcionales son verificables y tienen referencias a escenarios.
- [x] CHK007 Los siete criterios de éxito tienen resultados observables o cantidades verificables.
- [x] CHK008 Los criterios de éxito se expresan sin APIs ni detalles de implementación.
- [x] CHK009 Hay 23 escenarios identificados y ordenados por siete historias priorizadas.
- [x] CHK010 Se describen errores, mapas sin coordenadas, entradas repetidas, antorcha y observaciones futuras.
- [x] CHK011 El alcance distingue mapa y paneles de juego en tiempo real, 3D, arte final y empaquetado.
- [x] CHK012 Están identificados entorno, datos externos, compatibilidad v6, EX-01 y decisiones técnicas aprobadas en planificación.

## Preparación para planificar

- [x] CHK013 Cada FR-IG enlaza uno o más AC-IG existentes.
- [x] CHK014 Las historias cubren inicio, niebla, acciones, viaje, retroceso, historia, persistencia y cierre.
- [x] CHK015 Los criterios permiten verificar el resultado sin afirmar que ya se haya implementado.
- [x] CHK016 Las decisiones de presentación aprobadas por el usuario están separadas del diseño técnico futuro.

## Notas de revisión

- Resultado: **16/16** criterios de calidad revisados y satisfechos. Listo para planificación.
- El usuario pidió explícitamente Pygame; su nombre aparece en la identificación y restricción de la capacidad. No es una biblioteca elegida por el agente ni una prescripción técnica de los criterios de éxito.
- Aclaraciones incorporadas: mapa en cuadritos, sprites de enemigos, paneles/botones, turnos y memoria de últimos enemigos observados fuera de la sala actual.
- La adyacencia muestra salas avistadas sin contenido; la antorcha conserva las reglas de 002. Una sala revelada sin entrar no produce observaciones de enemigos.
- Revisión posterior al plan: D-IG-05/06/07 elegidas explícitamente. Se precisó que la selección de inventario puede registrar navegación sin turnos y que el viaje admite una única intención interruptora, sin cola de acciones. Los 16 criterios de calidad siguen satisfechos.
- Compatibilidad y memoria visual opcional se especifican como resultados. Las estructuras y el almacenamiento elegidos se detallan en el plan, el modelo de datos y los contratos.
- El plan está completado; no se crearon todavía tareas de implementación. Las 759 pruebas de la base no certifican los nuevos escenarios gráficos.
