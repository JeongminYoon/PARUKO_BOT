from discord.ext import commands
import discord
import os


class help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog: help is ready")
    
    @commands.command(name="help")
    async def help(self, ctx):
        embed = discord.Embed(title="파루코 명령어 모음", description = "접두사: ! 또는 슬래시 명령어 사용 가능",color=discord.Color.from_rgb(255, 215, 0))
        embed.add_field(name=":exclamation: 주의사항", value="스마트 팔콘을 수동으로 내보내지 마세요 \n'!l' 또는 '/leave' 명령어를 사용하세요" ,inline=False)
        embed.add_field(name=":musical_note: 레이스 음악", value="***음악 재생***\n!play, /play (유튜브 링크 또는 빠른 번호)\n\n***빠른 번호 목록***\n!quicknumber, /quicknumber \n\n***다음 레이스로***\n!skip, /skip \n\n***휴식 시간***\n!pause, /pause\n\n***레이스 재개***\n!resume, /resume\n\n***레이스 대기열***\n!queue, /queue (페이지 번호)\n\n***채널 떠나기***\n!leave, /leave \n\n***레이스에서 제외***\n!delete, /delete (대기열 번호)\n\n***현재 레이스 중***\n!nowplaying, /nowplaying \n" ,inline=False)
        embed.add_field(name=":bell: 파루코 호출 / 지정된 채널로 벨소리\n", value="!ringing (음성 채널 멘션)", inline=False)
        

        await ctx.reply(embed=embed)

    @discord.app_commands.command(name="help", description="파루코 봇의 명령어 목록을 보여줍니다")
    async def slash_help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="파루코 명령어 모음", description = "접두사: ! 또는 슬래시 명령어 사용 가능",color=discord.Color.from_rgb(255, 215, 0))
        embed.add_field(name=":exclamation: 주의사항", value="스마트 팔콘을 수동으로 내보내지 마세요 \n'!l' 또는 '/leave' 명령어를 사용하세요" ,inline=False)
        embed.add_field(name=":musical_note: 레이스 음악", value="***음악 재생***\n!play, /play (유튜브 링크 또는 빠른 번호)\n\n***빠른 번호 목록***\n!quicknumber, /quicknumber \n\n***다음 레이스로***\n!skip, /skip \n\n***휴식 시간***\n!pause, /pause\n\n***레이스 재개***\n!resume, /resume\n\n***레이스 대기열***\n!queue, /queue (페이지 번호)\n\n***채널 떠나기***\n!leave, /leave \n\n***레이스에서 제외***\n!delete, /delete (대기열 번호)\n\n***현재 레이스 중***\n!nowplaying, /nowplaying \n" ,inline=False)
        embed.add_field(name=":bell: 파루코 호출 / 지정된 채널로 벨소리\n", value="!ringing (음성 채널 멘션)", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(help(bot))