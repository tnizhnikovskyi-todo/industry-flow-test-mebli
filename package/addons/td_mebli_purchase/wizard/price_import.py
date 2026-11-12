import base64
import csv
import io

from odoo import api, fields, models
from odoo.exceptions import UserError

# header synonyms of the price lists of the suppliers (lower case); the first match wins
COLUMNS = {
    'code': ('code', 'sku', 'артикул', 'код', 'internal reference'),
    'name': ('name', 'product', 'найменування', 'назва', 'товар', 'наименование'),
    'price': ('price', 'ціна', 'цена', 'price, uah', 'ціна, грн'),
    'min_qty': ('min qty', 'minimum', 'мін', 'мінімальна', 'від', 'минимальная'),
    'delay': ('delay', 'lead time', 'строк', 'термін', 'днів', 'срок'),
}


def read_table(raw, filename):
    """Rows of text from CSV or the first sheet of an Excel file (.xlsx, openpyxl — the library of the standard import
    of Odoo, base_import)."""
    if raw[:2] == b'PK' or (filename or '').lower().endswith('.xlsx'):
        import openpyxl  # noqa: PLC0415
        book = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        rows = [['' if v is None else str(int(v)) if isinstance(v, float) and v.is_integer() else str(v) for v in values]
                for values in book.worksheets[0].iter_rows(values_only=True)]
        book.close()
    else:
        text = raw.decode('utf-8-sig', errors='replace')
        dialect = csv.Sniffer().sniff(text[:2048], delimiters=';,\t')
        rows = list(csv.reader(io.StringIO(text), dialect))
    return [row for row in rows if any((c or '').strip() for c in row)]


def to_number(text):
    text = (text or '').replace('\xa0', '').replace(' ', '').replace(',', '.')
    try:
        return float(text)
    except ValueError:
        return 0.0


class TdMebliPriceImport(models.TransientModel):
    """Position 19: the price list of a supplier from Excel or CSV goes into the standard vendor pricelist
    (product.supplierinfo: price, minimal quantity, lead time). Nothing is kept here: the wizard reads the file, shows
    what will change and writes the standard records."""
    _name = 'td.mebli.price.import'
    _description = 'Import of a Supplier Price List'

    partner_id = fields.Many2one('res.partner', string='Supplier', required=True)
    file = fields.Binary(string='Excel or CSV File', required=True)
    filename = fields.Char(string='File Name')
    date_start = fields.Date(string='Prices Valid From', default=fields.Date.context_today)
    mapping = fields.Text(string='Recognized Columns', readonly=True)
    line_ids = fields.One2many('td.mebli.price.import.line', 'wizard_id', string='Prices in the File', readonly=True)
    unknown_count = fields.Integer(string='Codes not Found', compute='_compute_counts')
    change_count = fields.Integer(string='Prices to Write', compute='_compute_counts')

    @api.depends('line_ids.status')
    def _compute_counts(self):
        for wizard in self:
            wizard.unknown_count = len(wizard.line_ids.filtered(lambda l: l.status == 'unknown'))
            wizard.change_count = len(wizard.line_ids.filtered(lambda l: l.status in ('new', 'update')))

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

    def _td_find_product(self, code, name):
        Product = self.env['product.product']
        product = Product.search([('default_code', '=', code)], limit=1) if code else Product
        if not product and code:  # the code of the supplier in his own pricelist line (standard product_code)
            product = self.env['product.supplierinfo'].search(
                [('partner_id', '=', self.partner_id.id), ('product_code', '=', code)], limit=1).product_tmpl_id.product_variant_id
        if not product and name:
            product = Product.search([('name', '=ilike', name)], limit=1)
        return product

    def action_recognize(self):
        self.ensure_one()
        try:
            rows = read_table(base64.b64decode(self.file or b''), self.filename)
        except Exception as error:  # noqa: BLE001 — a broken file is a user error
            raise UserError(self.env._("The file cannot be read: %s", error)) from error
        if len(rows) < 2:
            raise UserError(self.env._("The file has no prices."))
        mapping = self._td_map_header(rows[0])
        if 'price' not in mapping or not ({'code', 'name'} & set(mapping)):
            raise UserError(self.env._("Columns not recognized: the file needs a price and a code or a name."))
        _ = self.env._
        labels = {'code': _("code"), 'name': _("product"), 'price': _("price"), 'min_qty': _("minimal quantity"),
                  'delay': _("lead time, days")}
        lines = []
        for row in rows[1:]:
            cell = lambda f: (row[mapping[f]] if f in mapping and mapping[f] < len(row) else '').strip()  # noqa: E731
            price = to_number(cell('price'))
            if not price:
                continue
            product = self._td_find_product(cell('code'), cell('name'))
            min_qty = to_number(cell('min_qty'))
            current = self.env['product.supplierinfo'].search([
                ('partner_id', '=', self.partner_id.id), ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('min_qty', '=', min_qty)], limit=1) if product else self.env['product.supplierinfo']
            lines.append((0, 0, {
                'code': cell('code'), 'name': cell('name') or product.name, 'product_id': product.id,
                'price': price, 'min_qty': min_qty, 'delay': int(to_number(cell('delay'))) if 'delay' in mapping else 0,
                'has_delay': 'delay' in mapping, 'supplierinfo_id': current.id, 'old_price': current.price,
                'status': 'unknown' if not product else 'update' if current else 'new',
            }))
        self.line_ids = [(5, 0, 0)] + lines
        self.mapping = '\n'.join(f"«{rows[0][i]}» → {labels[f]}" for f, i in mapping.items())
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id, 'view_mode': 'form',
                'target': 'new', 'name': self.env._("Import of a Supplier Price List")}

    def action_import(self):
        """Writes the standard vendor pricelist: the existing line of the supplier (same product and minimal quantity)
        gets the new price, a missing one is created. Codes not found are left out (listed in the chatter)."""
        self.ensure_one()
        Info = self.env['product.supplierinfo']
        done = 0
        for line in self.line_ids.filtered(lambda l: l.status in ('new', 'update')):
            vals = {'price': line.price, 'date_start': self.date_start}
            if line.has_delay:
                vals['delay'] = line.delay
            if line.supplierinfo_id:
                line.supplierinfo_id.write(vals)
            else:
                Info.create(dict(vals, partner_id=self.partner_id.id, product_tmpl_id=line.product_id.product_tmpl_id.id,
                                 min_qty=line.min_qty, product_code=line.code or False))
            done += 1
        unknown = self.line_ids.filtered(lambda l: l.status == 'unknown')
        body = self.env._("Price list imported from «%(file)s»: %(done)s prices written.", file=self.filename or '',
                          done=done)
        if unknown:
            body += ' ' + self.env._("Not found: %s.", ', '.join(unknown.mapped(lambda l: l.code or l.name)))
        self.partner_id.message_post(body=body)
        action = self.env['ir.actions.act_window']._for_xml_id('product.product_supplierinfo_type_action')
        action.update(domain=[('partner_id', '=', self.partner_id.id)], context={'search_default_partner_id': self.partner_id.id})
        return action


class TdMebliPriceImportLine(models.TransientModel):
    _name = 'td.mebli.price.import.line'
    _description = 'Price of a Supplier Price List in the File'

    wizard_id = fields.Many2one('td.mebli.price.import', required=True, ondelete='cascade')
    code = fields.Char(string='Code')
    name = fields.Char(string='Product in the File')
    product_id = fields.Many2one('product.product', string='Product')
    price = fields.Float(string='New Price', digits='Product Price')
    old_price = fields.Float(string='Current Price', digits='Product Price')
    min_qty = fields.Float(string='Minimal Quantity', digits='Product Unit')
    delay = fields.Integer(string='Lead Time, days')
    has_delay = fields.Boolean()
    supplierinfo_id = fields.Many2one('product.supplierinfo', string='Pricelist Line')
    status = fields.Selection([('new', 'New price line'), ('update', 'Price changed'), ('unknown', 'Not found')],
                              string='Result')
