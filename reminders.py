import sqlite3
from datetime import datetime, timedelta
import pytz

async def check_reminders(context):
    tz = pytz.timezone('Asia/Irkutsk')
    now = datetime.now(tz)
    today = now.strftime('%d.%m')
    day1 = (now + timedelta(days=1)).strftime('%d.%m')
    day2 = (now + timedelta(days=2)).strftime('%d.%m')
    day3 = (now + timedelta(days=3)).strftime('%d.%m')
    
    conn = sqlite3.connect('reminders.db')
    cur = conn.cursor()
    cur.execute('SELECT id, chat_id, event_text, event_date FROM reminders')
    all_reminders = cur.fetchall()
    conn.close()
    
    for rem_id, chat_id, event_text, event_date in all_reminders:
        if event_date == today:
            message = f"🔔 **СЕГОДНЯ!**\n📅 {event_date}: {event_text}"
        elif event_date == day1:
            message = f"🔔 **ЗАВТРА!**\n📅 {event_date}: {event_text}"
        elif event_date == day2:
            message = f"🔔 **ЧЕРЕЗ 2 ДНЯ!**\n📅 {event_date}: {event_text}"
        elif event_date == day3:
            message = f"🔔 **ЧЕРЕЗ 3 ДНЯ!**\n📅 {event_date}: {event_text}"
        else:
            continue
        
        try:
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
        except:
            pass
