from datetime import datetime

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestA17Measure(TransactionCase):
    """A-17 №6 (AC-135): the smart button «Meetings» of the opportunity shows the calendars of everybody linked to it,
    never the customer's; №11 (AC-139): «Start the Measurement» on the meeting opens or creates the measurement sheet."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env

        def make(login, groups):
            return env['res.users'].with_context(no_reset_password=True).create({
                'name': login, 'login': login, 'group_ids': [(6, 0, [env.ref(g).id for g in groups])]})
        cls.salesman = make('td_a17_salon', ['sales_team.group_sale_salesman_all_leads'])
        cls.other_sales = make('td_a17_salon2', ['sales_team.group_sale_salesman_all_leads'])
        cls.measurer = make('td_a17_measure', ['td_mebli_measure.group_td_mebli_measurer'])
        cls.measurer2 = make('td_a17_measure2', ['td_mebli_measure.group_td_mebli_measurer'])
        cls.customer = env['res.partner'].create({'name': 'A-17 customer', 'street': 'Shevchenka 1', 'phone': '+380000'})
        cls.lead = env['crm.lead'].create({'name': 'Kitchen A-17', 'type': 'opportunity', 'partner_id': cls.customer.id,
                                           'user_id': cls.other_sales.id})

    def _filters(self, user):
        return self.env['calendar.filters'].search([('user_id', '=', user.id), ('partner_checked', '=', True)]).partner_id

    def test_06_no_measurement_yet_all_measurers(self):
        self.lead.with_user(self.salesman).action_schedule_meeting()
        shown = self._filters(self.salesman)
        self.assertIn(self.other_sales.partner_id, shown, "the salesperson of the opportunity")
        self.assertIn(self.measurer.partner_id, shown)
        self.assertIn(self.measurer2.partner_id, shown, "no measurement yet: every measurer")
        self.assertNotIn(self.customer, shown, "the customer is never shown")

    def test_06_measurer_of_the_sheet_and_attendees(self):
        self.env['td.mebli.measure'].create({'lead_id': self.lead.id, 'measurer_id': self.measurer.id})
        self.env['calendar.event'].create({
            'name': 'Measurement', 'start': datetime(2026, 12, 1, 9), 'stop': datetime(2026, 12, 1, 10),
            'opportunity_id': self.lead.id, 'partner_ids': [(6, 0, (self.measurer.partner_id | self.customer).ids)]})
        self.lead.with_user(self.salesman).action_schedule_meeting()
        shown = self._filters(self.salesman)
        self.assertIn(self.measurer.partner_id, shown)
        self.assertNotIn(self.measurer2.partner_id, shown, "a measurement exists: only its measurer")
        self.assertNotIn(self.customer, shown)
        # the second time — no duplicates (UNIQUE user/partner), still checked
        self.lead.with_user(self.salesman).action_schedule_meeting()

    def test_11_start_the_measurement_from_the_meeting(self):
        event = self.env['calendar.event'].create({
            'name': 'Measurement', 'start': datetime(2026, 12, 1, 9), 'stop': datetime(2026, 12, 1, 10),
            'user_id': self.measurer.id, 'opportunity_id': self.lead.id,
            'partner_ids': [(6, 0, (self.measurer.partner_id | self.customer).ids)]})
        action = event.with_user(self.measurer).action_td_start_measure()
        sheet = self.env['td.mebli.measure'].browse(action['res_id'])
        self.assertEqual(sheet.event_id, event)
        self.assertEqual(sheet.lead_id, self.lead, "the opportunity of the meeting")
        self.assertFalse(sheet.order_id, "the order stays empty: the salesperson chooses it")
        self.assertEqual(sheet.measurer_id, self.measurer)
        self.assertEqual(sheet.with_user(self.measurer).td_address, 'Shevchenka 1')
        again = event.with_user(self.measurer).action_td_start_measure()
        self.assertEqual(again['res_id'], sheet.id, "an existing sheet is opened, no double")
        self.assertEqual(self.env['td.mebli.measure'].search_count([('event_id', '=', event.id)]), 1)

    def test_11_button_for_the_measurer_only(self):
        arch = self.env['calendar.event'].with_user(self.measurer).get_views([(False, 'form')])['views']['form']['arch']
        self.assertIn('action_td_start_measure', arch)
        arch = self.env['calendar.event'].with_user(self.salesman).get_views([(False, 'form')])['views']['form']['arch']
        self.assertNotIn('action_td_start_measure', arch)
        action = self.env.ref('td_mebli_measure.td_mebli_measure_my_calendar_action')
        self.assertIn('td_measure_start', action.context)
