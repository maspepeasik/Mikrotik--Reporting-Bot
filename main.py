import asyncio
import logging
import time
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
import database
import snmp_poller
import reporter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
MAX_64BIT = 2**64

async def run_poller():
    """Runs in background every N minutes to collect SNMP data"""
    logger.info("Starting SNMP Poller loop...")
    database.init_db()
    
    while True:
        try:
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            
            data = snmp_poller.fetch_mikrotik_data()
            if data:
                # Update System Health
                database.update_system_health(date_str, data["system"]["cpu"], data["system"]["ram_pct"])
                
                # Update Interfaces
                for if_id, counters in data["interfaces"].items():
                    last_in = database.get_last_counter(f"if_in_{if_id}")
                    last_out = database.get_last_counter(f"if_out_{if_id}")
                    last_status = database.get_last_counter(f"if_status_{if_id}")
                    
                    curr_in = counters["in"]
                    curr_out = counters["out"]
                    curr_status = counters.get("status", 0) # 1 = up, 2 = down
                    
                    down_event = 0
                    if last_status == 1 and curr_status == 2:
                        down_event = 1
                    
                    delta_in = 0
                    delta_out = 0
                    
                    if last_in is not None:
                        if curr_in >= last_in:
                            delta_in = curr_in - last_in
                        else: # Counter wrapped
                            delta_in = (MAX_64BIT - last_in) + curr_in
                            
                    if last_out is not None:
                        if curr_out >= last_out:
                            delta_out = curr_out - last_out
                        else:
                            delta_out = (MAX_64BIT - last_out) + curr_out
                            
                    # Cap ridiculous spikes
                    if delta_in > MAX_64BIT // 2: delta_in = 0
                    if delta_out > MAX_64BIT // 2: delta_out = 0
                    
                    if delta_in > 0 or delta_out > 0 or down_event > 0:
                        database.add_traffic(date_str, if_id, delta_in, delta_out, down_event)
                        
                    database.set_last_counter(f"if_in_{if_id}", curr_in)
                    database.set_last_counter(f"if_out_{if_id}", curr_out)
                    database.set_last_counter(f"if_status_{if_id}", curr_status)
                    
            logger.info("Polled SNMP data successfully.")
        except Exception as e:
            logger.error(f"Error in poller: {e}")
            
        await asyncio.sleep(config.POLL_INTERVAL_MINUTES * 60)

async def check_schedules():
    """Checks every minute if a report should be sent"""
    while True:
        now = datetime.now()
        # Weekly report every Friday at 08:00
        if now.weekday() == 4 and now.hour == 8 and now.minute == 0:
            logger.info("Triggering Weekly Report")
            end_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
            reporter.generate_and_send_report("Mingguan", start_date, end_date)
            await asyncio.sleep(60) # prevent multiple triggers
            
        # Monthly report every 1st of the month at 08:05
        if now.day == 1 and now.hour == 8 and now.minute == 5:
            logger.info("Triggering Monthly Report")
            # First day of previous month to last day of previous month
            first_day_this_month = now.replace(day=1)
            last_day_prev_month = first_day_this_month - timedelta(days=1)
            first_day_prev_month = last_day_prev_month.replace(day=1)
            
            start_date = first_day_prev_month.strftime("%Y-%m-%d")
            end_date = last_day_prev_month.strftime("%Y-%m-%d")
            reporter.generate_and_send_report("Bulanan", start_date, end_date)
            await asyncio.sleep(60)
            
        # Cleanup old database entries (retain 6 months) at 01:00 AM
        if now.hour == 1 and now.minute == 0:
            logger.info("Running database cleanup to delete data older than 6 months...")
            database.cleanup_old_data()
            await asyncio.sleep(60)
            
        await asyncio.sleep(30)

# Telegram Commands
async def cmd_report_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Menyusun laporan mingguan (7 hari terakhir)...")
    now = datetime.now()
    end_date = now.strftime("%Y-%m-%d")
    start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    reporter.generate_and_send_report("Mingguan (On-Demand)", start_date, end_date)

async def cmd_report_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Menyusun laporan bulanan (30 hari terakhir)...")
    now = datetime.now()
    end_date = now.strftime("%Y-%m-%d")
    start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    reporter.generate_and_send_report("Bulanan (On-Demand)", start_date, end_date)

async def post_init(application):
    # Start background tasks
    asyncio.create_task(run_poller())
    asyncio.create_task(check_schedules())

def main():
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("No BOT TOKEN! Ensure .env is set.")
        return

    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("report_week", cmd_report_week))
    application.add_handler(CommandHandler("report_month", cmd_report_month))
    
    logger.info("🤖 Reporting Bot Started.")
    application.run_polling()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test-snmp":
        database.init_db()
        data = snmp_poller.fetch_mikrotik_data()
        print("SNMP Test Result:")
        print(data)
    elif len(sys.argv) > 1 and sys.argv[1] == "--test-telegram":
        reporter.send_telegram_message("Test message from Reporting Bot!")
        print("Test message sent.")
    else:
        main()
