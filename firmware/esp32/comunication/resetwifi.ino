#include <Arduino.h>
#include <WiFi.h>

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println("Menghapus konfigurasi WiFi...");

  WiFi.disconnect(true, true);

  delay(2000);

  Serial.println("WiFi tersimpan berhasil dihapus.");
  Serial.println("ESP32 akan restart...");

  delay(2000);
  ESP.restart();
}

void loop() {
}
