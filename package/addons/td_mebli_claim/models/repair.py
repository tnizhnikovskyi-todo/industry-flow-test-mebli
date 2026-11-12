from odoo import api, fields, models
from odoo.exceptions import UserError


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    td_claim_order_id = fields.Many2one(
        'sale.order', string='Claimed Order', index='btree_not_null', check_company=True,
        help="The furniture order the customer complains about (the standard «Sale Order» of a repair is the order the "
             "repair was sold from, a different thing).")
    td_part_id = fields.Many2one('td.mebli.part', string='Part', domain="[('bom_id.td_sale_order_id', '=', td_claim_order_id)]")
    td_reason = fields.Selection(
        [('production', 'Production'), ('installation', 'Installation'), ('supplier', 'Supplier'),
         ('transport', 'Transport'), ('customer', 'Customer')], string='Reason')
    td_payer = fields.Selection([('company', 'Company'), ('supplier', 'Supplier'), ('customer', 'Customer')],
                                string='Who Pays')
    td_photo = fields.Image(string='Photo', max_width=1024, max_height=1024)
    td_remake_production_id = fields.Many2one('mrp.production', string='Remake', readonly=True, copy=False)
    td_days_open = fields.Integer(string='Days Open', compute='_compute_td_days_open')
    td_overdue = fields.Boolean(string='Overdue', compute='_compute_td_days_open')

    @api.depends('create_date', 'state', 'schedule_date', 'write_date')
    def _compute_td_days_open(self):
        now = fields.Datetime.now()
        for repair in self:
            end = repair.write_date if repair.state in ('done', 'cancel') else now
            start = repair.create_date or now
            repair.td_days_open = max(0, (end - start).days)
            repair.td_overdue = repair.state not in ('done', 'cancel') and bool(repair.schedule_date) and repair.schedule_date < now

    def action_td_remake(self):
        """Remake in production: a standard manufacturing order of the claimed product."""
        self.ensure_one()
        bom = self.env['mrp.bom']._bom_find(self.product_id)[self.product_id] if self.product_id else False
        if not bom:
            raise UserError(self.env._("The product of the claim has no bill of materials: it is bought, not made. "
                                       "Order it again in Purchase."))
        production = self.env['mrp.production'].create({
            'product_id': self.product_id.id, 'product_qty': 1.0, 'bom_id': bom.id,
            'origin': f"{self.name} / {self.td_claim_order_id.name or ''}".strip(' /')})
        production.action_confirm()
        self.td_remake_production_id = production
        self.message_post(body=self.env._("Remake started: %s", production.name))
        return True


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    td_claim_ids = fields.One2many('repair.order', 'td_claim_order_id', string='Claims of the Order',
                                   groups='stock.group_stock_user')
    td_claim_count = fields.Integer(string='Claims', compute='_compute_td_claim_count', groups='stock.group_stock_user')

    @api.depends('td_claim_ids')
    def _compute_td_claim_count(self):
        for order in self:
            order.td_claim_count = len(order.td_claim_ids)

    def action_td_view_claims(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('td_mebli_claim.td_mebli_claim_action')
        action['domain'] = [('td_claim_order_id', '=', self.id)]
        action['context'] = {'default_td_claim_order_id': self.id, 'default_partner_id': self.partner_id.id}
        return action
