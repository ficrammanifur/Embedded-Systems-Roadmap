#include "HX711.h"

// ==============================
// PIN HX711
// ==============================
#define HX711_DOUT 32
#define HX711_SCK  33

HX711 scale;

// ==============================
// KALIBRASI
// ==============================
// Ganti nilai ini setelah proses kalibrasi
float calibration_factor = 454.542;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("================================");
  Serial.println("   LOAD CELL + HX711 + ESP32-S3");
  Serial.println("================================");

  scale.begin(HX711_DOUT, HX711_SCK);

  scale.set_scale(calibration_factor);
  scale.tare();  // Set kondisi awal = 0 gram

  Serial.println("Tare selesai.");
  Serial.println("Letakkan beban...");
}

void loop() {
  if (scale.is_ready()) {

    float weight = scale.get_units(10);

    Serial.print("Berat: ");
    Serial.print(weight, 2);
    Serial.println(" gram");

  } else {
    Serial.println("HX711 tidak terdeteksi!");
  }

  delay(500);
}
