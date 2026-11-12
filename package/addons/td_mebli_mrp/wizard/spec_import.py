import base64
import csv
import io

from odoo import api, fields, models
from odoo.exceptions import UserError

# header synonyms of the exports of the design programs (lower case); the first match wins
COLUMNS = {
    'name': ('name', 'part', 'деталь', 'назва', 'найменування'),
    'length_mm': ('length', 'l', 'довжина', 'длина'),
    'width_mm': ('width', 'w', 'ширина'),
    'thickness': ('thickness', 't', 'товщина', 'толщина'),
    'qty': ('qty', 'quantity', 'кількість', 'к-сть', 'количество'),
    'material': ('material', 'матеріал', 'декор', 'материал'),
    'edge_long_sides': ('edge long', 'кромка довж', 'кромка д'),
    'edge_short_sides': ('edge short', 'кромка шир', 'кромка ш'),
}


class TdMebliSpecImport(models.TransientModel):
    _name = 'td.mebli.spec.import'
    _description = 'Import of the Parts of a Specification from CSV'

    bom_id = fields.Many2one('mrp.bom', string='Specification', required=True)
    file = fields.Binary(string='CSV File', required=True)
    filename = fields.Char(string='File Name')
    mapping = fields.Text(string='Recognized Columns', readonly=True)
    preview_count = fields.Integer(string='Parts in the File', readonly=True)

    def _rows(self):
        raw = base64.b64decode(self.file or b'')
        text = raw.decode('utf-8-sig', errors='replace')
        dialect = csv.Sniffer().sniff(text[:2048], delimiters=';,\t')
        return list(csv.reader(io.StringIO(text), dialect))

    @api.model
    def _td_map_header(self, header):
        mapping = {}
        for index, title in enumerate(header):
            key = (title or '').strip().lower()
            for field, names in COLUMNS.items():
                if field not in mapping and (key in names or any(key.startswith(n) for n in names if len(n) > 2)):
                    mapping[field] = index
                    break
        return mapping

    def action_recognize(self):
        self.ensure_one()
        rows = self._rows()
        if not rows:
            raise UserError(self.env._("The file is empty."))
        mapping = self._td_map_header(rows[0])
        missing = [f for f in ('name', 'length_mm', 'width_mm') if f not in mapping]
        if missing:
            raise UserError(self.env._("Columns not recognized: %s. The file needs a part name, a length and a width.",
                                       ', '.join(missing)))
        _ = self.env._
        labels = {'name': _("part"), 'length_mm': _("length, mm"), 'width_mm': _("width, mm"), 'thickness': _("thickness"),
                  'qty': _("quantity"), 'material': _("material"), 'edge_long_sides': _("edged long sides"),
                  'edge_short_sides': _("edged short sides")}
        self.write({'mapping': '\n'.join(f"«{rows[0][i]}» → {labels[f]}" for f, i in mapping.items()),
                    'preview_count': len(rows) - 1})
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id, 'view_mode': 'form',
                'target': 'new', 'name': self.env._("Import of Parts")}

    def action_import(self):
        self.ensure_one()
        rows = self._rows()
        mapping = self._td_map_header(rows[0])
        if not all(f in mapping for f in ('name', 'length_mm', 'width_mm')):
            return self.action_recognize()
        materials = self.bom_id.bom_line_ids.product_id.filtered(lambda p: p.td_material_kind == 'board')
        default_material = materials[:1]
        if not default_material:
            raise UserError(self.env._("The specification has no board among its components: add the board first."))

        def number(row, field, default=0.0):
            index = mapping.get(field)
            if index is None or index >= len(row):
                return default
            try:
                return float((row[index] or '').replace(',', '.').strip() or default)
            except ValueError:
                return default

        vals = []
        for sequence, row in enumerate(rows[1:], start=1):
            if not row or not (row[mapping['name']] or '').strip():
                continue
            material = default_material
            if 'material' in mapping and mapping['material'] < len(row):
                wanted = (row[mapping['material']] or '').strip().lower()
                material = materials.filtered(lambda p: wanted and wanted in p.name.lower())[:1] or default_material
            vals.append({'bom_id': self.bom_id.id, 'sequence': sequence * 10, 'name': row[mapping['name']].strip(),
                         'length_mm': number(row, 'length_mm'), 'width_mm': number(row, 'width_mm'),
                         'qty': int(number(row, 'qty', 1.0)) or 1, 'material_id': material.id,
                         'edge_long_sides': int(number(row, 'edge_long_sides')),
                         'edge_short_sides': int(number(row, 'edge_short_sides'))})
        parts = self.env['td.mebli.part'].create(vals)
        self.bom_id.message_post(body=self.env._("Imported from %(file)s: %(count)s parts.",
                                                 file=self.filename or 'CSV', count=len(parts)))
        return {'type': 'ir.actions.act_window_close'}
