(venv) PS C:\Users\ucala\project\loadcell\loadcell-dashboard> pip list
Package            Version
------------------ ---------
blinker            1.9.0
certifi            2026.7.22
charset-normalizer 3.5.1
click              8.4.2
colorama           0.4.6
Flask              3.1.3
idna               3.19
itsdangerous       2.2.0
Jinja2             3.1.6
MarkupSafe         3.0.3
paho-mqtt          2.1.0
pip                23.2.1
requests           2.34.2
urllib3            2.7.0
Werkzeug           3.1.8

[notice] A new release of pip is available: 23.2.1 -> 26.2.1
[notice] To update, run: python.exe -m pip install --upgrade pip
(venv) PS C:\Users\ucala\project\loadcell\loadcell-dashboard> cat app.py
"""
===================================================================
ESP32-S3 Load Cell MQTT Dashboard Backend
Framework: Flask + Paho-MQTT
Architecture: ESP32-S3 -> MQTT -> Mosquitto (192.168.1.106:1883) -> Flask -> Web Dashboard
===================================================================
"""

from flask import Flask, render_template, jsonify
from config import (
    FLASK_HOST,
    FLASK_PORT,
    FLASK_DEBUG,
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_TOPIC_DATA,
    MQTT_TOPIC_STATUS,
    DEFAULT_DEVICE_NAME,
    DEFAULT_BOARD_NAME,
    DEFAULT_SENSOR_NAME
)
from mqtt_client import mqtt_subscriber

app = Flask(__name__)

# Start MQTT Background Subscriber saat Flask diinisialisasi
mqtt_subscriber.start()


@app.route("/")
def index():
    """
    Menampilkan antarmuka utama web dashboard monitoring beban.
    """
    return render_template(
        "index.html",
        device_name=DEFAULT_DEVICE_NAME,
        board_name=DEFAULT_BOARD_NAME,
        sensor_name=DEFAULT_SENSOR_NAME,
        mqtt_broker=f"{MQTT_BROKER}:{MQTT_PORT}",
        topic_data=MQTT_TOPIC_DATA,
        topic_status=MQTT_TOPIC_STATUS
    )


@app.route("/api/status", methods=["GET"])
def get_status():
    """
    Endpoint status realtime untuk frontend polling (setiap 500-1000 ms).
    Response:
    - Jika Online:
      {
        "device": "esp32s3-01",
        "weight": 1250.45,
        "unit": "gram",
        "rssi": -52,
        "uptime": 12345,
        "status": "online",
        "last_update": "2026-08-26T15:00:00"
      }
    - Jika Offline:
      {
        "device": "esp32s3-01",
        "weight": 0,
        "unit": "gram",
        "status": "offline"
      }
    """
    status_data = mqtt_subscriber.get_latest_status()
    return jsonify(status_data), 200


@app.route("/api/history", methods=["GET"])
def get_history():
    """
    Endpoint untuk mengambil maksimal 60 data terakhir untuk grafik.
    Response:
    [
        {"time": "15:00:01", "weight": 0.00},
        {"time": "15:00:02", "weight": 1250.45}
    ]
    """
    history_data = mqtt_subscriber.get_history()
    return jsonify(history_data), 200


if __name__ == "__main__":
    print("=" * 65)
    print("  ESP32-S3 + HX711 MQTT Weight Monitor Dashboard")
    print(f"  MQTT Broker Target   : {MQTT_BROKER}:{MQTT_PORT}")
    print(f"  MQTT Data Topic      : {MQTT_TOPIC_DATA}")
    print(f"  MQTT Status Topic    : {MQTT_TOPIC_STATUS}")
    print(f"  Dashboard URL (Local): http://127.0.0.1:{FLASK_PORT}")
    print(f"  Dashboard URL (LAN)  : http://{MQTT_BROKER}:{FLASK_PORT}")
    print("=" * 65)

    # Listen pada 0.0.0.0 agar dapat diakses dari jaringan LAN
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
(venv) PS C:\Users\ucala\project\loadcell\loadcell-dashboard> ls


    Directory: C:\Users\ucala\project\loadcell\loadcell-dashboard


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d-----         8/26/2026   3:38 PM                static
d-----         8/26/2026   3:38 PM                templates
d-----         8/26/2026   4:10 PM                __pycache__
-a----         8/26/2026   4:10 PM           2716 app.py
-a----         8/26/2026   4:09 PM           1436 config.py
-a----         8/26/2026   4:09 PM           9681 mqtt_client.py
-a----         8/26/2026   4:10 PM           6280 README.md
-a----         8/26/2026   4:28 PM            490 requirements.txt


(venv) PS C:\Users\ucala\project\loadcell\loadcell-dashboard> cat config.py
"""
===================================================================
Konfigurasi Terpusat Dashboard Monitoring Beban MQTT
Target: ESP32-S3 N16R8 + HX711 Load Cell
Broker: Mosquitto pada Windows PC (192.168.1.106:1883)
===================================================================
"""

import os

# ==========================================
# KONFIGURASI MQTT BROKER
# ==========================================
MQTT_BROKER = os.environ.get("MQTT_BROKER", "192.168.1.106")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
MQTT_KEEPALIVE = 60
MQTT_CLIENT_ID = "flask_weight_monitor_subscriber"

# Username dan Password MQTT (opsional jika broker menggunakan auth)
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", None)
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", None)

# Topic MQTT
MQTT_TOPIC_DATA = "loadcell/esp32s3-01/data"
MQTT_TOPIC_STATUS = "loadcell/esp32s3-01/status"

# ==========================================
# KONFIGURASI DATA BUFFER
# ==========================================
HISTORY_MAX_LEN = 60

# Informasi Perangkat
DEFAULT_DEVICE_NAME = "esp32s3-01"
DEFAULT_BOARD_NAME = "ESP32-S3 N16R8"
DEFAULT_SENSOR_NAME = "HX711 + Load Cell"

# ==========================================
# KONFIGURASI FLASK WEB SERVER
# ==========================================
FLASK_HOST = "0.0.0.0"
FLASK_PORT = int(os.environ.get("PORT", 5000))
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1")
(venv) PS C:\Users\ucala\project\loadcell\loadcell-dashboard> cat mqtt_client.py
"""
===================================================================
MQTT Subscriber Module (Thread-Safe)
Backend subscriber untuk menerima data load cell dari ESP32-S3
===================================================================
"""

import json
import time
import logging
import threading
from datetime import datetime
from collections import deque
import paho.mqtt.client as mqtt

from config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_KEEPALIVE,
    MQTT_CLIENT_ID,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    MQTT_TOPIC_DATA,
    MQTT_TOPIC_STATUS,
    HISTORY_MAX_LEN,
    DEFAULT_DEVICE_NAME
)

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MQTT_Client")


class MQTTLoadCellSubscriber:
    def __init__(self):
        self.lock = threading.Lock()

        # Status Koneksi Broker & ESP32
        self.broker_connected = False
        self.esp_status = "offline"  # "online" / "offline"

        # Data Terakhir dari ESP32
        self.latest_data = {
            "device": DEFAULT_DEVICE_NAME,
            "weight": 0.0,
            "unit": "gram",
            "rssi": None,
            "uptime": 0,
            "status": "offline",
            "last_update": None,
            "last_update_time": "--:--:--",
            "last_update_epoch": 0
        }

        # Riwayat Data Terakhir (Buffer Deque maksimal 60 elemen untuk grafik)
        self.history = deque(maxlen=HISTORY_MAX_LEN)

        # Inisialisasi MQTT Client dengan kompatibilitas Paho MQTT v1.x dan v2.x
        self.client = self._create_mqtt_client()

        # Set callback
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        if MQTT_USERNAME and MQTT_PASSWORD:
            self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    def _create_mqtt_client(self):
        """Membuat instance MQTT Client yang kompatibel dengan paho-mqtt v1 & v2."""
        try:
            # Paho-MQTT 2.0+
            if hasattr(mqtt, "CallbackAPIVersion"):
                return mqtt.Client(
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
                    client_id=MQTT_CLIENT_ID
                )
            # Paho-MQTT 1.x
            return mqtt.Client(client_id=MQTT_CLIENT_ID)
        except Exception:
            return mqtt.Client(client_id=MQTT_CLIENT_ID)

    def _on_connect(self, client, userdata, flags, rc, *extra):
        """Callback ketika subscriber terhubung ke broker Mosquitto."""
        if rc == 0:
            logger.info(f"Terhubung ke Mosquitto Broker [{MQTT_BROKER}:{MQTT_PORT}]")
            self.broker_connected = True

            # Subscribe ke topic data sensor dan status LWT
            client.subscribe([(MQTT_TOPIC_DATA, 0), (MQTT_TOPIC_STATUS, 0)])
            logger.info(f"Subscribed ke topic: {MQTT_TOPIC_DATA} & {MQTT_TOPIC_STATUS}")
        else:
            logger.error(f"Gagal terhubung ke Mosquitto Broker. Return code: {rc}")
            self.broker_connected = False

    def _on_disconnect(self, client, userdata, rc, *extra):
        """Callback ketika subscriber terputus dari Mosquitto."""
        logger.warning(f"Terputus dari Mosquitto Broker (rc: {rc}). Mencoba menyambung kembali...")
        self.broker_connected = False

    def _on_message(self, client, userdata, msg):
        """Callback saat menerima pesan MQTT."""
        topic = msg.topic
        payload_str = msg.payload.decode("utf-8", errors="ignore").strip()

        now = datetime.now()
        iso_time = now.isoformat(timespec="seconds")
        time_display = now.strftime("%H:%M:%S")
        epoch_ms = int(time.time() * 1000)

        # -------------------------------------------------------------
        # 1. Topic Status (Online / Offline LWT)
        # -------------------------------------------------------------
        if topic == MQTT_TOPIC_STATUS:
            raw_status = payload_str.lower()
            with self.lock:
                if "online" in raw_status:
                    self.esp_status = "online"
                    logger.info("Status ESP32 berubah menjadi: ONLINE")
                else:
                    self.esp_status = "offline"
                    logger.info("Status ESP32 berubah menjadi: OFFLINE (LWT/Disconnected)")

                self.latest_data["status"] = self.esp_status
                self.latest_data["last_update"] = iso_time
                self.latest_data["last_update_time"] = time_display
                self.latest_data["last_update_epoch"] = epoch_ms

        # -------------------------------------------------------------
        # 2. Topic Data Sensor Berat (JSON)
        # -------------------------------------------------------------
        elif topic == MQTT_TOPIC_DATA:
            try:
                data = json.loads(payload_str)
                raw_weight = float(data.get("weight", 0.0))
                device = data.get("device", DEFAULT_DEVICE_NAME)
                unit = data.get("unit", "gram")
                rssi = data.get("rssi", None)
                uptime = data.get("uptime", 0)

                # Filter noise: Range -1.0 s/d +1.0 gram dianggap 0.00 gram
                if -1.0 <= raw_weight <= 1.0:
                    weight_val = 0.00
                else:
                    weight_val = round(raw_weight, 2)

                with self.lock:
                    # Data masuk otomatis menandakan ESP32 online
                    self.esp_status = "online"

                    self.latest_data = {
                        "device": device,
                        "weight": weight_val,
                        "unit": unit,
                        "rssi": rssi,
                        "uptime": uptime,
                        "status": "online",
                        "last_update": iso_time,
                        "last_update_time": time_display,
                        "last_update_epoch": epoch_ms
                    }

                    # Tambahkan ke riwayat deque untuk grafik Chart.js
                    self.history.append({
                        "time": time_display,
                        "weight": weight_val
                    })

            except (json.JSONDecodeError, ValueError) as err:
                logger.error(f"Format payload data tidak valid pada topic {topic}: {payload_str} ({err})")

    def start(self):
        """Memulai MQTT loop di background thread tanpa blocking Flask."""
        def run_loop():
            while True:
                try:
                    logger.info(f"Menghubungkan ke Mosquitto [{MQTT_BROKER}:{MQTT_PORT}]...")
                    self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=MQTT_KEEPALIVE)
                    self.client.loop_forever()
                except Exception as ex:
                    self.broker_connected = False
                    logger.warning(f"Mosquitto broker tidak dapat dijangkau ({ex}). Reconnecting dalam 3 detik...")
                    time.sleep(3)

        thread = threading.Thread(target=run_loop, daemon=True, name="MQTT_Subscriber_Thread")
        thread.start()
        logger.info("MQTT Background Worker Thread berhasil dijalankan.")

    # =================================================================
    # THREAD-SAFE ACCESSORS UNTUK FLASK API
    # =================================================================

    def get_latest_status(self):
        """Mengambil data status terbaru secara thread-safe."""
        with self.lock:
            # Jika ESP32 offline
            if self.esp_status != "online":
                return {
                    "device": self.latest_data.get("device", DEFAULT_DEVICE_NAME),
                    "weight": 0,
                    "unit": self.latest_data.get("unit", "gram"),
                    "rssi": self.latest_data.get("rssi"),
                    "uptime": self.latest_data.get("uptime"),
                    "status": "offline",
                    "last_update": self.latest_data.get("last_update"),
                    "last_update_time": self.latest_data.get("last_update_time", "--:--:--"),
                    "last_update_epoch": self.latest_data.get("last_update_epoch", 0),
                    "mqtt_broker_status": "connected" if self.broker_connected else "disconnected"
                }

            # Jika ESP32 online
            return {
                "device": self.latest_data.get("device", DEFAULT_DEVICE_NAME),
                "weight": self.latest_data.get("weight", 0.0),
                "unit": self.latest_data.get("unit", "gram"),
                "rssi": self.latest_data.get("rssi", -52),
                "uptime": self.latest_data.get("uptime", 0),
                "status": "online",
                "last_update": self.latest_data.get("last_update"),
                "last_update_time": self.latest_data.get("last_update_time", "--:--:--"),
                "last_update_epoch": self.latest_data.get("last_update_epoch", 0),
                "mqtt_broker_status": "connected" if self.broker_connected else "disconnected"
            }

    def get_history(self):
        """Mengambil riwayat data berat untuk grafik secara thread-safe."""
        with self.lock:
            return list(self.history)

    def is_broker_connected(self):
        """Status konektivitas ke Mosquitto."""
        return self.broker_connected


# Global Singleton Instance
mqtt_subscriber = MQTTLoadCellSubscriber()
(venv) PS C:\Users\ucala\project\loadcell\loadcell-dashboard>
