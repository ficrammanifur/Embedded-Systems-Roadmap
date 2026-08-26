#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <WiFiManager.h>
#include "HX711.h"

// ========================================
// PIN ESP32-S3 N16R8
// ========================================
#define LOADCELL_DOUT_PIN 4
#define LOADCELL_SCK_PIN  5

// ========================================
// HX711
// ========================================
HX711 scale;

float calibration_factor = 459.542;

const float ZERO_THRESHOLD = 1.0;

// ========================================
// WEB SERVER
// ========================================
WebServer server(80);

float currentWeight = 0.0;

// ========================================
// API STATUS
// ========================================
void handleStatus() {

  float berat = scale.get_units(10);

  if (abs(berat) < ZERO_THRESHOLD) {
    berat = 0.0;
  }

  currentWeight = berat;

  String json = "{";
  json += "\"weight\":" + String(currentWeight, 2) + ",";
  json += "\"unit\":\"gram\",";
  json += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
  json += "\"rssi\":" + String(WiFi.RSSI());
  json += "}";

  server.send(200, "application/json", json);
}

// ========================================
// ROOT
// ========================================
void handleRoot() {

  String message = "ESP32-S3 HX711 Weight Sensor\n";
  message += "IP: ";
  message += WiFi.localIP().toString();
  message += "\nWeight: ";
  message += String(currentWeight, 2);
  message += " gram\n";

  server.send(200, "text/plain", message);
}

// ========================================
// SETUP
// ========================================
void setup() {

  Serial.begin(115200);
  delay(2000);

  Serial.println();
  Serial.println("================================");
  Serial.println("ESP32-S3 N16R8");
  Serial.println("HX711 + WiFiManager");
  Serial.println("================================");

  // ========================================
  // HX711
  // ========================================
  scale.begin(
    LOADCELL_DOUT_PIN,
    LOADCELL_SCK_PIN
  );

  scale.set_scale(calibration_factor);

  Serial.println("Pastikan load cell kosong...");
  delay(2000);

  scale.tare();

  Serial.println("Tare selesai.");
  Serial.println("Berat awal: 0 gram");

  // ========================================
  // WIFI MANAGER
  // ========================================
  WiFiManager wm;

  wm.setConfigPortalTimeout(180);

  Serial.println();
  Serial.println("Menghubungkan WiFi...");

  bool connected = wm.autoConnect(
    "ESP32-S3-HX711"
  );

  if (!connected) {

    Serial.println("Gagal terhubung WiFi.");
    Serial.println("Restart...");

    delay(3000);
    ESP.restart();
  }

  Serial.println();
  Serial.println("WiFi TERHUBUNG!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  Serial.print("RSSI: ");
  Serial.println(WiFi.RSSI());

  // ========================================
  // WEB SERVER
  // ========================================
  server.on("/", handleRoot);

  server.on("/api/status", handleStatus);

  server.begin();

  Serial.println();
  Serial.println("HTTP Server aktif.");
  Serial.println("API:");
  Serial.print("http://");
  Serial.print(WiFi.localIP());
  Serial.println("/api/status");

  Serial.println("================================");
}

// ========================================
// LOOP
// ========================================
void loop() {

  server.handleClient();

  float berat = scale.get_units(10);

  if (abs(berat) < ZERO_THRESHOLD) {
    berat = 0.0;
  }

  currentWeight = berat;

  Serial.print("Berat: ");
  Serial.print(currentWeight, 2);
  Serial.println(" gram");

  delay(500);
}
