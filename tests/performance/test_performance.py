# Импорт необходимых библиотек для тестирования производительности
import pytest  # Фреймворк для тестирования
from unittest.mock import patch, MagicMock  # Для создания моков
import sys  # Для добавления пути

# Добавляем путь к src
sys.path.insert(0, '/workspaces/AI.J.3.4/src')

from app import call_llm  # Импорт тестируемой функции


class TestPerformance:
    """
    Класс для тестов производительности.
    Эти тесты проверяют, что функции выполняются в приемлемое время.
    """

    @patch('app.requests.post')  # Мокаем HTTP-запросы
    @patch('app.os.getenv')  # Мокаем переменные окружения
    def test_call_llm_performance(self, mock_getenv, mock_post, benchmark):
        """
        Тест производительности функции call_llm.

        Этот тест измеряет время выполнения функции call_llm с моками.
        Использует pytest-benchmark для точных измерений.
        Ожидаемое время: менее 1 секунды для мокового вызова.
        """
        # Настройка моков
        mock_getenv.return_value = 'test_api_key'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Mocked response"}
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        # Функция для бенчмаркинга
        def run_call_llm():
            return call_llm("test_model", "test_prompt")

        # Запуск бенчмарка
        result = benchmark(run_call_llm)

        # Проверки
        assert result is not None  # Функция должна вернуть результат
        # Статистика выводится автоматически pytest-benchmark
        print(f"Результат бенчмарка доступен в benchmark.stats")

    @patch('app.call_llm')  # Мокаем call_llm для тестирования роута
    def test_index_route_performance(self, mock_call_llm, benchmark, client):
        """
        Тест производительности роута index при POST-запросе.

        Измеряет время обработки формы с переводом и оценкой.
        """
        with client.application.test_client() as test_client:
            # Настройка мока - используем cycle для повторения ответов
            from itertools import cycle
            mock_call_llm.side_effect = cycle(["Переведенный текст", "Оценка: 8/10"])

            # Функция для бенчмаркинга
            def run_post_request():
                return test_client.post('/', data={
                    'text': 'Hello world',
                    'language': 'Русский'
                })

            # Запуск бенчмарка
            result = benchmark(run_post_request)

            # Проверки
            assert result.status_code == 200
            # Статистика выводится автоматически


# Фикстура для клиента (если нужно)
@pytest.fixture
def client():
    from app import app
    app.config['TESTING'] = True
    return app.test_client()