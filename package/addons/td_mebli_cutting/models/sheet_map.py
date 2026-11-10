"""Drawing of a cutting sheet as inline SVG: parts by manufacturing order, offcuts, waste. No ORM here."""
from html import escape

from markupsafe import Markup

PALETTE = ('#d9b98a', '#a9c4d6', '#c3d6a1', '#e0b3b3', '#c9b7dd', '#e8d48a')


def _text(x, y, size, value, fill='#2b2118', anchor='middle', weight='500'):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
            f'font-family="Inter, Segoe UI, Roboto, sans-serif">{escape(value)}</text>')


def render_svg(length, width, placements, offcuts, productions, offcut_label, unit='мм'):
    """:param placements: list of dict(x, y, length, width, label, production_id)
    :param offcuts: list of dict(x, y, length, width)"""
    colour = {production: PALETTE[index % len(PALETTE)] for index, production in enumerate(productions)}
    unit_font = max(length // 34, 34)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-20 -20 {length + 40} {width + 40}" '
             f'style="width:{round(min(100.0, max(40.0, length / 28.0)), 1)}%;height:auto;max-height:250px;background:#fff" role="img">',
             '<defs><pattern id="td-hatch" width="40" height="40" patternUnits="userSpaceOnUse" '
             'patternTransform="rotate(45)"><rect width="40" height="40" fill="#e3f1df"/>'
             '<line x1="0" y1="0" x2="0" y2="40" stroke="#8fc08a" stroke-width="10"/></pattern></defs>',
             f'<rect x="0" y="0" width="{length}" height="{width}" fill="#f1ece4" stroke="#8c7a63" stroke-width="6"/>']
    for item in offcuts:
        parts.append(f'<rect x="{item["x"]}" y="{item["y"]}" width="{item["length"]}" height="{item["width"]}" '
                     f'fill="url(#td-hatch)" stroke="#4f8f49" stroke-width="5" stroke-dasharray="24 12"/>')
        centre_x, centre_y = item['x'] + item['length'] / 2, item['y'] + item['width'] / 2
        size = f'{item["length"]}×{item["width"]}'
        if item['length'] >= unit_font * 11:
            parts.append(_text(centre_x, centre_y + unit_font * 0.3, unit_font, f'{offcut_label} {size}',
                               fill='#2f6b2a', weight='700'))
        elif item['width'] >= unit_font * 6:
            # a narrow strip: the label is turned along it
            parts.append(f'<g transform="rotate(-90 {centre_x} {centre_y})">' +
                         _text(centre_x, centre_y + unit_font * 0.3, unit_font, size, fill='#2f6b2a', weight='700') + '</g>')
    for item in placements:
        fill = colour.get(item['production_id'], PALETTE[0])
        parts.append(f'<rect x="{item["x"]}" y="{item["y"]}" width="{item["length"]}" height="{item["width"]}" '
                     f'fill="{fill}" stroke="#6b5a45" stroke-width="3"/>')
        if item['length'] > unit_font * 8 and item['width'] > unit_font * 2.6:
            parts.append(_text(item['x'] + item['length'] / 2, item['y'] + item['width'] / 2 - unit_font * 0.15,
                               unit_font, item['label']))
            parts.append(_text(item['x'] + item['length'] / 2, item['y'] + item['width'] / 2 + unit_font * 1.0,
                               int(unit_font * 0.85), f'{item["length"]}×{item["width"]}', fill='#5b4a36', weight='400'))
        elif item['length'] > unit_font * 5 and item['width'] > unit_font * 1.4:
            parts.append(_text(item['x'] + item['length'] / 2, item['y'] + item['width'] / 2 + unit_font * 0.3,
                               int(unit_font * 0.8), f'{item["length"]}×{item["width"]}', fill='#5b4a36', weight='400'))
    parts.append('</svg>')
    return Markup(''.join(parts))


def legend(part_label, offcut_label, waste_label):
    """Legend under the cutting map: what the colours mean."""
    def swatch(style, label):
        return (f'<span class="d-inline-flex align-items-center me-4"><span style="display:inline-block;width:22px;height:14px;'
                f'margin-right:6px;{style}"></span>{escape(label)}</span>')
    return Markup('<div class="small text-muted mb-2">%s%s%s</div>') % (
        Markup(swatch('background:#d9b98a;border:1px solid #6b5a45', part_label)),
        Markup(swatch('background:#e3f1df;border:1px dashed #4f8f49', offcut_label)),
        Markup(swatch('background:#f1ece4;border:1px solid #8c7a63', waste_label)))
