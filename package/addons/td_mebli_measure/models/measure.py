from odoo import api, fields, models


class TdMebliMeasure(models.Model):
    _name = 'td.mebli.measure'
    _description = 'Measurement Sheet'
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(string='Number', required=True, readonly=True, copy=False, default='/')
    # the opportunity comes from the order (standard sale_crm: sale.order.opportunity_id); before the order it is entered
    lead_id = fields.Many2one('crm.lead', string='Opportunity', index=True, tracking=True, compute='_compute_lead_id',
                              store=True, readonly=False, precompute=True)
    order_id = fields.Many2one('sale.order', string='Order', index=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, index=True,
                                 compute='_compute_company_id', store=True, readonly=False, precompute=True)
    customer = fields.Char(string='Customer', compute='_compute_customer')
    # AC-006: the measurer has no right to read the order (prices): the address and the phone of the customer are read
    # with sudo, only these two values
    td_address = fields.Char(string='Address', compute='_compute_customer')
    td_phone = fields.Char(string='Phone', compute='_compute_customer')
    td_can_link = fields.Boolean(string='Can Link the Order', compute='_compute_td_can_link',
                                 help="Technical: the order and the opportunity are chosen by sales users only.")
    measurer_id = fields.Many2one('res.users', string='Measurer', default=lambda self: self.env.user, tracking=True)
    room = fields.Char(string='Room', help='Kitchen, hall, bedroom: where the furniture stands.')
    floor_slope_mm = fields.Integer(string='Floor Slope, mm', help='Difference of the floor level along the wall.')
    wall_angle_deg = fields.Float(string='Wall Angle, °', digits=(4, 1), default=90.0)
    utilities = fields.Text(string='Utilities', help='Water, drain, gas, sockets: where they are and how high.')
    niche_ids = fields.One2many('td.mebli.measure.niche', 'measure_id', string='Niches and Sizes')
    appliance_ids = fields.One2many('td.mebli.measure.appliance', 'measure_id', string='Appliances of the Customer')
    photo_ids = fields.Many2many('ir.attachment', string='Photos')
    state = fields.Selection([('draft', 'Measured'), ('checked', 'Checked against the Design')],
                             string='Status', default='draft', tracking=True)
    issue_count = fields.Integer(string='Does not Fit', compute='_compute_issue_count')
    issue_text = fields.Text(string='What does not Fit', compute='_compute_issue_count')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('td.mebli.measure') or '/'
        sheets = super().create(vals_list)
        # the opportunity is precomputed from the order: the counter of the opportunity is refreshed explicitly
        sheets.lead_id.invalidate_recordset(['td_measure_ids', 'td_measure_count'])
        return sheets

    @api.depends('order_id.opportunity_id')
    def _compute_lead_id(self):
        for sheet in self:
            if sheet.order_id.opportunity_id and sheet.lead_id != sheet.order_id.opportunity_id:
                sheet.lead_id = sheet.order_id.opportunity_id

    @api.depends('order_id.company_id', 'lead_id.company_id')
    def _compute_company_id(self):
        for sheet in self:
            sheet.company_id = sheet.order_id.company_id or sheet.lead_id.company_id or sheet.company_id or self.env.company

    @api.depends('lead_id.partner_id', 'order_id.partner_id', 'lead_id.contact_name')
    @api.depends_context('uid')
    def _compute_customer(self):
        for sheet in self:
            # sudo: read only — the customer, the address and the phone; a measurer has no access to orders (AC-006)
            data = sheet.sudo()
            order_partner = data.order_id.partner_shipping_id or data.order_id.partner_id
            partner = order_partner or data.lead_id.partner_id
            sheet.customer = partner.display_name or data.lead_id.contact_name or ''
            address = partner._display_address(without_company=True) if partner else ''
            if not address and data.lead_id:
                address = ', '.join(filter(None, [data.lead_id.street, data.lead_id.city]))
            sheet.td_address = ' '.join((address or '').split()) or False
            sheet.td_phone = partner.phone or data.lead_id.phone or False

    @api.depends_context('uid')
    def _compute_td_can_link(self):
        can = self.env.user.has_group('sales_team.group_sale_salesman')
        for sheet in self:
            sheet.td_can_link = can

    @api.depends('appliance_ids.fits', 'appliance_ids.issue')
    def _compute_issue_count(self):
        for sheet in self:
            bad = sheet.appliance_ids.filtered(lambda a: not a.fits)
            sheet.issue_count = len(bad)
            sheet.issue_text = '\n'.join(f'{a.name}: {a.issue}' for a in bad)

    def action_check(self):
        """Check against the design: every appliance against its niche; the result goes to the chatter."""
        for sheet in self:
            sheet.state = 'checked'
            if sheet.issue_count:
                sheet.message_post(body=sheet.issue_text)
            else:
                sheet.message_post(body=self.env._("All appliances fit their niches."))
        return True


class TdMebliMeasureNiche(models.Model):
    _name = 'td.mebli.measure.niche'
    _description = 'Niche of a Measurement Sheet'
    _order = 'measure_id, sequence, id'

    measure_id = fields.Many2one('td.mebli.measure', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Niche', required=True)
    width_mm = fields.Integer(string='Width, mm')
    height_mm = fields.Integer(string='Height, mm')
    depth_mm = fields.Integer(string='Depth, mm')
    # position 28: what the measurer saw in the niche and what is planned for it — the rules check the design against them
    protrusion_mm = fields.Integer(string='Protrusion, mm',
                                   help='A pipe, a duct or a ledge that takes depth off the niche along its wall.')
    order_line_id = fields.Many2one('sale.order.line', string='Product in the Niche', ondelete='set null',
                                    domain="[('order_id', '=', parent.order_id), ('td_is_parametric', '=', True)]")

    _positive = models.Constraint('CHECK(width_mm >= 0 AND height_mm >= 0 AND depth_mm >= 0 AND protrusion_mm >= 0)',
                                  'Sizes of a niche cannot be negative.')

    def _td_usable(self):
        """Width, height and depth that the furniture can take: the depth minus the protrusion."""
        self.ensure_one()
        depth = max(self.depth_mm - self.protrusion_mm, 0) if self.depth_mm else 0
        return {'width_mm': self.width_mm, 'height_mm': self.height_mm, 'depth_mm': depth}


class TdMebliMeasureAppliance(models.Model):
    _name = 'td.mebli.measure.appliance'
    _description = 'Appliance of the Customer'
    _order = 'measure_id, sequence, id'

    measure_id = fields.Many2one('td.mebli.measure', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Appliance', required=True)
    niche_id = fields.Many2one('td.mebli.measure.niche', string='Niche',
                               domain="[('measure_id', '=', measure_id)]")
    width_mm = fields.Integer(string='Width, mm')
    height_mm = fields.Integer(string='Height, mm')
    depth_mm = fields.Integer(string='Depth, mm')
    fits = fields.Boolean(string='Fits', compute='_compute_fits')
    td_check = fields.Selection([('fits', 'Fits'), ('no_fit', 'Does not fit'), ('unchecked', 'Not checked')],
                                string='Check Result', compute='_compute_fits')
    issue = fields.Char(string='Check', compute='_compute_fits')

    @api.depends('width_mm', 'height_mm', 'depth_mm', 'niche_id.width_mm', 'niche_id.height_mm', 'niche_id.depth_mm',
                 'niche_id.protrusion_mm')
    @api.depends_context('lang')
    def _compute_fits(self):
        _ = self.env._
        labels = {'width_mm': _("wider"), 'height_mm': _("higher"), 'depth_mm': _("deeper")}
        sizes = ('width_mm', 'height_mm', 'depth_mm')
        for item in self:
            if not item.niche_id:
                item.fits, item.td_check, item.issue = True, 'unchecked', _("no niche")
                continue
            niche = item.niche_id
            # AC-010: an empty size of the appliance or of the niche is not a «does not fit»: not checked, not counted
            if not all(item[f] for f in sizes) or not all(niche[f] for f in sizes):
                item.fits, item.td_check, item.issue = True, 'unchecked', _("Not checked (no sizes)")
                continue
            usable = niche._td_usable()
            over = [(labels[f], item[f] - usable[f]) for f in sizes if item[f] > usable[f]]
            item.fits = not over
            item.td_check = 'no_fit' if over else 'fits'
            # AC-008: «Does not fit: deeper by 30 mm»
            item.issue = _("Does not fit: %s", ', '.join(_("%(what)s by %(mm)s mm", what=what, mm=mm)
                                                          for what, mm in over)) if over else _("fits")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    td_measure_ids = fields.One2many('td.mebli.measure', 'order_id', string='Measurement Sheets')
    td_measure_count = fields.Integer(string='Measurements', compute='_compute_td_measure_count')
    td_measure_issue_count = fields.Integer(string='Does not Fit', compute='_compute_td_measure_count',
                                            help="Appliances of the measurement sheets of the order that do not fit their "
                                                 "niche (AC-008).")
    td_measure_problems = fields.Text(string='Design against the Measurement', compute='_compute_td_measure_problems',
                                      help="Rules, no AI: every appliance against its niche; the product placed in a niche "
                                           "(width, height, depth minus the protrusion); the longest part of its "
                                           "specification against the niche. Shown before the parts go to cutting.")

    def _td_measure_problem_list(self):
        """Position 28: the design of the order against its measurement sheets — fixed rules, no guessing."""
        self.ensure_one()
        _ = self.env._
        problems = []
        # sudo: read only — the workshop sees the result of the check, not necessarily the sheets of a salesperson
        for sheet in self.sudo().td_measure_ids:
            for appliance in sheet.appliance_ids.filtered(lambda a: not a.fits):
                problems.append(_("%(sheet)s: %(item)s — %(issue)s", sheet=sheet.name, item=appliance.name,
                                  issue=appliance.issue))
            for niche in sheet.niche_ids.filtered('order_line_id'):
                line = niche.order_line_id
                usable = niche._td_usable()
                labels = {'width_mm': (_("width"), line.td_width), 'height_mm': (_("height"), line.td_height),
                          'depth_mm': (_("depth"), line.td_depth)}
                for key, (what, size) in labels.items():
                    if usable[key] and size and size > usable[key]:
                        problems.append(_("%(sheet)s: %(product)s — %(what)s %(size)s mm, the niche «%(niche)s» takes "
                                          "%(usable)s mm", sheet=sheet.name, product=line.product_id.name, what=what,
                                          size=size, niche=niche.name, usable=usable[key]))
                longest = max(usable['width_mm'], usable['height_mm'])
                for part in line.sudo().td_bom_id.td_part_ids:
                    if longest and max(part.length_mm, part.width_mm) > longest:
                        problems.append(_("%(sheet)s: part «%(part)s» %(size)s mm is longer than the niche «%(niche)s» "
                                          "(%(longest)s mm)", sheet=sheet.name, part=part.name,
                                          size=int(max(part.length_mm, part.width_mm)), niche=niche.name, longest=longest))
        return problems

    @api.depends('td_measure_ids.appliance_ids.fits', 'td_measure_ids.niche_ids.order_line_id',
                 'td_measure_ids.niche_ids.protrusion_mm', 'order_line.td_width', 'order_line.td_height',
                 'order_line.td_depth')
    def _compute_td_measure_problems(self):
        for order in self:
            order.td_measure_problems = '\n'.join(order._td_measure_problem_list()) if order.id else False

    @api.depends('td_measure_ids.appliance_ids.fits')
    def _compute_td_measure_count(self):
        for order in self:
            # sudo: read only — a salesperson sees the count of every measurement of his order
            sheets = order.sudo().td_measure_ids
            order.td_measure_count = len(set(sheets.ids))
            order.td_measure_issue_count = sum(sheets.browse(set(sheets.ids)).mapped('issue_count'))

    def action_td_view_measures(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('td_mebli_measure.td_mebli_measure_action')
        action['domain'] = [('order_id', '=', self.id)]
        action['context'] = {'default_order_id': self.id}
        if len(self.td_measure_ids) == 1:
            action.update(view_mode='form', views=[(False, 'form')], res_id=self.td_measure_ids.id)
        return action


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    td_measure_problems = fields.Text(string='Design against the Measurement', compute='_compute_td_measure_problems')

    def _td_sale_orders(self):
        # sudo: read only — the order of a manufacturing order (standard links: references and the sale line)
        return self.sudo().reference_ids.sale_ids | self.sudo().sale_line_id.order_id

    def _compute_td_measure_problems(self):
        for production in self:
            problems = []
            for order in production._td_sale_orders():
                problems += order._td_measure_problem_list()
            production.td_measure_problems = '\n'.join(dict.fromkeys(problems)) or False


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    td_measure_ids = fields.One2many('td.mebli.measure', 'lead_id', string='Measurement Sheets')
    td_measure_count = fields.Integer(string='Measurements', compute='_compute_td_measure_count')

    @api.depends('td_measure_ids')
    def _compute_td_measure_count(self):
        # sudo: the count of every measurement of the opportunity (search: the cache of the inverse may be stale)
        Measure = self.env['td.mebli.measure'].sudo()
        for lead in self:
            lead.td_measure_count = Measure.search_count([('lead_id', '=', lead._origin.id)]) if lead._origin.id else 0

    def action_td_view_measures(self):
        """AC-005: the smart button «Measurements» of the opportunity."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('td_mebli_measure.td_mebli_measure_action')
        action['domain'] = [('lead_id', '=', self.id)]
        action['context'] = {'default_lead_id': self.id}
        if len(self.td_measure_ids) == 1:
            action.update(view_mode='form', views=[(False, 'form')], res_id=self.td_measure_ids.id)
        return action

    def action_td_book_measure(self):
        """Position 9: book a measurement visit in a free window of the measurer (standard calendar meeting)."""
        self.ensure_one()
        wizard = self.env['td.mebli.measure.booking'].create({'lead_id': self.id})
        wizard._td_fill_slots()
        return {'type': 'ir.actions.act_window', 'res_model': wizard._name, 'res_id': wizard.id, 'view_mode': 'form',
                'target': 'new', 'name': self.env._("Book a Measurement")}
