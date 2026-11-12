from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMeasure(TransactionCase):

    def test_fridge_deeper_than_the_niche(self):
        sheet = self.env['td.mebli.measure'].create({'room': 'Kitchen'})
        niche = self.env['td.mebli.measure.niche'].create(
            {'measure_id': sheet.id, 'name': 'Column', 'width_mm': 600, 'height_mm': 2100, 'depth_mm': 560})
        fridge = self.env['td.mebli.measure.appliance'].create(
            {'measure_id': sheet.id, 'niche_id': niche.id, 'name': 'Fridge', 'width_mm': 595, 'height_mm': 2010,
             'depth_mm': 590})
        oven = self.env['td.mebli.measure.appliance'].create(
            {'measure_id': sheet.id, 'niche_id': niche.id, 'name': 'Oven', 'width_mm': 595, 'height_mm': 595,
             'depth_mm': 550})
        self.assertNotEqual(sheet.name, '/')
        self.assertFalse(fridge.fits)
        self.assertIn('30', fridge.issue)
        self.assertTrue(oven.fits)
        self.assertEqual(sheet.issue_count, 1)
        sheet.action_check()
        self.assertEqual(sheet.state, 'checked')
