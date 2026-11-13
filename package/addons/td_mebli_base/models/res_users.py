from odoo import api, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._td_sync_margin_group()
        return users

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('td_margin_sync') and {'group_ids', 'company_id'} & set(vals):
            self._td_sync_margin_group()
        return res

    def _td_sync_margin_group(self):
        """AC-018: a salesman added later (or moved to another main company) gets «Sees the margin» by the parameter
        of his main company."""
        salesman = self.env.ref('sales_team.group_sale_salesman', raise_if_not_found=False)
        margin = self.env.ref('td_mebli_base.group_margin_view', raise_if_not_found=False)
        if not salesman or not margin:
            return
        for user in self.sudo().filtered(lambda u: not u.share):
            wanted = salesman in user.all_group_ids and user.company_id.td_margin_to_salesman
            has = margin in user.group_ids
            if wanted != has:
                user.with_context(td_margin_sync=True).write({'group_ids': [(4 if wanted else 3, margin.id)]})
