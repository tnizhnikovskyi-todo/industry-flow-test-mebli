from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # AC-050: address of the model provider for the AI hint of the column mapping; empty — no call (DATA_POLICY)
    td_ai_mapping_url = fields.Char(string='AI Mapping Provider', config_parameter='td_mebli_mrp.ai_mapping_url')
