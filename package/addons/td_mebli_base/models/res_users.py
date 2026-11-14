from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    # review A-11: «Sees the margin» was given by the parameter of the company (AC-018), not by an administrator — only
    # such a grant is taken back when the parameter is switched off
    td_margin_auto = fields.Boolean(string='Margin Visibility by the Company Parameter', readonly=True, copy=False,
                                    groups='base.group_system')

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
        # sudo: the group «Sees the margin» follows the parameter of the company also when a salesman edits his preferences
        for user in self.sudo().filtered(lambda u: not u.share):
            wanted = salesman in user.all_group_ids and user.company_id.td_margin_to_salesman
            has = margin in user.group_ids
            if wanted and not has:
                user.with_context(td_margin_sync=True).write({'group_ids': [(4, margin.id)], 'td_margin_auto': True})
            elif not wanted and has and user.td_margin_auto:
                user.with_context(td_margin_sync=True).write({'group_ids': [(3, margin.id)], 'td_margin_auto': False})
            elif not has and user.td_margin_auto:
                user.with_context(td_margin_sync=True).write({'td_margin_auto': False})
            # not wanted, has, no marker: the administrator gave the group by hand — it stays
