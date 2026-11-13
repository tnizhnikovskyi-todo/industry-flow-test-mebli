# Дефекти установки стенда
SHA стенда: b794c20 (`package/` = `1925fb8`)   Інстанс: demo-mebli-pkg-a   Профіль: package/demo/answers.yaml (A, ce)   Код повернення: A-14

## D-01 — модуль — **ЗАКРИТО** (A-11 спроба 6, `tests/reports/A-11-6.md`; `td_mebli_demo` 19.0.1.1.1; перевірено підйомом A-15 спроба 3, `tests/reports/A-15-3.md`)
- Місце: `package/addons/td_mebli_demo/showcase.py:225–227` (`_localize`, виклик із `seed_showcase`, `showcase.py:454`); крок up.sh «демо-документи (seed)» (код 50), після кроків 1–4 (модулі, конфіг A-12, шаблони A-13 — OK).
- Витяг з логу (`odoo-bin shell` < `package/demo/data/seed_demo.py`):
  ```
  File "/home/user/odoo19/delivery/td_mebli_demo/showcase.py", line 454, in seed_showcase
    _localize(env)
  File "/home/user/odoo19/delivery/td_mebli_demo/showcase.py", line 226, in _localize
    tax.with_context(lang='en_US').name = 'VAT 20%'
  File "/home/user/odoo19/src/addons/account/models/account_tax.py", line 249, in _constrains_name
    raise ValidationError(
  odoo.exceptions.ValidationError: Tax names must be unique!
  - VAT 20% in My Company
  ```
- Очікувалось / сталось: демо-шар має ставитися поверх налаштованої бази (модулі + конфіг A-12 + шаблони A-13); `_localize` перейменовує й переводить на 20 % **усі** податки зі ставкою ≠ 0, що розраховано на загальний план рахунків (еталонні демо-бази A-21 — без конфігу), а конфіг A-12 (`data/15_accounting.yaml`, план `ua_psbo`, VP-18) дає кілька податків — назви збігаються, seed падає (і перезаписав би ставки податків конфігу).
- Діагностика (scratch, без коміту): якщо перейменування податків пропустити, `seed_showcase` проходить до кінця на тій самій базі (124 замовлення, 110 MO, 49 закупівель, 123 задачі, 2209 партій) — інших дефектів демо-шару не виявлено.
- Проявляється на профілі: усі, де ставиться демо-шар (`answers.yaml` A; alt-2/alt-3 — B, перевірено лише з `--no-demo`); light (alt-1) — демо-шар не ставиться (залежність `td_mebli_bas`).
