import os
import json
import asyncio
import discord
from discord.ext import commands
from datetime import datetime, timedelta

# ===============================
# 기본 설정
# ===============================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"
user_data = {}

# ===============================
# 데이터 관리
# ===============================
def load_data():
    global user_data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            user_data = json.load(f)
            print("📂 데이터 불러오기 완료")
    else:
        user_data = {}
        print("📁 새 데이터 파일 생성")

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)
    print("💾 데이터 저장 완료")

# ===============================
# 자동 저장 루프
# ===============================
async def autosave_loop():
    while True:
        await asyncio.sleep(60)
        save_data()

# ===============================
# 유저 관리
# ===============================
def get_user(uid, name):
    if uid not in user_data:
        user_data[uid] = {
            "name": name,
            "exp": 0,
            "level": 1,
            "last_check": None,
            "last_greet": None
        }
    return user_data[uid]

def add_exp(uid, amount):
    user = user_data[uid]
    user["exp"] += amount
    if user["exp"] >= user["level"] * 100:
        user["exp"] -= user["level"] * 100
        user["level"] += 1
        return True
    return False

# ===============================
# 봇 준비 시
# ===============================
@bot.event
async def on_ready():
    load_data()
    print(f"✅ 봇 로그인 완료: {bot.user}")
    bot.loop.create_task(autosave_loop())

# ===============================
# 명령어
# ===============================
@bot.command()
async def 출석(ctx):
    uid = str(ctx.author.id)
    name = ctx.author.display_name
    user = get_user(uid, name)

    now = datetime.now()
    if user["last_check"]:
        last = datetime.fromisoformat(user["last_check"])
        if now.date() == last.date():
            await ctx.send(f"{name}님, 이미 오늘은 출석을 하셨어요!")
            return

    user["last_check"] = now.isoformat()
    leveled_up = add_exp(uid, 10)
    save_data()
    msg = f"✅ {name}님 출석 완료! +10 EXP"
    if leveled_up:
        msg += f"\n🎉 레벨업! 현재 레벨: {user['level']}"
    await ctx.send(msg)

@bot.command()
async def 인사(ctx):
    uid = str(ctx.author.id)
    name = ctx.author.display_name
    user = get_user(uid, name)

    now = datetime.now()
    if user["last_greet"]:
        last = datetime.fromisoformat(user["last_greet"])
        if now - last < timedelta(hours=3):
            remain = timedelta(hours=3) - (now - last)
            await ctx.send(f"{name}님, 인사는 {remain.seconds // 3600}시간 후에 다시 가능해요 ⏳")
            return

    user["last_greet"] = now.isoformat()
    leveled_up = add_exp(uid, 5)
    save_data()
    msg = f"👋 {name}님이 인사했어요! +5 EXP"
    if leveled_up:
        msg += f"\n🎉 레벨업! 현재 레벨: {user['level']}"
    await ctx.send(msg)

@bot.command()
async def 내정보(ctx):
    uid = str(ctx.author.id)
    name = ctx.author.display_name
    if uid not in user_data:
        await ctx.send(f"{name}님, 아직 출석체크를 한 적이 없어요!")
        return
    user = user_data[uid]
    await ctx.send(f"📊 {name}님의 정보\n레벨: {user['level']}\n경험치: {user['exp']} / {user['level']*100}")

@bot.command()
async def 랭킹(ctx):
    if not user_data:
        await ctx.send("아직 등록된 유저가 없습니다.")
        return

    sorted_users = sorted(
        user_data.items(),
        key=lambda x: (x[1]["level"], x[1]["exp"]),
        reverse=True
    )
    top = sorted_users[:10]

    embed = discord.Embed(
        title="🏆 서버 랭킹 TOP 10",
        description="레벨과 경험치 기준 상위 10명입니다!",
        color=discord.Color.gold()
    )

    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, data) in enumerate(top, start=1):
        name = data["name"]
        level = data["level"]
        exp = data["exp"]
        icon = medals[i-1] if i <= 3 else f"#{i}"
        embed.add_field(
            name=f"{icon} {name}",
            value=f"레벨: **{level}** ｜ 경험치: **{exp} / {level * 100}**",
            inline=False
        )

    embed.set_footer(
        text=f"명령어 실행자: {ctx.author.display_name}",
        icon_url=ctx.author.display_avatar.url
    )
    await ctx.send(embed=embed)

@bot.command()
async def 도움말(ctx):
    help_text = (
        "📘 **도움말 목록**\n"
        "`!출석` - 하루 1회 출석체크 (10 EXP)\n"
        "`!인사` - 3시간마다 인사 가능 (5 EXP)\n"
        "`!내정보` - 내 경험치/레벨 보기\n"
        "`!랭킹` - 레벨 상위 10명 보기\n"
        "`!도움말` - 이 메시지 보기"
    )
    await ctx.send(help_text)

# ===============================
# 봇 실행
# ===============================
TOKEN = os.environ.get("DISCORD_TOKEN")

if not TOKEN:
    print("🚨 환경 변수 DISCORD_TOKEN이 설정되지 않았습니다!")
else:
    bot.run(TOKEN)
