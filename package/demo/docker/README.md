# Локальний стенд у Docker (ручний тест власника)

Odoo 19 CE і PostgreSQL 16 у Docker; модулі `td_mebli_*` підключаються з `package/addons/` цього репо (лише читання).

## Запуск
Бекапу бази стенда в git немає (0.4.0, R-22: бінарники баз у репо не кладемо, `package/demo/.gitignore`). Демо-базу піднімають скриптами A-15.

**Варіант 1 — локально, без Docker (як A-15/A-16; потрібні Odoo 19 і PostgreSQL 16, `tools/odoo/env.local.sh`):**
```
DEMO_REPORT_URL=http://127.0.0.1:8079 package/demo/up.sh demo-mebli-pkg-a ce   # чиста база + модулі + конфіг + A-13 + демо-шар + знімок (~13 хв)
tools/odoo/serve.sh demo-mebli-pkg-a 8079                                      # http://127.0.0.1:8079
package/demo/reset.sh demo-mebli-pkg-a ce                                      # повернути стенд до знімка
```

**Варіант 2 — Docker (лише довідники й демо-каталог, без історії документів):**
1. Гілка з модулями пакета (гілка кроку A-15 або `main` після злиття).
2. З теки `package/demo/docker/`: `docker compose up -d`, далі http://localhost:8069/web/database/manager.
3. **Чиста база** (Create Database, мова — українська, без демо-даних Odoo), потім у «Додатках» встановити `td_mebli_demo` (тягне модулі коробки B,
   `td_home_menu`, `td_support`, `td_knowledge` ставляться окремо з «Додатків»). Документи й історію (124 замовлення, 110 MO…) дає
   `package/demo/data/seed_demo.py` (`seed_showcase` модуля `td_mebli_demo`) — він запускається скриптом `up.sh` (варіант 1); у Docker без нього —
   лише довідники.
4. Увійти: адміністратор бази або демо-ролі, створені `td_mebli_demo` (паролі задає `up.sh` змінною `DEMO_USERS_PASSWORD`; у варіанті 2 —
   задати в «Користувачах»).

## Примітки
- Образ закріплено на `odoo:19.0-20261112`, не плаваючий `odoo:19.0`: старіший локальний образ дає помилки подань (`"hr.employee"."version_revision" field is undefined`). Якщо базу створили на старому образі: `docker compose pull`, `docker compose stop odoo`, `docker compose run --rm odoo odoo -d mebli -u all --stop-after-init --db_host=db --db_user=odoo --db_password=odoo --addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons`, `docker compose up -d`.
- Друк PDF: якщо стилі не підтягуються — Налаштування → Технічне → Системні параметри: `report.url` = `http://localhost:8069`.
- Демо-дані лише вигадані (DATA_POLICY). Не підключати до продової пошти: вихідних поштових серверів у базі немає.
- Enterprise — не перевірено; мости EE у CE не встановлюються.
