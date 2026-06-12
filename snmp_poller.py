import logging
import subprocess
from config import (
    ROUTER_IP, SNMP_COMMUNITY, INTERFACES, 
    OID_CPU, OID_RAM_TOTAL, OID_RAM_USED, 
    OID_IF_IN_BASE, OID_IF_OUT_BASE, OID_UPTIME
)
OID_STATUS_BASE = "1.3.6.1.2.1.2.2.1.8"

logger = logging.getLogger(__name__)

def snmp_get_batch(oids, ip, community):
    """
    Menggunakan perintah sistem snmpget untuk menarik data, lebih stabil dari pysnmp library
    """
    results = {}
    try:
        cmd = ["snmpget", "-v2c", "-c", community, "-OQv", ip] + oids
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=5).decode('utf-8')
        lines = output.strip().split('\n')
        
        if len(lines) == len(oids):
            for oid, line in zip(oids, lines):
                try:
                    # remove quotes or types if any left, e.g., "Counter32: 123" -> "123"
                    val_str = line.split(':')[-1].strip()
                    results[oid] = int(val_str.replace('"', ''))
                except ValueError:
                    results[oid] = 0
            return results
    except Exception as e:
        logger.error(f"snmpget failed: {e}")
    return None

def fetch_mikrotik_data():
    oids_to_fetch = [
        OID_CPU,
        OID_RAM_TOTAL,
        OID_RAM_USED,
        OID_UPTIME
    ]
    
    # Add interface OIDs
    for if_id in INTERFACES.keys():
        oids_to_fetch.append(f"{OID_IF_IN_BASE}.{if_id}")
        oids_to_fetch.append(f"{OID_IF_OUT_BASE}.{if_id}")
        oids_to_fetch.append(f"{OID_STATUS_BASE}.{if_id}")

    results = snmp_get_batch(oids_to_fetch, ROUTER_IP, SNMP_COMMUNITY)
    
    if not results:
        return None
        
    data = {
        "system": {},
        "interfaces": {}
    }
    
    try:
        cpu = results.get(OID_CPU, 0)
        ram_total = results.get(OID_RAM_TOTAL, 1) # avoid div by zero
        ram_used = results.get(OID_RAM_USED, 0)
        uptime = results.get(OID_UPTIME, 0)
        
        data["system"]["cpu"] = cpu
        data["system"]["ram_pct"] = (ram_used / ram_total) * 100
        data["system"]["uptime"] = uptime
        
        for if_id in INTERFACES.keys():
            in_oid = f"{OID_IF_IN_BASE}.{if_id}"
            out_oid = f"{OID_IF_OUT_BASE}.{if_id}"
            status_oid = f"{OID_STATUS_BASE}.{if_id}"
            data["interfaces"][if_id] = {
                "in": results.get(in_oid, 0),
                "out": results.get(out_oid, 0),
                "status": results.get(status_oid, 0)
            }
            
        return data
    except Exception as e:
        logger.error(f"Error parsing SNMP data: {e}")
        return None
