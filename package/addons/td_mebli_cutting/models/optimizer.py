"""Deterministic strip (shelf) cutting heuristic. SIMULATION of an external cutting program.

Pure python: no ORM, so it can be tested and replaced without touching the models.
All sizes are millimetres.
"""


class PieceTooLarge(ValueError):
    pass


def _shelf_pack(pieces, length, width, kerf):
    """Place pieces on a rectangle length x width with shelves along the length.

    Returns (placements, unplaced, shelves). Pieces keep their orientation (decor grain)
    and are rotated only when they do not fit otherwise.
    """
    placements, unplaced, shelves = [], [], []

    def try_place(piece, plen, pwid, rotated):
        if plen > length or pwid > width:
            return False
        for shelf in shelves:
            if pwid <= shelf['h'] and shelf['x'] + plen <= length:
                placements.append(dict(piece, x=shelf['x'], y=shelf['y'], length=plen, width=pwid, rotated=rotated))
                shelf['x'] += plen + kerf
                return True
        y = shelves[-1]['y'] + shelves[-1]['h'] + kerf if shelves else 0
        if y + pwid <= width:
            shelves.append({'y': y, 'h': pwid, 'x': plen + kerf})
            placements.append(dict(piece, x=0, y=y, length=plen, width=pwid, rotated=rotated))
            return True
        return False

    for piece in pieces:
        if not (try_place(piece, piece['length'], piece['width'], False)
                or try_place(piece, piece['width'], piece['length'], True)):
            unplaced.append(piece)
    return placements, unplaced, shelves


def _offcuts(shelves, length, width, kerf, min_offcut):
    offcuts = []
    for shelf in shelves:
        right = length - shelf['x']
        if right >= min_offcut and shelf['h'] >= min_offcut:
            offcuts.append({'x': shelf['x'], 'y': shelf['y'], 'length': right, 'width': shelf['h']})
    if shelves:
        top = shelves[-1]['y'] + shelves[-1]['h'] + kerf
    else:
        top = 0
    remaining = width - top
    if remaining >= min_offcut and length >= min_offcut:
        offcuts.append({'x': 0, 'y': top, 'length': length, 'width': remaining})
    return offcuts


def pack(pieces, sources, virtual_source, kerf=4, trim=10, min_offcut=300):
    """Cut pieces of one material.

    :param pieces: list of dict(part_id, production_id, index, length, width)
    :param sources: ordered list of dict(lot_id, length, width, is_offcut) to use first
    :param virtual_source: dict(length, width) of a new sheet without lot, or None
    :return: list of sheets: dict(lot_id, length, width, is_offcut, placements, offcuts)
    """
    remaining = sorted(pieces, key=lambda p: (-p['length'], -p['width'], p['part_id'], p['production_id'], p['index']))
    sheets = []
    queue = list(sources)
    while remaining:
        if queue:
            source = queue.pop(0)
        elif virtual_source:
            source = dict(virtual_source, lot_id=False, is_offcut=False)
        else:
            raise PieceTooLarge("no sheet available")
        edge = 0 if source['is_offcut'] else trim
        usable_l, usable_w = source['length'] - 2 * edge, source['width'] - 2 * edge
        placements, unplaced, shelves = _shelf_pack(remaining, usable_l, usable_w, kerf)
        if not placements:
            if not queue and source['lot_id'] is False:
                raise PieceTooLarge("a part does not fit a whole sheet")
            continue
        for placement in placements:
            placement['x'] += edge
            placement['y'] += edge
        offcuts = _offcuts(shelves, usable_l, usable_w, kerf, min_offcut)
        for offcut in offcuts:
            offcut['x'] += edge
            offcut['y'] += edge
        sheets.append(dict(source, placements=placements, offcuts=offcuts))
        remaining = unplaced
    return sheets
