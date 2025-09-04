import urllib
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import requests
from bs4 import BeautifulSoup
import re
import sys
import random
from ddgs import DDGS

import nltk

nltk.download('punkt')
nltk.download('punkt_tab')

# Токен и ID группы
import os
TOKEN = os.getenv('VK_TOKEN')
GROUP_ID = int(os.getenv('VK_GROUP_ID'))

# Расширенный словарь для проверки брани
PROFANE_WORDS = [
    'мат', 'блядь', 'пизд', 'хуй', 'еб', 'fuck', 'shit', 'bitch', 'asshole',
    'идиот', 'дебил', 'оскорбление', 'сука', 'пидор', 'damn', 'cunt'
]

# Полезные ссылки
USEFUL_LINKS = (
    "🔗 Инструкция для студентов: https://cloud.mail.ru/public/UsGG/6cM6dBgEw\n"
    "🔗 Инструкция для преподавателей: https://cloud.mail.ru/public/q1VL/9z7FZKzyK\n"
    "🔗 Презентация проекта: https://cloud.mail.ru/public/vd1d/nMS5LHNBP"
)

# База знаний
KNOWLEDGE_BASE = {
    'who_can_participate': {
        'keywords': ['кто может', 'участвовать', 'участие', 'для кого', 'школьники', 'студенты', 'преподаватели', 'принять участие', 'кто принять участие'],
        'answer': "Участвовать могут школьники, студенты бакалавриата, специалитета, магистратуры и аспирантуры всех вузов России, а также научные руководители и преподаватели. \n\nЧтобы начать, скачай полезные материалы:\n" + USEFUL_LINKS
    },
    'multiple_tasks': {
        'keywords': ['несколько задач', 'много проектов', 'неограниченное', 'сколько можно', 'выбрать несколько'],
        'answer': "Да, можно решать неограниченное количество задач."
    },
    'use_solutions': {
        'keywords': ['где использовать', 'где можно использовать', 'применить кейсы', 'использовать кейсы', 'применить решения', 'использовать решения', 'для чего проекты', 'курсовые', 'дипломные', 'домашние задания'],
        'answer': "Задачи от VK можно использовать в практической части выпускных квалификационных, курсовых и научно-исследовательских работ, а также взять за основу домашних заданий."
    },
    'get_data': {
        'keywords': ['получить данные', 'необходимые данные', 'данные для решения', 'взять данные', 'найти данные', 'датасеты', 'материалы', 'регистрация', 'доступ к материалам'],
        'answer': "Выбери задачу, пройди регистрацию — и тебе откроется доступ к материалам, таким как датасеты и презентации. \n\nТакже скачай полезные инструкции:\n" + USEFUL_LINKS
    },
    'certificate': {
        'keywords': ['сертификат', 'получу ли', 'работа над проектом', 'сертификаты', 'получить сертификат'],
        'answer': "Если ты выполнишь все условия, описанные в выбранной задаче, то сможешь получить сертификат о работе над проектом VK."
    },
    'grades': {
        'keywords': ['оценки', 'баллы', 'оценивают', 'рецензия', 'оценка'],
        'answer': "Нет, оценки не предусмотрены. Но если твое решение высоко оценят эксперты, мы подготовим рецензию."
    },
    'task_formation': {
        'keywords': ['формировались задачи', 'откуда кейсы', 'придумал проекты', 'как составлены'],
        'answer': "Все задачи — исследовательские и экспериментальные, составлены с учётом актуального бизнес-контекста от сервисов VK."
    },
    'ask_questions': {
        'keywords': ['задать вопросы', 'контакты', 'эксперты', 'вебинары', 'спросить'],
        'answer': "Следи за расписанием вебинаров на странице проекта — там можно задать вопросы экспертам VK. Организационные вопросы — на обучающей платформе."
    },
    'no_task_found': {
        'keywords': ['не найти задачу', 'подходящий кейс', 'новые проекты', 'обновления', 'нет задачи', 'не могу найти', 'где задачи', 'список задач', 'банк задач', 'новые кейсы', 'старые кейсы' 'новые задачи', 'старые кейсы', 'не могу найти кесы', 'не найти кейсы', 'найти кейсы', 'где кейсы', 'найти задачи'],
        'answer': "В банке задач появляются новые кейсы от департаментов VK, следи за обновлениями. Или заполни профиль для персональных рекомендаций: https://education.vk.company/profile."
    },
    'directions': {
        'keywords': ['направления', 'темы проектов', 'какие кейсы', 'анализ данных', 'разработка', 'безопасность', 'креатив'],
        'answer': "Доступны задачи по пяти направлениям: анализ данных и машинное обучение, разработка, информационная безопасность, креативные индустрии и продукт. От сервисов как AI VK, All Cups, Почта Mail, VK Education и т.д."
    },
    'examples': {
        'keywords': ['примеры задач', 'список проектов', 'конкурентный анализ', 'ux', 'бот', 'какие проекты', 'проекты есть', 'какие проекты есть', 'какие есть проекты', 'проекты в vk', 'какие задачи', 'список кейсов', 'какие кейсы есть', 'есть проекты', 'проекты vk education'],
        'answer': "Примеры: Конкурентный анализ митапов в IT, Исследование UX мессенджера, Концепция конференции VK Инклюзия, Мини-сериал о карьере в VK, Поиск уязвимостей в VK Bug Bounty и т.д. Полный список на сайте."
    },
    'stages': {
        'keywords': ['этапы', 'сроки', 'когда вебинары', 'регистрация', 'награды', 'периоды'],
        'answer': "Сентябрь-октябрь/март-апрель: выбор проектов и регистрация. Ноябрь-декабрь/март-май: вебинары и работа. Январь-февраль/июнь-июль: сертификаты и награды."
    },
    'advantages': {
        'keywords': ['преимущества', 'зачем участвовать', 'портфолио', 'призы', 'бонусы'],
        'answer': "Прикладные кейсы для портфолио, поддержка от экспертов VK, рецензии, призы (мерч или бизнес-завтрак)."
    },
    'for_teachers': {
        'keywords': ['преподавателям', 'использовать в вузе', 'обратная связь', 'программа', 'для преподавателей'],
        'answer': "Преподаватели могут использовать задачи для обучения. Свяжитесь с нами: https://education.vk.company/program/417. Также скачай инструкцию для преподавателей:\n" + USEFUL_LINKS
    },
    'choose_task': {
        'keywords': ['выбрать задачу', 'начать проект', 'регистрация', 'согласование', 'как выбрать'],
        'answer': "Нажми на интересующую задачу на сайте, зарегистрируйся, получи материалы. Согласуй тему с преподавателем вуза. Чтобы узнать больше, скачай полезные материалы:\n" + USEFUL_LINKS
    },
    'webinars': {
        'keywords': ['вебинары', 'консультации', 'организационные встречи', 'вебинар'],
        'answer': "Организационные вебинары с экспертами VK проходят в ноябре-декабре и марте-мае. Следи за расписанием на сайте."
    },
    'contest': {
        'keywords': ['конкурс', 'награды', 'лучшие решения', 'призы', 'конкурс работ'],
        'answer': "Каждые полгода проходит конкурс — награждаем лучших студентов мерчем или бизнес-завтраком с экспертом VK."
    },
    'materials': {
        'keywords': ['материалы', 'инструкции', 'презентация', 'скачать', 'инструкция'],
        'answer': "\nСкачай инструкцию для студентов, для преподавателей или презентацию проекта на сайте:\n" + USEFUL_LINKS
    },
    'submit_solution': {
        'keywords': ['подать решение', 'загрузка', 'отправить проект', 'успехи', 'загрузить'],
        'answer': "Загружай решения на платформу в ноябре-декабре или марте-мае. Поделись успехами для сертификата."
    },
    'about_project': {
        'keywords': ['vk education projects', 'витрина', 'бизнес-кейсы', 'проект vk'],
        'answer': "Это витрина прикладных бизнес-кейсов от VK для студентов вузов России. Используй для учебы, портфолио и практики."
    },

    'materials_download': {
        'keywords': ['полезные материалы', 'скачать презентацию', 'инструкция для студентов', 'инструкция для преподавателей', 'презентация проекта', 'скачать инструкцию'],
        'answer': "Полезные материалы для скачивания:\n" + USEFUL_LINKS
    },

    'what_is_this': {
        'keywords': ['что это такое', 'что это', 'что за проект', 'о проекте', 'что такое vk education', 'что такое проекты vk', 'это что', 'расскажи о себе', 'кто ты', 'что ты такое'],
        'answer': "Это бот для проекта VK Education Projects — витрины прикладных бизнес-кейсов от VK для школьников и студентов России. Здесь ты можешь решать реальные задачи по анализу данных, разработке, безопасности и креативу, использовать их для курсовых, дипломов или портфолио. Получи сертификат, рецензии и призы! \n\nЧтобы начать: выбери задачу на https://education.vk.company/education_projects. \nСкачай материалы:\n" + USEFUL_LINKS + "\n\nЧто именно интересует? 😊"
    }
}

GREETINGS = {
    'hello': {
        'patterns': [r'привет', r'здравствуй', r'hello', r'hi', r'добрый день'],
        'responses': ["Привет! Рад тебя видеть. Чем могу помочь с VK Education Projects?", "Здравствуй! Я здесь, чтобы ответить на вопросы о проектах. Что интересует?", "Привет! Давай разберёмся с твоим вопросом."]
    },
    'how_are_you': {
        'patterns': [r'как дела', r'как ты', r'как поживаешь', r'че как', r'как сам'],
        'responses': ["У меня всё супер, я бот, всегда готов помочь! А у тебя? Что насчёт проектов VK?", "Отлично, спасибо! Я создан для ответов на вопросы. Расскажи, что тебя беспокоит?", "Всё в порядке, спасибо! Давай лучше о тебе — какой вопрос по VK Education?"]
    },
    'thanks': {
        'patterns': [r'спасибо', r'thanks', r'благодарю'],
        'responses': ["Пожалуйста! Если ещё вопросы — пиши.", "Рад помочь! Что ещё интересует?", "Не за что! 😊 Продолжим?"]
    },
    'bye': {
        'patterns': [r'пока', r'до свидания', r'bye'],
        'responses': ["Пока! Удачи с проектами VK!", "До свидания! Если что — возвращайся.", "Бай! Не забудь проверить сайт VK Education."]
    },
    'joke': {
        'patterns': [r'анекдот', r'шутка', r'пошути'],
        'responses': ["Почему программисты не любят природу? Слишком много багов! 😄 А теперь seriously — какой вопрос?", "Я бот, но шутки люблю. Вот: Что говорит бот, когда не знает ответ? 'Погугли!' 😂 Что у тебя за вопрос?"]
    },
}

def match_pattern(query, patterns):
    query_lower = query.lower()
    for pattern in patterns:
        if re.search(pattern, query_lower):
            return True
    return False


def match_pattern(query, patterns):
    query_lower = query.lower()
    for pattern in patterns:
        if re.search(pattern, query_lower):
            return True
    return False


def search_knowledge_base(query):
    if not query.strip():
        return random.choice(
            ["Эй, напиши вопрос! 😊 Чем помочь с проектами VK?", "Пустое сообщение?🤨 Давай что-нибудь спроси!"])

    query_lower = query.lower()
    for key, data in KNOWLEDGE_BASE.items():
        if '--test' in sys.argv:
            print(f"DEBUG: Проверяю базу для '{key}'...")
        for kw in data['keywords']:
            if kw in query_lower:
                if '--test' in sys.argv:
                    print(f"DEBUG: Сработала категория '{key}' на ключе '{kw}'.")
                intro = random.choice(["Понял твой вопрос! 👌",
                                       "Давай разбираться 😊, на основе сайта VK Education: \n",
                                       ""])
                return f"{intro} {data['answer']}"
    return None


def get_info_from_site(query):
    url = 'https://education.vk.company/education_projects'
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        faq_section = soup.find('section', class_='faq') or soup.find(string=re.compile(query, re.I))
        if faq_section:
            text = faq_section[:300] if isinstance(faq_section, str) else faq_section.text[:300]
            return f"🔍 Вот что мне удалось найти: \n\n{text}... \n\n🔗 Подробнее: {url}"
        return None
    except Exception as e:
        print(f"Ошибка парсинга: {e}")
        return None


def search_internet(query, is_wiki_bias=False):
    if len(query.split()) < 2:
        return random.choice(
            ["🔍 Твой запрос слишком короткий — уточни, пожалуйста! Что именно интересует по VK Education? 😊",
             "🤔 Не понял... Расскажи подробнее, чтобы я мог помочь!"])

    try:
        if is_wiki_bias:
            biased_query = f"{query} site:ru.wikipedia.org OR wikipedia.org"
            intro = random.choice(
                ["🌐 Не нашёл на сайте VK Education, но вот статья из Википедии:\n\n",
                 "🔍 Проверил в сети, вот немножко из Википедии:\n\n"])
        else:
            biased_query = f"{query} ВКонтакте OR VK Education site:vk.com OR education.vk.company"
            intro = random.choice(["🌐 Не нашёл на сайте VK, но вот что в интернете:\n\n",
                                   "🔍 Проверил в сети и вот что откопал:\n\n"])

        with DDGS() as ddgs:
            results = [r for r in ddgs.text(biased_query, region='ru-ru', safesearch='off', max_results=3)]
        if results:
            first = results[0]
            encoded_href = urllib.parse.quote(first['href'], safe=':/&?=#')
            return f"{intro}📘 {first['title']} 📘\n{first['body'][:200]}...\n\n🔗 Подробнее: {encoded_href}\n\n🤔 Если это не то, уточни вопрос!"
        return f"🤷‍♂️ Ничего не нашёл. Попробуй поискать в Yandex '{biased_query}' самостоятельно. 😊"
    except Exception as e:
        print(f"Ошибка поиска: {e}")
        return f"🤖 Ой, что-то пошло не так с поиском. Предлагаю тебе поискать '{query}' в Yandex самостоятельно. 🔍"


def check_profanity(text):
    text_lower = text.lower()
    if any(word in text_lower for word in PROFANE_WORDS):
        return True
    if re.search(r'\b(п[иы]зд|х[уюй]|еба|fuck|shit|сук|пид|damn|cunt)\b', text_lower):
        return True
    return False


def is_yes_no_question(query):
    yes_no_patterns = ['возможно ли', 'можно ли', 'да/нет', 'есть ли']
    if any(pattern in query.lower() for pattern in yes_no_patterns):
        if any(kw in query.lower() for kw in KNOWLEDGE_BASE['multiple_tasks']['keywords']):
            return random.choice(
                ["Да, конечно!😁 Ты можешь взять несколько задач.", "Абсолютно!😄 Нет ограничений на количество."])
        elif 'сертификат' in query.lower():
            return "Да, если выполнишь условия задачи. ✔️"
        elif 'вебинары' in query.lower():
            return "Да, они проходят регулярно — проверь расписание. 📅"
        return random.choice(["Да, это возможно.", "Нет, к сожалению."])
    return None


def process_query(query):
    query_lower = query.lower()

    if check_profanity(query_lower):
        return random.choice(['Пожалуйста, избегайте нецензурной брани. Давай общаться вежливо! 😐',
                              'Эй, давай без этого!😳 Твой вопрос не обработан.'])

    for category, data in GREETINGS.items():
        if match_pattern(query_lower, data['patterns']):
            return random.choice(data['responses'])

    yes_no_answer = is_yes_no_question(query_lower)
    if yes_no_answer:
        return yes_no_answer

    what_is_patterns = [r'что такое', r'что значит', r'что есть']
    if any(re.search(pattern, query_lower) for pattern in what_is_patterns):
        match = re.search(r'(что такое|что значит|что есть)\s*(.+)', query_lower)
        if match:
            term = match.group(2).strip()
            vk_related_keywords = ['vk', 'education', 'projects', 'проект', 'задача', 'кейс', 'сертификат', 'вебинар']
            if any(kw in term for kw in vk_related_keywords):
                knowledge_answer = search_knowledge_base(query)
                if knowledge_answer:
                    return knowledge_answer
            else:
                return search_internet(f"Что такое {term}", is_wiki_bias=True)

    knowledge_answer = search_knowledge_base(query)
    if knowledge_answer:
        return knowledge_answer

    site_info = get_info_from_site(query_lower)
    if site_info:
        return f"Не нашёл в своей базе, но проверил сайт напряму:\n {site_info}"

    internet_info = search_internet(query)
    if internet_info:
        return internet_info

    fallback = random.choice(
        ["Хмм, интересный вопрос! Не уверен, но давай подумаем вместе. \nПроверь FAQ на https://education.vk.company/education_projects или уточни.",
         "Извини, я не нашёл точного ответа. Может, перефразируй? Или спроси у администраторов."])
    return fallback + " Как ещё могу помочь?"


# Тестовый режим
def test_mode():
    print("Запущен тестовый режим. Вводите вопросы (exit для выхода).")
    while True:
        query = input("Пользователь: ").strip()
        if query.lower() == 'exit':
            break
        response = process_query(query)
        print(f"Бот: {response}")


# Основной запуск
if __name__ == "__main__":
    if '--test' in sys.argv:
        test_mode()
    else:
        vk_session = vk_api.VkApi(token=TOKEN)
        longpoll = VkLongPoll(vk_session, group_id=GROUP_ID)
        print("Бот запущен в реальном режиме.")

        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                query = event.text
                response = process_query(query)
                vk_session.method('messages.send', {
                    'user_id': event.user_id,
                    'message': response,
                    'random_id': vk_api.utils.get_random_id()

                })
