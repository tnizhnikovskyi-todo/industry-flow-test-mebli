// SC-01 ROLE-02 Менеджер продажу: від опцій покупця до монтажу (scenarios.md, кроки 1-6).
// Очікування — детермінований fallback: заголовок екрана S-xx (screens.md), статус при set.state, критерій на останньому кроці.
export default async ({ page, goto, step, click, seeTitle, seeState, seeText, pause }) => {
  // Обхід дефекту оболонки: підпис відео (#cap, position:fixed) перекриває кнопки дій унизу сторінки й перехоплює клік
  // (Playwright: «#cap intercepts pointer events»). Кнопки дій натискаються клавішею Enter за тим самим data-testid;
  // рядки списків і картки kanban — click. Очікування не змінено.
  const press = (tid) => page.getByTestId(tid).press('Enter', { timeout: 5000 });
  await goto('S-01');
  await step('SC-01.1', 'Підбирає з покупцем шафу: розміри, декор, фурнітуру, кромку — ціна перераховується відразу');
  await seeTitle('Підбір виробу з опцій'); await press('opt-add'); await press('price-recalc'); await seeTitle('Підбір виробу з опцій'); await pause(1200);
  await step('SC-01.2', 'Додає виріб у замовлення, бачить суму й дату готовності');
  await press('add-to-order'); await seeTitle('Замовлення клієнта'); await seeState('погоджено'); await pause(1200);
  await step('SC-01.3', 'Передає замовлення у виробництво зі специфікацією з обраних опцій');
  await press('order-to-production'); await seeTitle('Замовлення клієнта'); await seeState('у виробництві'); await pause();
  await step('SC-01.4', 'Планує доставку й монтаж на дату після готовності');
  await press('order-plan-delivery'); await seeTitle('Доставка й монтаж'); await press('delivery-plan'); await seeTitle('Доставка й монтаж'); await pause();
  await step('SC-01.5', 'Надсилає покупцю посилання на статус замовлення');
  await press('nav-S-13'); await seeTitle('Статус замовлення для покупця'); await press('link-send'); await pause();
  await step('SC-01.6', 'Переглядає графік доставок і монтажів на завтра');
  await press('nav-S-12'); await seeTitle('Доставка й монтаж');
  // критерій: від підбору опцій до запланованого монтажу — в одному місці; монтаж замовлення в графіку
  await seeText('Демо-Замовлення 0001'); await pause(1500);
};
