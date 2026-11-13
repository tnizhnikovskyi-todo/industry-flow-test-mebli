from odoo import api, fields, models
from odoo.exceptions import ValidationError

# Closed ranges of the integer answers of the questionnaire (SPEC §11.1, column «Варіанти»)
TD_RANGES = {
    'td_pay_reminder_days': (1, 7),       # VP-07
    'td_stuck_days': (1, 30),             # VP-10
    'td_price_threshold_pct': (1, 50),    # VP-11
    'td_min_offcut_mm': (100, 1000),      # VP-12
    'td_claim_overdue_days': (1, 60),     # VP-13
    'td_crew_pct': (0, 100),              # data of the client (B-04), a percent
}


class ResCompany(models.Model):
    """The answers of the questionnaire of the package (answers.yaml, SPEC §11) live on the legal entity (AI-A08-04):
    one field per VP. The modules td_mebli_* read these fields instead of system parameters or constants."""
    _inherit = 'res.company'

    td_contract_mode = fields.Selection(
        [('contract', 'Contract work'), ('sale', 'Sale contract')], string='Contract Mode',
        help="Text of the printed contract (contract_mode of the questionnaire). Empty — not chosen yet: the contract "
             "is not printed until the customer and the lawyer choose the mode (AC-034).")
    td_payment_control = fields.Selection(
        [('warn', 'Warn'), ('block', 'Block')], string='Payment Control Before the Visit', default='warn',
        help="VP-06: what happens when the crew is sent to an order whose payments before the installation are not paid.")
    td_pay_reminder_days = fields.Integer(
        string='Payment Reminder, Days Before the Visit', default=2,
        help="VP-07: the customer is reminded of the payment before the installation this many days before the visit (1–7).")
    td_margin_to_salesman = fields.Boolean(
        string='Salesman Sees the Margin', default=False,
        help="VP-08: the users of «Sales: own documents» of the company get the group «Sees the margin».")
    td_cutting_mode = fields.Selection(
        [('both', 'Own cutting and distributor'), ('distributor', 'Distributor only')], string='Board Cutting',
        default='both', help="VP-09: «Distributor only» — the menus of own cutting are hidden.")
    td_stuck_days = fields.Integer(
        string='Stuck Orders, Days', default=5,
        help="VP-10: an order without a move for longer than this many days is «stuck» (1–30).")
    td_price_threshold_pct = fields.Float(
        string='Price Above History, %', default=5.0, digits=(5, 2),
        help="VP-11: a purchase price above the average of the earlier purchases by more than this percent is marked (1–50).")
    td_min_offcut_mm = fields.Integer(
        string='Minimal Offcut, mm', default=300,
        help="VP-12: a rest of a board not smaller than this on both sides is kept as an offcut (100–1000).")
    td_claim_overdue_days = fields.Integer(
        string='Claim Overdue, Days', default=14,
        help="VP-13: a claim open for longer than this many days is overdue (1–60).")
    td_crew_split = fields.Selection(
        [('equal', 'Equally'), ('time', 'By time')], string='Crew Percent Split', default='equal',
        help="VP-14: how the percent of the crew is split between the installers of the act.")
    td_crew_base = fields.Selection(
        [('final', 'By the final act'), ('stage', 'By stages')], string='Crew Percent Base', default='final',
        help="VP-15: the percent of the crew is accrued from the final act or from the act of every stage.")
    td_crew_pct = fields.Float(
        string='Crew Percent', default=0.0, digits=(5, 2),
        help="Default percent of the order amount for the crew of a new act (data of the client, not a VP).")
    td_install_in_price = fields.Boolean(
        string='Installation in the Order Price', default=False,
        help="VP-16: the installation is a service line with a zero price included in the price of the furniture.")
    td_act_checklist = fields.Text(
        string='Act Checklist', translate=True,
        help="Points of the installation act, one per line (data of the client, not a VP).")
    td_legal_checked = fields.Boolean(
        string='Texts Checked by a Lawyer', default=False,
        help="After the conclusion of the lawyer (No 17): the mark «Template to be checked by a lawyer» disappears "
             "from the contract and the acts.")
    td_box_profile = fields.Selection(
        [('light', 'Light'), ('A', 'Box A'), ('B', 'Box B (full)'), ('C', 'Box C (full + Enterprise)')],
        string='Box Profile', default='A',
        help="VP-01, information only: the functions are switched on by the feature groups of box B.")

    @api.constrains(*TD_RANGES)
    def _check_td_ranges(self):
        for company in self:
            for name, (low, high) in TD_RANGES.items():
                value = company[name]
                if not low <= value <= high:
                    raise ValidationError(self.env._(
                        "%(field)s: the value %(value)s is outside the allowed range %(low)s–%(high)s.",
                        field=self._fields[name].get_description(self.env)['string'], value=value, low=low, high=high))

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        companies.filtered('td_margin_to_salesman')._td_sync_margin_group()
        return companies

    def write(self, vals):
        res = super().write(vals)
        if 'td_margin_to_salesman' in vals:
            self._td_sync_margin_group()
        return res

    def _td_sync_margin_group(self):
        """AC-018: «Sees the margin» follows the parameter of the company for the salesmen whose main company it is."""
        salesman = self.env.ref('sales_team.group_sale_salesman', raise_if_not_found=False)
        margin = self.env.ref('td_mebli_base.group_margin_view', raise_if_not_found=False)
        if not salesman or not margin:
            return
        for company in self:
            users = salesman.sudo().all_user_ids.filtered(lambda u: not u.share and u.company_id == company)
            if not users:
                continue
            command = 4 if company.td_margin_to_salesman else 3
            margin.sudo().write({'user_ids': [(command, user.id) for user in users]})
