import logging

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
NBU_URL = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json'


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    td_source = fields.Selection([('nbu', 'NBU'), ('nbu_imitation', 'NBU (imitation, no network)')],
                                 string='Source', readonly=True)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def _td_fetch_nbu(self):
        """Official rates of the NBU for today: {ISO code: UAH for one unit}."""
        response = requests.get(NBU_URL, timeout=10)
        response.raise_for_status()
        return {row['cc']: float(row['rate']) for row in response.json() if row.get('cc') and row.get('rate')}

    @api.model
    def td_update_nbu_rates(self, rates=None, imitation=False):
        """Writes the rates into the standard res.currency.rate of the companies in UAH. `rates` — {code: UAH per unit};
        without it the rates are loaded from the NBU if the online loading is on."""
        if rates is None:
            if not self.env['ir.config_parameter'].sudo().get_param('td_mebli_ua.nbu_online'):
                raise UserError(self.env._("Online loading of the NBU rates is off (system parameter "
                                           "td_mebli_ua.nbu_online)."))
            rates = self._td_fetch_nbu()
        uah = self.env.ref('base.UAH')
        today = fields.Date.context_today(self)
        Rate = self.env['res.currency.rate']
        written = 0
        for company in self.env['res.company'].search([('currency_id', '=', uah.id)]):
            for currency in self.with_context(active_test=False).search([('name', 'in', list(rates))]):
                if currency == uah or not rates.get(currency.name):
                    continue
                vals = {'rate': 1.0 / rates[currency.name], 'td_source': 'nbu_imitation' if imitation else 'nbu'}
                rate = Rate.search([('currency_id', '=', currency.id), ('company_id', '=', company.id), ('name', '=', today)])
                if rate:
                    rate.write(vals)
                else:
                    Rate.create({**vals, 'currency_id': currency.id, 'company_id': company.id, 'name': today})
                written += 1
        _logger.info('td_mebli_ua: %s NBU rates written', written)
        return written

    @api.model
    def _td_cron_nbu(self):
        try:
            self.td_update_nbu_rates()
        except (UserError, requests.RequestException) as error:
            _logger.warning('td_mebli_ua: NBU rates not loaded: %s', error)
