// SC-02 ROLE-01 Конструктор-технолог: від проєкту до карти розкрою (scenarios.md, кроки 1-5).
export default async ({ page, goto, step, click, seeTitle, seeState, seeText, pause }) => {
  // Обхід дефекту оболонки: підпис відео (#cap, position:fixed) перекриває кнопки дій унизу сторінки й перехоплює клік
  // (Playwright: «#cap intercepts pointer events»). Кнопки дій натискаються клавішею Enter за тим самим data-testid;
  // рядки списків і картки kanban — click. Очікування не змінено.
  const press = (tid) => page.getByTestId(tid).press('Enter', { timeout: 5000 });
  await goto('S-04');
  await step('SC-02.1', 'Відкриває нові замовлення, передані у виробництво');
  await seeTitle('Розкрій замовлень'); await pause(1200);
  await step('SC-02.2', 'Завантажує специфікацію й карту присадок виробу з програми проєктування');
  await click('row-sp13'); await seeTitle('Специфікація виробу'); await press('spec-load'); await seeState('завантажено'); await pause();
  await step('SC-02.3', 'Звіряє деталі, декор і кромку та затверджує специфікацію');
  await press('spec-approve'); await seeTitle('Специфікація виробу'); await seeState('затверджено'); await pause();
  await step('SC-02.4', 'Передає деталі кількох замовлень на розкрій');
  await press('nav-S-04'); await seeTitle('Розкрій замовлень'); await press('cut-send'); await pause();
  await step('SC-02.5', 'Приймає карту розкрою з відходами і перевіряє відсоток відходів');
  await press('cut-accept'); await seeTitle('Розкрій замовлень');
  // критерій: специфікація без ручного введення деталей, карта розкрою відкривається з рядка замовлення
  await seeText('Демо-Карта розкрою 0013'); await click('row-sp13'); await seeTitle('Специфікація виробу'); await seeText('Демо-Карта розкрою 0013'); await pause(1500);
};
