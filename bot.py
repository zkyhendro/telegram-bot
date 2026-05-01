import os
import aiohttp
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

load_dotenv()

TELEGRAM_TOKEN = "8515585947:AAEoRMswbRCUqqoyuwx_QKeF_8-RenblRfA"
HF_API_KEY = os.getenv("HF_API_KEY")

user_mode = {}

async def generate_image_hf(prompt):
    url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json={"inputs": prompt}) as resp:
            if resp.status == 200:
                return await resp.read()
            else:
                text = await resp.text()
                raise Exception(f"HF Error {resp.status}: {text}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🖼️ Text to Image", callback_data="mode_t2i")],
        [InlineKeyboardButton("🔄 Image to Image", callback_data="mode_i2i")],
        [InlineKeyboardButton("🎬 Image to Video", callback_data="mode_i2v")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Halo! Saya bot AI generator.\nPilih mode yang kamu inginkan:",
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
        await query.edit_message_text("🎬 Mode: Image to Video\nFitur ini butuh Replicate. Pilih mode lain dulu.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    mode = user_mode.get(uid)
    if not mode:
        await update.message.reply_text("Pilih mode dulu dengan /start")
        return
    if mode == "mode_t2i":
        prompt = update.message.text
        msg = await update.message.reply_text("⏳ Generating image, mohon tunggu 30-60 detik...")
        try:
            image_bytes = await generate_image_hf(prompt)
            await update.message.reply_photo(photo=image_bytes, caption=f"✅ {prompt}")
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
    if mode == "mode_i2i":
        prompt = update.message.caption or "enhance this image"
        msg = await update.message.reply_text("⏳ Processing...")
        try:
            image_bytes = await generate_image_hf(prompt)
            await update.message.reply_photo(photo=image_bytes, caption=f"✅ {prompt}")
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)}")
    else:
        await update.message.reply_text("Mode ini tidak butuh foto.")

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