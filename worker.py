"""
NetOutageMonitor Worker Service
Windows Service olarak çalışır.

Kurulum : python worker.py install
Başlatma : python worker.py start
Durdurma : python worker.py stop
Kaldırma : python worker.py remove
"""

import win32serviceutil
import win32service
import win32event
import win32con
import win32api
import win32ts
import servicemanager
import subprocess
import json
import os
import time
import logging
import logging.handlers
import threading
from datetime import datetime
from pathlib import Path

# ── Yollar ───────────────────────────────────────────────────────────────────
BASE_DIR    = Path(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = BASE_DIR / "config.json"
LOG_PATH    = BASE_DIR / "worker.log"

# ── Varsayılan config ─────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "aktif": 0,
    "ip": "192.168.1.1",
    "interval": 5,
    "cooldown": 30,    "startup_delay": 120,    "error_message": "Hedefe ulaşılamıyor!"
}

# ── Logger ────────────────────────────────────────────────────────────────────
logger = logging.getLogger("NetOutageMonitor")
logger.setLevel(logging.INFO)

# RotatingFileHandler: 5MB dosya boyutu limitinde en fazla 5 dosya sakla
handler = logging.handlers.RotatingFileHandler(
    str(LOG_PATH),
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=5               # 5 dosya tut (worker.log.1, worker.log.2, vs)
)
formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def log(msg: str):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    logger.info(line)
    # Servis modunda da standart output'a yaz (debug için)
    try:
        print(line, flush=True)
    except:
        pass


def load_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def ping(ip: str) -> bool:
    """Windows ping.exe ile tek paket gönder."""
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "1000", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def show_msgbox(title: str, message: str):
    """
    Kullanıcının oturumuna uyarı mesajı gönderir.
    Windows Service'ten masaüstüne ulaşmak için WTS API kullanılır.
    """
    try:
        # Tüm aktif session'ları bul
        try:
            sessions = win32ts.WTSEnumerateSessions()
            for session_info in sessions:
                # session_info = (SessionId, WinstationName, State)
                session_id = session_info[0]
                
                # Session 0 = Service session, atla
                if session_id == 0:
                    continue
                
                try:
                    # Kullanıcı session'ına uyarı gönder
                    result = win32ts.WTSSendMessage(
                        win32ts.WTS_CURRENT_SERVER_HANDLE,
                        int(session_id),  # session_id'yi int'e çevir
                        title,
                        message,
                        win32con.MB_OK | win32con.MB_ICONWARNING,
                        30,  # timeout (saniye)
                        False  # bWait
                    )
                    log(f"✓ Uyarı Session {session_id}'ye gönderildi.")
                except Exception as e:
                    log(f"Session {session_id} uyarısı başarısız: {e}")
        except Exception as e:
            log(f"WTS enumeration hatası: {e}")
            # Fallback: Bilinen session ID'leri dene
            for sid in range(1, 5):
                try:
                    win32ts.WTSSendMessage(
                        win32ts.WTS_CURRENT_SERVER_HANDLE,
                        sid,
                        title,
                        message,
                        win32con.MB_OK | win32con.MB_ICONWARNING,
                        30,
                        False
                    )
                    log(f"✓ Fallback: Uyarı Session {sid}'ye gönderildi.")
                    break
                except:
                    pass
    except Exception as e:
        # Son çare: loga yazıl
        log(f"❌ Uyarı gösterilemedi: {e}")
        log(f"📌 Uyarı İçeriği: {title}\n{message}")


# ── Windows Service ───────────────────────────────────────────────────────────
class NetOutageMonitorService(win32serviceutil.ServiceFramework):
    _svc_name_         = "NetOutageMonitorService"
    _svc_display_name_ = "NetOutageMonitor Service"
    _svc_description_  = (
        "Belirtilen IP adresini periyodik olarak ping'ler; "
        "erişilemezse ekranda uyarı gösterir."
    )

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running    = True

    # ── Servis durdurma isteği ────────────────────────────────────────────────
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        log("Servis durdurma isteği alındı.")

    # ── Servis başlatma ───────────────────────────────────────────────────────
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        log("=" * 50)
        log("Servis başlatıldı.")

        if not CONFIG_PATH.exists():
            save_config(DEFAULT_CONFIG.copy())
            log("config.json oluşturuldu (varsayılan).")

        self.main_loop()

    # ── Ana döngü ─────────────────────────────────────────────────────────────
    def main_loop(self):
        in_cooldown       = False
        cooldown_end_time = 0.0

        # İlk başlangıçta gecikme (ağ bağlantısının sağlanması için)
        cfg = load_config()
        startup_delay_sec = int(cfg.get("startup_delay", 120))
        if startup_delay_sec > 0:
            log(f"Servis başlangıcında {startup_delay_sec} saniye bekleniyor (ağ bağlantısı için)...")
            ret = win32event.WaitForSingleObject(self.stop_event, startup_delay_sec * 1000)
            if ret == win32event.WAIT_OBJECT_0:
                return

        while self.running:
            cfg = load_config()

            # Pasif mod → 5 sn bekle, tekrar kontrol et
            if not cfg.get("aktif", 0):
                ret = win32event.WaitForSingleObject(self.stop_event, 5000)
                if ret == win32event.WAIT_OBJECT_0:
                    break
                continue

            ip            = cfg.get("ip",            "192.168.1.1")
            interval_ms   = int(cfg.get("interval",  5))  * 1000
            cooldown_sec  = int(cfg.get("cooldown",  30))
            error_message = cfg.get("error_message", "Hedefe ulaşılamıyor!")

            # Cooldown sürüyorsa kısa kısa bekle (config değişikliğine duyarlı ol)
            now = time.time()
            if in_cooldown and now < cooldown_end_time:
                remaining_ms = int((cooldown_end_time - now) * 1000)
                wait_ms      = min(remaining_ms, 1000)
                ret = win32event.WaitForSingleObject(self.stop_event, wait_ms)
                if ret == win32event.WAIT_OBJECT_0:
                    break
                continue
            else:
                in_cooldown = False

            # Ping
            success = ping(ip)

            if success:
                log(f"{ip} ping başarılı.")
            else:
                log(f"{ip} ping başarısız! Uyarı gönderiliyor.")

                # Uyarı kutusunu ayrı thread'de göster
                threading.Thread(
                    target=show_msgbox,
                    args=(
                        "⚠ NetOutageMonitor Uyarısı",
                        (
                            f"{error_message}\n\n"
                            f"Hedef IP : {ip}\n"
                            f"Zaman    : {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
                        )
                    ),
                    daemon=True
                ).start()

                in_cooldown       = True
                cooldown_end_time = time.time() + cooldown_sec
                log(f"Cooldown başladı ({cooldown_sec} saniye).")

            # Interval kadar bekle
            ret = win32event.WaitForSingleObject(self.stop_event, interval_ms)
            if ret == win32event.WAIT_OBJECT_0:
                break

        log("Servis döngüsü sonlandı.")
        log("=" * 50)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(NetOutageMonitorService)
