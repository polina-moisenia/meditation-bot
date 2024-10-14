import logging
from telegram import Update
from telegram.ext import CommandHandler, Application, ContextTypes, CallbackContext
import datetime
import random
import os
from datetime import datetime, timedelta, timezone

from data.data_storage import DataStorage
from data.user_data import UserData

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
DATA_FILE = file_path = os.path.join(os.path.dirname(__file__), os.getenv('DATA_FILE'))

SLEEP_REMINDER_TIME = "19:00"
DAILY_SET_TIME = "07:00"
TESTING_MODE = True

data_storage = DataStorage(DATA_FILE)

def set_reminder_time():
    if TESTING_MODE:
        minutes_to_add = 1
        return datetime.now(timezone.utc) + timedelta(minutes=minutes_to_add)
    else:
        random_hour = random.randint(8, 18)
        random_minute = random.randint(0, 59)
        return datetime.now(timezone.utc).replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)

def get_user_name(update: Update):
    user_name = update.effective_user.username or str(update.effective_user.id)
    return user_name

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет 👋 Я буду напоминать о медитации каждый день в случайное время, если напишешь мне /letsmeditate. Напиши мне /done, и я буду знать, что сегодня ты помедитировала.')

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = data_storage.get_all_users()
    
    if users:
        message = "Зарегистрированные пользователи 👥\n" + ", ".join([f"@{user}" for user in users])
    else:
        message = "Никто еще не зарегистрировался ❗"
    
    await update.message.reply_text(message)

async def letsmeditate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = get_user_name(update)

    if data_storage.get_user(user_id):
        await update.message.reply_text(f"@{user_name}, ты уже давно готова медитировать 🔔")
    else:
        new_user = UserData(user_id, user_name)
        data_storage.add_user(new_user)
        await update.message.reply_text(f"@{user_name}, а дальше начинаем медитировать 🎉")

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = get_user_name(update)
    today = datetime.now(timezone.utc).date().isoformat()

    user_data = data_storage.get_user(user_id)
    if not user_data:
        await update.message.reply_text(f"Ты еще не в деле, @{user_name} ❌ \n Пожалуйста, напиши мне /letsmeditate, когда будешь готова начать.")
        return

    user_data.mark_training_done(today)
    data_storage.save_data()
    await update.message.reply_text(f'Молодец, @{user_data.user_name} ✅')

async def send_daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(context.job.chat_id, text='Сейчас хороший момент, чтобы помедитировать и улыбнуться 🧘‍♂️')

async def send_sleep_reminder(context: CallbackContext):
    logger.info("test!")
    chat_id = context.job.chat_id
    today = datetime.now(timezone.utc).date().isoformat()    
    message = "Скоро пора спать!\n"

    users_without_done = data_storage.get_users_without_training(today)

    if users_without_done:
        mentions = [f"@{user}" for user in users_without_done]
        message += "Напоминаю о медитации 🚨 \n" + ", ".join(mentions)
    else:
        message += "Сегодня все помедитировали, доброй ночи, котики ❤️"

    await context.bot.send_message(chat_id=chat_id, text=message)

async def schedule_daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    reminder_time = set_reminder_time()

    context.job_queue.run_once(send_daily_reminder, when=reminder_time, chat_id=chat_id)

def schedule_jobs(context: ContextTypes.DEFAULT_TYPE, chat_id) -> None:
    daily_time = datetime.strptime(DAILY_SET_TIME, "%H:%M").time()
    sleep_time = datetime.strptime(SLEEP_REMINDER_TIME, "%H:%M").time()

    context.job_queue.run_daily(schedule_daily_reminder, time=daily_time, chat_id=chat_id)
    context.job_queue.run_daily(send_sleep_reminder, time=sleep_time, chat_id=chat_id)

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("done", done))
    application.add_handler(CommandHandler("letsmeditate", letsmeditate))
    application.add_handler(CommandHandler("list_users", list_users))

    schedule_jobs(application, CHAT_ID)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
