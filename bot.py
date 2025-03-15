import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import json
import os

API_TOKEN = "7939343312:AAEywtJ96A6CSNR6qwxiImS5Ytpc5bSbzTE"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = FastAPI()

DB_FILE = "links.json"

# Função para carregar os links salvos
def carregar_links():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

# Função para salvar os links
def salvar_links(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

db = carregar_links()

# Rota para verificar se o WebApp está online
@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h1>Bot e WebApp rodando!</h1>"

@app.get("/webapp", response_class=HTMLResponse)
async def webapp(l: int):
    db = carregar_links()
    original_link = db.get(str(l))

    if not original_link:
        return HTMLResponse("<h1>Link não encontrado.</h1>", status_code=404)

    html_content = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <title>Visualize o anúncio</title>
        <script>
          function redirect() {{
            window.location.href = "{original_link}";
          }}
          setTimeout(redirect, 5000);
        </script>
      </head>
      <body>
        <h1>Visualize o anúncio</h1>
        <p>Você será redirecionado em breve...</p>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content)

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
    db[str(link_id)] = link
    salvar_links(db)

    replit_url = "https://botvertise.onrender.com"
    link_encurtado = f"{replit_url}/webapp?l={link_id}"

    await message.answer(f"✅ Seu link encurtado: {link_encurtado}")

async def start_webapp():
    port = int(os.environ.get("PORT", 10000))  # Usa a porta do Render
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    await bot.delete_webhook()
    task_bot = asyncio.create_task(dp.start_polling(bot))
    task_webapp = asyncio.create_task(start_webapp())
    await asyncio.gather(task_bot, task_webapp)

if __name__ == "__main__":
    asyncio.run(main())
