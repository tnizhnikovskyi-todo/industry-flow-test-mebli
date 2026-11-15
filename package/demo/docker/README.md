# Локальний стенд у Docker (ручний тест власника)

Odoo 19 CE і PostgreSQL 16 у Docker; модулі `td_mebli_*` підключаються з `package/addons/` цього репо (лише читання).

## Запуск
1. Гілка з модулями: `git checkout flow/A-12-2-test` (або `main` після мерджу PR #26).
2. З теки `package/demo/docker/`: `docker compose up -d`, далі відкрити http://localhost:8069/web/database/manager.
3. **Відновити демо-базу** (Restore Database): бекап стенда (у git не зберігається — 0.4.0; взяти в сесії, що піднімала стенд, або перезібрати скриптами A-15) (бекап стенда A-15: 124 замовлення, 110 MO, 49 закупівель); ім'я бази, напр. `mebli`; «This database is a copy» — так. Master password за замовчуванням образу — `admin`, якщо попросить створити — задайте свій.
4. Увійти: логіни `<роль>@demo-fabryka.example`, пароль `demo-local` — salon (менеджер салону), measure (замірник), tech (технолог), chief (цех), store (комірник), fin (фінансист), owner (директор), fitter (бригадир), tablet (кіоск).

Альтернатива без бекапу — чиста база з модулями: створити базу в менеджері й встановити `td_mebli_demo` (тягне коробку B); без демо-документів, лише довідники.

## Примітки
- Образ закріплено на `odoo:19.0-20261112`, не плаваючий `odoo:19.0`: бекап знято на збірці від 10.11.2026, а старіший локальний образ дає помилки подань (`"hr.employee"."version_revision" field is undefined`). Якщо базу вже відновили на старому образі: `docker compose pull`, `docker compose stop odoo`, `docker compose run --rm odoo odoo -d mebli -u all --stop-after-init --db_host=db --db_user=odoo --db_password=odoo --addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons`, `docker compose up -d`.
- Друк PDF: якщо стилі не підтягуються — Налаштування → Технічне → Системні параметри: `report.url` = `http://localhost:8069`.
- Бекап містить лише вигадані дані (DATA_POLICY). Не підключати до продової пошти: вихідних поштових серверів у базі немає.
- Enterprise — не перевірено; мости EE у CE не встановлюються.
