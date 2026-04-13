import struct
import time
import io
import paho.mqtt.client as mqtt
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- НАСТРОЙКИ ---
MQTT_BROKER = "e61156f4a33e444ba4cb7d478922e532.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "Pinut6969"
MQTT_PASS = "Pinut6969"
MQTT_TOPIC = "esp32/display"
TELEGRAM_TOKEN = "8510999438:AAEnXLBxbHn27Z7mUy5OfeDmcdWENHBjoKE"

WIDTH, HEIGHT = 160, 128


def convert_to_rgb565(img):
    """Финальная конвертация PIL Image в байты RGB565"""
    img = img.convert("RGB")
    img.thumbnail((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    background = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    offset = ((WIDTH - img.width) // 2, (HEIGHT - img.height) // 2)
    background.paste(img, offset)

    pixels = background.load()
    output = bytearray()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g, b = pixels[x, y]
            rgb = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            output.extend(struct.pack("<H", rgb))
    return output


def create_emoji_image(emoji_text):
    """Рисует эмодзи на черном фоне"""
    img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Попробуй путь к шрифту, если ОС Windows: "seguiemj.ttf" или Linux: "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
    try:
        font = ImageFont.truetype("arial.ttf", 80)
    except:
        font = ImageFont.load_default()

    # Центрируем текст
    left, top, right, bottom = draw.textbbox((0, 0), emoji_text, font=font)
    draw.text(((WIDTH - (right - left)) / 2, (HEIGHT - (bottom - top)) / 2), emoji_text, font=font, embedded_color=True)
    return img


async def send_to_mqtt(raw_data):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.tls_set()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.publish(MQTT_TOPIC, raw_data, qos=1)
    time.sleep(1)
    client.disconnect()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_data = None

    # 1. Если это ФОТО или СТИКЕР или GIF (Animation)
    if update.message.photo or update.message.sticker or update.message.animation:
        if update.message.photo:
            file = await update.message.photo[-1].get_file()
        elif update.message.sticker:
            if update.message.sticker.is_animated:
                await update.message.reply_text(
                    "Анимированные стикеры (.tgs) пока не поддерживаются, присылай обычные или видео!")
                return
            file = await update.message.sticker.get_file()
        else:  # Animation (GIF)
            file = await update.message.animation.get_file()

        img_bytes = await file.download_as_bytearray()
        img = Image.open(io.BytesIO(img_bytes))

        # Если это GIF/WEBP с кадрами - берем первый
        if getattr(img, "is_animated", False):
            img.seek(0)

        raw_data = convert_to_rgb565(img)

    # 2. Если это ТЕКСТ (Эмодзи)
    elif update.message.text:
        img = create_emoji_image(update.message.text)
        raw_data = convert_to_rgb565(img)

    if raw_data:
        try:
            await send_to_mqtt(raw_data)
            await update.message.reply_text("✅ Доставлено на ТВ!")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка MQTT: {e}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    # Ловим фото, стикеры, анимации и текст
    app.add_handler(
        MessageHandler(filters.PHOTO | filters.Sticker.ALL | filters.ANIMATION | filters.TEXT, handle_message))
    print("Бот запущен. Жду стикеры и эмодзи...")
    app.run_polling()