"""19.0.1.1.4 (A-11-fix6, AI-42): the exchange with the accounting system is excluded from the package by the decision of
the owner 2026-11-16; its modules td_mebli_bas and td_mebli_attendance are no longer delivered. A database of an older
version may still have them installed: their views, fields, menus and tables would stay in the database, the modules
«installed» without code. At the end of the update (all the modules are loaded) they are marked «to remove»: Odoo then
uninstalls them in the same update (odoo/modules/loading.py, step 5) from ir.model.data — with or without their code in
the addons path — and drops their fields, views, menus, rights. Without the code Odoo cannot drop the tables of their own
models (the model is not in the registry): they are dropped here. Their data are not kept (the codes of the accounting
system of partners, products and employees, the exchange batches): export them before the update if they are needed
(admin.md, «Оновлення версії»)."""
import logging

from odoo.modules.module import get_module_path

_logger = logging.getLogger(__name__)

EXCLUDED_MODULES = ('td_mebli_bas', 'td_mebli_attendance')
# the tables of its own models (exchange channel, batch, log); td_mebli_attendance had a wizard only
EXCLUDED_TABLES = ('td_mebli_bas_log', 'td_mebli_bas_batch', 'td_mebli_bas_channel')


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        "UPDATE ir_module_module SET state = 'to remove' WHERE name IN %s AND state IN ('installed', 'to upgrade')"
        " RETURNING name", (EXCLUDED_MODULES,))
    names = [name for (name,) in cr.fetchall()]
    if not names:
        return
    _logger.info("Modules excluded from the package are uninstalled at the end of the update: %s", names)
    if 'td_mebli_bas' in names and not get_module_path('td_mebli_bas', display_warning=False):
        for table in EXCLUDED_TABLES:
            cr.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')  # fixed names above, not input
