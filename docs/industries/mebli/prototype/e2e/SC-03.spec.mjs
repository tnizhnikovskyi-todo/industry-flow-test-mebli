// SC-03 ROLE-03 Начальник виробництва: зміна з простоєм і рекламацією (scenarios.md, кроки 1-8).
export default async ({ page, goto, step, click, seeTitle, seeState, seeText, pause }) => {
  // Обхід дефекту оболонки: підпис відео (#cap, position:fixed) перекриває кнопки дій унизу сторінки й перехоплює клік
  // (Playwright: «#cap intercepts pointer events»). Кнопки дій натискаються клавішею Enter за тим самим data-testid;
  // рядки списків і картки kanban — click. Очікування не змінено.
  const press = (tid) => page.getByTestId(tid).press('Enter', { timeout: 5000 });
  await goto('S-05');
  await step('SC-03.1', 'Переглядає замовлення за етапами і бачить затримані');
  await seeTitle('Дошка замовлень'); await pause(1200);
  await step('SC-03.2', 'Відкриває виробниче замовлення зі специфікацією і маршрутом дільниць');
  await click('card-mo12'); await seeTitle('Виробниче замовлення'); await pause();
  await step('SC-03.3', 'Запускає замовлення в роботу на першій дільниці');
  await press('mo-start'); await seeTitle('Виробниче замовлення'); await seeState('у роботі'); await pause();
  await step('SC-03.4', 'Фіксує простій дільниці через відключення електроенергії');
  await press('nav-S-07'); await seeTitle('План дільниць'); await click('row-wo12a'); await press('wo-downtime'); await seeTitle('План дільниць'); await pause();
  await step('SC-03.5', 'Переносить робочі завдання на нові терміни');
  await press('wo-move'); await seeTitle('План дільниць'); await pause();
  await step('SC-03.6', 'Бачить нову рекламацію з запитом на повторне виготовлення деталі');
  await press('nav-S-14'); await seeTitle('Рекламації'); await click('card-cl03'); await pause();
  await step('SC-03.7', 'Створює повторне виготовлення деталі в межах виробничого замовлення');
  await press('claim-rework'); await click('card-mo20'); await seeTitle('Виробниче замовлення'); await press('mo-rework'); await seeState('у роботі'); await pause();
  await step('SC-03.8', 'Перевіряє, що всі замовлення дня отримали актуальні етапи');
  await press('nav-S-05'); await seeTitle('Дошка замовлень'); await pause();
  // критерій: повторне виготовлення пов'язане з рекламацією; нові терміни завдань видно в плані
  await click('card-mo20'); await seeText('Демо-Рекламація 0003'); await press('nav-S-07'); await seeText('2026-11-10 18:30'); await pause(1500);
};
