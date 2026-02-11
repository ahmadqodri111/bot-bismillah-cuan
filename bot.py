import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd

from saham_list import SAHAM_ALL

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
# ENGINE ANALISA INTI
# ==============================

def hitung_indikator(data):
    close = data["Close"]
    high = data["High"]
    low = data["Low"]
    volume = data["Volume"]

    harga = close.iloc[-1]

    ma5 = close.rolling(5).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    rsi = 100 - (100 / (1 + rs))
    rsi_val = rsi.iloc[-1]

    avg_vol = volume.tail(20).mean()
    vol_now = volume.iloc[-1]

    support20 = low.tail(20).min()
    resistance20 = high.tail(20).max()
    resistance50 = high.tail(50).max()

    return {
        "harga": harga,
        "ma5": ma5,
        "ma20": ma20,
        "ma50": ma50,
        "rsi": rsi_val,
        "avg_vol": avg_vol,
        "vol_now": vol_now,
        "support20": support20,
        "res20": resistance20,
        "res50": resistance50
    }

# ==============================
# BOT READY
# ==============================

@bot.event
async def on_ready():
    print("Bot sudah online")
    print("Command:", [c.name for c in bot.commands])

# ==============================
# MODE ANALISA (KONSERVATIF)
# ==============================

@bot.command()
async def analisa(ctx, kode: str):
    try:
        saham = yf.Ticker(kode + ".JK")
        data = saham.history(period="6mo")

        if data.empty or len(data) < 60:
            await ctx.send("Data tidak cukup.")
            return

        ind = hitung_indikator(data)

        harga = int(ind["harga"])
        support = int(ind["support20"])
        resistance = int(ind["res20"])

        rr_target = resistance - harga
        rr_risk = harga - support

        if rr_risk <= 0:
            rr_ratio = 0
        else:
            rr_ratio = round(rr_target / rr_risk, 2)

        trend = "Bullish" if ind["ma20"] > ind["ma50"] else "Bearish"

        await ctx.send(
            f"📊 ANALISA {kode.upper()}\n\n"
            f"Harga        : {harga}\n"
            f"Trend        : {trend}\n"
            f"Support      : {support}\n"
            f"Resistance   : {resistance}\n"
            f"Risk/Reward  : {rr_ratio}\n"
        )

    except:
        await ctx.send("Terjadi error.")

# ==============================
# MODE CEPAT (MOMENTUM 5-8%)
# ==============================

@bot.command()
async def cepat(ctx):
    rekom = []

    await ctx.send("🚀 Scan momentum cepat...")

    for kode in SAHAM_ALL:
        try:
            saham = yf.Ticker(kode + ".JK")
            data = saham.history(period="3mo")

            if data.empty or len(data) < 40:
                continue

            ind = hitung_indikator(data)

            if (
                ind["harga"] >= ind["res20"] * 0.99 and
                ind["vol_now"] > ind["avg_vol"] * 1.2 and
                50 <= ind["rsi"] <= 75 and
                ind["ma5"] > ind["ma20"]
            ):
                rekom.append((kode, ind["harga"]))

        except:
            continue

    if not rekom:
        await ctx.send("Tidak ada momentum kuat hari ini.")
        return

    pesan = "🚀 MOMENTUM CEPAT\n\n"

    for i, r in enumerate(rekom[:3], start=1):
        target = int(r[1] * 1.07)
        sl = int(r[1] * 0.97)

        pesan += (
            f"{i}. {r[0]}\n"
            f"Harga : {int(r[1])}\n"
            f"Target: {target}\n"
            f"SL    : {sl}\n\n"
        )

    await ctx.send(pesan)

# ==============================
# MODE SWING
# ==============================

@bot.command()
async def swing(ctx):
    rekom = []

    await ctx.send("📈 Scan swing...")

    for kode in SAHAM_ALL:
        try:
            saham = yf.Ticker(kode + ".JK")
            data = saham.history(period="6mo")

            if data.empty or len(data) < 60:
                continue

            ind = hitung_indikator(data)

            if (
                ind["ma20"] > ind["ma50"] and
                ind["harga"] >= ind["res50"] * 0.99 and
                ind["vol_now"] > ind["avg_vol"]
            ):
                rekom.append((kode, ind["harga"]))

        except:
            continue

    if not rekom:
        await ctx.send("Tidak ada swing valid.")
        return

    pesan = "📈 SWING SETUP\n\n"

    for i, r in enumerate(rekom[:3], start=1):
        target = int(r[1] * 1.12)
        sl = int(r[1] * 0.95)

        pesan += (
            f"{i}. {r[0]}\n"
            f"Harga : {int(r[1])}\n"
            f"Target: {target}\n"
            f"SL    : {sl}\n\n"
        )

    await ctx.send(pesan)

# ==============================
# MODE REKOM (SCORING SYSTEM)
# ==============================

@bot.command()
async def rekom(ctx):
    hasil = []

    await ctx.send("🔎 Scan rekom hari ini...")

    for kode in SAHAM_ALL:
        try:
            saham = yf.Ticker(kode + ".JK")
            data = saham.history(period="3mo")

            if data.empty or len(data) < 40:
                continue

            ind = hitung_indikator(data)

            skor = 0

            if ind["ma20"] > ind["ma50"]:
                skor += 1
            if ind["vol_now"] > ind["avg_vol"]:
                skor += 1
            if 50 <= ind["rsi"] <= 70:
                skor += 1
            if ind["harga"] >= ind["res20"] * 0.98:
                skor += 1
            if ind["harga"] <= ind["support20"] * 1.03:
                skor += 1

            if skor >= 3:
                hasil.append((kode, skor, ind["harga"]))

        except:
            continue

    if not hasil:
        await ctx.send("Tidak ada peluang menarik hari ini.")
        return

    hasil.sort(key=lambda x: x[1], reverse=True)

    pesan = "🔥 REKOM HARI INI\n\n"

    for i, r in enumerate(hasil[:3], start=1):
        pesan += (
            f"{i}. {r[0]} | Skor: {r[1]}\n"
            f"Harga: {int(r[2])}\n\n"
        )

    await ctx.send(pesan)

bot.run(TOKEN)
