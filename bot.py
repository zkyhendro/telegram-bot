import os
import asyncio
import aiohttp
import replicate
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY")

os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_KEY

user_mode = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🖼️ Text to Image", callback_data="mode_t2i")],
        [InlineKeyboardButton("🔄 Image to Image", callback_data="mode_i2i")],
        [InlineKeyboardButton("🎬 Image to Video", callback_data="mode_i2v")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Halo! Saya bot AI generator.\nPilih mode:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    user_mode[uid] = query.data
    if query.data == "mode_t2i":
        await query.edit_message_text("🖼️ Mode: Text to Image\nKirim deskripsi gambar.")
    elif query.data == "mode_i2i":
        await query.edit_message_text("🔄 Mode: Image to Image\nKirim foto + caption prompt.")
    elif query.data == "mode_i2v":
        await query.edit_message_text("🎬 Mode: Image to Video\nKirim foto yang ingin dijadikan video.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    mode = user_mode.get(uid)
    if not mode:
        await update.message.reply_text("Pilih mode dulu dengan /start")
        return
    if mode == "mode_t2i":
        prompt = update.message.text
        msg = await update.message.reply_text("⏳ Generating image...")
        try:
            output = replicate.run(
                "black-forest-labs/flux-schnell",
                input={"prompt": prompt, "num_outputs": 1}
            )
            image_url = output[0] if isinstance(output, list) else str(output)
            await update.message.reply_photo(photo=image_url, caption=f"✅ {prompt}")
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)}")
    else:
        await update.message.reply_text("Mode ini butuh foto. Kirim foto.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    mode = user_mode.get(uid)
    if not mode:
        await update.message.reply_text("Pilih mode dulu dengan /start")
        return
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_url = file.file_path
    if mode == "mode_i2i":
        prompt = update.message.caption or "enhance this image, same style"
        msg = await update.message.reply_text("⏳ Processing image to image...")
        try:
            output = replicate.run(
                "black-forest-labs/flux-kontext-dev",
                input={"prompt": prompt, "input_image": file_url}
            )
            image_url = output[0] if isinstance(output, list) else str(output)
            await update.message.reply_photo(photo=image_url, caption=f"✅ {prompt}")
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)}")
    elif mode == "mode_i2v":
        msg = await update.message.reply_text("⏳ Converting to video (~1-2 menit)...")
        try:
            output = replicate.run(
                "lightricks/ltx-video",
                input={
                    "image": file_url,
                    "prompt": "animate this image naturally",
                    "num_frames": 49
                }
            )
            video_url = str(output)
            await update.message.reply_video(video=video_url, caption="✅ Video siap!")
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)}")
    else:
        await update.message.reply_text("Mode Text to Image tidak butuh foto.")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()