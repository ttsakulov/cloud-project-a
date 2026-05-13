#!/usr/bin/env python3
import psutil
import json
import time
import socket

def get_metrics():
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # RAM
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        mem_used_gb = mem.used / (1024**3)
        mem_total_gb = mem.total / (1024**3)
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        
        # Network
        net = psutil.net_io_counters()
        net_sent_mb = net.bytes_sent / (1024**2)
        net_recv_mb = net.bytes_recv / (1024**2)
        
        # Uptime
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_days = uptime_seconds // 86400
        uptime_hours = (uptime_seconds % 86400) // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60
        
        # Load average
        load_avg = psutil.getloadavg()
        
        # Processes
        processes = len(psutil.pids())
        
        return {
            "timestamp": time.time(),
            "hostname": socket.gethostname(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "load_avg_1min": round(load_avg[0], 2),
                "load_avg_5min": round(load_avg[1], 2),
                "load_avg_15min": round(load_avg[2], 2)
            },
            "memory": {
                "percent": mem_percent,
                "used_gb": round(mem_used_gb, 2),
                "total_gb": round(mem_total_gb, 2)
            },
            "disk": {
                "percent": disk_percent,
                "used_gb": round(disk_used_gb, 2),
                "total_gb": round(disk_total_gb, 2)
            },
            "network": {
                "sent_mb": round(net_sent_mb, 2),
                "recv_mb": round(net_recv_mb, 2)
            },
            "uptime": {
                "days": int(uptime_days),
                "hours": int(uptime_hours),
                "minutes": int(uptime_minutes)
            },
            "processes": processes
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print(json.dumps(get_metrics()))