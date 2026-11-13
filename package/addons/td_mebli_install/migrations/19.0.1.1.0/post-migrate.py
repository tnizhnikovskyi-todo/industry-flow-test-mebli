"""19.0.1.1.0 (AC-107, tr/td_mebli_install.md §5): the reasons of the bonuses and the penalties become a list.

The text of the reason of the existing bonuses and penalties is kept as the comment; a reason of the list is created
for every distinct text (per kind and company) and linked to the accrual."""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    Reason = env['td.mebli.accrual.reason'].with_context(active_test=False)
    accruals = env['td.mebli.accrual'].search([('kind', 'in', ('bonus', 'penalty')), ('reason_id', '=', False),
                                               ('reason', '!=', False)])
    cache = {}
    for accrual in accruals:
        key = (accrual.reason.strip(), accrual.kind, accrual.company_id.id)
        if key not in cache:
            cache[key] = Reason.search([('name', '=', key[0]), ('kind', '=', key[1]), ('company_id', '=', key[2])], limit=1) \
                or Reason.create({'name': key[0], 'kind': key[1], 'company_id': key[2]})
        # SQL: a confirmed accrual is read only by the ORM, the link does not change its figures
        cr.execute('UPDATE td_mebli_accrual SET reason_id = %s WHERE id = %s', (cache[key].id, accrual.id))
