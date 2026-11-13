import base64
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

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
# AC-046 / tr/td_mebli_mrp.md §8 rule 1: columns without which nothing is imported
REQUIRED = ('name', 'length_mm', 'width_mm', 'qty', 'material')
FIELD_SELECTION = [
    ('name', 'Part'), ('length_mm', 'Length'), ('width_mm', 'Width'), ('thickness', 'Thickness'), ('qty', 'Quantity'),
    ('material', 'Material'), ('edge_long_sides', 'Edged Long Sides'), ('edge_short_sides', 'Edged Short Sides'),
]
# AC-050: at most this many rows of the file leave the database for the AI hint, with the headers
AI_SAMPLE_ROWS = 10
AI_URL_PARAM = 'td_mebli_mrp.ai_mapping_url'


def header_signature(header):
    """Normalized titles of the columns: the key of a mapping template (AC-049)."""
    return '|'.join((title or '').strip().lower() for title in header)


class TdMebliImportTemplate(models.Model):
    """AC-049: a template of the mapping of the columns of a file of a design program («PRO100 of the showroom»)."""
    _name = 'td.mebli.import.template'
    _description = 'Mapping Template of the Columns of a Parts File'
    _order = 'name, id'

    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company,
                                 index=True)
    header_signature = fields.Char(string='Header Signature', required=True, index=True,
                                   help="Normalized titles of the columns of the file: a file with the same titles "
                                        "is recognized by this template.")
    mapping_json = fields.Json(string='Mapping', required=True,
                               help="Number of the column of the file for every field of the part.")
    active = fields.Boolean(default=True)

    @api.model
    def _td_find(self, header, company):
        return self.search([('header_signature', '=', header_signature(header)), ('company_id', '=', company.id)],
                           limit=1)


class TdMebliSpecImportColumn(models.TransientModel):
    _name = 'td.mebli.spec.import.column'
    _description = 'Column of a Parts File'
    _order = 'index'

    wizard_id = fields.Many2one('td.mebli.spec.import', required=True, ondelete='cascade')
    index = fields.Integer(string='No.', readonly=True)
    title = fields.Char(string='Column of the File', readonly=True)
    field_name = fields.Selection(FIELD_SELECTION, string='Field of the Part')
    suggested = fields.Boolean(string='AI Suggestion', readonly=True)


class TdMebliSpecImportMaterial(models.TransientModel):
    _name = 'td.mebli.spec.import.material'
    _description = 'Material of a Parts File Mapped by Hand'

    wizard_id = fields.Many2one('td.mebli.spec.import', required=True, ondelete='cascade')
    code = fields.Char(string='Material in the File', readonly=True)
    material_id = fields.Many2one('product.product', string='Board', domain=[('td_material_kind', '=', 'board')])


class TdMebliSpecImport(models.TransientModel):
    _name = 'td.mebli.spec.import'
    _description = 'Import of the Parts of a Specification from CSV'

    bom_id = fields.Many2one('mrp.bom', string='Specification', required=True)
    file = fields.Binary(string='CSV or Excel File', required=True)
    filename = fields.Char(string='File Name')
    mode = fields.Selection([('replace', 'Replace the parts'), ('append', 'Add to the existing parts')],
                            string='Mode', required=True, default='replace')
    mapping = fields.Text(string='Recognized Columns', readonly=True)
    preview_count = fields.Integer(string='Parts in the File', readonly=True)
    template_id = fields.Many2one('td.mebli.import.template', string='Mapping Template', readonly=True)
    column_ids = fields.One2many('td.mebli.spec.import.column', 'wizard_id', string='Columns')
    missing_columns = fields.Char(string='Columns not Found', readonly=True)
    unknown_lines = fields.Text(string='Rows with an Unknown Material', readonly=True)
    material_map_ids = fields.One2many('td.mebli.spec.import.material', 'wizard_id', string='Materials to Map')
    template_name = fields.Char(string='Save the Mapping as Template',
                                help="Name of the template, e.g. «PRO100 of the showroom»: the next file with the same "
                                     "headers is recognized without this step.")
    ai_note = fields.Char(string='AI Hint', readonly=True)

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------
    def _rows(self):
        """Rows of text of the file, read by the standard reader of the import of Odoo (base_import: CSV, XLSX, XLS,
        ODS) — the same reader the import of the price lists of the suppliers uses (td_mebli_purchase)."""
        raw = base64.b64decode(self.file or b'')
        if not raw:
            return []
        try:
            raw.decode('utf-8')
            encoding = 'utf-8-sig'
        except UnicodeDecodeError:
            encoding = ''  # the standard guesses the encoding (e.g. windows-1251 of an old Excel)
        importer = self.env['base_import.import'].create({'res_model': self._name, 'file': raw,
                                                          'file_name': self.filename or ''})
        try:
            result = importer._read_file({'quoting': '"', 'separator': '', 'encoding': encoding})
        except UserError:
            raise
        except Exception as error:  # noqa: BLE001 — any broken file is a user error, not a crash
            raise UserError(self.env._("The file cannot be read: %s", error)) from error
        rows = result[1] if result else []
        return [['' if cell is None else str(cell) for cell in row] for row in rows]

    @api.model
    def _td_map_header(self, header):
        """Dictionary of synonyms: {field: column index}."""
        mapping = {}
        for index, title in enumerate(header):
            key = (title or '').strip().lower()
            for field, names in COLUMNS.items():
                if field not in mapping and (key in names or any(key.startswith(n) for n in names if len(n) > 2)):
                    mapping[field] = index
                    break
        return mapping

    def _td_current_mapping(self, header):
        """Mapping of the columns: the lines of the wizard once they exist (set or corrected by hand), else the template
        of the same headers, else the dictionary of synonyms."""
        if self.column_ids:
            return {col.field_name: col.index for col in self.column_ids.sorted('index')
                    if col.field_name and col.index < len(header)}
        template = self.env['td.mebli.import.template']._td_find(header, self.bom_id.company_id or self.env.company)
        if template:
            self.template_id = template
            return {field: int(index) for field, index in (template.mapping_json or {}).items()
                    if int(index) < len(header)}
        return self._td_map_header(header)

    def _td_field_labels(self):
        """Translated names of the fields of a part (the selection of the column lines)."""
        return dict(self.env['td.mebli.spec.import.column']._fields['field_name']._description_selection(self.env))

    def _td_missing_text(self, missing):
        labels = self._td_field_labels()
        return ', '.join(labels[field] for field in missing)

    # ------------------------------------------------------------------
    # AC-050: AI hint of the mapping (box B, off by default)
    # ------------------------------------------------------------------
    @api.model
    def _td_ai_enabled(self):
        """The hint is asked only when the function is on (feature group of box B) and a model provider is set
        (system parameter, after the decision under DATA_POLICY): nothing leaves the database otherwise."""
        if not self.env.user.has_group('td_mebli_base.group_feature_ai_mapping'):
            return False
        return bool(self.env['ir.config_parameter'].sudo().get_param(AI_URL_PARAM))

    @api.model
    def _td_ai_payload(self, header, rows):
        """What leaves the database: the headers and at most AI_SAMPLE_ROWS rows of the file — sizes and materials of
        parts, no order, no customer (the file of the design program has no customer data)."""
        return {'headers': list(header), 'rows': [list(row) for row in rows[:AI_SAMPLE_ROWS]],
                'fields': [key for key, _label in FIELD_SELECTION]}

    @api.model
    def _td_ai_request(self, url, payload):
        import requests  # noqa: PLC0415 — only when the function is on
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()

    def _td_ai_suggest(self, header, rows):
        """{field: column index} proposed by the model, or {} — off, not reachable, bad answer: manual mapping without
        an error."""
        if not self._td_ai_enabled():
            return {}
        url = self.env['ir.config_parameter'].sudo().get_param(AI_URL_PARAM)
        try:
            answer = self._td_ai_request(url, self._td_ai_payload(header, rows))
            return {field: int(index) for field, index in (answer.get('mapping') or {}).items()
                    if field in COLUMNS and 0 <= int(index) < len(header)}
        except Exception as error:  # noqa: BLE001 — the hint is optional: any failure means manual mapping
            _logger.info("AI hint of the column mapping is not available: %s", error)
            return {}

    # ------------------------------------------------------------------
    # Materials (AC-047)
    # ------------------------------------------------------------------
    def _td_material_lookup(self, codes):
        """{code (lower case): product} — the board directory by internal reference or name, then the materials mapped
        by hand in the wizard."""
        found = {}
        Product = self.env['product.product']
        for code in codes:
            if not code:
                continue
            product = Product.search([('td_material_kind', '=', 'board'), ('default_code', '=ilike', code)], limit=1) \
                or Product.search([('td_material_kind', '=', 'board'), ('name', '=ilike', code)], limit=1)
            if product:
                found[code] = product
        for line in self.material_map_ids.filtered('material_id'):
            found[(line.code or '').strip().lower()] = line.material_id
        return found

    def _td_default_material(self):
        """A row without a material takes the board of the specification."""
        return self.bom_id.bom_line_ids.product_id.filtered(lambda p: p.td_material_kind == 'board')[:1]

    def _td_check_materials(self, rows, mapping):
        """Rows whose material is not in the directory: [(row number, code)], the lookup and the default board."""
        index = mapping.get('material')
        codes = {}
        for number, row in enumerate(rows[1:], start=2):
            if not row or not (row[mapping['name']] if mapping['name'] < len(row) else '').strip():
                continue
            codes[number] = (row[index] if index is not None and index < len(row) else '').strip()
        lookup = self._td_material_lookup({code.lower() for code in codes.values()})
        default = self._td_default_material()
        unknown = [(number, code) for number, code in codes.items()
                   if not (lookup.get(code.lower()) if code else default)]
        return unknown, lookup, default

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------
    def _td_reopen(self):
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id, 'view_mode': 'form',
                'target': 'new', 'name': self.env._("Import of Parts")}

    def action_recognize(self):
        """Shows the recognized columns, the number of parts and the rows with an unknown material (AC-045, AC-047);
        columns not recognized are mapped by hand in the same dialog (AC-049), with the AI hint in box B (AC-050)."""
        self.ensure_one()
        rows = self._rows()
        if not rows:
            raise UserError(self.env._("The file is empty."))
        header = rows[0]
        first = not self.column_ids
        mapping = self._td_current_mapping(header)
        suggested = {}
        if first and any(field not in mapping for field in REQUIRED):
            suggested = {field: index for field, index in self._td_ai_suggest(header, rows[1:]).items()
                         if field not in mapping and index not in mapping.values()}
            mapping.update(suggested)
        if first:
            by_index = {index: field for field, index in mapping.items()}
            self.column_ids = [(0, 0, {'index': index, 'title': title, 'field_name': by_index.get(index),
                                       'suggested': by_index.get(index) in suggested})
                               for index, title in enumerate(header)]
        labels = self._td_field_labels()
        missing = [field for field in REQUIRED if field not in mapping]
        vals = {
            'mapping': '\n'.join(f"«{header[index]}» → {labels[field]}"
                                 for field, index in sorted(mapping.items(), key=lambda item: item[1])),
            'preview_count': len([row for row in rows[1:] if row and any(cell.strip() for cell in row)]),
            'missing_columns': self._td_missing_text(missing) if missing else False,
            'unknown_lines': False,
        }
        if first:
            vals['ai_note'] = self.env._("AI suggestion: check the columns marked as suggested before the import.") \
                if suggested else False
        if not missing:
            unknown, _lookup, _default = self._td_check_materials(rows, mapping)
            if unknown:
                vals['unknown_lines'] = '\n'.join(
                    self.env._("Row %(row)s: «%(code)s» — Material not found", row=number, code=code or '—')
                    for number, code in unknown)
                known = set(self.material_map_ids.mapped('code'))
                self.material_map_ids = [(0, 0, {'code': code}) for code in
                                         dict.fromkeys(code.lower() for _number, code in unknown if code)
                                         if code not in known]
        self.write(vals)
        return self._td_reopen()

    def action_import(self):
        self.ensure_one()
        rows = self._rows()
        if not rows:
            raise UserError(self.env._("The file is empty."))
        header = rows[0]
        mapping = self._td_current_mapping(header)
        missing = [field for field in REQUIRED if field not in mapping]
        if missing:  # AC-046: nothing is written
            raise UserError(self.env._("Columns not found in the file: %s. Check the headers or set the mapping.",
                                       self._td_missing_text(missing)))
        unknown, lookup, default = self._td_check_materials(rows, mapping)
        if unknown:  # AC-047: no import while a row has a material out of the directory
            raise UserError(self.env._("Material not found in rows %s: map the material or remove the rows.",
                                       ', '.join(str(number) for number, _code in unknown)))

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
            if not row or not (row[mapping['name']] if mapping['name'] < len(row) else '').strip():
                continue
            code = (row[mapping['material']] if mapping['material'] < len(row) else '').strip()
            material = lookup.get(code.lower()) if code else default
            vals.append({'bom_id': self.bom_id.id, 'sequence': sequence * 10, 'name': row[mapping['name']].strip(),
                         'length_mm': number(row, 'length_mm'), 'width_mm': number(row, 'width_mm'),
                         'qty': int(number(row, 'qty', 1.0)) or 1, 'material_id': material.id,
                         'edge_long_sides': int(number(row, 'edge_long_sides')),
                         'edge_short_sides': int(number(row, 'edge_short_sides'))})
        bom = self.bom_id
        self.env['td.mebli.part']._td_check_not_sent(bom)  # AC-052: a sent specification is neither replaced nor extended
        if self.mode == 'replace' and bom.td_part_ids:
            # the technologist has no unlink right on parts in general: the wizard replaces the parts of this
            # specification only, as the system
            bom.td_part_ids.sudo().unlink()
        parts = self.env['td.mebli.part'].create(vals)  # one create for the whole file (AC-048)
        bom.sudo()._td_recompute_component_lines()
        if self.template_name and self.column_ids:
            self.env['td.mebli.import.template'].create({
                'name': self.template_name, 'company_id': (bom.company_id or self.env.company).id,
                'header_signature': header_signature(header), 'mapping_json': mapping})
        mode = dict(self._fields['mode']._description_selection(self.env))[self.mode]
        # the technologist (mrp user) may add parts but only reads the BoM: the log line in the chatter is written by
        # the system on behalf of the user (posting needs write access on the BoM)
        bom.sudo().message_post(
            body=self.env._("Imported from %(file)s: %(count)s parts, mode: %(mode)s.",
                            file=self.filename or 'CSV', count=len(parts), mode=mode),
            attachments=[(self.filename or 'parts.csv', base64.b64decode(self.file))],
            author_id=self.env.user.partner_id.id)
        return {'type': 'ir.actions.act_window_close'}
