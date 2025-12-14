# Импорт необходимых библиотек
from flask import Flask, render_template, request  # Flask для веб-приложения, render_template для шаблонов, request для обработки запросов
import requests  # Для выполнения HTTP-запросов к API
import os  # Для работы с переменными окружения

# Создание экземпляра Flask приложения
app = Flask(__name__, template_folder='templates')  # Указываем папку с шаблонами

# URL эндпоинта API
API_ENDPOINT = "https://api.mentorpiece.org/v1/process-ai-request"

# Вспомогательная функция для вызова LLM
def call_llm(model_name, messages):
    """
    Функция для отправки запроса к API LLM.
    
    Параметры:
    - model_name (str): Имя модели, например "Qwen/Qwen3-VL-30B-A3B-Instruct"
    - messages (list): Список сообщений, но в данном API это просто prompt
    
    Возвращает:
    - str: Ответ от модели или сообщение об ошибке
    """
    # Загрузка API ключа из переменных окружения
    api_key = os.getenv('API_KEY')
    if not api_key:
        return "Ошибка: API ключ не найден в переменных окружения."
    
    # Подготовка данных для запроса
    data = {
        "model_name": model_name,
        "prompt": messages  # В API это prompt, но передаем как messages для совместимости
    }
    
    # Заголовки для запроса
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"  # Добавляем API ключ в заголовки
    }
    
    try:
        # Отправка POST запроса
        response = requests.post(API_ENDPOINT, json=data, headers=headers)
        
        # Проверка статуса ответа
        if response.status_code == 200:
            # Парсинг JSON ответа
            result = response.json()
            return result.get("response", "Ответ не найден в JSON.")
        else:
            # Обработка ошибок HTTP
            return f"Ошибка API: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        # Обработка сетевых ошибок
        return f"Сетевая ошибка: {str(e)}"

# Роут для главной страницы (GET и POST)
@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Основной роут приложения.
    
    GET: Отображает форму для ввода текста и выбора языка.
    POST: Обрабатывает введенные данные, выполняет перевод и оценку, отображает результаты.
    """
    if request.method == 'POST':
        # Получение данных из формы
        original_text = request.form.get('text', '')  # Исходный текст
        language = request.form.get('language', 'Английский')  # Выбранный язык
        
        # Шаг 1: Перевод текста
        # Формирование промпта для перевода
        translation_prompt = f"Переведи следующий текст на {language}: {original_text}"
        translated_text = call_llm("Qwen/Qwen3-VL-30B-A3B-Instruct", translation_prompt)
        
        # Шаг 2: Оценка перевода
        # Формирование промпта для оценки
        evaluation_prompt = f"Оцени качество перевода от 1 до 10 и аргументируй. Оригинал: '{original_text}'. Перевод: '{translated_text}'."
        evaluation = call_llm("claude-sonnet-4-5-20250929", evaluation_prompt)
        
        # Передача данных в шаблон для отображения
        return render_template('index.html', 
                               original=original_text, 
                               translated=translated_text, 
                               evaluation=evaluation, 
                               language=language)
    
    # Для GET запроса просто рендерим форму
    return render_template('index.html')

# Запуск приложения в режиме отладки
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)