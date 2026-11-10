// SC-05 ROLE-06 Фінансист: маржа замовлень за курсом і фактична собівартість (scenarios.md, кроки 1-5).
export default async ({ page, goto, step, click, seeTitle, seeText, pause }) => {
  // Обхід дефекту оболонки: підпис відео (#cap, position:fixed) перекриває кнопки дій унизу сторінки й перехоплює клік
  // (Playwright: «#cap intercepts pointer events»). Кнопки дій натискаються клавішею Enter за тим самим data-testid;
  // рядки списків і картки kanban — click. Очікування не змінено.
  const press = (tid) => page.getByTestId(tid).press('Enter', { timeout: 5000 });
  await goto('S-11');
  await step('SC-05.1', 'Відкриває план і факт собівартості відкритих замовлень');
  await seeTitle('Собівартість замовлень'); await pause(1200);
  await step('SC-05.2', 'Перераховує собівартість і маржу за поточним курсом євро');
  await press('cost-recalc-rate'); await seeTitle('Собівартість замовлень'); await pause();
  await step('SC-05.3', 'Відкриває замовлення з найбільшим падінням маржі');
  await click('row-o07'); await seeTitle('Замовлення клієнта'); await pause(1200);
  await step('SC-05.4', 'Перевіряє, що матеріали й роботи списані на конкретне замовлення');
  await press('nav-S-11'); await seeTitle('Собівартість замовлень'); await pause();
  await step('SC-05.5', 'Переглядає відхилення факту від плану по закритих замовленнях');
  await seeTitle('Собівартість замовлень');
  // критерій: для будь-якого замовлення видно план, факт і маржу без вивантаження в таблицю
  await seeText('Планова собівартість'); await seeText('Фактична собівартість'); await seeText('Маржа, грн'); await pause(1500);
};
