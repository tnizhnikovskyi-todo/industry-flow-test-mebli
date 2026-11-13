from odoo import fields, models


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    # AC-126: the work order of Shop Floor shows the parts of the order (td_mebli_mrp); the pause reasons are the standard
    # loss reasons (mrp.workcenter.productivity.loss) filled by the template of A-13, the same in CE and EE.
    td_part_ids = fields.One2many(related='production_id.bom_id.td_part_ids', string='Parts')
