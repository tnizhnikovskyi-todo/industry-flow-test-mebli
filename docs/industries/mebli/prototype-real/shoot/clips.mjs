// Живі записи зрізу A-21 (спроба 2). ЗРАЗОК: кліп D_sample (~15 с) — менеджер продажу відкриває замовлення «кухня + шафа-купе»
// і бачить, що закупівля фарбованих фасадів (стандарт: MTO + «Купити», дата — у замовленні на купівлю) зсуває дату (S-02; F-23, F-31, NG-01; SALES §6 сцена 4; PAIN-16). Титри — лише події (бренд — A-21c).
import { clip, title, titleOff, hold, zoom, zoomOff, settle, press, glide, focus, scrollTo, fact } from './rec_lib.mjs';
const ORDER = process.env.ORDER_ID || '123';
export const PASS1 = [];
export const PASS2 = ['D_sample'];
export const CLIPS = {
    async D_sample() {
        return clip('D_sample', { role: 'salon', url: `/odoo/action-sale.action_orders/${ORDER}` }, async (c) => {
            await settle(c.page, 900);
            // планова маржа замовлення (sale_margin) — на вкладці рядків, до переходу на закупівлі
            await fact(c.page, 'D_sample', 'margin_percent', '.o_field_widget[name=margin_percent]', { re: '[\\d,.]+\\s*%' });
            c.mark();
            await title(c, 'Менеджер продажу', 'Обіцяли клієнту дату — система **вже бачить**, що її зірве');
            await hold(c, 1500);
            await focus(c, '.td_date_alert');
            await glide(c, 520, 120, 600);
            await hold(c, 2000);
            await zoom(c, '.o_group .o_field_widget[name=td_forecast_date]', 1.7, 900);
            await focus(c, '.o_group .o_field_widget[name=td_forecast_date]');
            await hold(c, 1900);
            await zoomOff(c);
            await titleOff(c);
            // закупівлі створив стандарт (MTO + «Купити»); менеджер салону лише читає закупівлі свого замовлення (без групи «Закупівлі»)
            await press(c, c.page.locator('.o_notebook_headers a', { hasText: 'Закупівлі під замовлення' }));
            await scrollTo(c, '.o_data_row.text-danger');
            await title(c, 'Причина зсуву', 'Фасади: дата постачальника в закупівлі — **пізніше на 2 тижні**');
            await zoom(c, '.o_data_row.text-danger', 1.5, 900);
            await focus(c, '.o_data_row.text-danger');
            await hold(c, 3500);
            await zoomOff(c);
            await hold(c, 800);
            await fact(c.page, 'D_sample', 'delay_days', '.o_group .o_field_widget[name=td_delay_days]', { re: '\\d+' });
            await fact(c.page, 'D_sample', 'late_item_ready', '.o_data_row.text-danger td[name=td_date_ready]');
        });
    },
};
