# Перевірка демо-стенда (бізнес-smoke): tools/odoo/smoke.sh <instance> <модулі> --script package/demo/data/verify_demo.py
# Лише читання + пробне замовлення з відкатом. Пороги — plan.md §3 (обсяги демо-шару td_mebli_demo); друкує «SMOKE OK» або «SMOKE FAIL ...».
import json

E = env  # noqa: F821
res, bad = {}, []


def need(key, value, ok):
    res[key] = value
    if not ok:
        bad.append(key)


MIN = {'sale.order': 80, 'mrp.production': 50, 'purchase.order': 10, 'project.task': 20, 'stock.lot': 100}
for model, n in MIN.items():
    c = E[model].search_count([])
    need(model, c, c >= n)
# майстер-дані A-13 (xml-id td_md.*) лишаються поруч із демо-шаром
need('td_md xmlids', E['ir.model.data'].search_count([('module', '=', 'td_md')]), E['ir.model.data'].search_count([('module', '=', 'td_md')]) >= 70)
# демо-ролі: активні, з групами ролей ТР (SPEC §2 / td_mebli_demo.showcase.USERS)
ROLES = {'salon': 'sales_team.group_sale_salesman', 'tech': 'mrp.group_mrp_user', 'chief': 'mrp.group_mrp_manager',
         'store': 'stock.group_stock_manager', 'fin': 'account.group_account_user',
         'owner': 'td_mebli_dashboard.group_td_mebli_director'}
for login, grp in ROLES.items():
    u = E['res.users'].with_context(active_test=False).search([('login', '=', login + '@demo-fabryka.example')])
    need('user ' + login, bool(u and u.active and u.has_group(grp)), bool(u and u.active and u.has_group(grp)))
# e-mail демо-шару — лише зарезервовані домени (.example, RFC 2606/6761)
mails = [m for m in E['res.partner'].with_context(active_test=False).search([('email', '!=', False)]).mapped('email')
         if not (m.endswith('.example') or m.endswith('@example.com'))]
need('emails outside .example', mails[:5], not mails)
# пробне замовлення з демо-номенклатури (фурнітура без конфігуратора; відкат); ставка ПДВ рядка — 20 % (D-01)
try:
    so = E['sale.order'].create({'partner_id': E.ref('td_mebli_demo.partner_salon').id,
                                 'order_line': [(0, 0, {'product_id': E.ref('td_mebli_demo.fit_hinge').product_variant_id.id,
                                                                 'product_uom_qty': 4})]})
    so.action_confirm()
    need('trial order confirmed', so.state, so.state == 'sale')
    need('trial order VAT 20%', so.order_line.tax_ids.mapped('amount'), so.order_line.tax_ids.mapped('amount') == [20.0])
except Exception as e:  # noqa: BLE001
    need('trial order confirmed', repr(e)[:200], False)
E.cr.rollback()
print('SMOKE ' + json.dumps(res, ensure_ascii=False, default=str))
print('SMOKE OK' if not bad else 'SMOKE FAIL ' + ','.join(bad))
