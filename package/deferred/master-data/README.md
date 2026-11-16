# Відкладені шаблони майстер-даних (A-13-5)

Відкладено рішенням власника 2026-11-16 (обмін з BAS/BAF поза збіркою; AI-37). Ці файли не входять у `package/master-data/` і порядок
імпорту (25 кроків); до відкладення були кроками 26–28 (`td_mebli_migration`, модуль `td_mebli_bas`, VP-04 = `true`).

| Файл | Модель (поле) | Рядків | Було після |
|---|---|---|---|
| `td/19b_res.partner.csv` | `res.partner` (`td_bas_code`) | 2 | `02` |
| `td/20b_product.product.csv` | `product.product` (`td_bas_code`) | 2 | `05` |
| `td/21b_hr.employee.csv` | `hr.employee` (`td_bas_code`) | 2 | `13` |

Повернення — разом з модулем `td_mebli_bas` (див. `package/deferred/README.md`).
