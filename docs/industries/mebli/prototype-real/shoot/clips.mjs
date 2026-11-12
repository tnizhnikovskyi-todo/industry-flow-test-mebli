// Живі записи зрізу A-21 (спроба 2). ЗРАЗОК: кліп D_sample (~15 с) — менеджер продажу відкриває замовлення «кухня + шафа-купе»
// і бачить, що замовні фасади зсувають дату (S-02; F-23, F-31, NG-01; SALES §6 сцена 4; PAIN-16). Титри — лише події (бренд — A-21c).
import { clip, title, titleOff, hold, zoom, zoomOff, settle, press, glide, focus, scrollTo, fact } from './rec_lib.mjs';
const ORDER = process.env.ORDER_ID || '123';
export const PASS1 = [];
export const PASS2 = ['D_sample'];
export const CLIPS = {
    async D_sample() {
        return clip('D_sample', { role: 'salon', url: `/odoo/action-sale.action_orders/${ORDER}` }, async (c) => {
            await settle(c.page, 900); c.mark();
            await title(c, 'Менеджер продажу', 'Обіцяли клієнту дату — система **вже бачить**, що її зірве');
            await hold(c, 1800);
            await focus(c, '.td_date_alert');
            await glide(c, 520, 120, 700);
            await hold(c, 1500);
            await zoom(c, '.o_group .o_field_widget[name=td_forecast_date]', 1.7, 900);
            await focus(c, '.o_group .o_field_widget[name=td_forecast_date]');
            await hold(c, 2400);
            await zoomOff(c);
            await titleOff(c);
            await settle(c.page, 300);
            await press(c, c.page.locator('.o_notebook_headers a', { hasText: 'Замовні позиції' }));
            await scrollTo(c, '.o_data_row.text-danger');
            await title(c, 'Причина зсуву', 'Фарбовані фасади від постачальника — **пізніше на 2 тижні**');
            await zoom(c, '.o_data_row.text-danger', 1.5, 900);
            await focus(c, '.o_data_row.text-danger');
            await hold(c, 3200);
            await zoomOff(c);
            await hold(c, 1200);
            await fact(c.page, 'D_sample', 'delay_days', '.o_group .o_field_widget[name=td_delay_days]', { re: '\\d+' });
        });
    },
};
