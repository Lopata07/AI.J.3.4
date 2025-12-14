const { defineConfig } = require('cypress');

module.exports = defineConfig({
  e2e: {
    specPattern: 'tests/ui/cypress/e2e/**/*.cy.js', // Путь к тестам
    supportFile: false, // Отключаем support файл, если не нужен
  },
});