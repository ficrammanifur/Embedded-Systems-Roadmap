#include <Arduino.h>
#include <WiFi.h>
#include <WiFiManager.h>
#include <PubSubClient.h>
#include "HX711.h"

// ========================================
// ESP32-S3 N16R8 + HX711
// ========================================
#define LOADCELL_DOUT_PIN 4
#define LOADCELL_SCK_PIN  5

// ========================================
// HX711
// ========================================
HX711 scale;

float calibration_factor = 459.542;

// Nilai di bawah threshold dianggap 0 gram
const float ZERO_THRESHOLD = 1.0;

// ========================================
// MQTT
// ========================================
// GANTI dengan IP Raspberry Pi 4
const char* MQTT_BROKER = "192.168.1.106";
const int   MQTT_PORT   = 1883;

// Topic
const char* MQTT_TOPIC_DATA   = "loadcell/esp32s3-01/data";
const char* MQTT_TOPIC_STATUS = "loadcell/esp32s3-01/status";

// ========================================
// NETWORK
// ========================================
WiFiClient espClient;
PubSubClient mqttClient(espClient);

unsigned long lastPublish = 0;
const unsigned long PUBLISH_INTERVAL = 500;

// ========================================
// MQTT CONNECT
// ========================================
void reconnectMQTT() {

  while (!mqttClient.connected()) {

    Serial.print("Menghubungkan MQTT... ");

    String clientId = "ESP32S3-LoadCell-01-";
    clientId += String((uint32_t)ESP.getEfuseMac(), HEX);

    if (mqttClient.connect(
      clientId.c_str(),
      MQTT_TOPIC_STATUS,
      0,
      true,
      "offline"
    )) {

      Serial.println("BERHASIL");

      // Status online
      mqttClient.publish(
        MQTT_TOPIC_STATUS,
        "online",
        true
      );

    } else {

      Serial.print("GAGAL, rc=");
      Serial.println(mqttClient.state());

      delay(3000);
    }
  }
}

// ========================================
// SETUP
// ========================================
void setup() {

  Serial.begin(115200);
  delay(2000);

  Serial.println();
  Serial.println("========================================");
  Serial.println("ESP32-S3 N16R8");
  Serial.println("HX711 + WiFiManager + MQTT");
  Serial.println("========================================");

  // ======================================
  // HX711
  // ======================================
  scale.begin(
    LOADCELL_DOUT_PIN,
    LOADCELL_SCK_PIN
  );

  scale.set_scale(calibration_factor);

  Serial.println("Pastikan load cell TANPA BEBAN...");
  delay(2000);

  scale.tare();

  Serial.println("Tare selesai.");
  Serial.println("Berat awal = 0 gram");

  // ======================================
  // WIFI MANAGER
  // ======================================
  WiFiManager wm;

  wm.setConfigPortalTimeout(180);

  Serial.println();
  Serial.println("Menghubungkan ke WiFi...");

  bool connected = wm.autoConnect(
    "ESP32-S3-LOADCELL"
  );

  if (!connected) {

    Serial.println("WiFi gagal terhubung.");
    Serial.println("Restart...");

    delay(3000);
    ESP.restart();
  }

  Serial.println();
  Serial.println("WiFi TERHUBUNG!");
  Serial.print("IP ESP32: ");
  Serial.println(WiFi.localIP());

  Serial.print("RSSI: ");
  Serial.println(WiFi.RSSI());

  // ======================================
  // MQTT
  // ======================================
  mqttClient.setServer(
    MQTT_BROKER,
    MQTT_PORT
  );

  mqttClient.setBufferSize(512);

  Serial.print("MQTT Broker: ");
  Serial.print(MQTT_BROKER);
  Serial.print(":");
  Serial.println(MQTT_PORT);

  Serial.println("========================================");
}

// ========================================
// LOOP
// ========================================
void loop() {

  // ======================================
  // MQTT CONNECTION
  // ======================================
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }

  mqttClient.loop();

  // ======================================
  // READ HX711
  // ======================================
  float berat = scale.get_units(10);

  // Auto zero
  if (abs(berat) < ZERO_THRESHOLD) {
    berat = 0.0;
  }

  // ======================================
  // SERIAL MONITOR
  // ======================================
  Serial.print("Berat: ");
  Serial.print(berat, 2);
  Serial.println(" gram");

  // ======================================
  // MQTT PUBLISH
  // ======================================
  if (millis() - lastPublish >= PUBLISH_INTERVAL) {

    lastPublish = millis();

    String payload = "{";
    payload += "\"device\":\"esp32s3-01\",";
    payload += "\"weight\":" + String(berat, 2) + ",";
    payload += "\"unit\":\"gram\",";
    payload += "\"rssi\":" + String(WiFi.RSSI()) + ",";
    payload += "\"uptime\":" + String(millis() / 1000);
    payload += "}";

    mqttClient.publish(
      MQTT_TOPIC_DATA,
      payload.c_str()
    );

    Serial.print("MQTT: ");
    Serial.println(payload);
  }

  delay(100);
}
