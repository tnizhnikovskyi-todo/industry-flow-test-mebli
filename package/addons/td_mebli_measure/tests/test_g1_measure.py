from datetime import datetime, time, timedelta

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestG1Measure(TransactionCase):
    """A-11 G1: S-15 measurement sheet — AC-003, AC-005…AC-008, AC-010, AC-036 (measurement sheets)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        env['res.lang']._activate_lang('uk_UA')
        cls.partner = env['res.partner'].create({'name': 'Покупець Тест', 'phone': '+380 50 000 00 00',
                                                 'street': 'вул. Вигадана, 1', 'city': 'Київ'})
        cls.measurer = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Замірник', 'login': 'td_g1_measurer', 'tz': 'Europe/Kyiv',
            'group_ids': [(6, 0, [env.ref('td_mebli_measure.group_td_mebli_measurer').id])]})

    def _sheet(self, **vals):
        return self.env['td.mebli.measure'].create(dict({'room': 'Кухня'}, **vals))

    def test_ac_003_no_free_windows(self):
        env = self.env
        lead = env['crm.lead'].create({'name': 'Кухня', 'type': 'opportunity', 'partner_id': self.partner.id})
        day = fields.Date.today() + timedelta(days=7)
        # the calendar of the measurer is busy for the whole period of the wizard
        env['calendar.event'].create({'name': 'Busy', 'start': datetime.combine(day - timedelta(days=1), time.min),
                                      'stop': datetime.combine(day + timedelta(days=3), time.max).replace(microsecond=0),
                                      'partner_ids': [(6, 0, self.measurer.partner_id.ids)]})
        events = env['calendar.event'].search_count([])
        wizard = env['td.mebli.measure.booking'].create({'lead_id': lead.id, 'measurer_id': self.measurer.id,
                                                         'date_from': day, 'days': 2})
        wizard._td_fill_slots()
        self.assertFalse(wizard.slot_ids)
        self.assertEqual(wizard.no_slot_text, "No free windows in the chosen period — increase the number of days or "
                                              "choose another measurer")
        self.assertEqual(wizard.with_context(lang='uk_UA').no_slot_text,
                         "Немає вільних вікон за обраний період — збільште кількість днів або оберіть іншого замірника")
        self.assertEqual(env['calendar.event'].search_count([]), events, "no meeting is created")
        # free windows exist again when the period grows past the busy days
        wizard.days = 6
        wizard._td_fill_slots()
        self.assertTrue(wizard.slot_ids)
        self.assertFalse(wizard.no_slot_text)

    def test_ac_005_number_company_and_smart_buttons(self):
        env = self.env
        lead = env['crm.lead'].create({'name': 'Кухня', 'type': 'opportunity', 'partner_id': self.partner.id})
        order = env['sale.order'].create({'partner_id': self.partner.id, 'opportunity_id': lead.id})
        sheet = self._sheet(order_id=order.id)
        year = fields.Date.today().year
        self.assertRegex(sheet.name, r'^ЗМ/%s/\d{4}$' % year)
        self.assertEqual(sheet.company_id, order.company_id)
        self.assertEqual(sheet.lead_id, lead)
        self.assertEqual(order.td_measure_count, 1)
        self.assertEqual(lead.td_measure_count, 1)
        self.assertEqual(lead.action_td_view_measures()['res_id'], sheet.id)
        self.assertEqual(order.action_td_view_measures()['res_id'], sheet.id)

    def test_ac_006_measurer_sees_own_sheets_without_prices(self):
        env = self.env
        order = env['sale.order'].create({'partner_id': self.partner.id, 'order_line': [
            (0, 0, {'product_id': env['product.product'].create({'name': 'Шафа', 'list_price': 1000}).id})]})
        own = self._sheet(order_id=order.id, measurer_id=self.measurer.id)
        other = self._sheet(measurer_id=env.user.id)
        Measure = env['td.mebli.measure'].with_user(self.measurer)
        self.assertEqual(Measure.search([]), own)
        with self.assertRaises(AccessError):
            other.with_user(self.measurer).read(['name'])
        # the address and the phone of the customer — yes
        data = own.with_user(self.measurer).read(['customer', 'td_address', 'td_phone', 'order_id'])[0]
        self.assertEqual(data['customer'], 'Покупець Тест')
        self.assertIn('Вигадана', data['td_address'])
        self.assertEqual(data['td_phone'], '+380 50 000 00 00')
        # the order, its price, amount and margin — no: direct access is an AccessError, no Sales menu
        with self.assertRaises(AccessError):
            order.with_user(self.measurer).read(['amount_total'])
        with self.assertRaises(AccessError):
            env['sale.order'].with_user(self.measurer).search([])
        self.assertFalse(self.measurer.has_group('sales_team.group_sale_salesman'))
        menus = env['ir.ui.menu'].with_user(self.measurer)._visible_menu_ids()
        self.assertNotIn(env.ref('sale.sale_menu_root').id, menus)
        self.assertIn(env.ref('td_mebli_measure.td_mebli_measure_root_menu').id, menus)
        # he fills his own sheet
        own.with_user(self.measurer).write({'niche_ids': [(0, 0, {'name': 'Колона', 'width_mm': 600, 'height_mm': 2100,
                                                                    'depth_mm': 560})]})
        self.assertEqual(len(own.niche_ids), 1)
        self.assertFalse(own.with_user(self.measurer).td_can_link)

    def test_ac_007_cards_on_a_phone(self):
        arch = self.env['td.mebli.measure'].get_views([(False, 'form')])['views']['form']['arch']
        for field in ('niche_ids', 'appliance_ids'):
            start = arch.index('name="%s"' % field)
            sub = arch[start:arch.index('</field>\n', arch.index('</kanban>', start))]
            self.assertIn('<kanban', sub, "the standard x2many shows the kanban on a small screen")
            self.assertIn('<list', sub)
        self.assertIn('many2many_binary', arch, "photos from the camera or the gallery (standard upload)")

    def test_ac_008_does_not_fit_text_and_order_counter(self):
        order = self.env['sale.order'].create({'partner_id': self.partner.id})
        sheet = self._sheet(order_id=order.id)
        niche = self.env['td.mebli.measure.niche'].create({'measure_id': sheet.id, 'name': 'Колона', 'width_mm': 600,
                                                            'height_mm': 2100, 'depth_mm': 560, 'protrusion_mm': 0})
        fridge = self.env['td.mebli.measure.appliance'].create({
            'measure_id': sheet.id, 'niche_id': niche.id, 'name': 'Холодильник', 'width_mm': 595, 'height_mm': 2010,
            'depth_mm': 590})
        self.assertEqual(fridge.with_context(lang='uk_UA').issue, "Не вміщається: глибше на 30 мм")
        self.assertEqual(fridge.td_check, 'no_fit')
        self.assertEqual(sheet.issue_count, 1)
        self.assertEqual(order.td_measure_issue_count, 1)

    def test_ac_010_empty_sizes_are_not_checked(self):
        sheet = self._sheet()
        niche = self.env['td.mebli.measure.niche'].create({'measure_id': sheet.id, 'name': 'Колона', 'width_mm': 600,
                                                            'height_mm': 2100, 'depth_mm': 560})
        no_depth = self.env['td.mebli.measure.appliance'].create({
            'measure_id': sheet.id, 'niche_id': niche.id, 'name': 'Холодильник', 'width_mm': 595, 'height_mm': 2010})
        empty_niche = self.env['td.mebli.measure.niche'].create({'measure_id': sheet.id, 'name': 'Ніша'})
        oven = self.env['td.mebli.measure.appliance'].create({
            'measure_id': sheet.id, 'niche_id': empty_niche.id, 'name': 'Духовка', 'width_mm': 595, 'height_mm': 595,
            'depth_mm': 550})
        for item in no_depth | oven:
            self.assertEqual(item.with_context(lang='uk_UA').issue, "Не перевірено (немає розмірів)")
            self.assertEqual(item.td_check, 'unchecked')
            self.assertTrue(item.fits)
        self.assertEqual(sheet.issue_count, 0, "«does not fit» is not counted")
        sheet.action_check()  # no error
        self.assertEqual(sheet.state, 'checked')

    def test_ac_036_measurements_by_company(self):
        env = self.env
        fop = env['res.company'].create({'name': 'ФОП Тест'})
        user = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Менеджер ТОВ', 'login': 'td_g1_tov_manager', 'company_id': env.company.id,
            'company_ids': [(6, 0, env.company.ids)],
            'group_ids': [(6, 0, [env.ref('sales_team.group_sale_manager').id])]})
        tov_sheet = self._sheet()
        fop_sheet = self._sheet(company_id=fop.id)
        Measure = env['td.mebli.measure'].with_user(user)
        self.assertEqual(Measure.search([('id', 'in', (tov_sheet | fop_sheet).ids)]), tov_sheet)
        with self.assertRaises(AccessError):
            fop_sheet.with_user(user).read(['name'])
        user.company_ids = [(4, fop.id)]
        both = Measure.with_context(allowed_company_ids=[env.company.id, fop.id])
        self.assertEqual(both.search([('id', 'in', (tov_sheet | fop_sheet).ids)]), tov_sheet | fop_sheet)

    def test_ac_036_lines_of_the_sheet_by_company_and_measurer(self):
        """Review A-11: the niches and the appliances follow the sheet — a user of company 1 does not read the lines
        of a sheet of company 2; the measurer reads the lines of his own sheets only and cannot delete a sheet."""
        env = self.env
        fop = env['res.company'].create({'name': 'ФОП Тест 2'})
        user = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Менеджер ТОВ 2', 'login': 'td_g1_tov_manager2', 'company_id': env.company.id,
            'company_ids': [(6, 0, env.company.ids)],
            'group_ids': [(6, 0, [env.ref('sales_team.group_sale_manager').id])]})
        lines = {'niche_ids': [(0, 0, {'name': 'Ніша', 'width_mm': 600})],
                 'appliance_ids': [(0, 0, {'name': 'Духова шафа', 'width_mm': 560})]}
        tov_sheet = self._sheet(measurer_id=self.measurer.id, **lines)
        fop_sheet = self._sheet(company_id=fop.id, measurer_id=self.measurer.id, **lines)
        foreign = self._sheet(**lines)  # a sheet of another measurer
        for model, field in (('td.mebli.measure.niche', 'niche_ids'), ('td.mebli.measure.appliance', 'appliance_ids')):
            all_lines = (tov_sheet | fop_sheet | foreign).mapped(field)
            visible = env[model].with_user(user).search([('id', 'in', all_lines.ids)])
            self.assertEqual(visible, (tov_sheet | foreign).mapped(field), model)
            with self.assertRaises(AccessError):
                fop_sheet[field].with_user(user).read(['name'])
            measurer = env[model].with_user(self.measurer).with_context(allowed_company_ids=env.company.ids)
            self.assertEqual(measurer.search([('id', 'in', all_lines.ids)]), tov_sheet[field], model)
            with self.assertRaises(AccessError):
                foreign[field].with_user(self.measurer).read(['name'])
        with self.assertRaises(AccessError):  # the measurer does not delete the sheets (review A-11)
            tov_sheet.with_user(self.measurer).unlink()
