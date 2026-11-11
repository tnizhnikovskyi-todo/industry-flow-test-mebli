# Usage: odoo-bin shell -c <conf> -d <db> < scripts/seed_showcase.py   (on a database with td_mebli_demo)
from odoo.addons.td_mebli_demo.showcase import seed_showcase

print(seed_showcase(env))  # noqa: F821 (env is given by odoo shell)
env.cr.commit()  # noqa: F821
