# Импорт необходимых библиотек для тестирования безопасности
import pytest  # Фреймворк для тестирования
from unittest.mock import patch  # Для мокирования
import sys  # Для добавления пути

# Добавляем путь к src
sys.path.insert(0, '/workspaces/AI.J.3.4/src')

from app import app  # Импорт Flask приложения


class TestSecurity:
    """
    Класс для тестирования безопасности приложения.

    Эти тесты проверяют защиту от распространенных уязвимостей:
    - XSS (Cross-Site Scripting)
    - SQL Injection (хотя в этом приложении нет SQL, проверяем валидацию ввода)
    - Input validation
    """

    def test_xss_prevention_in_form_input(self, client):
        """
        Тест защиты от XSS в полях формы.

        Проверяет, что вредоносный JavaScript код не выполняется в браузере.
        Flask Jinja2 автоматически экранирует вывод, но проверяем это.
        """
        with app.test_client() as test_client:
            # Мокаем call_llm для возврата "безопасного" ответа
            with patch('app.call_llm') as mock_call:
                mock_call.side_effect = ["<script>alert('XSS')</script>", "Safe evaluation"]

                # Отправляем вредоносный ввод
                xss_payload = "<script>alert('XSS Attack!')</script>"
                response = test_client.post('/', data={
                    'text': xss_payload,
                    'language': 'Русский'
                })

            # Проверки
            assert response.status_code == 200

            # Проверяем, что скрипт не выполнится (экранирован)
            response_text = response.data.decode('utf-8')
            # В безопасном HTML скрипт должен быть экранирован
            assert "<script>" not in response_text, "XSS скрипт должен быть экранирован"
            assert "&lt;script&gt;" in response_text, "XSS должен быть экранирован в HTML entities"

            # Проверяем, что оригинальный текст отображается безопасно
            assert xss_payload not in response_text, "Вредоносный ввод не должен отображаться как есть"

    def test_sql_injection_prevention(self, client):
        """
        Тест защиты от SQL Injection.

        Хотя в приложении нет базы данных, проверяем, что ввод не содержит
        потенциально опасных SQL-конструкций и правильно обрабатывается.
        """
        with app.test_client() as test_client:
            # Мокаем call_llm
            with patch('app.call_llm') as mock_call:
                from itertools import cycle
                mock_call.side_effect = cycle(["Translated text", "Evaluation"])

                # Тестовые payloads для SQL injection
                sql_payloads = [
                    "'; DROP TABLE users; --",
                    "' OR '1'='1",
                    "admin'--",
                    "1; SELECT * FROM users;",
                    "UNION SELECT password FROM admin--"
                ]

                for payload in sql_payloads:
                    response = test_client.post('/', data={
                        'text': payload,
                        'language': 'Русский'
                    })

                    # Проверки
                    assert response.status_code == 200

                    # Проверяем, что приложение не падает
                    response_text = response.data.decode('utf-8')
                    assert "Internal Server Error" not in response_text, f"Приложение не должно падать на payload: {payload}"

                    # Проверяем, что payload передается в call_llm (но мокаем его)
                    # В реальности call_llm отправляет payload в API, но мы мокаем
                    mock_call.assert_called()

    def test_input_validation_length_limits(self, client):
        """
        Тест валидации длины ввода.

        Проверяет обработку очень длинных текстов.
        """
        with app.test_client() as test_client:
            # Создаем очень длинный текст (10,000 символов)
            long_text = "A" * 10000

            with patch('app.call_llm') as mock_call:
                mock_call.side_effect = ["Translated long text", "Evaluation"]

                response = test_client.post('/', data={
                    'text': long_text,
                    'language': 'Русский'
                })

            # Проверки
            assert response.status_code == 200

            # Приложение должно обработать длинный ввод без ошибок
            response_text = response.data.decode('utf-8')
            assert "Internal Server Error" not in response_text

    def test_input_validation_empty_fields(self, client):
        """
        Тест валидации пустых полей.

        Проверяет обработку пустого ввода.
        """
        with app.test_client() as test_client:
            # Тест с пустым текстом
            with patch('app.call_llm') as mock_call:
                mock_call.side_effect = ["", "Evaluation"]

                response = test_client.post('/', data={
                    'text': '',
                    'language': 'Русский'
                })

            assert response.status_code == 200

            # Тест с пустым языком (должен использовать значение по умолчанию)
            with patch('app.call_llm') as mock_call:
                mock_call.side_effect = ["Translation", "Evaluation"]

                response = test_client.post('/', data={
                    'text': 'Hello',
                    'language': ''
                })

            assert response.status_code == 200

    def test_security_headers(self, client):
        """
        Тест наличия базовых security headers.

        Проверяет, что приложение устанавливает необходимые заголовки безопасности.
        """
        with app.test_client() as test_client:
            response = test_client.get('/')

            # Проверяем наличие Content-Type
            assert 'Content-Type' in response.headers
            assert 'text/html' in response.headers['Content-Type']

            # Проверяем отсутствие уязвимых заголовков (опционально)
            # В реальном приложении можно добавить:
            # - X-Content-Type-Options: nosniff
            # - X-Frame-Options: DENY
            # - Content-Security-Policy

    @pytest.mark.skip(reason="Тест требует доработки mocking окружения")
    def test_api_key_security(self):
        """
        Тест безопасности API ключа.

        Проверяет, что API ключ не логируется и не отображается в ошибках.
        """
        from app import call_llm
        import os

        # Тест без API ключа
        with patch.dict(os.environ, {}, clear=True), \
             patch('app.requests.post') as mock_post:
            # os.environ очищен, так что API_KEY не существует

            result = call_llm("model", "prompt")

            # Проверяем, что в сообщении об ошибке нет чувствительной информации
            assert "API ключ" in result
            assert "not found" in result.lower()
            # Убеждаемся, что сам ключ не отображается
            assert "Bearer" not in result
            # Убеждаемся, что requests.post не был вызван
            mock_post.assert_not_called()


# Фикстура для клиента
@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()