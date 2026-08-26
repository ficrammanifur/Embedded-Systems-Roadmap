#include <Arduino.h>
#include "HX711.h"

// ==============================
// ESP32-S3 N16R8 + HX711
// ==============================
#define LOADCELL_DOUT_PIN 4
#define LOADCELL_SCK_PIN  5

HX711 scale;

// Calibration factor sementara
float calibration_factor = 459.542;

// Batas noise yang dianggap 0 gram
const float ZERO_THRESHOLD = 1.0;

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println();
  Serial.println("================================");
  Serial.println("ESP32-S3 N16R8 + HX711");
  Serial.println("================================");

  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);

  // Gunakan calibration factor
  scale.set_scale(calibration_factor);

  // Pastikan load cell kosong
  Serial.println("Pastikan load cell TANPA BEBAN...");
  delay(2000);

  // Tare otomatis
  scale.tare();

  Serial.println("Tare selesai.");
  Serial.println("Berat awal = 0 gram");
  Serial.println("================================");
}

void loop() {

  float berat = scale.get_units(10);

  // Hilangkan noise kecil di sekitar titik nol
  if (abs(berat) < ZERO_THRESHOLD) {
    berat = 0.0;
  }

  Serial.print("Berat: ");
  Serial.print(berat, 2);
  Serial.println(" gram");

  delay(500);
}
