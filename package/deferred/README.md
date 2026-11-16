# Відкладене зі збірки пакета mebli

**Відкладено рішенням власника 2026-11-16:** «Приберіть зі збірки поки все, що пов'язано з BAS» — обмін з BAS/BAF не входить у
збірку до окремого рішення (`flow/decisions.md` рядок 53; рішення AI — AI-37, AI-38 у `docs/industries/mebli/research/AI-DECISIONS.md`).

Каталог `package/deferred/` **не входить** в `addons_path`, конфіг-пакет (`package/config/`), порядок імпорту майстер-даних
(`package/master-data/`), демо-стенд (A-15), тури (A-16) і посібники (A-16b). Код не видалено — лише перенесено (A-11-fix5,
A-12-6, A-13-5).

| Що | Звідки | Куди | Примітка |
|---|---|---|---|
| модуль `td_mebli_bas` 19.0.1.1.3 (обмін з BAS/BAF: канали, пакети, журнал, коди BAS, «Передати в BAS», статус «Передано в BAS») | `package/addons/td_mebli_bas/` | `td_mebli_bas/` | AC-039…AC-042, AC-109 |
| модуль `td_mebli_attendance` 19.0.1.1.1 («Табель для BAS (імітація)») | `package/addons/td_mebli_attendance/` | `td_mebli_attendance/` | AC-078; кіоск за PIN — стандарт `hr_attendance` лишається (AC-077) |
| конвертор `convert_bas.py` і його тест | `package/addons/td_mebli_migration/scripts/`, `tests/test_migration.py` | `td_mebli_migration/scripts/convert_bas.py`, `td_mebli_migration/tests/test_convert_bas.py` | AC-089 (частина BAS) |
| шаблони майстер-даних `td/19b_res.partner.csv`, `td/20b_product.product.csv`, `td/21b_hr.employee.csv` (поле `td_bas_code`) | `package/master-data/td/` | `master-data/td/` | кроки імпорту 26–28 прибрано |
| параметр VP-04 «Обмін з BAS/BAF» | `package/config/`, `package/templates/answers.yaml` | лишається в схемі з `default: false`, позначка «відкладено»; `true` зупиняє застосування (PF-10) | — |

## Існуючі бази, де модулі вже встановлено (AI-38)
1. Поки код ще доступний (додати `package/deferred` в `addons_path`), за потреби вивантажити коди BAS (контрагенти, товари, працівники).
2. «Застосунки» → `td_mebli_bas` → «Видалити»; потім `td_mebli_attendance` → «Видалити» (Odoo прибирає поля, моделі, меню, права).
3. Лише після цього оновлювати модулі `td_*` на версію без них. Якщо каталог зникне раніше — модулі стануть «uninstallable», а їхні подання й колонки лишаться в базі.

## Повернення
Перенести каталоги назад у `package/addons/`, `convert_bas.py` — у `td_mebli_migration/scripts/`, тест — у `TestMigrationConverters`, шаблони — у
`package/master-data/td/`; повернути рядки «Модулі до установки», кроки імпорту 26–28, `when` VP-04; прогнати гейти A-14. Залежності:
`td_mebli_bas` → `td_mebli_install`, `td_mebli_attendance`, `account`; `td_mebli_install._td_cancel_pay_marks` (хук AC-042) лишився в збірці.
