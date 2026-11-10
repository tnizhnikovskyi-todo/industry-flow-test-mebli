// SC-04 ROLE-05 Комірник: залишки, обрізки й нестача під замовлення (scenarios.md, кроки 1-5).
export default async ({ page, goto, step, click, seeTitle, seeText, pause }) => {
  // Обхід дефекту оболонки: підпис відео (#cap, position:fixed) перекриває кнопки дій унизу сторінки й перехоплює клік
  // (Playwright: «#cap intercepts pointer events»). Кнопки дій натискаються клавішею Enter за тим самим data-testid;
  // рядки списків і картки kanban — click. Очікування не змінено.
  const press = (tid) => page.getByTestId(tid).press('Enter', { timeout: 5000 });
  await goto('S-08');
  await step('SC-04.1', 'Переглядає потребу в матеріалах під замовлення дня');
  await seeTitle('Потреба в матеріалах'); await pause(1200);
  await step('SC-04.2', 'Резервує плиту, кромку й фурнітуру під замовлення');
  await click('row-n01'); await press('need-reserve'); await click('row-n02'); await press('need-reserve'); await click('row-n03'); await press('need-reserve');
  await seeTitle('Потреба в матеріалах'); await pause();
  await step('SC-04.3', 'Бачить нестачу фурнітури і затриману поставку, передає нестачу в закупівлю');
  await press('need-to-purchase'); await seeTitle('Потреба в матеріалах'); await pause();
  await step('SC-04.4', 'Приймає ділові обрізки після розкрою як залишок із розмірами');
  await press('nav-S-09'); await seeTitle('Залишки й ділові обрізки'); await press('offcut-add'); await pause();
  await step('SC-04.5', 'Перевіряє залишки плит і обрізків за декором');
  await seeTitle('Залишки й ділові обрізки');
  // критерій: обрізок потрібного розміру видно на складі з декором; нестача під замовлення видна закупівлі
  await seeText('1180×620 мм'); await press('nav-S-08'); await seeText('передано в закупівлю'); await pause(1500);
};
