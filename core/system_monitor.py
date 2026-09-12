import os
import psutil
from datetime import datetime
from pathlib import Path

class SystemMonitor:
    @staticmethod
    def get_system_time() -> str:
        return datetime.now().strftime("%H:%M:%S | %d/%m/%Y")

    @staticmethod
    def get_battery_info() -> dict:
        battery = psutil.sensors_battery()
        if not battery:
            return {"percent": "N/A", "plugged": False, "status": "No Battery"}
        return {
            "percent": f"{int(battery.percent)}%",
            "plugged": battery.power_plugged,
            "status": "⚡ Charging" if battery.power_plugged else "🔋 Discharging"
        }

    @staticmethod
    def get_formatted_size(path_obj: Path) -> str:
        """Tính dung lượng file hoặc folder chính xác"""
        if not path_obj.exists():
            return "0 B"
        
        total_size = 0
        if path_obj.is_file():
            total_size = path_obj.stat().st_size
        else:
            for root, _, files in os.walk(path_obj):
                for f in files:
                    fp = os.path.join(root, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)

        # Convert sang KB, MB, GB
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if total_size < 1024.0:
                return f"{total_size:.2f} {unit}"
            total_size /= 1024.0
        return f"{total_size:.2f} PB"