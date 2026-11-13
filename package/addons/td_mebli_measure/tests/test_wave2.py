from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestWave2Measure(TdMebliSaleCommon):
    """F-62 the design against the measurement (rules), F-54 free windows of the measurer and the booking."""

    def test_rules_find_what_does_not_fit(self):
        order = self._make_order(width=1000, height=700, depth=500)
        order.order_line.action_td_generate_bom()
        line = order.order_line[:1]
        sheet = self.env['td.mebli.measure'].create({'order_id': order.id})
        niche = self.env['td.mebli.measure.niche'].create({
            'measure_id': sheet.id, 'name': 'Hall', 'width_mm': 1200, 'height_mm': 2000, 'depth_mm': 520,
            'order_line_id': line.id})
        self.assertFalse(order.td_measure_problems, "500 mm deep into 520 mm fits")
        niche.protrusion_mm = 40
        order.invalidate_recordset(['td_measure_problems'])
        self.assertIn('500', order.td_measure_problems, "a duct of 40 mm leaves 480 mm")
        niche.write({'protrusion_mm': 0, 'width_mm': 600, 'height_mm': 600})
        order.invalidate_recordset(['td_measure_problems'])
        problems = order._td_measure_problem_list()
        self.assertTrue(any('1000' in p for p in problems), "the product is wider than the niche")
        self.assertTrue(any('part' in p or 'деталь' in p.lower() for p in problems), "a part is longer than the niche")
        production = self.env['mrp.production'].create({'product_id': line.product_id.id, 'bom_id': line.td_bom_id.id,
                                                        'product_qty': 1, 'sale_line_id': line.id})
        self.assertTrue(production.td_measure_problems)

    def test_free_windows_and_booking(self):
        env = self.env
        env.user.tz = 'Europe/Kyiv'
        measurer = env.user
        partner = env['res.partner'].create({'name': 'Buyer', 'email': 'buyer@example.com'})
        lead = env['crm.lead'].create({'name': 'Kitchen', 'type': 'opportunity', 'partner_id': partner.id})
        day = fields.Date.today() + timedelta(days=7)
        while day.weekday() >= 5:
            day += timedelta(days=1)
        wizard = env['td.mebli.measure.booking'].create({'lead_id': lead.id, 'measurer_id': measurer.id,
                                                         'date_from': day, 'days': 1})
        wizard._td_fill_slots()
        free = len(wizard.slot_ids)
        self.assertGreaterEqual(free, 3, "working hours of the company calendar in 2-hour windows")
        slot = wizard.slot_ids[0]
        action = slot.action_book()
        event = env['calendar.event'].browse(action['res_id'])
        self.assertEqual(event.opportunity_id, lead)
        self.assertIn(partner, event.partner_ids)
        self.assertEqual(event.alarm_ids, env.ref('td_mebli_measure.alarm_mail_measure_1day'))
        self.assertEqual(event.alarm_ids.alarm_type, 'email', "the reminder is the standard e-mail alarm")
        wizard._td_fill_slots()
        self.assertEqual(len(wizard.slot_ids), free - 1, "the booked window is busy now")

    def test_booking_rechecks_the_window_and_measurer_by_group(self):
        env = self.env
        env.user.tz = 'Europe/Kyiv'
        measurer = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Measurer', 'login': 'td_measurer_group', 'tz': 'Europe/Kyiv',
            'group_ids': [(6, 0, [env.ref('td_mebli_measure.group_td_mebli_measurer').id])]})
        lead = env['crm.lead'].create({'name': 'Hall', 'type': 'opportunity',
                                       'partner_id': env['res.partner'].create({'name': 'Buyer 2'}).id})
        day = fields.Date.today() + timedelta(days=7)
        while day.weekday() >= 5:
            day += timedelta(days=1)
        wizard = env['td.mebli.measure.booking'].create({'lead_id': lead.id, 'date_from': day, 'days': 1})
        self.assertEqual(wizard.measurer_id, measurer, "the default measurer comes from the group, not from the login")
        wizard._td_fill_slots()
        slot = wizard.slot_ids[0]
        # another salesperson books the same window meanwhile
        env['calendar.event'].create({'name': 'Other visit', 'start': slot.start, 'stop': slot.stop,
                                      'partner_ids': [(6, 0, measurer.partner_id.ids)]})
        with self.assertRaises(UserError):
            slot.action_book()
