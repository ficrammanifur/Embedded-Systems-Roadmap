#include <Arduino.h>
#include <WiFi.h>

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println();
  Serial.println("================================");
  Serial.println("RESET WIFI CONFIG");
  Serial.println("================================");

  WiFi.mode(WIFI_STA);

  // Hapus SSID + password yang tersimpan
  WiFi.disconnect(true, true);

  delay(3000);

  Serial.println("WiFi configuration DIHAPUS.");
  Serial.println("Restart ESP32...");

  delay(2000);
  ESP.restart();
}

void loop() {
}
