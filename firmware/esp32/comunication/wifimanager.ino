#include <WiFi.h>
#include <WiFiManager.h>

WiFiManager wm;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("Starting WiFiManager...");

  // Membuat AP jika belum ada WiFi tersimpan
  bool res = wm.autoConnect("ESP32-S3-Setup", "12345678");

  if (!res) {
    Serial.println("Gagal terhubung WiFi");
    ESP.restart();
  }

  Serial.println("WiFi terhubung!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
}
