import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

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
async def analisa(ctx):
    await ctx.send("📊 Analisa saham: fitur sedang disiapkan")

bot.run(TOKEN)
