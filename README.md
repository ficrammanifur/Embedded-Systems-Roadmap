Arsitektur final:

```text
ESP32-S3 + HX711
       │
       │ WiFi
       ▼
Raspberry Pi 4
 ┌─────────────────────┐
 │ Mosquitto :1883     │
 │        ↓            │
 │ Python Dashboard    │
 │        ↓            │
 │ Web UI              │
 └─────────────────────┘
```

## 1. Install Mosquitto di Raspberry Pi

Di Pi:

```bash
sudo apt update
sudo apt install -y mosquitto mosquitto-clients
```

Aktifkan:

```bash
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

Cek:

```bash
sudo systemctl status mosquitto
```

Harus terlihat:

```text
Active: active (running)
```

---

## 2. Set Mosquitto supaya bisa menerima ESP32

Ini penting.

Buat konfigurasi:

```bash
sudo nano /etc/mosquitto/conf.d/loadcell.conf
```

Isi:

```conf
listener 1883 0.0.0.0

allow_anonymous true
```

Simpan:

**Ctrl + O → Enter → Ctrl + X**

Kemudian:

```bash
sudo systemctl restart mosquitto
```

Cek:

```bash
sudo ss -lntp | grep 1883
```

Targetnya:

```text
0.0.0.0:1883
```

Bukan hanya:

```text
127.0.0.1:1883
```

Karena ESP32 harus bisa masuk dari jaringan WiFi.

> `allow_anonymous true` cocok untuk jaringan LAN pribadi/testing. Untuk deployment yang lebih serius nanti kita bisa pasang username/password.

---

## 3. Cari IP Raspberry Pi

Jalankan:

```bash
hostname -I
```

Misalnya keluar:

```text
192.168.1.50
```

Berarti nanti ESP32:

```cpp
const char* MQTT_BROKER = "192.168.1.50";
const int MQTT_PORT = 1883;
```

**Jangan lagi pakai:**

```cpp
192.168.1.106
```

karena itu IP PC Windows kamu.

---

## 4. Tes MQTT lokal di Pi

Buka terminal pertama:

```bash
mosquitto_sub -h localhost -p 1883 -t "loadcell/test" -v
```

Biarkan terminal ini terbuka.

Buka terminal kedua:

```bash
mosquitto_pub -h localhost -p 1883 -t "loadcell/test" -m "Hello MQTT"
```

Terminal pertama harus mendapatkan:

```text
loadcell/test Hello MQTT
```

Kalau ini berhasil → **Mosquitto Pi sudah beres.** ✅

---

## 5. Tes dari jaringan

Ini juga penting sebelum ESP32.

Di Raspberry Pi:

```bash
mosquitto_sub -h 0.0.0.0 -p 1883 -t "loadcell/test" -v
```

Sebenarnya untuk subscriber lebih baik tetap:

```bash
mosquitto_sub -h localhost -p 1883 -t "loadcell/test" -v
```

Yang penting broker listen di:

```text
0.0.0.0:1883
```

Lalu ESP32 diarahkan ke IP Pi.

---

# 6. Set ESP32

Kode kamu sekarang:

```cpp
const char* MQTT_BROKER = "192.168.1.106";
```

ubah menjadi IP Pi.

Contoh Pi:

```text
192.168.1.50
```

Maka:

```cpp
const char* MQTT_BROKER = "192.168.1.50";
const int MQTT_PORT = 1883;
```

Topic **tetap**:

```cpp
const char* MQTT_TOPIC_DATA =
    "loadcell/esp32s3-01/data";

const char* MQTT_TOPIC_STATUS =
    "loadcell/esp32s3-01/status";
```

Tidak perlu diubah.

---

# 7. Tes ESP32 → Pi

Di Raspberry Pi jalankan:

```bash
mosquitto_sub -h localhost -p 1883 -t "loadcell/esp32s3-01/#" -v
```

Kemudian nyalakan ESP32.

Harus muncul:

```text
loadcell/esp32s3-01/status online
```

dan:

```text
loadcell/esp32s3-01/data {"device":"esp32s3-01","weight":0.00,...}
```

Ketika diberi beban:

```text
loadcell/esp32s3-01/data {"device":"esp32s3-01","weight":520.29,...}
```

Kalau sampai sini berhasil:

**ESP32-S3 → WiFi → Mosquitto Pi = SELESAI.** ✅

---

# 8. Baru sambungkan dashboard

Karena dashboard kamu **sudah jalan di Raspberry Pi**, kita tinggal ubah konfigurasi MQTT-nya menjadi:

```python
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
```

dan topic:

```python
MQTT_TOPIC_DATA = "loadcell/esp32s3-01/data"
MQTT_TOPIC_STATUS = "loadcell/esp32s3-01/status"
```

Kemudian Python/Paho menerima data:

```text
Mosquitto
   ↓
Paho MQTT
   ↓
Backend dashboard
   ↓
Web UI
```

---

## Urutan setting yang paling aman

Jangan langsung semuanya sekaligus. Kita lakukan:

```text
① Install Mosquitto
       ↓
② Konfigurasi listener 1883
       ↓
③ Test MQTT lokal
       ↓
④ Ambil IP Raspberry Pi
       ↓
⑤ Ganti IP broker di ESP32
       ↓
⑥ Test ESP32 → Pi menggunakan mosquitto_sub
       ↓
⑦ Sambungkan Paho Python
       ↓
⑧ Integrasikan ke dashboard
```

**Untuk sekarang fokus sampai nomor ⑥ dulu.** Setelah `mosquitto_sub` di Pi sudah bisa melihat berat dari ESP32, baru kita sentuh dashboard.

## 🔗 Navigasi

- [➡ Lanjut ke code ESP32](../firmware/esp32)
