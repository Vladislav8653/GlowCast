#include <Arduino.h>
#include <Adafruit_GFX.h>    // Ядро графической библиотеки
#include <Adafruit_ST7735.h> // Библиотека для ST7735
#include <SPI.h>

#define TFT_CS     5
#define TFT_RST    4 
#define TFT_DC     2

Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS,  TFT_DC, TFT_RST);

void setup() {
  Serial.begin(115200);

  // Инициализация дисплея (для 1.8" обычно используется INITR_BLACKTAB)
  tft.initR(INITR_BLACKTAB); 
  
  tft.fillScreen(ST77XX_WHITE); // Заливка черным
  
  // Настройка текста
  tft.setCursor(10, 30);        // Координаты X, Y
  tft.setTextColor(ST77XX_YELLOW); 
  tft.setTextSize(2);           // Масштаб текста
  tft.println("ESP32 TEST");

  tft.setCursor(10, 60);
  tft.setTextColor(ST77XX_GREEN);
  tft.setTextSize(1);
  tft.println("Hello, Gemini!");
  
  // Рисуем простой символ (круг)
  tft.drawCircle(64, 100, 20, ST77XX_RED);
}

void loop() {
  // Здесь можно обновлять данные, например, выводить счетчик
}

