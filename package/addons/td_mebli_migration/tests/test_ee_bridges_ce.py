from odoo.modules.module import get_manifest
from odoo.tests import TransactionCase, tagged

# tr/ee-bridges.md: bridge → (module of the core, Enterprise app)
BRIDGES = {
    'td_mebli_shopfloor': ('td_mebli_shop', 'mrp_workorder'),
    'td_mebli_quality': ('td_mebli_shop', 'quality_control'),
    'td_mebli_fsm': ('td_mebli_install', 'industry_fsm'),
    'td_mebli_planning': ('td_mebli_install', 'planning'),
    'td_mebli_helpdesk': ('td_mebli_claim', 'helpdesk'),
    'td_mebli_sign': ('td_mebli_install', 'sign'),
}


@tagged('post_install', '-at_install')
class TestEeBridgesOnCommunity(TransactionCase):
    """AC-130: on a Community database with the core of the package no bridge is installed and nothing fails; a bridge
    installs by itself on Enterprise (auto_install) when both its modules are there."""

    def test_ac_130_no_bridge_on_community(self):
        Module = self.env['ir.module.module']
        Module.update_list()
        for bridge, (core, enterprise) in BRIDGES.items():
            manifest = get_manifest(bridge)
            self.assertTrue(manifest, f'{bridge} is in the package')
            self.assertEqual(set(manifest['auto_install']), {core, enterprise}, f'{bridge}: auto_install')
            self.assertEqual(set(manifest['depends']), {core, enterprise}, bridge)
            self.assertEqual(manifest['license'], 'LGPL-3', bridge)
            record = Module.search([('name', '=', bridge)])
            self.assertTrue(record, f'{bridge} is listed')
            self.assertNotEqual(record.state, 'installed', f'{bridge} is not installed on Community')
            self.assertNotEqual(Module.search([('name', '=', enterprise)]).state, 'installed',
                                f'{enterprise} is an Enterprise app')
        # the core of the package (td_mebli_sale and what it needs) is installed: no dependency error on Community
        self.assertEqual(Module.search([('name', '=', 'td_mebli_sale')]).state, 'installed')
        self.assertFalse(Module.search([('name', '=like', 'td_mebli_%'), ('state', 'in', ('to install', 'to upgrade'))]))
