#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "HX711.h"

// ========================================
// ESP32-S3 N16R8 + HX711
// ========================================
#define LOADCELL_DOUT_PIN 4
#define LOADCELL_SCK_PIN  5

HX711 scale;

float calibration_factor = 459.542;

// Berat di bawah threshold dianggap 0 gram
const float ZERO_THRESHOLD = 1.0;

// ========================================
// WIFI
// ========================================
const char* WIFI_SSID = "UCOLLECT";
const char* WIFI_PASSWORD = "ucollect123";

// ========================================
// MQTT
// ========================================
const char* MQTT_BROKER = "192.168.100.148";
const int MQTT_PORT = 1883;

const char* MQTT_TOPIC_DATA =
  "loadcell/esp32s3-01/data";

const char* MQTT_TOPIC_STATUS =
  "loadcell/esp32s3-01/status";

// ========================================
// NETWORK
// ========================================
WiFiClient espClient;
PubSubClient mqttClient(espClient);

unsigned long lastPublish = 0;
const unsigned long PUBLISH_INTERVAL = 500;

// ========================================
// WIFI CONNECT
// ========================================
void connectWiFi() {

  Serial.println();
  Serial.println("========================================");
  Serial.println("Menghubungkan ke WiFi UCOLLECT...");
  Serial.println("========================================");

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  delay(500);

  WiFi.begin(
    WIFI_SSID,
    WIFI_PASSWORD
  );

  int attempts = 0;

  while (WiFi.status() != WL_CONNECTED) {

    delay(500);

    Serial.print(".");

    attempts++;

    if (attempts >= 60) {

      Serial.println();
      Serial.println("WiFi gagal terhubung.");
      Serial.println("Restart ESP32...");

      delay(2000);
      ESP.restart();
    }
  }

  Serial.println();
  Serial.println("WiFi TERHUBUNG!");

  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  Serial.print("IP ESP32: ");
  Serial.println(WiFi.localIP());

  Serial.print("Gateway: ");
  Serial.println(WiFi.gatewayIP());

  Serial.print("RSSI: ");
  Serial.println(WiFi.RSSI());

  Serial.println("========================================");
}

// ========================================
// MQTT CONNECT
// ========================================
void reconnectMQTT() {

  while (!mqttClient.connected()) {

    Serial.print("Menghubungkan MQTT... ");

    String clientId = "ESP32S3-LoadCell-01-";
    clientId += String(
      (uint32_t)ESP.getEfuseMac(),
      HEX
    );

    if (mqttClient.connect(
      clientId.c_str(),
      MQTT_TOPIC_STATUS,
      0,
      true,
      "offline"
    )) {

      Serial.println("BERHASIL");

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
  Serial.println("HX711 + UCOLLECT + MQTT");
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
  // WIFI
  // ======================================
  connectWiFi();

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
  // WIFI CHECK
  // ======================================
  if (WiFi.status() != WL_CONNECTED) {

    Serial.println("WiFi terputus!");
    connectWiFi();
  }

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

    bool success = mqttClient.publish(
      MQTT_TOPIC_DATA,
      payload.c_str()
    );

    Serial.print("MQTT: ");

    if (success) {
      Serial.println(payload);
    } else {
      Serial.println("GAGAL PUBLISH");
    }
  }

  delay(100);
}
