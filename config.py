import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_IDS = [x.strip() for x in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if x.strip()]
ROUTER_IP = os.getenv("ROUTER_IP", "192.168.1.1")
SNMP_COMMUNITY = os.getenv("SNMP_COMMUNITY", "public")
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "5"))

# OID Mapping for RB5009 (64-bit counters usually)
# Base OIDs
OID_UPTIME = "1.3.6.1.2.1.1.3.0"
OID_CPU = "1.3.6.1.4.1.2021.11.10.0"
OID_RAM_TOTAL = "1.3.6.1.2.1.25.2.3.1.5.65536"
OID_RAM_USED = "1.3.6.1.2.1.25.2.3.1.6.65536"

# 64-bit Interface Counters
OID_IF_IN_BASE = "1.3.6.1.2.1.31.1.1.1.6"
OID_IF_OUT_BASE = "1.3.6.1.2.1.31.1.1.1.10"

# Interface Index Mapping based on user input
# Ether1 to Ether8 usually maps to index 1 to 8 in default config
INTERFACES = {
    1: {"name": "Ether1 - Fibernet", "type": "isp"},
    2: {"name": "Ether2 - AP RuangTengah", "type": "dist"},
    3: {"name": "Ether3 - MyRep", "type": "isp"},
    4: {"name": "Ether4 - Switch", "type": "dist"},
    5: {"name": "Ether5 - Indibiz", "type": "isp"},
    6: {"name": "Ether6 - AP Container", "type": "dist"},
    7: {"name": "Ether7 - AP Direktur", "type": "dist"},
    8: {"name": "Ether8 - AP Sysadmin", "type": "dist"}
}
