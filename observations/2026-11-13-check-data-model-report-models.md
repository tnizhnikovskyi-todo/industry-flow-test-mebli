# Зауваження: check_data_model.py рахує моделі QWeb-звітів як td_-моделі (2026-11-13)

- Крок: A-11 (наряд `tests/naryad/A-11.yaml`); скрипт `flow-research/skills/prototype-builder/scripts/check_data_model.py`.
- Що очікували: абстрактні моделі значень звіту `report.<модуль>.<шаблон>` (стандартний механізм Odoo `_get_report_values`) не вимагають рядка в таблиці моделі даних.
- Що вийшло: DM-table = FAIL на `report.td_mebli_sale.report_contract`; рядок у таблиці моделі даних FAIL не прибирає.
- Пропозиція: виключати моделі з префіксом `report.` (AbstractModel) або приймати для них рядок таблиці.
