"""19.0.1.1.1: the import steps follow the templates of A-13 v1.1 (new steps td/01b, 14b, 17, 18, 19b-21b come from the
XML). The steps are noupdate data, so the changed values of the existing steps are written here: name of step 1 (the
warranty is now td/01b), note of step 2 (the BAS code is td/19b), sequence and module of the steps td/."""
import json

from odoo import SUPERUSER_ID, api
from odoo.tools import SQL

CHANGES = {
    'step_01': {'name': ('Product categories', 'Категорії товарів')},
    'step_02': {'note': ('BAS code — step 24 (td/19b)', 'код BAS — крок 24 (td/19b)')},
    'step_16': {'sequence': 17, 'module_name': 'td_mebli_mrp'},
    'step_17': {'sequence': 18, 'module_name': 'td_mebli_mrp'},
    'step_18': {'sequence': 19, 'module_name': 'td_mebli_shop'},
    'step_19': {'sequence': 21, 'module_name': 'td_mebli_mrp'},
}


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid, values in CHANGES.items():
        step = env.ref(f'td_mebli_migration.{xmlid}', raise_if_not_found=False)
        if not step:
            continue
        plain = {key: value for key, value in values.items() if not isinstance(value, tuple)}
        if plain:
            step.write(plain)
        for field, (en_us, uk_ua) in ((k, v) for k, v in values.items() if isinstance(v, tuple)):
            # both languages of the translated field at once (the uk_UA value of uk.po; harmless without uk_UA)
            cr.execute(SQL("UPDATE td_mebli_migration_step SET %s = COALESCE(%s, '{}'::jsonb) || %s::jsonb WHERE id = %s",
                           SQL.identifier(field), SQL.identifier(field),
                           json.dumps({'en_US': en_us, 'uk_UA': uk_ua}), step.id))
    env['td.mebli.migration.step'].invalidate_model()
