import struct
import paho.mqtt.client as mqtt
from PIL import Image

WIDTH = 160
HEIGHT = 128


def convert_to_rgb565(image_path):
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    background = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    offset = ((WIDTH - img.width) // 2, (HEIGHT - img.height) // 2)
    background.paste(img, offset)

    pixels = background.load()
    output = bytearray()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g, b = pixels[x, y]
            # Формат RGB565 (Big Endian)
            rgb = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            output.extend(struct.pack("<H", rgb))
    print(output)
    return output


def send_image():
    # Создаем клиент (Callback API v2 для совместимости)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    # Настройка TLS (обязательно для порта 8883)
    client.tls_set()

    # Авторизация
    client.username_pw_set(MQTT_USER, MQTT_PASS)

    print(f"Подключение к {MQTT_BROKER}...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)

        print("Конвертация картинки...")
        image_data = convert_to_rgb565("sticker2.png"
                                       "")
        print(f"Отправка {len(image_data)} байт...")
        #Используем qos=1 для надежности доставки тяжелых данных
        client.publish(MQTT_TOPIC, image_data, qos=1)
        # Вместо байтов картинки отправляем простую строку-ссылку
        #client.publish("esp32/ota", "https://your-server.com/firmware_v2.bin")

        # Даем время на завершение отправки перед разрывом
        time.sleep(2)
        client.disconnect()
        print("Успешно отправлено!")
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    import time

    send_image()