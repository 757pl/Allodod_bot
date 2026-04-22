import sqlite3
from datetime import datetime

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

def add_reminder(chat_id, event_date, event_text):
    conn = sqlite3.connect('reminders.db')
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO reminders (chat_id, event_date, event_text, created_at)
        VALUES (?, ?, ?, ?)
    ''', (chat_id, event_date, event_text, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_reminders(chat_id):
    conn = sqlite3.connect('reminders.db')
    cur = conn.cursor()
    cur.execute('SELECT id, event_date, event_text FROM reminders WHERE chat_id = ? ORDER BY id', (chat_id,))
    reminders = cur.fetchall()
    conn.close()
    return reminders

def delete_reminder(reminder_id, chat_id):
    conn = sqlite3.connect('reminders.db')
    cur = conn.cursor()
    cur.execute('DELETE FROM reminders WHERE id = ? AND chat_id = ?', (reminder_id, chat_id))
    conn.commit()
    conn.close()