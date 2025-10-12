from discord.ext import commands
import discord
import random
import glob
import asyncio
from mutagen.mp3 import MP3

################ Message ##################
###########################################

message_success = "스마트 팔콘 도착!"
message_fail = "레이스 중이야!"

ringing_path = "./mp3/ringing/*.mp3"
ffmpeg_path = "./ffmpeg/bin/ffmpeg"

###########################################
###########################################

def server_check(self, channel: discord.VoiceChannel):
    server_num = None
    for server_num in range(0, len(self.bot.voice_clients)):
                if channel == self.bot.voice_clients[server_num].channel:
                    break
                else:
                    server_num = None
    return server_num


class ringing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        option = {
                'format': 'bestaudio/best', 
                'noplaylist': True,
                'extract_flat': False,
                'no_warnings': True,
                'default_search': 'auto'
                }
        
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog: ringing is ready")
    

    @commands.command(name="ringing")
    async def ringing(self, ctx, channel: discord.VoiceChannel):
        await ctx.message.delete()
        rng = random.randint(0,100)
        
        link = glob.glob(ringing_path)
        audio = MP3(link[0])
        
        

        
        
        
        player = discord.FFmpegPCMAudio(executable=ffmpeg_path, source=link[0])

        # failed
        if rng in range(1,31): # 30%
            await ctx.send(f"{ctx.author.mention} tried ringing <#{channel.id}>.\n{message_fail}")
            return

        #succeed
        if self.bot.voice_clients == []:
            await channel.connect()
            num = server_check(self, channel)
            ctx.voice_client.play(player)
            await ctx.send(f"{message_success}")
            await asyncio.sleep(audio.info.length)
            await self.bot.voice_clients[num].disconnect()
        else: 
            await ctx.send(f"미안! 파루코 지금 다른 곳에서 레이스 중이야!")

    @discord.app_commands.command(name="ringing", description="파루코를 지정된 음성 채널로 호출합니다")
    @discord.app_commands.describe(channel="파루코를 호출할 음성 채널")
    async def slash_ringing(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        rng = random.randint(0,100)
        
        link = glob.glob(ringing_path)
        audio = MP3(link[0])
        
        player = discord.FFmpegPCMAudio(executable=ffmpeg_path, source=link[0])

        # failed
        if rng in range(1,31): # 30%
            await interaction.response.send_message(f"{interaction.user.mention} tried ringing <#{channel.id}>.\n{message_fail}")
            return

        #succeed
        if self.bot.voice_clients == []:
            await channel.connect()
            num = server_check(self, channel)
            voice_client = interaction.guild.voice_client
            voice_client.play(player)
            await interaction.response.send_message(f"{message_success}")
            await asyncio.sleep(audio.info.length)
            await self.bot.voice_clients[num].disconnect()
        else: 
            await interaction.response.send_message(f"미안! 파루코 지금 다른 곳에서 레이스 중이야!")
        
        

async def setup(bot):
    await bot.add_cog(ringing(bot))

