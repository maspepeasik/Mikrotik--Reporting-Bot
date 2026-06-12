import sqlite3
import os
from datetime import datetime
from config import INTERFACES

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Table for traffic
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS traffic_log (
            date TEXT,
            interface_id INTEGER,
            bytes_in INTEGER DEFAULT 0,
            bytes_out INTEGER DEFAULT 0,
            down_events INTEGER DEFAULT 0,
            PRIMARY KEY (date, interface_id)
        )
    ''')
    try:
        cursor.execute('ALTER TABLE traffic_log ADD COLUMN down_events INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass # Column already exists
    # Table for system health
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_log (
            date TEXT PRIMARY KEY,
            cpu_sum REAL DEFAULT 0,
            cpu_count INTEGER DEFAULT 0,
            cpu_max REAL DEFAULT 0,
            ram_sum REAL DEFAULT 0,
            ram_count INTEGER DEFAULT 0
        )
    ''')
    # Table to store last counter values to calculate delta
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS counter_state (
            id TEXT PRIMARY KEY,
            value INTEGER,
            updated_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_last_counter(counter_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM counter_state WHERE id = ?', (counter_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_last_counter(counter_id, value):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO counter_state (id, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
    ''', (counter_id, value, now_str))
    conn.commit()
    conn.close()

def add_traffic(date_str, interface_id, delta_in, delta_out, down_events=0):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO traffic_log (date, interface_id, bytes_in, bytes_out, down_events)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(date, interface_id) DO UPDATE SET 
            bytes_in = bytes_in + excluded.bytes_in,
            bytes_out = bytes_out + excluded.bytes_out,
            down_events = down_events + excluded.down_events
    ''', (date_str, interface_id, delta_in, delta_out, down_events))
    conn.commit()
    conn.close()

def update_system_health(date_str, cpu, ram):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO system_log (date, cpu_sum, cpu_count, cpu_max, ram_sum, ram_count)
        VALUES (?, ?, 1, ?, ?, 1)
        ON CONFLICT(date) DO UPDATE SET 
            cpu_sum = cpu_sum + excluded.cpu_sum,
            cpu_count = cpu_count + 1,
            cpu_max = MAX(cpu_max, excluded.cpu_max),
            ram_sum = ram_sum + excluded.ram_sum,
            ram_count = ram_count + 1
    ''', (date_str, cpu, cpu, ram))
    conn.commit()
    conn.close()

def get_traffic_summary(start_date, end_date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT interface_id, SUM(bytes_in), SUM(bytes_out), SUM(down_events) 
        FROM traffic_log 
        WHERE date >= ? AND date <= ?
        GROUP BY interface_id
    ''', (start_date, end_date))
    rows = cursor.fetchall()
    conn.close()
    
    result = {}
    for r in rows:
        result[r[0]] = {"in": r[1], "out": r[2], "down_events": r[3] or 0}
    return result

def get_system_summary(start_date, end_date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT SUM(cpu_sum), SUM(cpu_count), MAX(cpu_max), SUM(ram_sum), SUM(ram_count)
        FROM system_log
        WHERE date >= ? AND date <= ?
    ''', (start_date, end_date))
    row = cursor.fetchone()
    conn.close()

    if not row or not row[1]:
        return None
        
    return {
        "cpu_avg": row[0] / row[1],
        "cpu_max": row[2],
        "ram_avg": row[3] / row[4]
    }

def cleanup_old_data():
    """Menghapus data yang umurnya lebih dari 6 bulan (180 hari)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM traffic_log WHERE date < date('now', '-6 months')")
        cursor.execute("DELETE FROM system_log WHERE date < date('now', '-6 months')")
        cursor.execute("VACUUM")
        conn.commit()
    except Exception as e:
        print(f"Cleanup error: {e}")
    finally:
        conn.close()
