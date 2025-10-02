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
        embed = discord.Embed(title="파루코 명령어 모음", description = "접두사: !",color=discord.Color.from_rgb(255, 215, 0))
        embed.add_field(name=":exclamation: 주의사항", value="스마트 팔콘을 수동으로 내보내지 마세요 \n'!l' 명령어를 사용하세요" ,inline=False)
        embed.add_field(name=":musical_note: 레이스 음악", value="***음악 재생***\nplay, p, P, ㅔ (유튜브 링크 또는 빠른 번호)\n\n***빠른 번호 목록***\nquicknumber, qn, Qn, 부 \n\n***다음 레이스로***\nskip, s, S, ㄴ \n\n***휴식 시간***\npause, ps, Ps, ㅔㄴ\n\n***레이스 재개***\nresume, rs, Rs, ㄱㄴ\n\n***레이스 대기열***\nqueue, q, Q, ㅂ (페이지 번호)\n\n***채널 떠나기***\nleave, l, L, ㅣ \n\n***레이스에서 제외***\ndelete, d, D, ㅇ (대기열 번호)\n\n***현재 레이스 중***\nnowplaying, np, Np, NP, ㅞ \n" ,inline=False)
        embed.add_field(name=":bell: 파루코 호출 / 지정된 채널로 벨소리\n", value="ringing (음성 채널 멘션)", inline=False)
        

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(help(bot))