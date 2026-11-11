# Usage: odoo-bin shell -c <conf> -d <db> < scripts/show_scenario.py   (env UPTO=<step>, default 14)
import os

from odoo.addons.td_mebli_demo.scenario import run

result = run(env, upto=int(os.environ.get('UPTO', '14')))  # noqa: F821 (env is given by odoo shell)
env.cr.commit()  # noqa: F821
print({key: str(value) for key, value in result.items()})
