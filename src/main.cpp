#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <HTTPUpdate.h> 


const char* ssid = "Dungeon";
const char* password = "86536969";

const char* mqtt_server = "e61156f4a33e444ba4cb7d478922e532.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_user = "Pinut6969";
const char* mqtt_pass = "Pinut6969";

#define TFT_CS     5
#define TFT_RST    4 
#define TFT_DC     2

Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_RST);
WiFiClientSecure espClient;
PubSubClient client(espClient);

void runOTA(String url) {
    tft.fillScreen(ST77XX_BLACK);
    tft.setCursor(0, 40);
    tft.setTextColor(ST77XX_YELLOW);
    tft.println("OTA UPDATE STARTED...");
    tft.println("Please wait...");
    
    Serial.println("Starting OTA from: " + url);

    // Важно: для скачивания прошивки по HTTPS тоже нужен Insecure режим
    WiFiClientSecure updateClient;
    updateClient.setInsecure();

    // Запускаем обновление
    t_httpUpdate_return ret = httpUpdate.update(updateClient, url);

    switch (ret) {
        case HTTP_UPDATE_FAILED:
            Serial.printf("OTA Failed (%d): %s\n", httpUpdate.getLastError(), httpUpdate.getLastErrorString().c_str());
            tft.fillScreen(ST77XX_RED);
            tft.setCursor(0, 40);
            tft.println("OTA FAILED!");
            delay(5000);
            break;

        case HTTP_UPDATE_NO_UPDATES:
            Serial.println("No updates found.");
            break;

        case HTTP_UPDATE_OK:
            Serial.println("OTA OK!"); 
            // Плата сама уйдет в ребут
            break;
    }
}

void callback(char* topic, byte* payload, unsigned int length) {
    String msgTopic = String(topic);
    
    // 1. Логика отрисовки картинок
    if (msgTopic == "esp32/display") {
        tft.setRotation(1);
        tft.drawRGBBitmap(0, 0, (uint16_t*)payload, 160, 128);
    } 
    
    // 2. Логика OTA обновления
    else if (msgTopic == "esp32/ota") {
        char message[length + 1];
        memcpy(message, payload, length);
        message[length] = '\0';
        String url = String(message);
        
        runOTA(url);
    }
}

void setup() {
    Serial.begin(115200);
    tft.initR(INITR_BLACKTAB);
    tft.fillScreen(ST77XX_BLACK);
    tft.println("Connecting WiFi...");

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) { delay(500); }
    
    tft.fillScreen(ST77XX_BLACK);
    tft.println("WiFi OK. Connecting MQTT...");

    // Настройка безопасности TLS
    espClient.setInsecure(); // Пропускаем проверку цепочки сертификатов для экономии ОЗУ

    client.setServer(mqtt_server, mqtt_port);
    client.setCallback(callback);
    
    // ВАЖНО: Резервируем буфер под картинку 160*128*2 байта + заголовки
    client.setBufferSize(42000); 

    client.subscribe("esp32/display");
    client.subscribe("esp32/ota");
}

void reconnect() {
    while (!client.connected()) {
        Serial.print("NEW VERSION: Attempting MQTT connection...");
        if (client.connect("ESP32_Client", mqtt_user, mqtt_pass)) {
            Serial.println("connected");
            client.subscribe("esp32/display");
            client.subscribe("esp32/ota"); // Подписка при переподключении
        } else {
            delay(5000);
        }
    }
}

void loop() {
    if (!client.connected()) reconnect();
    client.loop();
}