from odoo import fields, models
from odoo.exceptions import UserError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # AC-113: the ticket of the customer is linked to the order, the part and the claim (repair.order of td_mebli_claim)
    td_sale_order_id = fields.Many2one('sale.order', string='Furniture Order', index='btree_not_null')
    td_part_id = fields.Many2one('td.mebli.part', string='Part',
                                 domain="[('bom_id.td_sale_order_id', '=', td_sale_order_id)]")
    td_repair_id = fields.Many2one('repair.order', string='Claim', readonly=True, copy=False)

    def action_td_create_claim(self):
        """The claim (repair.order) of the ticket: the order and the part of the ticket."""
        self.ensure_one()
        if not self.td_sale_order_id:
            raise UserError(self.env._("Choose the order of the ticket first."))
        if not self.td_repair_id:
            self.td_repair_id = self.env['repair.order'].create({
                'partner_id': (self.partner_id or self.td_sale_order_id.partner_id).id,
                'td_claim_order_id': self.td_sale_order_id.id, 'td_part_id': self.td_part_id.id,
                'internal_notes': self.name})
        return {'type': 'ir.actions.act_window', 'res_model': 'repair.order', 'res_id': self.td_repair_id.id,
                'view_mode': 'form'}

    def action_td_remake(self):
        """«Remake» from the ticket: the remake of the claim (td_mebli_claim)."""
        self.ensure_one()
        if not self.td_repair_id:
            self.action_td_create_claim()
        return self.td_repair_id.action_td_remake()
