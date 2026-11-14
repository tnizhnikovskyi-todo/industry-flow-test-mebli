# Паролі демо-ролей (В-4: рішення Тімліда) — лише зі змінної середовища DEMO_USERS_PASSWORD, у репо не пишуться.
# Запуск: DEMO_USERS_PASSWORD=... tools/odoo/apply.py shell --db <instance> --script package/demo/data/set_passwords.py
import os

pwd = os.environ.get('DEMO_USERS_PASSWORD')
if pwd:
    users = env['res.users'].search([('login', '=like', '%@demo-fabryka.example')])  # noqa: F821
    users.write({'password': pwd})
    env.cr.commit()  # noqa: F821
