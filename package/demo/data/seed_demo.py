# Демо-шар стенда A-15 (запуск: tools/odoo/apply.py shell --db <instance> --script package/demo/data/seed_demo.py).
# Джерело синтетики — модуль td_mebli_demo (A-11; не дублюється тут): каталог/робочі центри/склад — data/*.xml модуля,
# документи (замовлення, виробництво, закупівлі, оплати, монтажі, рекламації) — td_mebli_demo.showcase.seed_showcase.
# Детермінованість: random.Random(2026) / Random(7) у модулі; дати — відносно дня підйому (див. README «Склад демо-даних»).
# Ідемпотентно: seed_showcase нічого не робить, якщо в базі вже є непскасоване замовлення. Коміт — явний.
from odoo.addons.td_mebli_demo.showcase import seed_showcase

seed_showcase(env)  # noqa: F821 (env дає odoo-bin shell)
env.cr.commit()  # noqa: F821
