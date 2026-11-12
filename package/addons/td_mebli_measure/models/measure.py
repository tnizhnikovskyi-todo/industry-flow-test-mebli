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
        return super().create(vals_list)

    @api.depends('order_id.opportunity_id')
    def _compute_lead_id(self):
        for sheet in self:
            if sheet.order_id.opportunity_id:
                sheet.lead_id = sheet.order_id.opportunity_id

    @api.depends('order_id.company_id', 'lead_id.company_id')
    def _compute_company_id(self):
        for sheet in self:
            sheet.company_id = sheet.order_id.company_id or sheet.lead_id.company_id or sheet.company_id or self.env.company

    @api.depends('lead_id.partner_id', 'order_id.partner_id', 'lead_id.contact_name')
    def _compute_customer(self):
        for sheet in self:
            partner = sheet.order_id.partner_id or sheet.lead_id.partner_id
            sheet.customer = partner.display_name or sheet.lead_id.contact_name or ''

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
                sheet.message_post(body=self.env._("Does not fit: %s", sheet.issue_text))
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

    _positive = models.Constraint('CHECK(width_mm >= 0 AND height_mm >= 0 AND depth_mm >= 0)',
                                  'Sizes of a niche cannot be negative.')


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
    issue = fields.Char(string='Check', compute='_compute_fits')

    @api.depends('width_mm', 'height_mm', 'depth_mm', 'niche_id.width_mm', 'niche_id.height_mm', 'niche_id.depth_mm')
    def _compute_fits(self):
        _ = self.env._
        labels = {'width_mm': _("wider"), 'height_mm': _("higher"), 'depth_mm': _("deeper")}
        for item in self:
            if not item.niche_id:
                item.fits, item.issue = True, _("no niche")
                continue
            over = [(labels[f], item[f] - item.niche_id[f]) for f in ('width_mm', 'height_mm', 'depth_mm')
                    if item.niche_id[f] and item[f] > item.niche_id[f]]
            item.fits = not over
            item.issue = ', '.join(_("%(what)s by %(mm)s mm", what=what, mm=mm) for what, mm in over) if over else _("fits")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    td_measure_ids = fields.One2many('td.mebli.measure', 'order_id', string='Measurement Sheets')
    td_measure_count = fields.Integer(string='Measurements', compute='_compute_td_measure_count')

    @api.depends('td_measure_ids')
    def _compute_td_measure_count(self):
        for order in self:
            order.td_measure_count = len(order.td_measure_ids)

    def action_td_view_measures(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('td_mebli_measure.td_mebli_measure_action')
        action['domain'] = [('order_id', '=', self.id)]
        action['context'] = {'default_order_id': self.id}
        if len(self.td_measure_ids) == 1:
            action.update(view_mode='form', views=[(False, 'form')], res_id=self.td_measure_ids.id)
        return action


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    td_measure_ids = fields.One2many('td.mebli.measure', 'lead_id', string='Measurement Sheets')
