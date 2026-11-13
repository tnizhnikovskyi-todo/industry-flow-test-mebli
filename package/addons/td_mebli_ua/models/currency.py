import logging

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
NBU_URL = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json'
# Network, HTTP and format errors of the NBU service (AC-038): the rates are not changed, the finance users get an activity.
NBU_ERRORS = (requests.RequestException, ValueError, KeyError, TypeError)


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    td_source = fields.Selection([('nbu', 'NBU'), ('nbu_imitation', 'NBU (imitation, no network)')],
                                 string='Source', readonly=True)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def _td_nbu_online(self):
        return bool(self.env['ir.config_parameter'].sudo().get_param('td_mebli_ua.nbu_online'))

    @api.model
    def _td_fetch_nbu(self):
        """Official rates of the NBU for today: {ISO code: UAH for one unit}."""
        response = requests.get(NBU_URL, timeout=10)
        response.raise_for_status()
        rates = {row['cc']: float(row['rate']) for row in response.json() if row.get('cc') and row.get('rate')}
        if not rates:
            raise ValueError('the NBU answer has no rates')
        return rates

    @api.model
    def td_update_nbu_rates(self, rates=None, imitation=False):
        """Writes the rates into the standard res.currency.rate of the companies in UAH. `rates` — {code: UAH per unit};
        without it the rates are loaded from the NBU if the online loading is on."""
        if rates is None:
            if not self._td_nbu_online():
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
        """Daily job «NBU exchange rates» (AC-037, AC-038). The next attempt is the next run of the job."""
        if not self._td_nbu_online():
            _logger.info('td_mebli_ua: online loading of the NBU rates is off, nothing loaded')
            return False
        try:
            rates = self._td_fetch_nbu()
        except NBU_ERRORS as error:
            _logger.error('td_mebli_ua: NBU rates not loaded, the rates are not changed: %s', error)
            self._td_notify_nbu_failure(error)
            return False
        self.td_update_nbu_rates(rates)
        return True

    @api.model
    def _td_notify_nbu_failure(self, error):
        """Activity «NBU rate not updated» to the finance users of each company in UAH (one open activity per user)."""
        finance = self.env.ref('td_mebli_base.group_finance').sudo().all_user_ids.filtered(lambda u: u.active and not u.share)
        todo = self.env.ref('mail.mail_activity_data_todo')
        summary = self.env._("NBU rate not updated")
        Activity = self.env['mail.activity'].sudo()
        for company in self.env['res.company'].sudo().search([('currency_id', '=', self.env.ref('base.UAH').id)]):
            partner = company.partner_id
            for user in finance.filtered(lambda u: company in u.company_ids):
                if Activity.search_count([('res_model', '=', 'res.partner'), ('res_id', '=', partner.id),
                                          ('user_id', '=', user.id), ('summary', '=', summary)]):
                    continue
                partner.activity_schedule(
                    activity_type_id=todo.id, summary=summary, user_id=user.id,
                    note=self.env._("The NBU service did not answer or answered with an error: %(error)s. The rates "
                                    "are not changed; the next attempt is the next run of the job.", error=error))
