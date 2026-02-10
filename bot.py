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

@bot.event
async def on_ready():
    print("Bot sudah online")
    print("Command terdaftar:", [c.name for c in bot.commands])

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
        # Zona entry berbasis support
        jarak_support = abs(harga - support1) / support1 * 100

        if harga < support2:
            zona_entry = "🔴 HINDARI"
            alasan_zona = "Support 2 jebol, risiko downtrend"
        elif jarak_support <= 2:
            zona_entry = "🟢 IDEAL (EKSEKUSI)"
            alasan_zona = "Harga sangat dekat support kuat"
        elif jarak_support <= 5:
            zona_entry = "🟡 BOLEH (AGRESIF)"
            alasan_zona = "Harga masih wajar di atas support"
        else:
            zona_entry = "🔴 HINDARI"
            alasan_zona = "Harga terlalu jauh dari support"
        
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
             f"Zona Entry : {zona_entry}\n"
             f"Catatan      : {alasan_zona}\n"
       )
      
    except Exception as e:
        await ctx.send("⚠️ Terjadi error saat analisa")

@bot.command()
async def scalping(ctx, min_harga: int = 0, max_harga: int = 10_000_000):
    rekom = []

    await ctx.send("🔍 Mencari peluang scalping (target minimal +3%)...")

    for kode in SAHAM_ALL:
        saham = yf.Ticker(kode + ".JK")
        data = saham.history(period="3mo")

        if data.empty or len(data) < 50:
            continue

        close = data["Close"]
        high = data["High"]
        low = data["Low"]

        harga = int(close.iloc[-1])

        # filter harga (opsional)
        if harga < min_harga or harga > max_harga:
            continue

        # MA
        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]

        # RSI
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        rs = gain.rolling(14).mean() / loss.rolling(14).mean()
        rsi = 100 - (100 / (1 + rs))
        rsi_val = rsi.iloc[-1]

        # target realistis (lihat high 20 hari)
        target_wajar = high.tail(20).max()
        potensi_naik = (target_wajar - harga) / harga * 100

        # ===== FILTER KERAS =====
        if (
            potensi_naik >= 3 and          # peluang minimal 3%
            ma20 >= ma50 and               # arah tidak melawan
            rsi_val <= 65                  # belum kemahalan
        ):
            entry_bawah = int(harga * 0.98)
            entry_atas = harga
            target = int(harga * 1.03)
            sl = int(harga * 0.99)

            rekom.append({
                "kode": kode,
                "harga": harga,
                "entry": f"{entry_bawah} – {entry_atas}",
                "target": target,
                "sl": sl,
                "alasan": "harga masih punya ruang naik, risiko masih masuk akal"
            })

    # ===== HASIL =====
    if not rekom:
        await ctx.send(
            "⚡ REKOMENDASI SCALPING\n\n"
            "❌ Tidak ada saham dengan peluang naik ≥3% saat ini.\n"
            "Catatan: kondisi pasar kurang ideal, lebih baik menunggu."
        )
        return

    pesan = "⚡ REKOMENDASI SCALPING (POTENSI ≥3%)\n\n"

    for i, r in enumerate(rekom[:5], start=1):
        pesan += (
            f"{i}️⃣ {r['kode']}\n"
            f"Harga sekarang : {r['harga']}\n"
            f"Masuk ideal    : {r['entry']} (tunggu turun dikit, jangan kejar)\n"
            f"Target         : {r['target']} (+3%)\n"
            f"Batas rugi     : {r['sl']} (-1%)\n"
            f"Alasan         : {r['alasan']}\n\n"
        )

    pesan += "Catatan: kalau harga sudah di atas area masuk, lebih baik tunggu."

    await ctx.send(pesan)

@bot.command()
async def swing(ctx, min_harga: int = 0, max_harga: int = 10_000_000):
    rekom = []

    await ctx.send("🔍 Mencari peluang swing (potensi naik ≥3%)...")

    for kode in SAHAM_ALL:
        saham = yf.Ticker(kode + ".JK")
        data = saham.history(period="6mo")

        if data.empty or len(data) < 80:
            continue

        close = data["Close"]
        high = data["High"]
        low = data["Low"]

        harga = int(close.iloc[-1])

        # filter harga (opsional)
        if harga < min_harga or harga > max_harga:
            continue

        # MA
        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]

        # RSI
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        rs = gain.rolling(14).mean() / loss.rolling(14).mean()
        rsi = 100 - (100 / (1 + rs))
        rsi_val = rsi.iloc[-1]

        # target wajar (lihat high 50 hari)
        target_wajar = high.tail(50).max()
        potensi_naik = (target_wajar - harga) / harga * 100

        # ===== FILTER SWING (LEBIH KETAT) =====
        if (
            potensi_naik >= 3 and          # ruang naik ada
            ma20 > ma50 and                # arah naik jelas
            rsi_val <= 70                  # belum kepanasan
        ):
            entry_bawah = int(harga * 0.98)
            entry_atas = harga
            target = int(harga * 1.05)     # target swing 5%
            sl = int(harga * 0.975)         # batas rugi lebih longgar

            rekom.append({
                "kode": kode,
                "harga": harga,
                "entry": f"{entry_bawah} – {entry_atas}",
                "target": target,
                "sl": sl,
                "alasan": "arah naik masih kuat, ruang ke atas masih terbuka"
            })

    # ===== HASIL =====
    if not rekom:
        await ctx.send(
            "⏳ REKOMENDASI SWING (POTENSI ≥3%)\n\n"
            "❌ Tidak ada saham yang layak ditahan saat ini.\n"
            "Catatan: kondisi belum mendukung, lebih baik menunggu."
        )
        return

    pesan = "⏳ REKOMENDASI SWING (POTENSI ≥3%)\n\n"

    for i, r in enumerate(rekom[:5], start=1):
        pesan += (
            f"{i}️⃣ {r['kode']}\n"
            f"Harga sekarang : {r['harga']}\n"
            f"Masuk ideal    : {r['entry']} (beli di area bawah, jangan kejar)\n"
            f"Target         : {r['target']} (~5%)\n"
            f"Batas rugi     : {r['sl']} (~2.5%)\n"
            f"Alasan         : {r['alasan']}\n\n"
        )

    pesan += "Catatan: swing butuh sabar, jangan panik dengan fluktuasi kecil."

    await ctx.send(pesan)

@bot.command()
async def bsjp(ctx, min_harga: int = 0, max_harga: int = 10_000_000):
    rekom = []

    await ctx.send("🔍 Mencari peluang beli sore jual pagi (potensi ≥3%)...")

    for kode in SAHAM_ALL:
        saham = yf.Ticker(kode + ".JK")
        data = saham.history(period="3mo")

        if data.empty or len(data) < 30:
            continue

        close = data["Close"]
        high = data["High"]
        low = data["Low"]

        harga = int(close.iloc[-1])

        # filter harga (opsional)
        if harga < min_harga or harga > max_harga:
            continue

        # MA pendek
        ma5 = close.rolling(5).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]

        # RSI
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        rs = gain.rolling(14).mean() / loss.rolling(14).mean()
        rsi = 100 - (100 / (1 + rs))
        rsi_val = rsi.iloc[-1]

        # support pendek (10 hari)
        support_pendek = low.tail(10).min()
        jarak_support = (harga - support_pendek) / support_pendek * 100

        # target cepat (lihat high 10 hari)
        target_wajar = high.tail(10).max()
        potensi_naik = (target_wajar - harga) / harga * 100

        # ===== FILTER BSJP =====
        if (
            potensi_naik >= 3 and          # masih ada ruang mantul
            jarak_support <= 3 and         # dekat area bawah
            rsi_val <= 45 and              # sudah agak ditekan
            ma5 >= ma20                    # mulai ditahan
        ):
            entry_bawah = int(harga * 0.98)
            entry_atas = harga
            target = int(harga * 1.03)
            sl = int(harga * 0.99)

            rekom.append({
                "kode": kode,
                "harga": harga,
                "entry": f"{entry_bawah} – {entry_atas}",
                "target": target,
                "sl": sl,
                "alasan": "harga dekat area bawah, sering mantul cepat keesokan hari"
            })

    # ===== HASIL =====
    if not rekom:
        await ctx.send(
            "🌙 BELI SORE JUAL PAGI (BSJP)\n\n"
            "❌ Tidak ada saham yang peluang pantulnya aman saat ini.\n"
            "Catatan: kondisi kurang ideal, lebih baik menunggu."
        )
        return

    pesan = "🌙 BELI SORE JUAL PAGI (BSJP) – POTENSI ≥3%\n\n"

    for i, r in enumerate(rekom[:5], start=1):
        pesan += (
            f"{i}️⃣ {r['kode']}\n"
            f"Harga sekarang : {r['harga']}\n"
            f"Masuk ideal    : {r['entry']} (beli sore, jangan kejar)\n"
            f"Target         : {r['target']} (+3%)\n"
            f"Batas rugi     : {r['sl']} (-1%)\n"
            f"Alasan         : {r['alasan']}\n\n"
        )

    pesan += "Catatan: BSJP fokus cepat, disiplin batas rugi."

    await ctx.send(pesan)

bot.run(TOKEN)
