import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
from replit import db  # Replit DB para armazenamento simples

# Substitua pelo seu token do BotFather
API_TOKEN = "7939343312:AAEywtJ96A6CSNR6qwxiImS5Ytpc5bSbzTE"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ========= Handlers do Bot =========

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
    # Gera um ID simples para o link (pode ser melhorado para evitar colisões)
    link_id = abs(hash(link)) % 1000000

    # Armazena no Replit DB: chave = link_id, valor = link original
    db[str(link_id)] = link

    # Constrói o link encurtado que aponta para o MiniApp
    # Em Replit, geralmente a URL é no formato: https://<REPL_SLUG>.<REPL_OWNER>.repl.co
    replit_url = "https://botvertise.onrender.com"
    link_encurtado = f"{replit_url}/webapp?l={link_id}"

    await message.answer(f"✅ Seu link encurtado: {link_encurtado}")

# ========= Criação do MiniApp (WebApp) com FastAPI =========

app = FastAPI()

@app.get("/webapp", response_class=HTMLResponse)
async def webapp(l: int):
    # Busca o link original no banco de dados
    original_link = db.get(str(l))
    if not original_link:
        return "Link não encontrado."

    # Página HTML que simula a exibição de anúncio e redireciona após 5 segundos
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
        <p>Em breve você será redirecionado...</p>
        <!-- Insira aqui o código do seu anúncio, se desejar -->
      </body>
    </html>
    """
    return html_content

# ========= Rodando Bot e MiniApp Conjuntamente =========

async def start_webapp():
    # Replit define a porta via variável de ambiente "PORT", ou usa 3000 por padrão
    port = int(os.environ.get("PORT", 3000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    # Remove qualquer webhook ativo, para usar polling
    await bot.delete_webhook()

    # Cria tarefas concorrentes para o bot e para o webapp
    task_bot = asyncio.create_task(dp.start_polling(bot))
    task_webapp = asyncio.create_task(start_webapp())
    await asyncio.gather(task_bot, task_webapp)

if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot))
