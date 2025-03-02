# Bot configuration and constants
import os

# Telegram Bot Token
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# States for ConversationHandler
PROFILE = range(1, 8)
(
    AGE,
    HEIGHT,
    WEIGHT,
    SEX,
    GOALS,
    FITNESS_LEVEL,
    EQUIPMENT,
) = PROFILE

# Command list
COMMANDS = {
    'start': 'Начать работу с ботом',
    'profile': 'Создать или обновить профиль',
    'workout': 'Получить тренировку',
    'start_workout': 'Начать интерактивную тренировку',
    'progress': 'Посмотреть прогресс',
    'reminder': 'Установить напоминание',
    'help': 'Получить помощь'
}

# Fitness goals
FITNESS_GOALS = [
    "Похудение",
    "Набор мышечной массы",
    "Общая физическая подготовка"
]

# Fitness levels
FITNESS_LEVELS = [
    "Начинающий",
    "Средний",
    "Продвинутый"
]

# Equipment options
EQUIPMENT_OPTIONS = [
    "Только вес тела",
    "Доступ в спортзал"
]