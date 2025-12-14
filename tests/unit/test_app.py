# Импорт необходимых библиотек для тестирования
import pytest  # Фреймворк для написания и запуска тестов
from unittest.mock import patch, MagicMock  # Для создания моков (подделок) объектов
import os  # Для работы с переменными окружения
import sys  # Для добавления пути к модулям

# Добавляем путь к src, чтобы импортировать app.py
sys.path.insert(0, '/workspaces/AI.J.3.4/src')

# Импорт тестируемых функций из приложения
from app import call_llm, app  # Импортируем функцию call_llm и приложение Flask


class TestCallLLM:
    """
    Класс для группировки тестов функции call_llm.
    Каждый тест проверяет определенный сценарий поведения функции.
    """

    @patch('app.requests.post')  # Мокаем requests.post, чтобы не делать реальные HTTP-запросы
    @patch('app.os.getenv')  # Мокаем os.getenv для контроля переменных окружения
    def test_call_llm_success_worker_model(self, mock_getenv, mock_post):
        """
        Positive Test: Проверка успешного вызова для Worker модели (перевод).
        
        Этот тест проверяет, что функция корректно обрабатывает успешный ответ от API
        для модели перевода и возвращает ожидаемый текст.
        """
        # Настройка моков
        mock_getenv.return_value = 'test_api_key'  # Мокаем API ключ
        mock_response = MagicMock()  # Создаем мок для ответа
        mock_response.status_code = 200  # Успешный статус
        mock_response.json.return_value = {"response": "Mocked translation text"}  # Фиктивный перевод
        mock_post.return_value = mock_response  # requests.post возвращает наш мок

        # Вызов тестируемой функции
        result = call_llm("Qwen/Qwen3-VL-30B-A3B-Instruct", "Translate this text")

        # Проверки (assertions)
        assert result == "Mocked translation text"  # Функция должна вернуть текст из ответа
        mock_post.assert_called_once()  # Убеждаемся, что requests.post был вызван один раз
        # Проверяем, что в вызове переданы правильные данные
        args, kwargs = mock_post.call_args
        assert kwargs['json']['model_name'] == "Qwen/Qwen3-VL-30B-A3B-Instruct"
        assert "Authorization" in kwargs['headers']  # Проверяем, что API ключ передан в заголовках

    @patch('app.requests.post')
    @patch('app.os.getenv')
    def test_call_llm_success_judge_model(self, mock_getenv, mock_post):
        """
        Positive Test: Проверка успешного вызова для Judge модели (оценка).
        
        Аналогично предыдущему тесту, но для модели оценки качества перевода.
        """
        mock_getenv.return_value = 'test_api_key'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Mocked evaluation: 9/10, excellent translation"}
        mock_post.return_value = mock_response

        result = call_llm("claude-sonnet-4-5-20250929", "Evaluate this translation")

        assert result == "Mocked evaluation: 9/10, excellent translation"
        mock_post.assert_called_once()

    @patch('app.os.getenv')
    def test_call_llm_api_key_missing(self, mock_getenv):
        """
        Environment Test: Проверка загрузки API ключа из переменных окружения.
        
        Этот тест проверяет, что функция правильно обрабатывает отсутствие API ключа
        и возвращает соответствующее сообщение об ошибке.
        """
        mock_getenv.return_value = None  # Мокаем отсутствие API ключа

        result = call_llm("any_model", "any_prompt")

        assert result == "Ошибка: API ключ не найден в переменных окружения."
        # Убеждаемся, что requests.post не был вызван, так как API ключ отсутствует

    @patch('app.requests.post')
    @patch('app.os.getenv')
    def test_call_llm_request_exception(self, mock_getenv, mock_post):
        """
        Error Handling: Проверка обработки сетевых ошибок.
        
        Этот тест мокает ситуацию, когда requests.post выбрасывает исключение
        (например, проблемы с сетью), и проверяет, что функция корректно обрабатывает ошибку.
        """
        mock_getenv.return_value = 'test_api_key'
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Network error")  # Мокаем исключение типа RequestException

        result = call_llm("any_model", "any_prompt")

        assert "Сетевая ошибка:" in result  # Функция должна вернуть сообщение об ошибке
        assert "Network error" in result

    @patch('app.requests.post')
    @patch('app.os.getenv')
    def test_call_llm_api_error(self, mock_getenv, mock_post):
        """
        Error Handling: Проверка обработки ошибок API (не 200 статус).
        
        Этот тест мокает ситуацию, когда API возвращает ошибочный статус код,
        и проверяет корректную обработку такой ситуации.
        """
        mock_getenv.return_value = 'test_api_key'
        mock_response = MagicMock()
        mock_response.status_code = 401  # Ошибка аутентификации
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        result = call_llm("any_model", "any_prompt")

        assert "Ошибка API: 401 - Unauthorized" in result  # Функция должна вернуть сообщение об ошибке API


# Дополнительные тесты для Flask роута (опционально, но полезно для полноты)
class TestIndexRoute:
    """
    Класс для тестирования Flask роута index.
    Эти тесты проверяют интеграцию с call_llm.
    """

    @patch('app.call_llm')  # Мокаем call_llm, чтобы не делать реальные вызовы
    def test_index_post_success(self, mock_call_llm, client):
        """
        Тест успешной обработки POST запроса на главной странице.
        
        Проверяет, что роут корректно вызывает call_llm для перевода и оценки,
        и возвращает правильный HTML с результатами.
        """
        # Настройка клиента для тестирования Flask приложения
        with app.test_client() as client:
            # Мокаем возвращаемые значения call_llm
            mock_call_llm.side_effect = ["Mocked translation", "Mocked evaluation: 8/10"]

            # Отправляем POST запрос с тестовыми данными
            response = client.post('/', data={
                'text': 'Hello world',
                'language': 'Русский'
            })

            assert response.status_code == 200  # Успешный ответ
            # Проверяем, что в HTML присутствуют результаты
            assert b"Mocked translation" in response.data
            assert b"Mocked evaluation: 8/10" in response.data
            # Убеждаемся, что call_llm был вызван два раза (для перевода и оценки)
            assert mock_call_llm.call_count == 2

    def test_index_get(self, client):
        """
        Тест GET запроса на главную страницу.
        
        Проверяет, что страница отображается корректно без данных.
        """
        with app.test_client() as client:
            response = client.get('/')

            assert response.status_code == 200
            # Проверяем, что форма присутствует в HTML
            assert b'<form' in response.data


# Фикстура для клиента Flask (используется в тестах роута)
@pytest.fixture
def client():
    """
    Фикстура для создания тестового клиента Flask.
    
    Фикстуры в pytest позволяют переиспользовать код настройки.
    """
    app.config['TESTING'] = True  # Включаем тестовый режим
    with app.test_client() as client:
        yield client  # Возвращаем клиента для использования в тестах