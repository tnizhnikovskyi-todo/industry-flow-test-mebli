from odoo import fields, models
from odoo.exceptions import UserError


class TdMebliKitScan(models.TransientModel):
    """AC-062 (box B, label scanning): the packer scans the QR of the part labels with a camera or a scanner; the code
    is typed into the field (a scanner types it and presses Enter) and the line of the packing list is packed."""
    _name = 'td.mebli.kit.scan'
    _description = 'Scanning of the Part Labels of a Packing List'

    order_id = fields.Many2one('sale.order', string='Order', required=True)
    code = fields.Char(string='Label Code')
    last_scanned = fields.Char(string='Last Packed', readonly=True)
    missing = fields.Integer(related='order_id.td_kit_missing', string='Not Packed')

    def action_scan(self):
        self.ensure_one()
        code = (self.code or '').strip()
        line = self.order_id.td_kit_line_ids.filtered(lambda kit_line: kit_line.label == code)[:1]
        if not code or not line:
            raise UserError(self.env._("The label does not belong to this order"))
        if not line.packed:
            line.write({'packed': True})  # «Packed» with the user (td.mebli.kit.line.write)
        self.write({'code': False, 'last_scanned': f"{line.label} — {line.item}"})
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id, 'view_mode': 'form',
                'target': 'new', 'name': self.env._("Scan Labels")}
