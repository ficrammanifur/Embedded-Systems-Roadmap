"""
===================================================================
ESP32-S3 + HX711 Weight Monitoring Backend
Framework: Flask
Target Device: ESP32-S3 N16R8 + HX711 ADC (DOUT=GPIO4, SCK=GPIO5)
===================================================================
"""

import os
import socket
import time
import requests
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# ===================================================================
# KONFIGURASI SISTEM
# ===================================================================
# Ganti IP ESP32 di bawah ini sesuai alamat IP yang didapat dari WiFiManager
# atau atur melalui environment variable ESP32_IP
DEFAULT_ESP32_IP = os.environ.get("ESP32_IP", "192.168.1.104")
CURRENT_ESP32_IP = DEFAULT_ESP32_IP

# Konfigurasi Jaringan PC & ESP32
PC_SERVER_IP = "15.15.0.227"
NETWORK_SUBNET = "255.255.248.0"
NETWORK_GATEWAY = "15.15.0.1"
REQUEST_TIMEOUT = 1.0  # detik (agar polling realtime tetap responsif)

def get_server_ip():
    """Mendeteksi IP Server lokal aktif (WiFi / Ethernet)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.1.104", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("15.15.0.1", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return PC_SERVER_IP

SERVER_IP = get_server_ip()

# ===================================================================
# ROUTES & ENDPOINTS
# ===================================================================

@app.route("/")
def index():
    """Halaman utama dashboard monitoring berat."""
    return render_template(
        "index.html",
        esp32_ip=CURRENT_ESP32_IP,
        server_ip=SERVER_IP,
        subnet=NETWORK_SUBNET,
        gateway=NETWORK_GATEWAY
    )

@app.route("/api/weight", methods=["GET"])
def get_weight():
    """
    Endpoint untuk mengambil data berat dari ESP32-S3.
    ESP32 API: GET http://<ESP32_IP>/api/status
    Response Format:
    {
      "weight": 123.45,
      "unit": "gram",
      "ip": "15.15.0.xxx",
      "rssi": -55
    }
    """
    global CURRENT_ESP32_IP

    # Cek apakah ada override IP via parameter query
    target_ip = request.args.get("ip", CURRENT_ESP32_IP).strip()
    # Cek mode simulasi/demo jika diinginkan (misal untuk testing UI tanpa hardware)
    demo_mode = request.args.get("demo", "false").lower() == "true"

    if demo_mode:
        import math
        t = time.time()
        sim_weight = round(max(0.0, 500.0 + 250.0 * math.sin(t / 3.0) + (time.time() % 10)), 2)
        return jsonify({
            "online": True,
            "weight": sim_weight,
            "unit": "gram",
            "esp_ip": target_ip + " (Demo)",
            "rssi": -58,
            "hx711_status": "CONNECTED",
            "server_ip": SERVER_IP,
            "error": None,
            "timestamp": int(time.time() * 1000)
        })

    esp32_url = f"http://{target_ip}/api/status"

    try:
        # Request ke ESP32 dengan timeout terukur
        response = requests.get(esp32_url, timeout=REQUEST_TIMEOUT)

        if response.status_code == 200:
            data = response.json()

            # Parsing data dari ESP32
            weight = float(data.get("weight", 0.0))
            unit = data.get("unit", "gram")
            esp_ip = data.get("ip", target_ip)
            rssi = data.get("rssi", -60)

            # Deteksi status HX711 (bisa dikirim langsung oleh firmware ESP32 atau diverifikasi)
            # Jika firmware mengirim field sensor_status, kita gunakan itu, atau default CONNECTED
            hx711_status = data.get("sensor", "CONNECTED")
            if isinstance(hx711_status, bool):
                hx711_status = "CONNECTED" if hx711_status else "DISCONNECTED"

            return jsonify({
                "online": True,
                "weight": weight,
                "unit": unit,
                "esp_ip": esp_ip,
                "rssi": rssi,
                "hx711_status": hx711_status,
                "server_ip": SERVER_IP,
                "error": None,
                "timestamp": int(time.time() * 1000)
            }), 200
        else:
            return jsonify({
                "online": False,
                "weight": 0.0,
                "unit": "gram",
                "esp_ip": target_ip,
                "rssi": None,
                "hx711_status": "DISCONNECTED",
                "server_ip": SERVER_IP,
                "error": f"ESP32 merespons dengan status code {response.status_code}",
                "timestamp": int(time.time() * 1000)
            }), 200

    except (requests.exceptions.RequestException, ValueError) as err:
        # Tangani kegagalan koneksi / timeout tanpa membuat dashboard crash
        return jsonify({
            "online": False,
            "weight": 0.0,
            "unit": "gram",
            "esp_ip": target_ip,
            "rssi": None,
            "hx711_status": "DISCONNECTED",
            "server_ip": SERVER_IP,
            "error": "ESP32 tidak dapat dihubungi",
            "error_detail": str(err),
            "timestamp": int(time.time() * 1000)
        }), 200


@app.route("/api/config", methods=["GET", "POST"])
def manage_config():
    """Endpoint untuk membaca dan memperbarui konfigurasi IP ESP32 tanpa restart."""
    global CURRENT_ESP32_IP

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        new_ip = payload.get("esp32_ip")
        if new_ip and isinstance(new_ip, str):
            CURRENT_ESP32_IP = new_ip.strip()
            return jsonify({
                "status": "success",
                "message": f"IP ESP32 berhasil diubah ke {CURRENT_ESP32_IP}",
                "esp32_ip": CURRENT_ESP32_IP
            }), 200
        return jsonify({"status": "error", "message": "Format IP tidak valid"}), 400

    return jsonify({
        "esp32_ip": CURRENT_ESP32_IP,
        "server_ip": SERVER_IP,
        "subnet": NETWORK_SUBNET,
        "gateway": NETWORK_GATEWAY,
        "timeout": REQUEST_TIMEOUT
    }), 200


# ===================================================================
# MAIN RUNNER
# ===================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  ESP32-S3 Weight Monitor Dashboard Server")
    print(f"  Target ESP32 IP   : http://{CURRENT_ESP32_IP}/api/status")
    print(f"  PC Server IP      : http://{SERVER_IP}:5000")
    print(f"  Local Access      : http://127.0.0.1:5000")
    print(f"  LAN Access        : http://15.15.0.227:5000")
    print("=" * 60)

    # Menjalankan server pada semua interface (0.0.0.0) port 5000
    app.run(host="0.0.0.0", port=5000, debug=True)
