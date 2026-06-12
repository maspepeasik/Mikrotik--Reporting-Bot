import requests
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_IDS, INTERFACES
import database

logger = logging.getLogger(__name__)

def format_bytes(byte_count):
    if byte_count >= 1024**4:
        return f"{byte_count / (1024**4):.2f} TB"
    elif byte_count >= 1024**3:
        return f"{byte_count / (1024**3):.2f} GB"
    elif byte_count >= 1024**2:
        return f"{byte_count / (1024**2):.2f} MB"
    else:
        return f"{byte_count / 1024:.2f} KB"

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN:
        logger.error("No Telegram token provided.")
        return
        
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data=payload, timeout=10)
        except Exception as e:
            logger.error(f"Failed to send telegram to {chat_id}: {e}")

def generate_and_send_report(report_type, start_date, end_date):
    """
    report_type: "Mingguan" or "Bulanan"
    """
    traffic_data = database.get_traffic_summary(start_date, end_date)
    system_data = database.get_system_summary(start_date, end_date)
    
    msg = f"📊 *Laporan Jaringan {report_type}*\n"
    msg += f"📅 Periode: {start_date} s/d {end_date}\n"
    msg += f"🏢 Router: Mikrotik RB5009\n\n"
    
    # System Health
    if system_data:
        msg += "🧠 *Kesehatan Perangkat*\n"
        msg += f"• Rata-rata CPU: {system_data['cpu_avg']:.1f}%\n"
        msg += f"• CPU Puncak (Max): {system_data['cpu_max']:.1f}%\n"
        msg += f"• Rata-rata RAM: {system_data['ram_avg']:.1f}%\n\n"
    
    # Traffic ISP
    msg += "🌐 *Trafik ISP (WAN)*\n"
    for if_id, info in INTERFACES.items():
        if info["type"] == "isp":
            data = traffic_data.get(if_id, {"in": 0, "out": 0, "down_events": 0})
            msg += f"*{info['name']}*\n"
            msg += f"📥 DL: {format_bytes(data['in'])} | 📤 UL: {format_bytes(data['out'])} | ❌ Down: {data.get('down_events', 0)}x\n"
    
    msg += "\n🏢 *Trafik Distribusi (LAN/AP)*\n"
    dist_list = []
    for if_id, info in INTERFACES.items():
        if info["type"] == "dist":
            data = traffic_data.get(if_id, {"in": 0, "out": 0, "down_events": 0})
            total = data['in'] + data['out']
            dist_list.append((info['name'], data['in'], data['out'], total, data.get('down_events', 0)))
            
    # Sort by total traffic descending
    dist_list.sort(key=lambda x: x[3], reverse=True)
    
    for item in dist_list:
        msg += f"*{item[0]}*\n"
        msg += f"📥 DL: {format_bytes(item[1])} | 📤 UL: {format_bytes(item[2])} | ❌ Down: {item[4]}x\n"

    send_telegram_message(msg)
