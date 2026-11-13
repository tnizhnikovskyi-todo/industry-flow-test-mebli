import base64
import time
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import TdMebliCommon

HEADER = "Деталь;Довжина;Ширина;К-сть;Матеріал;Кромка довж\n"
CSV = HEADER + "Боковина;720;560;2;Board A;1\nПолиця;564;540;1;;1\n"


@tagged('post_install', '-at_install')
class TestG2Spec(TdMebliCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.board_a.default_code = 'DSP-A'

    def _bom(self):
        return self.env['mrp.bom'].create({'product_tmpl_id': self.cabinet_tmpl.id,
                                           'bom_line_ids': [(0, 0, {'product_id': self.board_a.id, 'product_qty': 1})]})

    def _wizard(self, bom, text, **vals):
        return self.env['td.mebli.spec.import'].create(dict({
            'bom_id': bom.id, 'filename': 'kitchen.csv', 'file': base64.b64encode(text.encode())}, **vals))

    def _import(self, bom, text, **vals):
        wizard = self._wizard(bom, text, **vals)
        wizard.action_recognize()
        wizard.action_import()
        return wizard

    # AC-045 -------------------------------------------------------------
    def test_ac_045_replace_is_the_default_and_append_adds(self):
        bom = self._bom()
        self._import(bom, CSV)
        self.assertEqual(bom.td_part_ids.mapped('name'), ['Боковина', 'Полиця'])
        wizard = self._wizard(bom, HEADER + "Дно;800;500;1;DSP-A;0\n")
        self.assertEqual(wizard.mode, 'replace')
        wizard.action_recognize()
        wizard.action_import()
        self.assertEqual(bom.td_part_ids.mapped('name'), ['Дно'])
        self._import(bom, HEADER + "Кришка;800;500;1;Board A;0\n", mode='append')
        self.assertEqual(sorted(bom.td_part_ids.mapped('name')), ['Дно', 'Кришка'])

    def test_ac_045_board_lines_from_the_parts_and_chatter(self):
        bom = self._bom()
        wizard = self._wizard(bom, CSV)
        wizard.action_recognize()
        self.assertEqual(wizard.preview_count, 2)
        self.assertIn('Довжина', wizard.mapping)
        wizard.action_import()
        board_line = bom.bom_line_ids.filtered(lambda line: line.product_id == self.board_a)
        self.assertEqual(len(board_line), 1)
        self.assertTrue(board_line.td_from_parts)  # «From parts»: recalculated from the imported parts
        self.assertAlmostEqual(board_line.product_qty, bom._td_part_quantities()[self.board_a], places=3)
        message = bom.message_ids[:1]
        self.assertIn('kitchen.csv', message.body)
        self.assertIn('2', message.body)
        self.assertIn('Replace the parts', message.body)
        self.assertTrue(message.attachment_ids)

    # AC-046 -------------------------------------------------------------
    def test_ac_046_no_width_column_nothing_written(self):
        bom = self._bom()
        wizard = self._wizard(bom, "Деталь;Довжина;К-сть;Матеріал\nБоковина;720;2;Board A\n")
        wizard.action_recognize()
        self.assertEqual(wizard.missing_columns, 'Width')
        with self.assertRaisesRegex(UserError, r'^Columns not found in the file: Width\. Check the headers or set the '
                                               r'mapping\.$'):
            wizard.action_import()
        self.assertFalse(bom.td_part_ids)

    # AC-047 -------------------------------------------------------------
    def test_ac_047_unknown_material_blocks_until_mapped(self):
        bom = self._bom()
        wizard = self._wizard(bom, HEADER + "Боковина;720;560;2;Board A;1\nДно;800;500;1;Egger W980;0\n"
                                            "Кришка;800;500;1;egger w980;0\n")
        wizard.action_recognize()
        self.assertIn('Row 3', wizard.unknown_lines)
        self.assertIn('Row 4', wizard.unknown_lines)
        self.assertIn('Material not found', wizard.unknown_lines)
        self.assertNotIn('Row 2', wizard.unknown_lines)
        with self.assertRaisesRegex(UserError, 'Material not found in rows 3, 4'):
            wizard.action_import()
        self.assertFalse(bom.td_part_ids)
        self.assertEqual(wizard.material_map_ids.mapped('code'), ['egger w980'])
        wizard.material_map_ids.material_id = self.board_b  # mapped by hand
        wizard.action_recognize()
        self.assertFalse(wizard.unknown_lines)
        wizard.action_import()
        self.assertEqual(bom.td_part_ids.filtered(lambda p: p.name == 'Дно').material_id, self.board_b)

    # AC-048 -------------------------------------------------------------
    def test_ac_048_three_hundred_parts(self):
        bom = self._bom()
        text = HEADER + ''.join(f"Деталь {n};{300 + n};{200 + n % 50};1;DSP-A;1\n" for n in range(300))
        started = time.monotonic()
        self._import(bom, text)
        elapsed = time.monotonic() - started
        self.assertEqual(len(bom.td_part_ids), 300)
        self.assertLess(elapsed, 30.0)  # functional bound; the measurement on the reference stand is A-15

    # AC-049 -------------------------------------------------------------
    def test_ac_049_manual_mapping_saved_as_template(self):
        bom = self._bom()
        text = "Poz;Dl;Sz;Ile;Plyta\nBok;720;560;2;DSP-A\n"
        wizard = self._wizard(bom, text)
        wizard.action_recognize()
        self.assertTrue(wizard.missing_columns)
        with self.assertRaises(UserError):
            wizard.action_import()
        for column, field in zip(wizard.column_ids.sorted('index'), ('name', 'length_mm', 'width_mm', 'qty', 'material')):
            column.field_name = field
        wizard.template_name = 'PRO100 of the showroom'
        wizard.action_recognize()
        self.assertFalse(wizard.missing_columns)
        wizard.action_import()
        self.assertEqual(bom.td_part_ids.mapped('length_mm'), [720.0])
        template = self.env['td.mebli.import.template'].search([('name', '=', 'PRO100 of the showroom')])
        self.assertTrue(template)
        # the next file with the same headers: recognized by the template, without the manual step
        bom2 = self._bom()
        wizard2 = self._wizard(bom2, "Poz;Dl;Sz;Ile;Plyta\nDno;800;500;1;DSP-A\n")
        wizard2.action_recognize()
        self.assertEqual(wizard2.template_id, template)
        self.assertFalse(wizard2.missing_columns)
        wizard2.action_import()
        self.assertEqual(bom2.td_part_ids.mapped('name'), ['Dno'])

    # AC-050 -------------------------------------------------------------
    def test_ac_050_ai_hint_off_by_default_no_call(self):
        bom = self._bom()
        self.env['ir.config_parameter'].set_param('td_mebli_mrp.ai_mapping_url', 'https://ai.example.invalid/map')
        Wizard = type(self.env['td.mebli.spec.import'])
        with patch.object(Wizard, '_td_ai_request', autospec=True) as request:
            wizard = self._wizard(bom, "Poz;Dl;Sz;Ile;Plyta\nBok;720;560;2;DSP-A\n")
            wizard.action_recognize()  # no error: manual mapping
        request.assert_not_called()
        self.assertTrue(wizard.missing_columns)
        self.assertFalse(wizard.ai_note)

    def test_ac_050_ai_hint_on_sends_headers_and_ten_rows(self):
        bom = self._bom()
        self.env.user.group_ids = [(4, self.env.ref('td_mebli_base.group_feature_ai_mapping').id)]
        Wizard = type(self.env['td.mebli.spec.import'])
        text = "Poz;Dl;Sz;Ile;Plyta\n" + ''.join(f"P{n};{300 + n};200;1;DSP-A\n" for n in range(25))
        # function on, no provider: no call, manual mapping
        with patch.object(Wizard, '_td_ai_request', autospec=True) as request:
            self._wizard(bom, text).action_recognize()
        request.assert_not_called()
        self.env['ir.config_parameter'].set_param('td_mebli_mrp.ai_mapping_url', 'https://ai.example.invalid/map')
        answer = {'mapping': {'name': 0, 'length_mm': 1, 'width_mm': 2, 'qty': 3, 'material': 4}}
        with patch.object(Wizard, '_td_ai_request', autospec=True, return_value=answer) as request:
            wizard = self._wizard(bom, text)
            wizard.action_recognize()
        payload = request.call_args.args[2]
        self.assertEqual(payload['headers'], ['Poz', 'Dl', 'Sz', 'Ile', 'Plyta'])
        self.assertLessEqual(len(payload['rows']), 10)
        self.assertEqual(set(payload), {'headers', 'rows', 'fields'})  # nothing of the order or the customer
        self.assertTrue(wizard.ai_note)  # shown as a proposal
        self.assertTrue(all(wizard.column_ids.mapped('suggested')))
        self.assertFalse(bom.td_part_ids)  # a proposal, not an import
        # provider not reachable: manual mapping without an error
        with patch.object(Wizard, '_td_ai_request', autospec=True, side_effect=OSError('down')):
            wizard = self._wizard(bom, text)
            wizard.action_recognize()
        self.assertTrue(wizard.missing_columns)

    # AC-052 -------------------------------------------------------------
    def test_ac_052_parts_of_a_sent_specification_are_locked(self):
        bom = self._bom()
        self._import(bom, CSV)
        part = bom.td_part_ids[0]
        self.assertFalse(part.locked)
        part.length_mm = 700  # not sent yet: free to change
        versions = bom._td_mark_sent_to_cutting()
        self.assertEqual(versions[bom.id], 1)
        self.assertEqual(bom.td_cut_version, 1)
        self.assertTrue(part.locked)
        message = r'^The specification was sent to cutting \(version 1\) — change only by an additional order\.$'
        with self.assertRaisesRegex(UserError, message):
            part.length_mm = 650
        with self.assertRaisesRegex(UserError, message):
            part.unlink()
        with self.assertRaisesRegex(UserError, message):
            self.env['td.mebli.part'].create({'bom_id': bom.id, 'name': 'Extra', 'material_id': self.board_a.id,
                                              'length_mm': 100, 'width_mm': 100})
        with self.assertRaisesRegex(UserError, message):
            self._import(bom, CSV, mode='append')
        self.assertEqual(part.length_mm, 700)
        # review A-11: a context flag from a client (RPC) does not unlock; the private object of the module does
        with self.assertRaisesRegex(UserError, message):
            part.with_context(td_cut_unlock=True).length_mm = 650
        from odoo.addons.td_mebli_mrp.models.part import CUT_UNLOCK
        part.with_context(td_cut_unlock=CUT_UNLOCK).length_mm = 690
        self.assertEqual(part.length_mm, 690)
        bom._td_mark_sent_to_cutting()
        self.assertEqual(bom.td_cut_version, 2)

    # AC-036 (review A-11) ------------------------------------------------
    def test_ac_036_parts_by_company_of_the_specification(self):
        """The part has the company of its specification (stored related) and a rule of the allowed companies:
        a technologist of company 1 does not see the parts of a specification of company 2; a shared specification
        (without a company) is seen by both."""
        env = self.env
        other = env['res.company'].create({'name': 'Second factory of the parts'})
        shared = self._bom()
        own = self._bom()
        own.company_id = env.company
        foreign = env['mrp.bom'].create({'product_tmpl_id': self.cabinet_tmpl.id, 'company_id': other.id})
        Part = env['td.mebli.part']
        parts = Part.browse()
        for bom in (shared, own, foreign):
            parts |= Part.create({'bom_id': bom.id, 'name': 'Side', 'material_id': self.board_a.id,
                                  'length_mm': 720, 'width_mm': 560})
        self.assertEqual(parts.mapped('company_id'), env.company | other)
        tech = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Technologist MC', 'login': 'td_tech_mc', 'company_id': env.company.id,
            'company_ids': [(6, 0, env.company.ids)], 'group_ids': [(6, 0, [env.ref('mrp.group_mrp_user').id])]})
        visible = Part.with_user(tech).search([('id', 'in', parts.ids)])
        self.assertEqual(visible, parts.filtered(lambda p: p.bom_id in shared | own))
        with self.assertRaises(AccessError):
            parts.filtered(lambda p: p.bom_id == foreign).with_user(tech).read(['name'])
