import os
from datetime import datetime, timedelta, time
import pytz
import sqlite3
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
        "/list — список напоминаний (сортировка по дате)\n"
        "/del <номер> — удалить напоминание\n"
        "/today — напоминания на сегодня\n"
        "/tomorrow — напоминания на завтра\n\n"
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

# ========== КОМАНДА /list (сортировка по дате + группировка) ==========
async def list_reminders(update, context):
    tz = pytz.timezone('Asia/Irkutsk')
    today = datetime.now(tz)
    today_str = today.strftime('%d.%m')
    tomorrow_str = (today + timedelta(days=1)).strftime('%d.%m')
    day2_str = (today + timedelta(days=2)).strftime('%d.%m')
    day3_str = (today + timedelta(days=3)).strftime('%d.%m')
    
    chat_id = update.effective_chat.id
    reminders = get_reminders(chat_id)
    
    if not reminders:
        await update.message.reply_text("📭 Нет активных напоминаний")
        return
    
    # Сохраняем соответствие для удаления
    context.chat_data['reminder_ids'] = {idx+1: rem_id for idx, (rem_id, event_date, event_text) in enumerate(reminders)}
    
    # Группировка
    today_list = []
    tomorrow_list = []
    day2_list = []
    day3_list = []
    other_list = []
    
    for rem_id, event_date, event_text in reminders:
        if event_date == today_str:
            today_list.append((rem_id, event_date, event_text))
        elif event_date == tomorrow_str:
            tomorrow_list.append((rem_id, event_date, event_text))
        elif event_date == day2_str:
            day2_list.append((rem_id, event_date, event_text))
        elif event_date == day3_str:
            day3_list.append((rem_id, event_date, event_text))
        else:
            other_list.append((rem_id, event_date, event_text))
    
    text = "📋 **Список напоминаний:**\n\n"
    
    if today_list:
        text += "🔴 **СЕГОДНЯ:**\n"
        for idx, (rem_id, event_date, event_text) in enumerate(today_list, 1):
            text += f"   {idx}. {event_text}\n"
        text += "\n"
    
    if tomorrow_list:
        text += "🟠 **ЗАВТРА:**\n"
        start_idx = len(today_list) + 1
        for idx, (rem_id, event_date, event_text) in enumerate(tomorrow_list, start_idx):
            text += f"   {idx}. {event_text}\n"
        text += "\n"
    
    if day2_list:
        text += "🟡 **ЧЕРЕЗ 2 ДНЯ:**\n"
        start_idx = len(today_list) + len(tomorrow_list) + 1
        for idx, (rem_id, event_date, event_text) in enumerate(day2_list, start_idx):
            text += f"   {idx}. {event_text}\n"
        text += "\n"
    
    if day3_list:
        text += "🟢 **ЧЕРЕЗ 3 ДНЯ:**\n"
        start_idx = len(today_list) + len(tomorrow_list) + len(day2_list) + 1
        for idx, (rem_id, event_date, event_text) in enumerate(day3_list, start_idx):
            text += f"   {idx}. {event_text}\n"
        text += "\n"
    
    if other_list:
        text += "⚪ **ОСТАЛЬНЫЕ:**\n"
        start_idx = len(today_list) + len(tomorrow_list) + len(day2_list) + len(day3_list) + 1
        for idx, (rem_id, event_date, event_text) in enumerate(other_list, start_idx):
            text += f"   {idx}. {event_date} — {event_text}\n"
    
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
            await update.message.reply_text("❌ Неверный номер. Используй `/list` чтобы увидеть актуальные номера.", parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ Используй: `/del <номер>`\nНомер можно узнать через `/list`", parse_mode='Markdown')

# ========== КОМАНДА /today ==========
async def today(update, context):
    tz = pytz.timezone('Asia/Irkutsk')
    today_date = datetime.now(tz).strftime('%d.%m')
    chat_id = update.effective_chat.id
    
    conn = sqlite3.connect('reminders.db')
    cur = conn.cursor()
    cur.execute('SELECT event_text FROM reminders WHERE chat_id = ? AND event_date = ?', (chat_id, today_date))
    reminders = cur.fetchall()
    conn.close()
    
    if not reminders:
        await update.message.reply_text(f"📭 На сегодня ({today_date}) напоминаний нет")
        return
    
    text = f"📅 **Напоминания на сегодня ({today_date}):**\n\n"
    for r in reminders:
        text += f"🔹 {r[0]}\n"
    await update.message.reply_text(text, parse_mode='Markdown')

# ========== КОМАНДА /tomorrow ==========
async def tomorrow(update, context):
    tz = pytz.timezone('Asia/Irkutsk')
    tomorrow_date = (datetime.now(tz) + timedelta(days=1)).strftime('%d.%m')
    chat_id = update.effective_chat.id
    
    conn = sqlite3.connect('reminders.db')
    cur = conn.cursor()
    cur.execute('SELECT event_text FROM reminders WHERE chat_id = ? AND event_date = ?', (chat_id, tomorrow_date))
    reminders = cur.fetchall()
    conn.close()
    
    if not reminders:
        await update.message.reply_text(f"📭 На завтра ({tomorrow_date}) напоминаний нет")
        return
    
    text = f"📅 **Напоминания на завтра ({tomorrow_date}):**\n\n"
    for r in reminders:
        text += f"🔹 {r[0]}\n"
    await update.message.reply_text(text, parse_mode='Markdown')

# ========== ПОДКЛЮЧЕНИЕ КОМАНД ==========
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("list", list_reminders))
app.add_handler(CommandHandler("del", delete))
app.add_handler(CommandHandler("today", today))
app.add_handler(CommandHandler("tomorrow", tomorrow))

# ========== НАСТРОЙКА НАПОМИНАНИЙ (12:00 Улан-Удэ) ==========
tz = pytz.timezone('Asia/Irkutsk')
app.job_queue.run_daily(check_reminders, time=time(hour=12, minute=0, tzinfo=tz))

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("✅ Бот запущен! Напоминания в 12:00 (Улан-Удэ)")
    app.run_polling()
