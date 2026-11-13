import base64
import re
from datetime import timedelta

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

# a number written by a person: «12 345,00 грн», «1.234,5», «845.50 UAH», «5 дн.», «7 days»; the text after the number
# may only be a unit (letters, dots); anything else (two numbers, «5-7 днів», «за запитом») is not recognized
NUMBER = re.compile(r'^\s*([-+]?\d[\d\s\u00a0\u202f.,\']*)\s*([^\W\d_][\w.]*\.?|[₴$€])?\s*$')


def to_number(text):
    """The number in the cell or None when the cell is not a number (never 0 instead of an error)."""
    match = NUMBER.match(str(text or ''))
    if not match:
        return None
    digits = re.sub(r"[\s\u00a0\u202f']", '', match.group(1))
    if ',' in digits and '.' in digits:  # the last separator is the decimal one, the other groups the thousands
        thousand = ',' if digits.rfind('.') > digits.rfind(',') else '.'
        digits = digits.replace(thousand, '')
    elif digits.count(',') > 1 or digits.count('.') > 1:  # «1,234,567» or «1.234.567»: groups only
        digits = digits.replace(',', '').replace('.', '')
    digits = digits.replace(',', '.')
    try:
        return float(digits)
    except ValueError:
        return None


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
    error_count = fields.Integer(string='Rows not Recognized', compute='_compute_counts',
                                 help="Rows whose price or quantity is not a number: they are not written.")

    @api.depends('line_ids.status')
    def _compute_counts(self):
        for wizard in self:
            wizard.unknown_count = len(wizard.line_ids.filtered(lambda l: l.status == 'unknown'))
            wizard.change_count = len(wizard.line_ids.filtered(lambda l: l.status in ('new', 'update')))
            wizard.error_count = len(wizard.line_ids.filtered(lambda l: l.status == 'error'))

    @api.model
    def _td_read_rows(self, raw, filename):
        """Rows of text of the file, read by the standard reader of the import of Odoo (base_import: CSV, XLSX, XLS,
        ODS) — the same reader the import of the parts of a specification uses. A CSV saved in UTF-8 is read as UTF-8,
        else the standard guesses the encoding (e.g. windows-1251 of an old Excel)."""
        if not raw:
            return []
        try:
            raw.decode('utf-8')
            encoding = 'utf-8-sig'
        except UnicodeDecodeError:
            encoding = ''
        importer = self.env['base_import.import'].create({'res_model': self._name, 'file': raw,
                                                          'file_name': filename or ''})
        result = importer._read_file({'quoting': '"', 'separator': '', 'encoding': encoding})
        rows = result[1] if result else []
        return [['' if cell is None else str(cell) for cell in row] for row in rows]

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
            rows = self._td_read_rows(base64.b64decode(self.file or b''), self.filename)
        except UserError:
            raise
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
        today = self.date_start or fields.Date.context_today(self)
        for row in rows[1:]:
            cell = lambda f: (row[mapping[f]] if f in mapping and mapping[f] < len(row) else '').strip()  # noqa: E731
            if not cell('price') and not cell('code') and not cell('name'):
                continue  # a title or an empty row of the price list
            if not cell('price'):
                continue  # a section header of the price list («Плити ДСП»): no price, nothing to write
            errors = []
            price = to_number(cell('price'))
            if price is None or price <= 0:
                errors.append(_("price «%s» is not a number", cell('price')) if price is None
                              else _("price %s is not positive", cell('price')))
            min_qty = to_number(cell('min_qty')) if cell('min_qty') else 0.0
            if min_qty is None or min_qty < 0:
                errors.append(_("minimal quantity «%s» is not a number", cell('min_qty')))
                min_qty = 0.0
            delay = to_number(cell('delay')) if cell('delay') else None
            note = ''
            if cell('delay') and (delay is None or delay < 0 or delay != int(delay)):
                # the lead time of the pricelist line is kept as it is: no zero instead of «5-7 днів»
                note = _("lead time «%s» is not recognized: the current lead time is kept", cell('delay'))
                delay = None
            product = self._td_find_product(cell('code'), cell('name'))
            current = self._td_current_line(product, min_qty, today) if product else self.env['product.supplierinfo']
            status = 'error' if errors else 'unknown' if not product else 'update' if current else 'new'
            lines.append((0, 0, {
                'code': cell('code'), 'name': cell('name') or product.name, 'product_id': product.id,
                'price': price or 0.0, 'min_qty': min_qty, 'delay': int(delay) if delay is not None else 0,
                'has_delay': delay is not None, 'supplierinfo_id': current.id, 'old_price': current.price,
                'status': status, 'error': '; '.join(errors + ([note] if note else [])),
            }))
        self.line_ids = [(5, 0, 0)] + lines
        self.mapping = '\n'.join(f"«{rows[0][i]}» → {labels[f]}" for f, i in mapping.items())
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id, 'view_mode': 'form',
                'target': 'new', 'name': self.env._("Import of a Supplier Price List")}

    def _td_current_line(self, product, min_qty, day):
        """The pricelist line of the supplier valid on the day for the product and the minimal quantity (standard
        validity dates of product.supplierinfo); lines that ended before the day are history and are not touched."""
        return self.env['product.supplierinfo'].search([
            ('partner_id', '=', self.partner_id.id), ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('min_qty', '=', min_qty), '|', ('date_start', '=', False), ('date_start', '<=', day),
            '|', ('date_end', '=', False), ('date_end', '>=', day)], order='date_start desc, id desc', limit=1)

    def action_import(self):
        """Writes the standard vendor pricelist. The line valid from the same date gets the new price; a line valid from
        an earlier date keeps its price as history (it ends the day before) and a new dated line is created, so the
        earlier purchases keep their price. Rows with errors and codes not found are not written (listed in the chatter).
        The lead time is written only when it was recognized."""
        self.ensure_one()
        Info = self.env['product.supplierinfo']
        start = self.date_start or fields.Date.context_today(self)
        done = 0
        for line in self.line_ids.filtered(lambda l: l.status in ('new', 'update')):
            vals = {'price': line.price}
            if line.has_delay:
                vals['delay'] = line.delay
            current = line.supplierinfo_id
            if current and current.date_start == start:
                current.write(vals)
            elif current and current.price == line.price and not current.date_end:
                if line.has_delay:
                    current.write({'delay': line.delay})
            else:
                if current:
                    vals.setdefault('delay', current.delay)
                    current.date_end = start - timedelta(days=1)
                Info.create(dict(vals, partner_id=self.partner_id.id, product_tmpl_id=line.product_id.product_tmpl_id.id,
                                 min_qty=line.min_qty, date_start=start,
                                 product_code=line.code or current.product_code or False))
            done += 1
        unknown = self.line_ids.filtered(lambda l: l.status == 'unknown')
        errors = self.line_ids.filtered(lambda l: l.status == 'error')
        body = self.env._("Price list imported from «%(file)s»: %(done)s prices written.", file=self.filename or '',
                          done=done)
        if unknown:
            body += ' ' + self.env._("Not found: %s.", ', '.join(unknown.mapped(lambda l: l.code or l.name)))
        if errors:
            body += ' ' + self.env._("Not written, errors: %s.", '; '.join(
                errors.mapped(lambda l: '%s — %s' % (l.code or l.name, l.error))))
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
    status = fields.Selection([('new', 'New price line'), ('update', 'Price changed'), ('unknown', 'Not found'),
                               ('error', 'Not recognized')], string='Result')
    error = fields.Char(string='Problem', help="Why the row is not written, or what is not written (the lead time).")
