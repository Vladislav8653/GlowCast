import struct
import time
import io
from PIL import Image
import paho.mqtt.client as mqtt
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- НАСТРОЙКИ MQTT ---
MQTT_BROKER = "e61156f4a33e444ba4cb7d478922e532.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "Pinut6969"
MQTT_PASS = "Pinut6969"
MQTT_TOPIC = "esp32/display"

# --- НАСТРОЙКИ ТЕЛЕГРАМ ---
TELEGRAM_TOKEN = "8510999438:AAEnXLBxbHn27Z7mUy5OfeDmcdWENHBjoKE"

# --- ГАБАРИТЫ ЭКРАНА ---
WIDTH = 160
HEIGHT = 128


def process_and_convert(image_bytes):
    """Обрезает 512x512, сжимает до 160x128 и конвертирует в RGB565"""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # 1. Делаем квадратный кроп (центрированный)
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) / 2
    top = (h - min_dim) / 2
    right = (w + min_dim) / 2
    bottom = (h + min_dim) / 2
    img = img.crop((left, top, right, bottom))

    # 2. Ресайз до 512x512 (как просил), а затем до 160x128 для дисплея
    img = img.resize((512, 512), Image.Resampling.LANCZOS)
    img.thumbnail((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    # 3. Создаем черный фон и центрируем (на случай, если пропорции чуть уплыли)
    background = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    offset = ((WIDTH - img.width) // 2, (HEIGHT - img.height) // 2)
    background.paste(img, offset)

    pixels = background.load()
    output = bytearray()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g, b = pixels[x, y]
            # Формат RGB565 (Little Endian для большинства библиотек ESP32)
            rgb = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            output.extend(struct.pack("<H", rgb))
    return output


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Получил фото! Обрабатываю и отправляю на ТВ...")

    try:
        # Скачиваем самое большое фото из сообщения
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()

        # Конвертируем
        raw_data = process_and_convert(image_bytes)

        # Отправляем в MQTT
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.tls_set()
        client.username_pw_set(MQTT_USER, MQTT_PASS)

        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.publish(MQTT_TOPIC, raw_data, qos=1)
        time.sleep(1)  # Даем время на отправку
        client.disconnect()

        await update.message.reply_text("✅ Картинка отправлена!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    print("Бот запущен...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Обработчик только для фото
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    app.run_polling()