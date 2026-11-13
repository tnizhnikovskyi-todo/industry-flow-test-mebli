"""19.0.1.1.3: the import steps follow the templates of A-13 v1.1, attempt 3 (28 steps, light 25): the new steps td/03b and
td/04b (td_mebli_mrp) come from the XML after td/01b. The steps are noupdate data, so the sequence of the following steps and
the note of step 2 (the BAS code is now step 26) are written here."""
import json

from odoo import SUPERUSER_ID, api
from odoo.tools import SQL

SEQUENCES = {
    'step_td_01b': 16, 'step_td_03b': 17, 'step_td_04b': 18, 'step_16': 19, 'step_17': 20, 'step_18': 21,
    'step_td_14b': 22, 'step_19': 23, 'step_td_17': 24, 'step_td_18': 25, 'step_td_19b': 26, 'step_td_20b': 27,
    'step_td_21b': 28,
}
NOTE_STEP_02 = ('BAS code — step 26 (td/19b)', 'код BAS — крок 26 (td/19b)')


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid, sequence in SEQUENCES.items():
        step = env.ref(f'td_mebli_migration.{xmlid}', raise_if_not_found=False)
        if step and step.sequence != sequence:
            step.write({'sequence': sequence})
    step = env.ref('td_mebli_migration.step_02', raise_if_not_found=False)
    if step:
        # both languages of the translated field at once (the uk_UA value of uk.po; harmless without uk_UA)
        en_us, uk_ua = NOTE_STEP_02
        cr.execute(SQL("UPDATE td_mebli_migration_step SET note = COALESCE(note, '{}'::jsonb) || %s::jsonb WHERE id = %s",
                       json.dumps({'en_US': en_us, 'uk_UA': uk_ua}), step.id))
    env['td.mebli.migration.step'].invalidate_model()
