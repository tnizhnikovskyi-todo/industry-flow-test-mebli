# td_mebli_shopfloor — міст до Shop Floor (Enterprise)

**Статус: не перевірено на EE** (ВП-4: доступу до Odoo 19 Enterprise немає). Код написано за `tr/ee-bridges.md`;
поля й методи моделей EE — припущення, їх перевіряє тест `tests/test_ee_bridge.py`, який запускається лише на EE
(на CE модуль не встановлюється, AC-130).

- `depends`: `td_mebli_shop`, `mrp_workorder`; `auto_install: True` — ставиться сам, коли в базі EE є обидва модулі.
- AC: AC-126 (F-32).
