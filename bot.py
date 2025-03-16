import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

API_TOKEN = "7939343312:AAEywtJ96A6CSNR6qwxiImS5Ytpc5bSbzTE"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Olá! Envie um link usando /encurtar <link> para encurtá-lo.")

@dp.message(Command("encurtar"))
async def encurtar_link(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Por favor, envie um link válido. Exemplo: /encurtar https://exemplo.com")
        return

    link = parts[1]
    link_id = abs(hash(link)) % 1000000
    link_encurtado = f"https://exemplo.com/webapp?l={link_id}"

    await message.answer(f"✅ Seu link encurtado: {link_encurtado}")

async def main():
    print("🔄 Iniciando o bot do Telegram...")  # Log para debug
    await bot.delete_webhook()  # Remove WebHook caso esteja ativado
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
