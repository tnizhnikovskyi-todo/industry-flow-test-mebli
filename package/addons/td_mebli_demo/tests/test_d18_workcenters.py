from odoo.tests import TransactionCase, tagged
from odoo.tools import convert_file

from odoo.addons.td_mebli_demo.hooks import (
    TEMPLATE_WORKCENTERS,
    _adopt_template_workcenters,
)


@tagged('post_install', '-at_install')
class TestD18WorkCenters(TransactionCase):
    """D-18: the demo layer takes the work centers of the templates A-13 when they are there (package/demo/up.sh imports
    the templates first): no second «Розкрій», «Присадка» on the stand."""

    def _templates(self):
        """The 4 work centers of package/master-data/09_mrp.workcenter.csv with their xmlids (as import.sh loads them)."""
        rows = {'cutting': ('Розкрій', 'CUT'), 'edging': ('Кромкування', 'EDGE'), 'drilling': ('Присадка', 'DRILL'),
                'assembly': ('Збирання', 'ASSY')}
        centers = {}
        for key, (name, code) in rows.items():
            center = self.env['mrp.workcenter'].create({'name': name, 'code': code})
            self.env['ir.model.data'].create({'module': 'td_md', 'name': f'mrp_workcenter_{key}',
                                              'model': 'mrp.workcenter', 'res_id': center.id})
            centers[f'td_md.mrp_workcenter_{key}'] = center
        return centers

    def _forget_demo_xmlids(self):
        self.env['ir.model.data'].search([('module', '=', 'td_mebli_demo'), ('name', 'in', list(TEMPLATE_WORKCENTERS))]).unlink()

    def test_demo_layer_takes_the_template_work_centers(self):
        """The install of the demo layer after the templates: the same 4 work centers, with the demo name, code, cost."""
        self._forget_demo_xmlids()
        centers = self._templates()
        count = self.env['mrp.workcenter'].search_count([])
        _adopt_template_workcenters(self.env)
        convert_file(self.env, 'td_mebli_demo', 'data/workcenter_data.xml', {}, mode='init', noupdate=True)
        self.assertEqual(self.env['mrp.workcenter'].search_count([]), count, "no new work center")
        for name, (template, _names, _codes) in TEMPLATE_WORKCENTERS.items():
            self.assertEqual(self.env.ref(f'td_mebli_demo.{name}'), centers[template], name)
        self.assertEqual(self.env.ref('td_mebli_demo.wc_edge').code, 'EDG', "the code of the demo scripts (full.py)")
        self.assertEqual(self.env.ref('td_mebli_demo.wc_cut').costs_hour, 600)

    def test_by_code_or_name_without_xmlid(self):
        self.env.ref('td_mebli_demo.wc_drill').write({'name': 'Old drilling', 'code': 'OLD'})
        self._forget_demo_xmlids()
        center = self.env['mrp.workcenter'].create({'name': 'Присадка', 'code': 'DRILL'})
        _adopt_template_workcenters(self.env)
        self.assertEqual(self.env.ref('td_mebli_demo.wc_drill'), center)

    def test_installed_demo_is_not_touched(self):
        """Already installed demo layer: its xmlids stay (the hook runs before the first install only)."""
        before = {name: self.env.ref(f'td_mebli_demo.{name}') for name in TEMPLATE_WORKCENTERS}
        self._templates()
        _adopt_template_workcenters(self.env)
        self.assertEqual({name: self.env.ref(f'td_mebli_demo.{name}') for name in TEMPLATE_WORKCENTERS}, before)

    def test_no_duplicate_work_center_names(self):
        names = self.env['mrp.workcenter'].search([]).mapped('name')
        self.assertEqual(len(names), len(set(names)), names)
