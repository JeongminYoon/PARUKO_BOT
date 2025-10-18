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

    

    # 특정 Cog 파일들만 로드
    cog_files = ['DJ', 'ringing', 'help']
    for cog_name in cog_files:
        try:
            await bot.load_extension(f"cogs.{cog_name}")
            print(f"✅ {cog_name} 확장 로드 성공")
        except Exception as e:
            print(f"❌ {cog_name} 확장 로드 실패: {e}")

    # 전역 변수로 현재 재생 중인 음악 정보 저장
    current_music = None
    status_cycle = cycle(idle_messages)

    @tasks.loop(seconds=3)
    async def presence():
        if current_music:
            # 음악 재생 중일 때
            await bot.change_presence(activity=discord.CustomActivity(name=f"{current_music} 공연중!"))
        else:
            # 음악 재생 안할 때
            await bot.change_presence(activity=discord.CustomActivity(name=next(status_cycle)))

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
        
        # 슬래시 명령어 동기화
        try:
            print("슬래시 명령어 동기화 시작...")
            synced = await bot.tree.sync()
            print(f"✅ {len(synced)}개의 슬래시 명령어가 성공적으로 동기화되었습니다!")
            for cmd in synced:
                print(f"  - /{cmd.name}: {cmd.description}")
        except Exception as e:
            print(f"❌ 슬래시 명령어 동기화 실패: {e}")
            import traceback
            traceback.print_exc()

    @bot.command(name="reload")
    async def reload(ctx, extenseion):
        await bot.unload_extension(f"cogs.{extenseion}")
        await bot.load_extension(f"cogs.{extenseion}")
        await ctx.send(f"{extenseion} reloaded")

    @bot.command(name="sync")
    async def sync_commands(ctx):
        """슬래시 명령어를 강제로 동기화합니다"""
        try:
            synced = await bot.tree.sync()
            await ctx.send(f"✅ {len(synced)}개의 슬래시 명령어가 동기화되었습니다!")
            for cmd in synced:
                await ctx.send(f"  - /{cmd.name}: {cmd.description}")
        except Exception as e:
            await ctx.send(f"❌ 슬래시 명령어 동기화 실패: {e}")

    

    await bot.start(BOT_TOKEN)

asyncio.run(main())
    






