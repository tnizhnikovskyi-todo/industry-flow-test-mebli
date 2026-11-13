from odoo import fields, models

# VP-02 value -> feature group of box B (SPEC §11.1, tr/00-architecture.md §3)
TD_FEATURES = ('configurator', 'offcut', 'cutting_batch', 'kiosk', 'quality', 'label_scan', 'change_sign', 'nbu',
               'ai_mapping', 'analog', 'shop_board')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    td_contract_mode = fields.Selection(related='company_id.td_contract_mode', readonly=False)
    td_payment_control = fields.Selection(related='company_id.td_payment_control', readonly=False)
    td_pay_reminder_days = fields.Integer(related='company_id.td_pay_reminder_days', readonly=False)
    td_margin_to_salesman = fields.Boolean(related='company_id.td_margin_to_salesman', readonly=False)
    td_cutting_mode = fields.Selection(related='company_id.td_cutting_mode', readonly=False)
    td_stuck_days = fields.Integer(related='company_id.td_stuck_days', readonly=False)
    td_price_threshold_pct = fields.Float(related='company_id.td_price_threshold_pct', readonly=False)
    td_min_offcut_mm = fields.Integer(related='company_id.td_min_offcut_mm', readonly=False)
    td_claim_overdue_days = fields.Integer(related='company_id.td_claim_overdue_days', readonly=False)
    td_crew_split = fields.Selection(related='company_id.td_crew_split', readonly=False)
    td_crew_base = fields.Selection(related='company_id.td_crew_base', readonly=False)
    td_crew_pct = fields.Float(related='company_id.td_crew_pct', readonly=False)
    td_install_in_price = fields.Boolean(related='company_id.td_install_in_price', readonly=False)
    td_act_checklist = fields.Text(related='company_id.td_act_checklist', readonly=False)
    td_legal_checked = fields.Boolean(related='company_id.td_legal_checked', readonly=False)
    td_box_profile = fields.Selection(related='company_id.td_box_profile', readonly=False)

    # Functions of box B (VP-02): a checked box adds the feature group to all internal users (implied by base.group_user)
    group_td_feature_configurator = fields.Boolean(
        string='Product Configurator', implied_group='td_mebli_base.group_feature_configurator')
    group_td_feature_offcut = fields.Boolean(string='Offcuts', implied_group='td_mebli_base.group_feature_offcut')
    group_td_feature_cutting_batch = fields.Boolean(
        string='Cutting Batches', implied_group='td_mebli_base.group_feature_cutting_batch')
    group_td_feature_kiosk = fields.Boolean(string='Workshop Kiosk', implied_group='td_mebli_base.group_feature_kiosk')
    group_td_feature_quality = fields.Boolean(string='Quality Control', implied_group='td_mebli_base.group_feature_quality')
    group_td_feature_label_scan = fields.Boolean(
        string='Label Scanning', implied_group='td_mebli_base.group_feature_label_scan')
    group_td_feature_change_sign = fields.Boolean(
        string='Signature of Order Changes', implied_group='td_mebli_base.group_feature_change_sign')
    group_td_feature_nbu = fields.Boolean(string='NBU Exchange Rates', implied_group='td_mebli_base.group_feature_nbu')
    group_td_feature_ai_mapping = fields.Boolean(
        string='AI Column Mapping', implied_group='td_mebli_base.group_feature_ai_mapping')
    group_td_feature_analog = fields.Boolean(string='Analogs', implied_group='td_mebli_base.group_feature_analog')
    group_td_feature_shop_board = fields.Boolean(
        string='Workshop Board', implied_group='td_mebli_base.group_feature_shop_board')
