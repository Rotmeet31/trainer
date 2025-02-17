from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters
)
from telegram.ext.filters import TEXT
from telegram.ext._contexttypes import ContextTypes
from config import AGE, HEIGHT, WEIGHT, SEX, GOALS, FITNESS_LEVEL, EQUIPMENT
import messages
import keyboards
from datetime import datetime, timedelta
import logging
import asyncio
import time

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self, database, workout_manager, reminder_manager):
        self.db = database
        self.workout_manager = workout_manager
        self.reminder_manager = reminder_manager
        self.active_workouts = {}  # Store active workout sessions
        self.active_timers = {}    # Store active timer sessions

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            messages.WELCOME_MESSAGE,
            parse_mode='HTML'
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await update.message.reply_text(messages.HELP_MESSAGE)

    async def start_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start profile creation process"""
        await update.message.reply_text(messages.PROFILE_PROMPTS['age'])
        return AGE

    async def age(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle age input"""
        try:
            age = int(update.message.text)
            if 12 <= age <= 100:
                context.user_data['age'] = age
                await update.message.reply_text(messages.PROFILE_PROMPTS['height'])
                return HEIGHT
            else:
                raise ValueError()
        except ValueError:
            await update.message.reply_text(messages.INVALID_INPUT)
            return AGE

    async def height(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle height input"""
        try:
            height = int(update.message.text)
            if 100 <= height <= 250:
                context.user_data['height'] = height
                await update.message.reply_text(messages.PROFILE_PROMPTS['weight'])
                return WEIGHT
            else:
                raise ValueError()
        except ValueError:
            await update.message.reply_text(messages.INVALID_INPUT)
            return HEIGHT

    async def weight(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle weight input"""
        try:
            weight = float(update.message.text)
            if 30 <= weight <= 250:
                context.user_data['weight'] = weight
                await update.message.reply_text(
                    messages.PROFILE_PROMPTS['sex'],
                    reply_markup=keyboards.get_sex_keyboard()
                )
                return SEX
            else:
                raise ValueError()
        except ValueError:
            await update.message.reply_text(messages.INVALID_INPUT)
            return WEIGHT

    async def sex(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle sex input"""
        sex = update.message.text
        if sex in ['Мужской', 'Женский']:
            context.user_data['sex'] = sex
            await update.message.reply_text(
                messages.PROFILE_PROMPTS['goals'],
                reply_markup=keyboards.get_goals_keyboard()
            )
            return GOALS
        else:
            await update.message.reply_text(messages.INVALID_INPUT)
            return SEX

    async def goals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle goals input"""
        goals = update.message.text
        context.user_data['goals'] = goals
        await update.message.reply_text(
            messages.PROFILE_PROMPTS['fitness_level'],
            reply_markup=keyboards.get_fitness_level_keyboard()
        )
        return FITNESS_LEVEL

    async def fitness_level(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle fitness level input"""
        level = update.message.text
        context.user_data['fitness_level'] = level
        await update.message.reply_text(
            messages.PROFILE_PROMPTS['equipment'],
            reply_markup=keyboards.get_equipment_keyboard()
        )
        return EQUIPMENT

    async def equipment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle equipment input and complete profile"""
        equipment = update.message.text
        context.user_data['equipment'] = equipment

        # Get user's telegram handle
        user = update.effective_user
        telegram_handle = user.username if user.username else None

        # Save complete profile with telegram handle
        self.db.save_user_profile(
            user_id=update.effective_user.id,
            profile_data=context.user_data,
            telegram_handle=telegram_handle
        )

        await update.message.reply_text(
            messages.PROFILE_COMPLETE,
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    async def workout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /workout command"""
        user_id = update.effective_user.id
        profile = self.db.get_user_profile(user_id)

        if not profile:
            await update.message.reply_text("Сначала создайте профиль командой /profile")
            return

        # Get user's feedback history
        feedback_history = self.db.get_user_feedback(user_id)

        # Generate workout with feedback history
        workout = self.workout_manager.generate_workout(profile, feedback_history)
        if not workout or not workout['exercises']:
            await update.message.reply_text("К сожалению, не удалось создать тренировку. Попробуйте позже.")
            return

        # Format workout message
        message = f"🏋️‍♂️ Ваша тренировка на сегодня:\n\n"
        message += f"Всего упражнений: {len(workout['exercises'])}\n\n"

        # List all exercises
        for i, exercise in enumerate(workout['exercises'], 1):
            message += f"{i}. {exercise['name']}\n"
            if 'target_muscle' in exercise:
                message += f"   💪 Целевые мышцы: {exercise['target_muscle']}\n"
            if 'time' in exercise:
                time_value = int(exercise['time'])
                if time_value >= 60:
                    minutes = time_value // 60
                    seconds = time_value % 60
                    time_str = f"{minutes} мин" + (f" {seconds} сек" if seconds > 0 else "")
                else:
                    time_str = f"{time_value} сек"
                message += f"   ⏱ Время: {time_str}\n"
            if 'reps' in exercise:
                message += f"   🔄 Повторения: {exercise['reps']}\n"
            if 'weight' in exercise:
                message += f"   🏋️ Вес: {exercise['weight']} кг\n"
            if 'circuits' in exercise and exercise['circuits'] > 1:
                message += f"   🔄 Подходы: {exercise['circuits']}\n\n"

        message += "\n✨ Используйте команду /start_workout, чтобы начать тренировку."

        await update.message.reply_text(message, parse_mode='HTML')

    async def progress(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /progress command"""
        user_id = update.effective_user.id
        progress_data = self.db.get_user_progress(user_id)

        if not progress_data:
            await update.message.reply_text("У вас пока нет завершенных тренировок.")
            return

        # Get streak information
        streak_info = self.db.get_workout_streak(user_id)

        # Get intensity statistics for the last 30 days
        intensity_stats = self.db.get_workout_intensity_stats(user_id, days=30)

        # Create progress summary
        message = "📊 Ваш прогресс:\n\n"

        # Add streak information
        message += "🔥 Статистика тренировок:\n"
        message += f"• Текущая серия: {streak_info['current_streak']} дней\n"
        message += f"• Лучшая серия: {streak_info['longest_streak']} дней\n\n"

        # Show last 5 workouts
        message += "📅 Последние тренировки:\n"
        recent_workouts = progress_data[-5:]
        for workout in recent_workouts:
            message += f"• {workout['date']}\n"
            message += f"  ✅ Выполнено упражнений: {workout['exercises_completed']}/{workout['total_exercises']}\n"
            completion_rate = (workout['exercises_completed'] / workout['total_exercises']) * 100
            message += f"  📈 Эффективность: {completion_rate:.1f}%\n"
            if workout['workout_completed']:
                message += "  ✨ Тренировка завершена полностью\n"
            else:
                message += "  ⏸ Тренировка не завершена\n"
            message += "\n"

        # Add total workouts statistics
        total_workouts = len(progress_data)
        completed_workouts = sum(1 for w in progress_data if w.get('workout_completed', False))
        avg_completion = sum(w['exercises_completed'] / w['total_exercises'] * 100 for w in progress_data) / len(progress_data)

        message += f"📈 Общая статистика:\n"
        message += f"• Всего тренировок: {total_workouts}\n"
        message += f"• Завершено полностью: {completed_workouts}\n"
        message += f"• Средняя эффективность: {avg_completion:.1f}%\n"

        await update.message.reply_text(message)

    async def reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /reminder command"""
        await update.message.reply_text(
            "Выберите время для напоминания:",
            reply_markup=keyboards.get_reminder_keyboard()
        )

    async def reminder_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle reminder time selection"""
        query = update.callback_query
        await query.answer()

        time = query.data.replace('reminder_', '')
        user_id = update.effective_user.id

        self.reminder_manager.set_reminder(user_id, time)

        await query.edit_message_text(
            messages.REMINDER_SET.format(time)
        )

    async def start_workout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start an interactive workout session"""
        user_id = update.effective_user.id
        profile = self.db.get_user_profile(user_id)

        if not profile:
            await update.message.reply_text("Сначала создайте профиль командой /profile")
            return

        workout = self.workout_manager.generate_workout(profile)

        # Ensure all exercises have the same number of circuits
        total_circuits = workout['exercises'][0].get('circuits', 1)
        for exercise in workout['exercises']:
            exercise['circuits'] = total_circuits

        workout['current_exercise'] = 0
        workout['current_circuit'] = 1
        workout['total_exercises'] = len(workout['exercises'])

        logger.info(f"Starting new workout - Total exercises: {workout['total_exercises']}, Circuits: {total_circuits}")

        self.active_workouts[user_id] = workout
        await self._show_exercise(update, context)

    async def _show_exercise(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display current exercise with controls"""
        user_id = update.effective_user.id if update.callback_query else update.effective_user.id
        workout = self.active_workouts.get(user_id)

        if not workout:
            message = "Тренировка не найдена. Используйте /workout для начала."
            if update.callback_query:
                await update.callback_query.message.reply_text(message)
            else:
                await update.message.reply_text(message)
            return

        exercise = workout['exercises'][workout['current_exercise']]
        current = workout['current_exercise'] + 1
        total = workout['total_exercises']
        total_circuits = max(ex.get('circuits', 1) for ex in workout['exercises'])
        circuit = workout['current_circuit']

        # Build the message with only non-empty fields
        message = f"🎯 Круг {circuit}/{total_circuits}\n"
        message += f"💪 Упражнение {current}/{total}\n\n"
        message += f"📍 {exercise['name']}\n\n"

        if 'target_muscle' in exercise:
            message += f"🎯 Целевые мышцы: {exercise['target_muscle']}\n"

        if 'difficulty' in exercise:
            message += f"⭐ Сложность: {exercise['difficulty']}\n"

        message += "\n"

        # Format time display
        if 'time' in exercise:
            time_value = exercise['time']
            if time_value >= 60:
                minutes = time_value // 60
                seconds = time_value % 60
                time_str = f"{minutes} мин" + (f" {seconds} сек" if seconds > 0 else "")
            else:
                time_str = f"{time_value} сек"
            message += f"⏱ Время: {time_str}\n"
            # Add instructions for time-based exercises
            message += "\n📝 Порядок выполнения:\n"
            message += "1. Нажмите '⏱ Запустить таймер'\n"
            message += "2. После окончания таймера отдохните\n"
            message += "3. После отдыха нажмите '✅ Готово'\n"

        if 'reps' in exercise:
            message += f"🔄 Повторения: {exercise['reps']}\n"

        if 'weight' in exercise:
            message += f"🏋️ Вес: {exercise['weight']} кг\n"

        # Create keyboard for exercise navigation
        keyboard = []

        # Add timer button for time-based exercises
        if 'time' in exercise:
            keyboard.append([InlineKeyboardButton("⏱ Запустить таймер", callback_data=f"timer_{exercise['time']}")])

        # Rest of the navigation buttons
        nav_buttons = []
        if workout['current_exercise'] > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Предыдущее", callback_data="prev_exercise"))

        nav_buttons.append(InlineKeyboardButton("✅ Готово", callback_data="exercise_done"))

        if workout['current_exercise'] < workout['total_exercises'] - 1:
            nav_buttons.append(InlineKeyboardButton("➡️ Следующее", callback_data="next_exercise"))

        keyboard.append(nav_buttons)

        # Add rest timer button if there's a rest period
        if 'exercises_rest' in exercise:
            rest_time = exercise['exercises_rest']
            keyboard.append([InlineKeyboardButton(f"⏰ Отдых {int(rest_time)} сек", callback_data=f"rest_{rest_time}")])

        keyboard.append([InlineKeyboardButton("🏁 Закончить тренировку", callback_data="finish_workout")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            # Always send a new message instead of editing
            if 'gif_url' in exercise and exercise['gif_url']:
                try:
                    # Send new message with GIF
                    if update.callback_query:
                        await update.callback_query.message.reply_animation(
                            animation=exercise['gif_url'],
                            caption=message,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                        # Try to delete the old message, but don't fail if we can't
                        try:
                            await update.callback_query.message.delete()
                        except Exception:
                            pass
                    else:
                        await update.message.reply_animation(
                            animation=exercise['gif_url'],
                            caption=message,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                except Exception as e:
                    logging.error(f"Failed to send GIF: {str(e)}")
                    # Fall back to text-only message
                    if update.callback_query:
                        await update.callback_query.message.reply_text(
                            text=message,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                        try:
                            await update.callback_query.message.delete()
                        except Exception:
                            pass
                    else:
                        await update.message.reply_text(
                            text=message,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
            else:
                # Send text-only message
                if update.callback_query:
                    await update.callback_query.message.reply_text(
                        text=message,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                    try:
                        await update.callback_query.message.delete()
                    except Exception:
                        pass
                else:
                    await update.message.reply_text(
                        text=message,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )

        except Exception as e:
            logging.error(f"Error in _show_exercise: {str(e)}")
            error_message = "Произошла ошибка. Пожалуйста, начните тренировку заново с помощью /workout"
            if update.callback_query:
                await update.callback_query.message.reply_text(error_message)
            else:
                await update.message.reply_text(error_message)

    async def handle_timer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle exercise timer callback"""
        query = update.callback_query
        await query.answer()

        data = query.data.split('_')
        timer_type = data[0]  # 'timer' or 'rest'
        seconds = int(data[1])

        # Create timer message
        timer_message = await query.message.reply_text(
            f"⏱ {'Таймер' if timer_type == 'timer' else 'Отдых'}: {seconds} сек"
        )

        # Start countdown
        while seconds > 0:
            await asyncio.sleep(1)
            seconds -= 1
            try:
                await timer_message.edit_text(
                    f"⏱ {'Таймер' if timer_type == 'timer' else 'Отдых'}: {seconds} сек"
                )
            except Exception as e:
                logging.error(f"Error updating timer: {str(e)}")
                break

        # Timer finished with instructions
        try:
            if timer_type == 'timer':
                message = (
                    "✅ Время упражнения истекло!\n\n"
                    "👉 Теперь нажмите кнопку '⏰ Отдых' для восстановления.\n"
                    "После отдыха нажмите '✅ Готово', чтобы перейти к следующему упражнению."
                )
            else:  # rest timer
                message = (
                    "✅ Отдых завершен!\n\n"
                    "👉 Нажмите '✅ Готово', чтобы перейти к следующему упражнению."
                )
            await timer_message.edit_text(message)
        except Exception as e:
            logging.error(f"Error updating final timer message: {str(e)}")

    async def handle_workout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle workout navigation callbacks"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        workout = self.active_workouts.get(user_id)

        if not workout:
            await query.message.reply_text("Тренировка не найдена. Используйте /workout для новой тренировки.")
            return

        # Get the total number of circuits from the first exercise (should be same for all)
        total_circuits = workout['exercises'][0].get('circuits', 1)
        logger.info(f"Current workout state - Exercise: {workout['current_exercise'] + 1}/{workout['total_exercises']}, Circuit: {workout['current_circuit']}/{total_circuits}")

        if query.data == "exercise_done":
            if workout['current_exercise'] < workout['total_exercises'] - 1:
                # Move to next exercise in the current circuit
                workout['current_exercise'] += 1
                logger.info(f"Moving to next exercise: {workout['current_exercise'] + 1} in circuit {workout['current_circuit']}")
                await self._show_exercise(update, context)
            else:
                # Completed all exercises in current circuit
                if workout['current_circuit'] < total_circuits:
                    # Show circuit completion message
                    completion_message = (
                        f"🎯 Круг {workout['current_circuit']} завершен!\n\n"
                        f"✨ Выполнено упражнений: {workout['total_exercises']}\n"
                        f"💪 Следующий круг: {workout['current_circuit'] + 1}/{total_circuits}"
                    )
                    await query.message.reply_text(completion_message)

                    # Reset to first exercise and increment circuit
                    workout['current_circuit'] += 1
                    workout['current_exercise'] = 0
                    logger.info(f"Starting new circuit {workout['current_circuit']}")

                    # Add a small delay before showing the next exercise
                    await asyncio.sleep(2)
                    await self._show_exercise(update, context)
                else:
                    # All circuits completed
                    logger.info("All circuits completed, finishing workout")
                    await self._finish_workout(update, context)

        elif query.data == "prev_exercise" and workout['current_exercise'] > 0:
            workout['current_exercise'] -= 1
            await self._show_exercise(update, context)

        elif query.data == "next_exercise" and workout['current_exercise'] < workout['total_exercises'] - 1:
            workout['current_exercise'] += 1
            await self._show_exercise(update, context)

        elif query.data == "finish_workout":
            await self._finish_workout(update, context)

    async def _finish_workout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Complete the workout and save progress"""
        user_id = update.effective_user.id
        workout = self.active_workouts.pop(user_id, None)

        if workout:
            # Save workout completion in database
            completion_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'exercises_completed': workout['current_exercise'] + 1,
                'total_exercises': workout['total_exercises'],
                'workout_completed': workout['current_exercise'] == workout['total_exercises'] - 1,
                'workout_id': f"workout_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }

            self.db.save_workout_progress(user_id, completion_data)

            # Ask for feedback
            message = (
                "🎉 Тренировка завершена!\n\n"
                f"✅ Выполнено упражнений: {completion_data['exercises_completed']}/{completion_data['total_exercises']}\n\n"
                "Как вам сложность тренировки?"
            )

            context.user_data['last_workout_id'] = completion_data['workout_id']

            # Always send a new message for the completion screen
            if isinstance(update, Update) and update.callback_query:
                # Delete the old message first to avoid confusion
                try:
                    await update.callback_query.message.delete()
                except Exception:
                    pass  # Ignore deletion errors
                await update.callback_query.message.reply_text(
                    text=message,
                    reply_markup=keyboards.get_workout_feedback_keyboard()
                )
            else:
                await update.message.reply_text(
                    text=message,
                    reply_markup=keyboards.get_workout_feedback_keyboard()
                )

    async def handle_workout_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle workout feedback"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        feedback = query.data.replace('feedback_', '')
        workout_id = context.user_data.get('last_workout_id')

        if workout_id:
            feedback_data = {
                'feedback': feedback,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.db.save_workout_feedback(user_id, workout_id, feedback_data)

            # Prepare response message based on feedback
            response_messages = {
                'too_hard': "Следующая тренировка будет легче. Не сдавайтесь! 💪",
                'good': "Отлично! Продолжайте в том же духе! 🎯",
                'too_easy': "Следующая тренировка будет интенсивнее. Вы молодец! 🚀"
            }

            await query.edit_message_text(
                f"Спасибо за отзыв! {response_messages.get(feedback, '')}\n"
                "Используйте /progress для просмотра истории тренировок."
            )

    async def show_calendar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show workout calendar"""
        user_id = update.effective_user.id
        today = datetime.now()

        # Get all workouts for current month
        first_day = today.replace(day=1)
        last_day = (first_day.replace(month=first_day.month % 12 + 1, day=1) - timedelta(days=1))

        workouts = self.db.get_workouts_by_date(user_id, first_day.date(), last_day.date())
        workout_dates = {workout['date'] for workout in workouts}

        await update.message.reply_text(
            "Календарь тренировок:",
            reply_markup=keyboards.get_calendar_keyboard(today.year, today.month, workout_dates)
        )

    async def handle_calendar_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle calendar navigation"""
        query = update.callback_query
        await query.answer()

        data = query.data.split('_')
        if data[0] == 'calendar':
            year = int(data[1])
            month = int(data[2])

            # Get workouts for selected month
            first_day = datetime(year, month, 1)
            last_day = (first_day.replace(month=month % 12 + 1, day=1) - timedelta(days=1))

            workouts = self.db.get_workouts_by_date(
                update.effective_user.id,
                first_day.date(),
                last_day.date()
            )
            workout_dates = {workout['date'] for workout in workouts}

            await query.edit_message_text(
                "Календарь тренировок:",
                reply_markup=keyboards.get_calendar_keyboard(year, month, workout_dates)
            )
        elif data[0] == 'date':
            date = data[1]
            workouts = self.db.get_workouts_by_date(
                update.effective_user.id,
                datetime.strptime(date, '%Y-%m-%d').date(),
                datetime.strptime(date, '%Y-%m-%d').date()
            )

            if workouts:
                message = f"Тренировки {date}:\n\n"
                for workout in workouts:
                    message += (
                        f"✅ Выполнено упражнений: {workout['exercises_completed']}/{workout['total_exercises']}\n"
                        f"{'✨ Тренировка завершена' if workout['workout_completed'] else '❌ Тренировка не завершена'}\n\n"
                    )
            else:
                message = f"На {date} тренировок не найдено."

            await query.answer(message, show_alert=True)

    def get_handlers(self):
        """Return all handlers"""
        handlers = [
            CommandHandler('start', self.start),
            CommandHandler('help', self.help),
            CommandHandler('workout', self.workout),
            CommandHandler('progress', self.progress),
            CommandHandler('calendar', self.show_calendar),
            CommandHandler('reminder', self.reminder),
            CallbackQueryHandler(self.reminder_callback, pattern='^reminder_'),
            CallbackQueryHandler(self.handle_workout_feedback, pattern='^feedback_'),
            CallbackQueryHandler(self.handle_calendar_navigation, pattern='^(calendar|date)_'),
            CallbackQueryHandler(self.handle_timer, pattern='^(timer|rest)_'),  # Add timer handler
            ConversationHandler(
                entry_points=[CommandHandler('profile', self.start_profile)],
                states={
                    AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.age)],
                    HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.height)],
                    WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.weight)],
                    SEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.sex)],
                    GOALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.goals)],
                    FITNESS_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.fitness_level)],
                    EQUIPMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.equipment)],
                },
                fallbacks=[],
            ),
            CommandHandler('start_workout', self.start_workout),
            CallbackQueryHandler(self.handle_workout_callback, pattern='^(prev_exercise|next_exercise|exercise_done|finish_workout)$')
        ]
        return handlers