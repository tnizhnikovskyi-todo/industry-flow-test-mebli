// SC-06 ROLE-08 Керівник: огляд замовлень, цін сировини й собівартості (scenarios.md, кроки 1-5).
export default async ({ page, goto, step, click, seeTitle, seeText, pause }) => {
  // Обхід дефекту оболонки: підпис відео (#cap, position:fixed) перекриває кнопки дій унизу сторінки й перехоплює клік
  // (Playwright: «#cap intercepts pointer events»). Кнопки дій натискаються клавішею Enter за тим самим data-testid;
  // рядки списків і картки kanban — click. Очікування не змінено.
  const press = (tid) => page.getByTestId(tid).press('Enter', { timeout: 5000 });
  await goto('S-05');
  await step('SC-06.1', 'Переглядає замовлення за етапами і затримки');
  await seeTitle('Дошка замовлень'); await pause(1200);
  await step('SC-06.2', 'Відкриває специфікацію замовлення — та сама для продажу, розкрою й обліку');
  await press('nav-S-03'); await seeTitle('Специфікація виробу'); await pause();
  await step('SC-06.3', 'Переглядає динаміку цін закупівлі плит і пиломатеріалів за постачальниками');
  await press('nav-S-10'); await seeTitle('Ціни закупівлі сировини'); await pause();
  await step('SC-06.4', 'Переглядає маржу й відхилення собівартості по замовленнях');
  await press('nav-S-11'); await seeTitle('Собівартість замовлень'); await pause();
  await step('SC-06.5', 'Порівнює ціни сировини за попередній період');
  await press('nav-S-10'); await seeTitle('Ціни закупівлі сировини'); await press('price-compare');
  // критерій: стан замовлень, ціни сировини й маржа — без запиту звітів у відділів
  await seeText('Зміна, %'); await pause(1500);
};
