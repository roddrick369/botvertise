import asyncio
import json
import os
import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from urllib.parse import urlparse, parse_qs

API_TOKEN = ""
# URL do seu serviço (atualize conforme sua configuração; aqui continua com o ngrok, por exemplo)
service_url = ""

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

# Rota do miniapp via FastAPI
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
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
          body {{
            margin: 0;
            padding: 20px;
            background: #f0f2f5;
            font-family: Arial, sans-serif;
            text-align: center;
          }}
          button {{
            padding: 10px 20px;
            background: #0088cc;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
          }}
        </style>
        <script>
          Telegram.WebApp.ready();
          function enviarLink() {{
            const dataToSend = JSON.stringify({{
              type: "link_original",
              url: "{original_link}"
            }});
            console.log("📩 Enviando dados:", dataToSend);
            Telegram.WebApp.sendData(dataToSend);
            // Aguarda 2000ms para garantir que os dados sejam enviados
            setTimeout(() => {{
              console.log("🚪 Fechando MiniApp...");
              Telegram.WebApp.close();
            }}, 2000);
          }}
        </script>
      </head>
      <body>
        <h1>🎥 Anúncio Concluído!</h1>
        <p>Clique no botão abaixo para receber o link no chat:</p>
        <button onclick="enviarLink()">📩 Receber Link</button>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Bot do Telegram
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Olá! Use /encurtar <link> para gerar um link encurtado.")

@dp.message(Command("encurtar"))
async def encurtar_link(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Formato incorreto. Use: /encurtar <link>")
        return
    link = parts[1]
    link_id = abs(hash(link)) % 1000000
    db[str(link_id)] = link
    salvar_links(db)
    link_encurtado = f"{service_url}/webapp?l={link_id}"
    await message.answer(
        f"✅ Link encurtado gerado:\n{link_encurtado}\n\n"
        "Compartilhe esse link! Quem enviar esse link ao bot verá a propaganda antes de receber o link original."
    )

@dp.message(Command("acessar"))
async def acessar_link(message: types.Message):
    if len(message.text.split()) < 2:
        await message.answer("❌ Formato incorreto. Exemplo: /acessar <link_encurtado>")
        return
    url = message.text.split()[1]
    parsed_url = urlparse(url)
    link_id = parse_qs(parsed_url.query).get("l", [None])[0]
    if not link_id:
        await message.answer("❌ Link inválido. Certifique-se de usar o link completo!")
        return
    original_link = db.get(str(link_id))
    if not original_link:
        await message.answer("❌ Link não encontrado. Pode ter expirado!")
        return

    # Usa KeyboardButton para abrir o miniapp via ReplyKeyboardMarkup
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(
                text="👀 Ver Anúncio",
                web_app=types.WebAppInfo(url=f"{service_url}/webapp?l={link_id}")
            )]
        ],
        resize_keyboard=True
    )
    await message.answer("🔍 Clique para visualizar o anúncio:", reply_markup=keyboard)

# Handler para capturar os dados enviados pelo miniapp usando um lambda filter
@dp.message(lambda message: message.web_app_data is not None)
async def handle_web_app_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        print("📩 Dados recebidos do MiniApp:", data)
        if data.get("type") == "link_original":
            await message.answer(
                text=f"🔗 Link original: {data['url']}",
                disable_web_page_preview=True
            )
    except json.JSONDecodeError:
        print("Erro: Dados inválidos (não é JSON).")
    except KeyError:
        print("Erro: Campo 'url' ausente nos dados.")
    except Exception as e:
        print(f"Erro inesperado: {e}")

# Inicializa o WebApp (FastAPI) e o Bot juntos
async def start_webapp():
    port = int(os.environ.get("PORT", 10000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def start_bot():
    print("🔄 Iniciando o bot do Telegram...")
    await bot.delete_webhook()
    await dp.start_polling(bot)

async def main():
    task_bot = asyncio.create_task(start_bot())
    task_webapp = asyncio.create_task(start_webapp())
    await asyncio.gather(task_bot, task_webapp)

if __name__ == "__main__":
    asyncio.run(main())
