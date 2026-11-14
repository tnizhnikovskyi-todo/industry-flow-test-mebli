from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    td_support_email = fields.Char('Support address', config_parameter='td_support.email')
    td_support_webhook_enabled = fields.Boolean('Send to the webhook', config_parameter='td_support.webhook_enabled')
    td_support_webhook_url = fields.Char('Webhook URL', config_parameter='td_support.webhook_url')
    td_support_webhook_secret = fields.Char('Webhook secret', config_parameter='td_support.webhook_secret')
