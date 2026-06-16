#include <DHT.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <ESP32Servo.h>

// ── Pines ──────────────────────────────────
#define DHT_PIN      4
#define DHT_TYPE     DHT11
#define LDR_PIN      34
#define LLUVIA_PIN   35
#define SERVO_PIN    26   // molino, actuador del DHT11
#define LED_PIN      23
#define BUZZER_PIN   25

// ── Umbrales ───────────────────────────────
#define TEMP_MAX        30.0
#define HUM_MAX         80.0
#define LUZ_UMBRAL      400
#define LLUVIA_UMBRAL   2000
#define BUZZER_TONO     1000

DHT dht(DHT_PIN, DHT_TYPE);
LiquidCrystal_I2C lcd(0x27, 16, 2);
Servo molino;

void setup() {
  Serial.begin(115200);
  dht.begin();

  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  noTone(BUZZER_PIN);

  molino.attach(SERVO_PIN);
  molino.write(0);

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Iniciando...");
  delay(2000);
}

void girarMolino() {
  for (int angulo = 0; angulo <= 180; angulo += 5) {
    molino.write(angulo);
    delay(15);
  }
  for (int angulo = 180; angulo >= 0; angulo -= 5) {
    molino.write(angulo);
    delay(15);
  }
}

void loop() {
  float temp = dht.readTemperature();
  float hum  = dht.readHumidity();

  if (isnan(temp) || isnan(hum)) {
    Serial.println("ERROR_DHT,0,0,0");
    delay(2000);
    return;
  }

  int luz_raw    = analogRead(LDR_PIN);
  int lluvia_raw = analogRead(LLUVIA_PIN);

  bool molino_on = (temp > TEMP_MAX || hum > HUM_MAX);
  bool led_on    = (luz_raw < LUZ_UMBRAL);
  bool lluvia_on = (lluvia_raw < LLUVIA_UMBRAL);

  if (molino_on) {
    girarMolino();
  }

  digitalWrite(LED_PIN, led_on ? HIGH : LOW);

  if (lluvia_on) {
    tone(BUZZER_PIN, BUZZER_TONO);
  } else {
    noTone(BUZZER_PIN);
  }

  Serial.print(temp);       Serial.print(",");
  Serial.print(hum);        Serial.print(",");
  Serial.print(luz_raw);    Serial.print(",");
  Serial.println(lluvia_raw);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("T:"); lcd.print(temp, 1);
  lcd.print("C H:"); lcd.print((int)hum); lcd.print("%");
  lcd.setCursor(0, 1);
  lcd.print(lluvia_on ? "LLUVIA " : "Seco   ");
  lcd.print(molino_on ? "MOLINO" : "      ");

  delay(500);
}