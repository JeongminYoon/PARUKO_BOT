from discord.ext import tasks, commands
import discord
import os
from itertools import cycle
import asyncio

# 토큰 파일에서 읽기
def get_bot_token():
    try:
        with open('token.txt', 'r', encoding='utf-8') as f:
            token = f.read().strip()
            if token == '실제_봇_토큰_여기에_입력':
                print("⚠️  token.txt 파일에 실제 봇 토큰을 입력해주세요!")
                return ''
            return token
    except FileNotFoundError:
        print("❌ token.txt 파일을 찾을 수 없습니다!")
        return ''

BOT_TOKEN = get_bot_token()

# 기본 상태 메시지 (음악 재생 안할 때)
idle_messages = ["기숙사에서 쉬는중...", "!help "]


async def main():
    
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

    

    for filename in os.listdir('./cogs'):
        if'.py'in filename:
            filename = filename.replace('.py','')
            await bot.load_extension(f"cogs.{filename}")

    # 전역 변수로 현재 재생 중인 음악 정보 저장
    current_music = None
    status_cycle = cycle(idle_messages)

    @tasks.loop(seconds=3)
    async def presence():
        if current_music:
            # 음악 재생 중일 때
            await bot.change_presence(activity=discord.Game(f"{current_music} 공연중!"))
        else:
            # 음악 재생 안할 때
            await bot.change_presence(activity=discord.Game(next(status_cycle)))

    # 음악 상태 업데이트 함수
    def update_music_status(music_title=None):
        nonlocal current_music
        current_music = music_title

    # DJ cog에 상태 업데이트 함수 전달
    bot.update_music_status = update_music_status

    @bot.event
    async def on_ready():
        print("System: Smart Falcon Ready!")
        presence.start()

    @bot.command(name="reload")
    async def reload(ctx, extenseion):
        await bot.unload_extension(f"cogs.{extenseion}")
        await bot.load_extension(f"cogs.{extenseion}")
        await ctx.send(f"{extenseion} reloaded")

    

    await bot.start(BOT_TOKEN)

asyncio.run(main())
    






