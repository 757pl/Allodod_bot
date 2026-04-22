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
            created_at TEXT,
            display_order INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def migrate_db():
    """Добавляет колонку display_order, если её нет"""
    conn = sqlite3.connect('reminders.db')
    cur = conn.cursor()
    try:
        cur.execute('ALTER TABLE reminders ADD COLUMN display_order INTEGER DEFAULT 0')
        print("✅ Колонка display_order добавлена")
        
        # Обновляем display_order для старых записей
        cur.execute('SELECT id FROM reminders ORDER BY id')
        rows = cur.fetchall()
        for idx, (row_id,) in enumerate(rows, 1):
            cur.execute('UPDATE reminders SET display_order = ? WHERE id = ?', (idx, row_id))
        if rows:
            print(f"✅ Обновлено {len(rows)} записей")
    except sqlite3.OperationalError:
        print("ℹ️ Колонка display_order уже есть")
    conn.commit()
    conn.close()

def add_reminder(chat_id, event_date, event_text):
    conn = sqlite3.connect('reminders.db')
    cur = conn.cursor()
    
    # Получаем максимальный display_order для этого чата
    cur.execute('SELECT COALESCE(MAX(display_order), 0) FROM reminders WHERE chat_id = ?', (chat_id,))
    max_order = cur.fetchone()[0]
    new_order = max_order + 1
    
    cur.execute('''
        INSERT INTO reminders (chat_id, event_date, event_text, created_at, display_order)
        VALUES (?, ?, ?, ?, ?)
    ''', (chat_id, event_date, event_text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), new_order))
    conn.commit()
    conn.close()

def get_reminders(chat_id):
    conn = sqlite3.connect('reminders.db')
    cur = conn.cursor()
    cur.execute('SELECT id, event_date, event_text, display_order FROM reminders WHERE chat_id = ? ORDER BY display_order', (chat_id,))
    reminders = cur.fetchall()
    conn.close()
    return reminders

def delete_reminder(display_order, chat_id):
    conn = sqlite3.connect('reminders.db')
    cur = conn.cursor()
    
    # Удаляем задачу по display_order
    cur.execute('DELETE FROM reminders WHERE display_order = ? AND chat_id = ?', (display_order, chat_id))
    
    # Перенумеровываем оставшиеся задачи
    cur.execute('SELECT id FROM reminders WHERE chat_id = ? ORDER BY display_order', (chat_id,))
    remaining = cur.fetchall()
    
    new_order = 1
    for (row_id,) in remaining:
        cur.execute('UPDATE reminders SET display_order = ? WHERE id = ?', (new_order, row_id))
        new_order += 1
    
    conn.commit()
    conn.close()
