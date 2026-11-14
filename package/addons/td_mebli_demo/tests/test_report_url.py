import os
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.td_mebli_demo.wave2 import _set_report_url


@tagged('post_install', '-at_install')
class TestDemoReportUrl(TransactionCase):
    """D-17 (AC-N.06): the demo layer does not fix the address of the report server (no 127.0.0.1:8072): report.url is
    the address of the stand given by DEMO_REPORT_URL, without it report.url is empty and Odoo prints with web.base.url."""

    def _param(self):
        return self.env['ir.config_parameter'].sudo().get_param('report.url')

    def test_d17_address_of_the_stand(self):
        with patch.dict(os.environ, {'DEMO_REPORT_URL': 'http://127.0.0.1:8079/'}):
            _set_report_url(self.env)
        self.assertEqual(self._param(), 'http://127.0.0.1:8079')
        report = self.env['ir.actions.report'].search([('report_name', '=like', 'td_mebli_%')], limit=1) or self.env['ir.actions.report'].search([], limit=1)
        self.assertEqual(report._get_report_url(), 'http://127.0.0.1:8079')

    def test_d17_no_variable_web_base_url(self):
        self.env['ir.config_parameter'].sudo().set_param('report.url', 'http://127.0.0.1:8072')
        env = {k: v for k, v in os.environ.items() if k != 'DEMO_REPORT_URL'}
        with patch.dict(os.environ, env, clear=True):
            _set_report_url(self.env)
        self.assertFalse(self._param())
        report = self.env['ir.actions.report'].search([], limit=1)
        self.assertEqual(report._get_report_url(), report.get_base_url())
        self.assertNotIn('8072', report._get_report_url())

    def test_d17_not_an_address(self):
        with self.assertRaises(ValueError):
            _set_report_url(self.env, 'localhost:8079')
