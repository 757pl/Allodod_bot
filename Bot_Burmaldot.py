import os
import sqlite3
from datetime import datetime, timedelta
import pytz
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes)
from dotenv import load_dotenv

# ========== ПОДКЛЮЧЕНИЕ ==========
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
app = ApplicationBuilder().token(TOKEN).build()

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect('reminders.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            event_date TEXT,
            event_text TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ========== ДОБАВИТЬ НАПОМИНАНИЕ ==========
def add_reminder(chat_id, event_date, event_text):
    conn = sqlite3.connect('reminders.db')
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO reminders (chat_id, event_date, event_text, created_at)
        VALUES (?, ?, ?, ?)
    ''', (chat_id, event_date, event_text, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

# ========== ПОЛУЧИТЬ ВСЕ НАПОМИНАНИЯ ==========
def get_reminders(chat_id):
    conn = sqlite3.connect('reminders.db')
    cur = conn.cursor()
    cur.execute('SELECT id, event_date, event_text FROM reminders WHERE chat_id = ?', (chat_id,))
    reminders = cur.fetchall()
    conn.close()
    return reminders

# ========== УДАЛИТЬ НАПОМИНАНИЕ ==========
def delete_reminder(reminder_id, chat_id):
    conn = sqlite3.connect('reminders.db')
    cur = conn.cursor()
    cur.execute('DELETE FROM reminders WHERE id = ? AND chat_id = ?', (reminder_id, chat_id))
    conn.commit()
    conn.close()

# ========== ПРОВЕРКА НАПОМИНАНИЙ (КАЖДЫЙ ДЕНЬ) ==========
async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    tz = pytz.timezone('Asia/Irkutsk')
    today = datetime.now(tz).strftime('%d.%m')
    
    conn = sqlite3.connect('reminders.db')
    cur = conn.cursor()
    cur.execute('SELECT id, chat_id, event_text FROM reminders WHERE event_date = ?', (today,))
    reminders = cur.fetchall()
    conn.close()
    
    for rem_id, chat_id, event_text in reminders:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🔔 **Напоминание!**\n📅 Сегодня: {event_text}",
                parse_mode='Markdown'
            )
        except:
            pass

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
    
    text = "📋 **Список напоминаний:**\n\n"
    for rem_id, event_date, event_text in reminders:
        text += f"🔹 `{rem_id}`. {event_date} — {event_text}\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ========== КОМАНДА /del ==========
async def delete(update, context):
    try:
        reminder_id = int(context.args[0])
        chat_id = update.effective_chat.id
        delete_reminder(reminder_id, chat_id)
        await update.message.reply_text(f"✅ Напоминание {reminder_id} удалено!")
    except:
        await update.message.reply_text("❌ Используй: `/del <номер>`\nНомер можно узнать через `/list`", parse_mode='Markdown')

# ========== КОМАНДА /start ==========
async def start(update, context):
    await update.message.reply_text(
        "👋 **Привет!**\n\n"
        "Я бот-напоминалка для класса.\n\n"
        "📌 **Команды:**\n"
        "/add 28.04 Текст — добавить напоминание\n"
        "/list — список всех напоминаний\n"
        "/del <номер> — удалить напоминание\n\n"
        "Пример: `/add 28.04 Контрольная по математике`",
        parse_mode='Markdown'
    )

# ========== ПОДКЛЮЧЕНИЕ КОМАНД ==========
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("list", list_reminders))
app.add_handler(CommandHandler("del", delete))

# ========== НАСТРОЙКА НАПОМИНАНИЙ (каждый день в 9:00) ==========
from datetime import time
app.job_queue.run_daily(check_reminders, time=time(hour=9, minute=0))

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("✅ Бот запущен!")
    app.run_polling()