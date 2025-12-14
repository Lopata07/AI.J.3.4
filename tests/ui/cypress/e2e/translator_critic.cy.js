describe('AI Translator & Critic UI Tests', () => {
  it('Успешный перевод и оценка текста', () => {
    // Посещаем главную страницу приложения
    cy.visit('http://127.0.0.1:5000/');

    // Вводим текст в textarea
    cy.get('textarea').type('Солнце светит.');

    // Выбираем язык перевода из select
    cy.get('select').select('Английский');

    // Нажимаем кнопку "Перевести"
    cy.get('button').contains('Перевести').click();

    // Ожидаем появления текста перевода в блоке результатов
    // Используем cy.contains для проверки асинхронного контента
    cy.contains('The sun is shining.', { timeout: 10000 }).should('be.visible');

    // Нажимаем кнопку "Оценить при помощи LLM-as-a-Judge"
    cy.get('button').contains('Оценить при помощи LLM-as-a-Judge').click();

    // Ожидаем появления текста оценки в блоке оценки
    cy.contains('9/10', { timeout: 10000 }).should('be.visible');
  });
});