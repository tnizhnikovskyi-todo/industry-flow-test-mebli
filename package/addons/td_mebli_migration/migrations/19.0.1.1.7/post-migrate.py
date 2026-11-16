"""19.0.1.1.7 (A-11-fix5, AI-37; A-11-fix6): the exchange with the accounting system is excluded from the package by the
decision of the owner 2026-11-16. Its three import steps (templates td/19b-21b, removed from the package) are
noupdate data, so they are removed here, with their xmlids; the note of step 2 that pointed to them is cleared."""
from odoo import SUPERUSER_ID, api

EXCLUDED_STEPS = ('step_td_19b', 'step_td_20b', 'step_td_21b')


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    Step = env['td.mebli.migration.step']
    for xmlid in EXCLUDED_STEPS:
        step = env.ref(f'td_mebli_migration.{xmlid}', raise_if_not_found=False)
        if step:
            step.unlink()  # unlink also removes its ir.model.data
    step = env.ref('td_mebli_migration.step_02', raise_if_not_found=False)
    if step:
        cr.execute("UPDATE td_mebli_migration_step SET note = NULL WHERE id = %s", (step.id,))
    Step.invalidate_model()
