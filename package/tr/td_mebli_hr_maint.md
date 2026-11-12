# `td_mebli_maint` і `td_mebli_attendance` — обслуговування верстатів і табель цеху

**Призначення.** F-60 (обслуговування верстатів у завантаженні), F-61 (кіоск відвідувань і табель для BAS). Обидва — стандарт CE + тонкий `td_`-шар (README зрізу §3б). Коробка A. AC: AC-076…AC-078.
**Звірка:** `addons/maintenance/models/maintenance.py:111` (`maintenance.equipment`), `:182` (`maintenance.request`), `:215` (`equipment_id`), `:227` (`maintenance_type`), `:228` (`schedule_date`), `:244` (`recurring_maintenance`); модуль `mrp_maintenance` (зв'язок обладнання з робочим центром) у CE 19.0 відсутній (каталогу немає, заглушки теж) — тому зв'язок наш; `addons/mrp/models/mrp_workcenter.py:477` (втрати), `:531` (рядок часу дільниці); `addons/hr_attendance/models/res_company.py:34` (`attendance_kiosk_use_pin`), `addons/hr_attendance/models/hr_attendance.py:28`.

## 1. `td_mebli_maint` — хвиля 2

| Модель / поле | Тип | Звідки | Примітка |
|---|---|---|---|
| `maintenance.equipment.td_workcenter_id` (Дільниця) | m2o `mrp.workcenter` | технолог | `check_company=True` |
| `maintenance.request.td_workcenter_id` | related `equipment_id.td_workcenter_id` | — | — |
| `maintenance.request.td_downtime_id` (Простій) | m2o `mrp.workcenter.productivity`, readonly | запит виду «Корекційний» («Поломка») | рядок втрат дільниці з причиною «Обслуговування» (дані) |
| `maintenance.request.td_downtime_open`, `td_downtime_hours` | boolean / float compute | рядок простою | — |
| `mrp.workcenter.td_equipment_count`, `td_request_open_count` | integer compute | — | смарт-кнопки дільниці |

**Правила.** Запит виду «Корекційний» на верстат дільниці відкриває простій (стандартна модель рядка часу з `loss_id`); закриття запиту (стадія «Виконано») закриває простій. Планове ТО — стандартний `recurring_maintenance`; заплановані запити видно в календарі обслуговування й у завантаженні дільниці як зайняті години (AC-076).

## 2. `td_mebli_attendance` — хвиля 2
Кіоск відвідувань — стандарт (`attendance_kiosk_use_pin` — дані конфіг-пакета, AC-077).
Майстер `td.mebli.timesheet.export` (TransientModel): `date_from`, `date_to` (required), `line_ids` (o2m `td.mebli.timesheet.export.line`: `employee_id`, `days`, `hours`), `file`/`filename` (binary, readonly), `total_hours` (compute). Формування — агрегати `hr.attendance` за період. У зрізі формат — CSV «імітація»; у пакеті формат і транспорт — адаптер `td_mebli_bas` (тип пакета «Табель»), до контракту — CSV: табельний код (зовнішній код BAS працівника), ПІБ, днів, годин (AC-078; ВП-1). Період без відвідувань — попередження «За період немає відвідувань», файл порожній.

## 3. Права
Обслуговування — стандартні групи `maintenance` (майстер цеху — `maintenance.group_equipment_manager` через конфіг-пакет); табель — `group_finance`, `hr_attendance.group_hr_attendance_officer`.
