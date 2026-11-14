"""Informes compartidos por los modos de consola y ventana."""

def informe_verificacion(resultado):
    """Presentación textual sin instanciar la vista; tablas sin duplicar ubicaciones."""
    mapa = resultado.mapa
    lineas = [f'Cripta {mapa.id_cripta} ({mapa.version}): ' +
              ('resoluble.' if resultado.resoluble else 'no resoluble.')]
    if resultado.resoluble:
        lineas.append('Orden de llaves: ' + ', '.join(mapa.llaves[k].id for k in resultado.cierre.orden))
    else:
        for k in resultado.no_obtenibles:
            llave = mapa.llaves[k]
            lugares = ', '.join(str(mapa.salas[u.sala].sala_id) +
                                (f' (enemigo {u.enemigo})' if u.enemigo else '')
                                for u in llave.ubicaciones)
            lineas.append(f'Llave no obtenible {llave.id}: {lugares or "sin ubicación"}.')
        for p in resultado.frontera:
            salida = next(s for s in mapa.puertas[p] if resultado.cierre.salas[s.origen])
            llave = mapa.llaves[salida.llave].id if salida.llave >= 0 else 'sin llave'
            lineas.append(f'Frontera puerta {p}: {mapa.salas[salida.origen].sala_id} '
                          f'{salida.direccion} → {mapa.salas[salida.destino].sala_id}; {llave}.')
        def nodo(v):
            return ('sala ' + str(mapa.salas[v].sala_id) if v < len(mapa.salas)
                    else mapa.llaves[v - len(mapa.salas)].id)
        def procedencia_texto(causa):
            if causa[0] == 'puerta':
                return (f'puerta {causa[1]}, desde sala '
                        f'{mapa.salas[causa[2]].sala_id} por {causa[3]}')
            if causa[0] == 'ubicacion':
                return ('ubicación en sala ' + str(mapa.salas[causa[2]].sala_id)
                        + (f', enemigo {causa[3]}' if causa[3] else ''))
            return 'sin ubicación físicamente accesible desde el inicio'
        for i, certificado in enumerate(resultado.certificados):
            lineas.append(f'Grupo circular {i}: ' + ', '.join(nodo(v) for v in certificado.nodos))
            lineas.append('Ciclo concreto de reglas: ' + ' → '.join(nodo(v) for v in certificado.ciclo))
            for a, b, procedencia in certificado.reglas:
                lineas.append(f'Alternativa: {nodo(a)} requiere {nodo(b)}; '
                              f'{procedencia_texto(procedencia)}.')
        for nodo_id, causa in resultado.estructurales:
            lineas.append(f'Imposibilidad estructural: {nodo(nodo_id)}; {procedencia_texto(causa)}.')
    for sala_id, direccion, aviso in mapa.avisos:
        lineas.append(f'Aviso sala {sala_id} {direccion}: {aviso}.')
    return '\n'.join(lineas)

