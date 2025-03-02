from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from config import FITNESS_GOALS, FITNESS_LEVELS, EQUIPMENT_OPTIONS
from datetime import datetime, timedelta
import calendar

def get_sex_keyboard():
    keyboard = [['Мужской', 'Женский']]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

def get_goals_keyboard():
    keyboard = [[goal] for goal in FITNESS_GOALS]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

def get_fitness_level_keyboard():
    keyboard = [[level] for level in FITNESS_LEVELS]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

def get_equipment_keyboard():
    keyboard = [[option] for option in EQUIPMENT_OPTIONS]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

def get_workout_feedback_keyboard():
    """Return keyboard with workout feedback options"""
    keyboard = [
        [InlineKeyboardButton("😅 Слишком сложно", callback_data='feedback_too_hard')],
        [InlineKeyboardButton("👍 В самый раз", callback_data='feedback_good')],
        [InlineKeyboardButton("😴 Слишком легко", callback_data='feedback_too_easy')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reminder_keyboard():
    times = [
        ["07:00", "09:00", "11:00"],
        ["13:00", "15:00", "17:00"],
        ["19:00", "21:00"]
    ]
    keyboard = [[InlineKeyboardButton(time, callback_data=f"reminder_{time}") for time in row] for row in times]
    return InlineKeyboardMarkup(keyboard)

def get_calendar_keyboard(year, month, workout_dates):
    keyboard = []

    # Add month and year header
    month_name = calendar.month_name[month]
    keyboard.append([InlineKeyboardButton(f"{month_name} {year}", callback_data="ignore")])

    # Add day names header
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    keyboard.append([InlineKeyboardButton(day, callback_data="ignore") for day in week_days])

    # Get calendar for month
    cal = calendar.monthcalendar(year, month)

    for week in cal:
        row = []
        for day in week:
            if day == 0:
                # Empty day
                btn = InlineKeyboardButton(" ", callback_data="ignore")
            else:
                date = f"{year}-{month:02d}-{day:02d}"
                # Check if workout exists for this date
                if date in workout_dates:
                    btn = InlineKeyboardButton(f"💪{day}", callback_data=f"date_{date}")
                else:
                    btn = InlineKeyboardButton(f"{day}", callback_data=f"date_{date}")
            row.append(btn)
        keyboard.append(row)

    # Add navigation buttons
    nav_row = []
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    nav_row.extend([
        InlineKeyboardButton("◀️", callback_data=f"calendar_{prev_year}_{prev_month}"),
        InlineKeyboardButton("▶️", callback_data=f"calendar_{next_year}_{next_month}")
    ])
    keyboard.append(nav_row)

    return InlineKeyboardMarkup(keyboard)