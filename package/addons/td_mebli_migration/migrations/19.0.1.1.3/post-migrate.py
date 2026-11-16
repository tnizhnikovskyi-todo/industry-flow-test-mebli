"""19.0.1.1.3: the import steps follow the templates of A-13 v1.1, attempt 3 (28 steps, light 25): the new steps td/03b and
td/04b (td_mebli_mrp) come from the XML after td/01b. The steps are noupdate data, so the sequence of the following steps is
written here (step 2 has no note since 19.0.1.1.7)."""
from odoo import SUPERUSER_ID, api

SEQUENCES = {
    'step_td_01b': 16, 'step_td_03b': 17, 'step_td_04b': 18, 'step_16': 19, 'step_17': 20, 'step_18': 21,
    'step_td_14b': 22, 'step_19': 23, 'step_td_17': 24, 'step_td_18': 25,
}


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid, sequence in SEQUENCES.items():
        step = env.ref(f'td_mebli_migration.{xmlid}', raise_if_not_found=False)
        if step and step.sequence != sequence:
            step.write({'sequence': sequence})
    env['td.mebli.migration.step'].invalidate_model()
