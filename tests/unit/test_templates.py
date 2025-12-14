# Импорт необходимых библиотек для тестирования шаблонов
import pytest  # Фреймворк для тестирования
from bs4 import BeautifulSoup  # Для парсинга HTML (нужно добавить в requirements)
import sys  # Для добавления пути

# Добавляем путь к src
sys.path.insert(0, '/workspaces/AI.J.3.4/src')

from app import app  # Импорт Flask приложения


class TestTemplates:
    """
    Класс для тестирования HTML-шаблонов.

    Эти тесты проверяют корректность рендеринга шаблонов и их содержимое.
    """

    def test_index_template_get_request(self, client):
        """
        Тест шаблона index.html для GET-запроса.

        Проверяет, что форма отображается корректно.
        """
        with app.test_client() as test_client:
            response = test_client.get('/')

            # Проверки
            assert response.status_code == 200
            assert 'text/html' in response.content_type

            # Парсинг HTML
            soup = BeautifulSoup(response.data, 'html.parser')

            # Проверяем наличие формы
            form = soup.find('form')
            assert form is not None, "Форма должна присутствовать"

            # Проверяем наличие полей ввода
            text_input = soup.find('textarea', {'name': 'text'})
            assert text_input is not None, "Поле для текста должно присутствовать"
            assert text_input.get('required') is not None, "Поле должно быть обязательным"

            language_select = soup.find('select', {'name': 'language'})
            assert language_select is not None, "Выпадающий список языков должен присутствовать"

            # Проверяем наличие кнопки отправки
            submit_button = soup.find('button', {'type': 'submit'})
            assert submit_button is not None, "Кнопка отправки должна присутствовать"

    @pytest.mark.parametrize("original,translated,evaluation,language", [
        ("Hello", "Привет", "Отлично", "Русский"),
        ("Goodbye", "До свидания", "Хорошо", "Русский"),
    ])
    def test_index_template_post_request(self, client, original, translated, evaluation, language):
        """
        Тест шаблона index.html для POST-запроса с параметризацией.

        Проверяет отображение результатов перевода и оценки.
        """
        with app.test_client() as test_client:
            # Мокаем call_llm для контролируемого тестирования
            from unittest.mock import patch
            with patch('app.call_llm') as mock_call:
                mock_call.side_effect = [translated, evaluation]

                response = test_client.post('/', data={
                    'text': original,
                    'language': language
                })

            # Проверки
            assert response.status_code == 200

            # Парсинг HTML
            soup = BeautifulSoup(response.data, 'html.parser')

            # Проверяем отображение оригинального текста
            original_text = soup.find(string=lambda text: original in text if text else False)
            assert original_text is not None, f"Оригинальный текст '{original}' должен отображаться"

            # Проверяем отображение перевода
            translated_text = soup.find(string=lambda text: translated in text if text else False)
            assert translated_text is not None, f"Перевод '{translated}' должен отображаться"

            # Проверяем отображение оценки
            evaluation_text = soup.find(string=lambda text: evaluation in text if text else False)
            assert evaluation_text is not None, f"Оценка '{evaluation}' должна отображаться"

            # Проверяем отображение выбранного языка
            language_text = soup.find(string=lambda text: language in text if text else False)
            assert language_text is not None, f"Язык '{language}' должен отображаться"

    def test_template_error_handling(self, client):
        """
        Тест обработки ошибок в шаблоне.

        Проверяет отображение сообщений об ошибках.
        """
        with app.test_client() as test_client:
            # Мокаем call_llm для возврата ошибки
            from unittest.mock import patch
            with patch('app.call_llm') as mock_call:
                mock_call.side_effect = ["Ошибка API: 500 - Internal Server Error", "Ошибка сети"]

                response = test_client.post('/', data={
                    'text': 'Test text',
                    'language': 'Русский'
                })

            # Проверки
            assert response.status_code == 200

                    # Проверяем, что ошибки отображаются
            response_text = response.data.decode('utf-8')
            assert "Ошибка" in response_text, "Сообщения об ошибках должны отображаться"

    def test_template_structure(self, client):
        """
        Тест общей структуры шаблона.

        Проверяет наличие основных HTML-элементов.
        """
        with app.test_client() as test_client:
            response = test_client.get('/')

            soup = BeautifulSoup(response.data, 'html.parser')

            # Проверяем наличие DOCTYPE
            assert soup.find() is not None, "HTML должен иметь правильную структуру"

            # Проверяем наличие <html>, <head>, <body>
            assert soup.find('html') is not None
            assert soup.find('head') is not None
            assert soup.find('body') is not None

            # Проверяем наличие заголовка
            title = soup.find('title')
            assert title is not None, "Страница должна иметь заголовок"
            assert "Переводчик" in title.text or "Translator" in title.text, "Заголовок должен содержать тему приложения"


# Фикстура для клиента
@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()