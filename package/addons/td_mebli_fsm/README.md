# td_mebli_fsm — міст до Field Service (Enterprise)

**Статус: не перевірено на EE** (ВП-4: доступу до Odoo 19 Enterprise немає). Код написано за `tr/ee-bridges.md`;
поля й методи моделей EE — припущення, їх перевіряє тест `tests/test_ee_bridge.py`, який запускається лише на EE
(на CE модуль не встановлюється, AC-130).

- `depends`: `td_mebli_install`, `industry_fsm`; `auto_install: True` — ставиться сам, коли в базі EE є обидва модулі.
- AC: AC-128 (F-38).
