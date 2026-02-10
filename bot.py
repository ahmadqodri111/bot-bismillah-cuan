import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import yfinance as yf

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("Bot sudah online")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! Bot hidup 24 jam")
@bot.command()
async def analisa(ctx, kode: str):
    try:
        saham = yf.Ticker(kode + ".JK")
        data = saham.history(period="1d")

        if data.empty:
            await ctx.send("❌ Kode saham tidak ditemukan")
            return

        harga = int(data["Close"].iloc[-1])

        await ctx.send(
            f"📊 ANALISA {kode.upper()}\n"
            f"Harga terakhir : {harga}"
        )

    except Exception:
        await ctx.send("⚠️ Terjadi error saat ambil data")

bot.run(TOKEN)
