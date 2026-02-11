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
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ==============================
# UTIL FUNCTION
# ==============================

def hitung_indikator(data):
    close = data["Close"]
    high = data["High"]
    low = data["Low"]
    volume = data["Volume"]

    harga = close.iloc[-1]

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

    return {
        "harga": harga,
        "ma20": ma20,
        "ma50": ma50,
        "rsi": rsi_val,
        "avg_vol": avg_vol,
        "vol_now": vol_now,
        "high20": high.tail(20).max(),
        "low10": low.tail(10).min(),
        "high50": high.tail(50).max()
    }

# ==============================
# BOT READY
# ==============================

@bot.event
async def on_ready():
    print("Bot sudah online")
    print("Command terdaftar:", [c.name for c in bot.commands])

# ==============================
# HELP
# ==============================

@bot.command()
async def help(ctx):
    await ctx.send(
        "📘 DAFTAR COMMAND BOT\n\n"
        "!analisa KODE → Detail 1 saham\n"
        "Waktu: 15.30–18.00 atau malam hari\n\n"
        "!cepat → Day trade (1 hari)\n"
        "Waktu: 08.30–10.30\n\n"
        "!bsjp → Beli sore jual pagi\n"
        "Waktu: 14.30–15.00\n\n"
        "!swing → 2–4 minggu\n"
        "Waktu: Weekend / setelah market tutup\n\n"
        "!rekom → 1 terbaik hari ini\n\n"
        "Jika kosong → market tidak ideal."
    )

# ==============================
# ANALISA DETAIL
# ==============================

@bot.command()
async def analisa(ctx, kode: str):
    try:
        saham = yf.Ticker(kode + ".JK")
        data = saham.history(period="6mo")

        if data.empty:
            await ctx.send("❌ Data tidak ditemukan")
            return

        ind = hitung_indikator(data)

        trend = "📈 Bullish" if ind["ma20"] > ind["ma50"] else "📉 Bearish"

        support = int(data["Low"].tail(20).min())
        resistance = int(data["High"].tail(20).max())

        target = int(ind["harga"] * 1.05)
        sl = int(ind["harga"] * 0.97)
        rr = round((target - ind["harga"]) / (ind["harga"] - sl), 2)

        status = "🟢 Layak Entry" if rr >= 1.5 and trend == "📈 Bullish" else "🔴 Tunggu"

        await ctx.send(
            f"📊 ANALISA {kode.upper()}\n\n"
            f"Harga      : {int(ind['harga'])}\n"
            f"Trend      : {trend}\n"
            f"RSI        : {ind['rsi']:.2f}\n"
            f"Support    : {support}\n"
            f"Resistance : {resistance}\n\n"
            f"Target     : {target}\n"
            f"Stoploss   : {sl}\n"
            f"RR         : {rr}\n\n"
            f"Status     : {status}"
        )

    except:
        await ctx.send("⚠️ Error analisa")

# ==============================
# MODE CEPAT (DAY TRADE)
# ==============================

@bot.command()
async def cepat(ctx):
    rekom = []

    for kode in SAHAM_ALL:
        try:
            saham = yf.Ticker(kode + ".JK")
            data = saham.history(period="3mo")
            if data.empty or len(data) < 50:
                continue

            ind = hitung_indikator(data)

            potensi = (ind["high20"] - ind["harga"]) / ind["harga"] * 100

            if (
                potensi >= 3 and
                ind["ma20"] > ind["ma50"] and
                ind["rsi"] >= 55 and ind["rsi"] <= 70 and
                ind["vol_now"] > 1.5 * ind["avg_vol"]
            ):
                target = int(ind["harga"] * 1.04)
                sl = int(ind["harga"] * 0.97)
                rr = round((target - ind["harga"]) / (ind["harga"] - sl), 2)

                rekom.append((kode, ind["harga"], target, sl, rr))

        except:
            continue

    if not rekom:
        await ctx.send("⚡ MODE CEPAT\n\n❌ Tidak ada momentum sehat.\nStatus: 🔴 Tunggu")
        return

    rekom = sorted(rekom, key=lambda x: x[4], reverse=True)[:3]

    pesan = "⚡ MODE CEPAT (DAY TRADE)\n\n"
    for r in rekom:
        status = "🟢 Layak Entry" if r[4] >= 1.5 else "🔴 Tunggu"
        pesan += (
            f"{r[0]}\n"
            f"Harga : {int(r[1])}\n"
            f"Target: {r[2]}\n"
            f"SL    : {r[3]}\n"
            f"RR    : {r[4]}\n"
            f"Status: {status}\n\n"
        )

    await ctx.send(pesan)

# ==============================
# BSJP
# ==============================

@bot.command()
async def bsjp(ctx):
    rekom = []

    for kode in SAHAM_ALL:
        try:
            saham = yf.Ticker(kode + ".JK")
            data = saham.history(period="3mo")
            if data.empty:
                continue

            ind = hitung_indikator(data)

            jarak = (ind["harga"] - ind["low10"]) / ind["low10"] * 100

            if jarak <= 3 and ind["rsi"] <= 50:
                target = int(ind["harga"] * 1.03)
                sl = int(ind["harga"] * 0.98)
                rr = round((target - ind["harga"]) / (ind["harga"] - sl), 2)
                rekom.append((kode, ind["harga"], target, sl, rr))

        except:
            continue

    if not rekom:
        await ctx.send("🌙 MODE BSJP\n\n❌ Tidak ada pantulan sehat.\nStatus: 🔴 Tunggu")
        return

    rekom = rekom[:2]

    pesan = "🌙 MODE BSJP\n\n"
    for r in rekom:
        pesan += (
            f"{r[0]}\n"
            f"Harga : {int(r[1])}\n"
            f"Target: {r[2]}\n"
            f"SL    : {r[3]}\n\n"
        )

    await ctx.send(pesan)

# ==============================
# SWING
# ==============================

@bot.command()
async def swing(ctx):
    rekom = []

    for kode in SAHAM_ALL:
        try:
            saham = yf.Ticker(kode + ".JK")
            data = saham.history(period="6mo")
            if data.empty:
                continue

            ind = hitung_indikator(data)

            potensi = (ind["high50"] - ind["harga"]) / ind["harga"] * 100

            if potensi >= 8 and ind["ma20"] > ind["ma50"]:
                target = int(ind["harga"] * 1.1)
                sl = int(ind["harga"] * 0.94)
                rr = round((target - ind["harga"]) / (ind["harga"] - sl), 2)
                rekom.append((kode, ind["harga"], target, sl, rr))

        except:
            continue

    if not rekom:
        await ctx.send("⏳ MODE SWING\n\n❌ Tidak ada trend kuat.\nStatus: 🔴 Tunggu")
        return

    rekom = rekom[:2]

    pesan = "⏳ MODE SWING\n\n"
    for r in rekom:
        pesan += (
            f"{r[0]}\n"
            f"Harga : {int(r[1])}\n"
            f"Target: {r[2]}\n"
            f"SL    : {r[3]}\n\n"
        )

    await ctx.send(pesan)

# ==============================
# REKOM (1 TERBAIK)
# ==============================

@bot.command()
async def rekom(ctx):
    await ctx.send("🔥 REKOMENDASI HARI INI\nGunakan !cepat untuk peluang utama.")

bot.run(TOKEN)
