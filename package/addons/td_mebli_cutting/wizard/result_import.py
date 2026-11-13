import base64
import csv
import io

from odoo import fields, models
from odoo.exceptions import UserError

# AC-131: the result file of the cutting program. The real format of the cutting program of the client is not known
# (SPEC ВП-1): this is the CSV described by SPEC (sheet, part, position, offcuts), one row per placed part or offcut:
#   sheet;material;sheet_length;sheet_width;lot;type;code;x;y;length;width;rotated
# type — «part» or «offcut»; code — the code of the part from the cutting file (<manufacturing order>-<No.>);
# material — internal reference or name of the board (empty: the board of the part); lot — optional sheet/offcut lot.
RESULT_COLUMNS = ('sheet', 'material', 'sheet_length', 'sheet_width', 'lot', 'type', 'code', 'x', 'y', 'length',
                  'width', 'rotated')


class TdMebliCuttingResultImport(models.TransientModel):
    _name = 'td.mebli.cutting.result.import'
    _description = 'Import of the Result of the Cutting Program'

    job_id = fields.Many2one('td.mebli.cutting.job', string='Cutting Job', required=True)
    file = fields.Binary(string='Result File (CSV)', required=True)
    filename = fields.Char(string='File Name')

    def _td_read(self):
        raw = base64.b64decode(self.file or b'')
        try:
            text = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            text = raw.decode('cp1251')
        first = text.splitlines()[0] if text else ''
        delimiter = ';' if first.count(';') >= first.count(',') else ','
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        header = [(name or '').strip().lower() for name in (reader.fieldnames or [])]
        missing = [name for name in ('sheet', 'type', 'code', 'x', 'y', 'length', 'width') if name not in header]
        if missing:
            raise UserError(self.env._("The result file has no columns: %s.", ', '.join(missing)))
        return [{(key or '').strip().lower(): (value or '').strip() for key, value in row.items()} for row in reader]

    def _td_payload(self, rows):
        job = self.job_id
        parts = {}
        for production in job.production_ids:
            for code, part in job._td_part_codes(production):
                parts[code] = (part, production)

        def integer(row, key):
            try:
                return int(round(float((row.get(key) or '0').replace(',', '.'))))
            except ValueError as error:
                raise UserError(self.env._("Not a number in column %(column)s: «%(value)s».",
                                           column=key, value=row.get(key))) from error

        Product = self.env['product.product']
        sheets, counters = {}, {}
        for row in rows:
            kind = (row.get('type') or 'part').lower()
            code = row.get('code') or ''
            if kind == 'part' and code not in parts:
                raise UserError(self.env._("Part %s does not belong to the job", code))
            key = row.get('sheet') or '1'
            if key not in sheets:
                material = row.get('material') or ''
                product = Product.search([('td_material_kind', '=', 'board'), '|', ('default_code', '=', material),
                                          ('name', '=', material)], limit=1) if material else Product
                lot = self.env['stock.lot'].search([('name', '=', row['lot'])], limit=1) if row.get('lot') else False
                sheets[key] = {'product_id': product.id, 'lot_id': lot.id if lot else False,
                               'length': integer(row, 'sheet_length'), 'width': integer(row, 'sheet_width'),
                               'placements': [], 'offcuts': []}
            sheet = sheets[key]
            if kind == 'offcut':
                sheet['offcuts'].append({'x': integer(row, 'x'), 'y': integer(row, 'y'),
                                         'length': integer(row, 'length'), 'width': integer(row, 'width')})
                continue
            part, production = parts[code]
            if not sheet['product_id']:
                sheet['product_id'] = part.material_id.id
            counters[code] = counters.get(code, 0) + 1
            sheet['placements'].append({
                'part_id': part.id, 'production_id': production.id, 'index': counters[code] - 1,
                'x': integer(row, 'x'), 'y': integer(row, 'y'), 'length': integer(row, 'length'),
                'width': integer(row, 'width'), 'rotated': (row.get('rotated') or '').lower() in ('1', 'yes', 'true', 'так')})
        for key, sheet in sheets.items():
            if not sheet['product_id']:
                raise UserError(self.env._("Sheet %s: the board is not known.", key))
        return {'source': 'imported', 'sheets': [sheets[key] for key in sheets]}

    def action_import(self):
        """AC-131: sheets, placements and offcuts from the result file; a part not of this job — nothing is written."""
        self.ensure_one()
        self.job_id._check_state('sent', 'result')
        rows = self._td_read()
        if not rows:
            raise UserError(self.env._("The file is empty."))
        payload = self._td_payload(rows)
        self.job_id._td_apply_result(payload)
        if self.filename:
            self.env['ir.attachment'].create({
                'name': self.filename, 'datas': self.file, 'res_model': self.job_id._name, 'res_id': self.job_id.id})
        return {'type': 'ir.actions.act_window_close'}
