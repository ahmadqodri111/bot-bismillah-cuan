import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd

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
        data = saham.history(period="3mo")

        if data.empty:
            await ctx.send("❌ Kode saham tidak ditemukan")
            return

        close = data["Close"]

        # Moving Average
        ma20 = close.rolling(window=20).mean().iloc[-1]
        ma50 = close.rolling(window=50).mean().iloc[-1]

        # RSI
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi_val = rsi.iloc[-1]

        harga = int(close.iloc[-1])

        # Trend
        if ma20 > ma50:
            trend = "📈 Bullish"
        else:
            trend = "📉 Bearish"

        # Gaya trading
        selisih_ma = abs(ma20 - ma50) / ma50 * 100

        if selisih_ma < 1 and 40 <= rsi_val <= 60:
            gaya = "⚡ Scalping"
        else:
            gaya = "⏳ Swing"

        # Entry, TP, SL
        entry = harga

        if gaya == "⚡ Scalping":
            tp = int(entry * 1.02)
            sl = int(entry * 0.99)
        else:
            tp = int(entry * 1.05)
            sl = int(entry * 0.975)

        # Support level
        support1 = int(data["Low"].tail(20).min())
        support2 = int(data["Low"].tail(50).min())

        if harga < support2:
            breakdown = "🔴 Support 2 jebol → Potensi Downtrend"
        elif harga < support1:
            breakdown = "🟡 Waspada (di bawah support kuat)"
        else:
            breakdown = "🟢 Aman di atas support"
        # Validasi entry di support
        jarak_support = abs(harga - support1) / support1 * 100

        if (
            jarak_support <= 1 and
            harga >= support2 and
            trend != "📉 Bearish" and
            rsi_val <= 65
        ):
            entry_valid = "✅ Ya"
            alasan_entry = "Harga dekat support kuat + trend mendukung"
        else:
            entry_valid = "❌ Tidak"
            alasan_entry = "Belum ada konfirmasi support"

        # Sinyal
        if rsi_val < 30 and ma20 > ma50:
            sinyal = "🟢 Layak dipantau"
        elif rsi_val > 70:
            sinyal = "🔴 Waspada (overbought)"
        else:
            sinyal = "🟡 Netral"

        await ctx.send(
             f"📊 ANALISA {kode.upper()}\n"
             f"Harga : {harga}\n"
             f"MA20   : {int(ma20)}\n"
             f"MA50   : {int(ma50)}\n"
             f"RSI    : {rsi_val:.2f}\n"
             f"Trend  : {trend}\n"
             f"Gaya   : {gaya}\n"
             f"Entry  : {entry}\n"
             f"TP     : {tp}\n"
             f"SL     : {sl}\n"
             f"Support 1 : {support1}\n"
             f"Support 2 : {support2}\n"
             f"Status S  : {breakdown}\n"
             f"Sinyal : {sinyal}\n"
             f"Entry Valid : {entry_valid}\n"
             f"Alasan      : {alasan_entry}\n"
       )
      
    except Exception as e:
        await ctx.send("⚠️ Terjadi error saat analisa")

bot.run(TOKEN)
