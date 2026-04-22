import os
from datetime import time
import pytz
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes)
from dotenv import load_dotenv
from database import init_db, add_reminder, get_reminders, delete_reminder
from reminders import check_reminders

# ========== ПОДКЛЮЧЕНИЕ ==========
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
app = ApplicationBuilder().token(TOKEN).build()
init_db()

# ========== КОМАНДА /start ==========
async def start(update, context):
    await update.message.reply_text(
        "👋 **Привет!**\n\n"
        "Я бот-напоминалка для класса.\n\n"
        "📌 **Команды:**\n"
        "/add 28.04 Текст — добавить напоминание\n"
        "/list — список всех напоминаний\n"
        "/del <номер> — удалить напоминание\n\n"
        "⏰ Напоминания приходят в 12:00 (Улан-Удэ)\n"
        "   за 3 дня, за 1 день и в день события\n\n"
        "Пример: `/add 28.04 Контрольная по математике`",
        parse_mode='Markdown'
    )

# ========== КОМАНДА /add ==========
async def add(update, context):
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "❌ **Формат:** `/add <дата> <текст>`\n"
                "Пример: `/add 28.04 Контрольная по математике`",
                parse_mode='Markdown'
            )
            return
        
        event_date = args[0]
        event_text = ' '.join(args[1:])
        chat_id = update.effective_chat.id
        
        add_reminder(chat_id, event_date, event_text)
        await update.message.reply_text(f"✅ Напоминание добавлено!\n📅 {event_date}: {event_text}")
    except:
        await update.message.reply_text("❌ Ошибка. Используй: `/add 28.04 Текст`", parse_mode='Markdown')

# ========== КОМАНДА /list ==========
async def list_reminders(update, context):
    chat_id = update.effective_chat.id
    reminders = get_reminders(chat_id)
    
    if not reminders:
        await update.message.reply_text("📭 Нет активных напоминаний")
        return
    
    context.chat_data['reminder_ids'] = {idx+1: rem_id for idx, (rem_id, event_date, event_text) in enumerate(reminders)}
    
    text = "📋 **Список напоминаний:**\n\n"
    for idx, (rem_id, event_date, event_text) in enumerate(reminders, 1):
        text += f"🔹 `{idx}`. {event_date} — {event_text}\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ========== КОМАНДА /del ==========
async def delete(update, context):
    try:
        temp_id = int(context.args[0])
        chat_id = update.effective_chat.id
        
        reminder_ids = context.chat_data.get('reminder_ids', {})
        real_id = reminder_ids.get(temp_id)
        
        if real_id:
            delete_reminder(real_id, chat_id)
            await update.message.reply_text(f"✅ Напоминание {temp_id} удалено!")
        else:
            await update.message.reply_text("❌ Неверный номер. Используй `/list`", parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ Используй: `/del <номер>`\nНомер можно узнать через `/list`", parse_mode='Markdown')

# ========== ПОДКЛЮЧЕНИЕ КОМАНД ==========
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("list", list_reminders))
app.add_handler(CommandHandler("del", delete))

# ========== НАСТРОЙКА НАПОМИНАНИЙ (12:00 Улан-Удэ) ==========
tz = pytz.timezone('Asia/Irkutsk')
app.job_queue.run_daily(check_reminders, time=time(hour=12, minute=0, tzinfo=tz))

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("✅ Бот запущен! Напоминания в 12:00 (Улан-Удэ)")
    app.run_polling()
