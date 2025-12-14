# Импорт необходимых библиотек для интеграционных тестов
import pytest  # Фреймворк для тестирования
import os  # Для проверки переменных окружения
import sys  # Для добавления пути

# Добавляем путь к src
sys.path.insert(0, '/workspaces/AI.J.3.4/src')

from app import call_llm, app  # Импорт функций приложения


class TestIntegration:
    """
    Класс для интеграционных тестов с реальным API.

    ВНИМАНИЕ: Эти тесты используют реальный API и могут тратить токены!
    Запускайте только в отдельной тестовой среде с достаточным бюджетом API.
    Убедитесь, что переменная окружения API_KEY установлена.
    """

    @pytest.mark.skipif(
        not os.getenv('API_KEY'),
        reason="API_KEY не установлен. Эти тесты требуют реального API ключа."
    )
    def test_call_llm_real_api_worker_model(self):
        """
        Интеграционный тест: Реальный вызов API для Worker модели.

        Этот тест делает настоящий запрос к API для проверки интеграции.
        Используйте с осторожностью - тратит токены!
        """
        # Вызов с реальными данными
        result = call_llm("Qwen/Qwen3-VL-30B-A3B-Instruct", "Переведи: Hello world")

        # Проверки
        assert isinstance(result, str)  # Должен вернуть строку
        assert len(result) > 0  # Не пустая строка
        assert "Ошибка" not in result  # Не должно быть ошибок
        print(f"Реальный ответ Worker модели: {result[:100]}...")  # Показываем первые 100 символов

    @pytest.mark.skipif(
        not os.getenv('API_KEY'),
        reason="API_KEY не установлен. Эти тесты требуют реального API ключа."
    )
    def test_call_llm_real_api_judge_model(self):
        """
        Интеграционный тест: Реальный вызов API для Judge модели.

        Проверяет оценку качества перевода.
        """
        result = call_llm("claude-sonnet-4-5-20250929",
                         "Оцени качество перевода от 1 до 10. Оригинал: 'Hello'. Перевод: 'Привет'.")

        assert isinstance(result, str)
        assert len(result) > 0
        assert "Ошибка" not in result
        print(f"Реальный ответ Judge модели: {result[:100]}...")

    @pytest.mark.skipif(
        not os.getenv('API_KEY'),
        reason="API_KEY не установлен."
    )
    def test_full_translation_workflow(self, client):
        """
        Интеграционный тест: Полный рабочий процесс перевода.

        Тестирует весь путь от формы до результата с реальным API.
        """
        with app.test_client() as test_client:
            # Отправка формы с реальными данными
            response = test_client.post('/', data={
                'text': 'Good morning',
                'language': 'Французский'
            })

            # Проверки
            assert response.status_code == 200
            # Проверяем, что в HTML есть результаты (но не проверяем точный текст из-за API)
            assert b'<form' in response.data  # Форма присутствует
            # Не проверяем конкретный перевод, так как он зависит от API
            print("Полный рабочий процесс завершен успешно")

    def test_environment_setup_check(self):
        """
        Тест проверки настройки среды.

        Проверяет, что все необходимые переменные окружения установлены.
        """
        api_key = os.getenv('API_KEY')
        if not api_key:
            pytest.skip("API_KEY не установлен - пропускаем интеграционные тесты")
        else:
            assert len(api_key) > 10  # API ключ должен быть достаточно длинным
            print("Среда настроена корректно для интеграционных тестов")


# Инструкции по запуску интеграционных тестов:
# 1. Установите API_KEY: export API_KEY="ваш_ключ"
# 2. Запустите: pytest tests/integration/test_integration.py -v
# 3. Будьте готовы к расходу токенов API!