from discord.ext import tasks, commands
import discord
import asyncio
from yt_dlp import YoutubeDL
import datetime
import time
import glob
from mutagen.mp3 import MP3








################# Setup ###################
###########################################
ffmpeg_options = {
            'options': '-vn',
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        }

ffmpeg_location = "./ffmpeg/bin/ffmpeg" 

entry_path = "./mp3/entry/*.mp3"

url_quick = ["https://youtu.be/ttVUZOkTxuM?si=fxizUn_G7tTvaN_-", "https://youtu.be/kHGJkDqS2Ek?si=trSzzEpyRV5fTkOl", "https://youtu.be/i8OUh3YvRpk?si=kENGCpCK_39EgHAy"]

entry = 1
###########################################
###########################################
        





################ Functions ################
##########################################
async def leave(self, num):
    self.server.pop(num)
    await self.bot.voice_clients[num].disconnect()

def server_check(self, channel: discord.VoiceChannel):
    server_num = None
    for server_num in range(0, len(self.bot.voice_clients)):
        if channel == self.bot.voice_clients[server_num].channel:
            break
        else:
            server_num = None
    return server_num

###########################################
###########################################





################# Class ###################
###########################################
class player():
    def __init__(self):
        
        self.q_list = []
        self.np_time = time.time()

    def queue_insert(self, y_link, y_title, y_duration, o_url, o_author, insert_num):
        q_dic = {'link':'', 'title':'', 'duration':'', 'url':'', 'author':''}
        q_dic['link'] = y_link
        q_dic['title'] = y_title
        q_dic['duration'] = datetime.timedelta(seconds=y_duration)
        q_dic['url'] = o_url
        q_dic['author'] = o_author
        self.q_list.insert(insert_num, q_dic)

        return self.q_list
        

    def queue_set(self, y_link, y_title, y_duration, o_url, o_author):
        q_dic = {'link':'', 'title':'', 'duration':'', 'url':'', 'author':''}
        q_dic['link'] = y_link
        q_dic['title'] = y_title
        q_dic['duration'] = datetime.timedelta(seconds=y_duration)
        q_dic['url'] = o_url
        q_dic['author'] = o_author
        self.q_list.append(q_dic)

        return self.q_list
    
    
    def channel_set(self, channel: discord.TextChannel):
        self.channel = channel

        return self.channel
        
###########################################
###########################################





################## DJ #####################
###########################################
class DJ(commands.Cog):

    
    
    def __init__(self, bot):
        self.bot = bot
        option = {
                'format':'bestaudio/best', 
                'noplaylist':True,
                'skip_download':True, 
                'extractor_args': {'youtube': {'player_client': ['web']}}
                }
        self.DL = YoutubeDL(option)
        self.server = []

        self.out.start()



    

    ################# Methods #################
    ###########################################
    async def left(self):
        try:
            for i in range(0, len(self.bot.voice_clients)):
                if self.bot.voice_clients[i].is_connected() is True and len(self.bot.voice_clients[i].channel.members) == 1:
                    await self.server[i].channel.send("*Never left without saying goodbye...*")
                    await leave(self, i)
                        
        except:
            pass
    ###########################################
    ###########################################





    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog: DJ is ready")


    @tasks.loop(seconds=0.1)
    async def out(self):
        await self.left()


    ################ Commands #################
    ###########################################

    @commands.command(name="play", aliases=["p", "P", "ㅔ"])
    async def play(self, ctx, url, insert_num:int = 0):


        if insert_num < 0:
            await ctx.reply("index error")
            return
        
        
        server_0 = player()
        

        

        #단축키
        for i in range(0, len(url_quick)):
            if url == f"{i+1}":
                url = url_quick[i]
            else:
                pass


        
        #접속
        try:
            channel = ctx.author.voice.channel
        except:
            await ctx.reply("You are not in voice channel")
            return
        


        try:
            await channel.connect()
            server_num = server_check(self, channel)
            self.server.append(server_0)
            self.server[server_num].channel_set(ctx.channel)

            #입장음
            if entry == 1:
                entry_link = glob.glob(entry_path)
                entry_audio = MP3(entry_link[0])
                entry_player = discord.FFmpegPCMAudio(executable=ffmpeg_location, source=entry_link[0])
                ctx.voice_client.play(entry_player)
                await asyncio.sleep(entry_audio.info.length)
            else:
                pass
    
        except:
            server_num = server_check(self, channel)

            
            
  
        
        #큐
        try:
            q_info = self.DL.extract_info(url, download=False)
        except:
            await ctx.reply("ERROR: URL invalid")
            return
        
        
        


        if ctx.author.nick == None:
            author = ctx.author.name
        else:
            author = ctx.author.nick


        if len(self.server[server_num].q_list) == 0:
            self.server[server_num].queue_set(q_info['url'], q_info['title'], q_info['duration'], url, author)
            queue_list = self.server[server_num].q_list

        elif insert_num == 0:
            self.server[server_num].queue_set(q_info['url'], q_info['title'], q_info['duration'], url, author)
            queue_list = self.server[server_num].q_list
            q_num = len(queue_list) - 1
            

            embed=discord.Embed(title='Queued', description=f'[{queue_list[q_num]["title"]}]({queue_list[q_num]["url"]})', color=discord.Color.from_rgb(255, 0, 0))
            embed.add_field(name='Position', value=f'{q_num}')
            embed.add_field(name='Duration', value=f'{queue_list[q_num]["duration"]}', inline=True)
            embed.add_field(name='Requested by', value=f'{queue_list[q_num]["author"]}', inline=True)
            await ctx.send(embed=embed)

            return
        
        else:
            self.server[server_num].queue_insert(q_info['url'], q_info['title'], q_info['duration'], url, author, insert_num)


            queue_list = self.server[server_num].q_list
            q_num = insert_num
            

            embed=discord.Embed(title='Queued', description=f'[{queue_list[q_num]["title"]}]({queue_list[q_num]["url"]})', color=discord.Color.from_rgb(255, 0, 0))
            embed.add_field(name='Position', value=f'{q_num}')
            embed.add_field(name='Duration', value=f'{queue_list[q_num]["duration"]}', inline=True)
            embed.add_field(name='Requested by', value=f'{queue_list[q_num]["author"]}', inline=True)
            await ctx.send(embed=embed)

            
            return
        

        

        link = queue_list[0]['link']
        title = queue_list[0]['title']
        o_url = queue_list[0]['url'] 
        o_author = queue_list[0]['author']
        o_duration = queue_list[0]['duration']


        track = discord.FFmpegPCMAudio(link, **ffmpeg_options, executable=ffmpeg_location)
        ctx.voice_client.play(track)
        self.server[server_num].np_time = time.time()


        embed=discord.Embed(title='Play', description=f'[{title}]({o_url})', color=discord.Color.from_rgb(255, 0, 0))
        embed.add_field(name='Duration', value=f'{o_duration}', inline=True)
        embed.add_field(name='Requested by', value=f'{o_author}', inline=True)
        await ctx.send(embed=embed)

        
        
        while True:

            try:
            
                if not ctx.voice_client.is_playing() and ctx.voice_client.is_paused() is False:
                    queue_list.pop(0)

                    link = queue_list[0]['link']
                    title = queue_list[0]['title']
                    o_url = queue_list[0]['url'] 
                    o_author = queue_list[0]['author']
                    o_duration = queue_list[0]['duration']


                    track = discord.FFmpegPCMAudio(link, **ffmpeg_options, executable=ffmpeg_location)
                    ctx.voice_client.play(track)
                    self.server[server_num].np_time = time.time()

                    embed=discord.Embed(title='Play', description=f'[{title}]({o_url})', color=discord.Color.from_rgb(255, 0, 0))
                    embed.add_field(name='Duration', value=f'{o_duration}', inline=True)
                    embed.add_field(name='Requested by', value=f'{o_author}', inline=True)
                    await ctx.send(embed=embed)
                    
                else:
                    await asyncio.sleep(0.1)

                
                
                
                    
            
            except:
                track.cleanup()
                break





    ###########################################
    ###########################################

    @commands.command(name="queue", aliases=["q", "Q", "ㅂ"])
    async def queue(self, ctx, num:int = 1):

        try:
            a_voice = ctx.author.voice.channel
        except:
            await ctx.reply("You are not in voice channel")
            return

        server_num = server_check(self, a_voice)

        

        embed = discord.Embed(title="Queue Info")
        q_num = len(self.server[server_num].q_list)
        playlist = ""
        playlist_page = []
        play_time = datetime.timedelta(seconds=0)
        index = num-1
        count = 0

        if q_num <= 1:
            embed.add_field(name='Empty', value='')
        
        else:
            for i in range(1, q_num):
                p_title = self.server[server_num].q_list[i]['title']
                p_url = self.server[server_num].q_list[i]['url']
                p_author = self.server[server_num].q_list[i]['author']
                p_duration = self.server[server_num].q_list[i]['duration']

                
        
                playlist += f"{i}. [{p_title}]({p_url}) | {p_duration} | {p_author}\n"
                count += 1
                
                #페이지당 7곡, 임베드 용량 초과하지 않도록 잘라냄
                if len(playlist) > 800 or count == 7:
                    playlist_page.append(playlist)
                    playlist = ""
                    count = 0
                #마지막 곡
                elif i+1 == q_num:
                    playlist_page.append(playlist)

                play_time += p_duration
            
            embed.add_field(name=f'Lists {play_time}', value=f"{playlist_page[index]}\n{num} / {len(playlist_page)}")

        await ctx.send(embed=embed)
    




    ###########################################
    ###########################################

    @commands.command(name="skip", aliases=["s", "S", "ㄴ"])
    async def skip(self, ctx):

        try:
            a_voice = ctx.author.voice.channel
        except:
            await ctx.reply("You are not in voice channel")
            return
        
        server_num = server_check(self, a_voice)
        
        if ctx.voice_client.is_playing():
            await ctx.send("Skipping...")
            self.bot.voice_clients[server_num].stop()
        elif not ctx.voice_client.is_playing():
            await ctx.send("Nothing to skip")
        




    ###########################################
    ###########################################
    
    @commands.command(name="leave", aliases=["l", "L", "ㅣ"])
    async def leave(self, ctx):

        try:
            a_voice = ctx.author.voice.channel
        except:
            await ctx.reply("You are not in voice channel")
            return

        server_num = server_check(self, a_voice)

        channel_id = self.bot.voice_clients[server_num].channel.id
        
        await leave(self, server_num)
        await ctx.send(f"Leave from <#{channel_id}>")
    

        


    ###########################################
    ###########################################

    @commands.command(name="delete", aliases=["d", "D", "ㅇ"]) 
    async def delete(self, ctx, index:int):
        
        if index <= 0: 
            await ctx.reply("index error")
            return
            

        try:
            a_voice = ctx.author.voice.channel
        except:
            await ctx.reply("You are not in voice channel")
            return

        server_num = server_check(self, a_voice)

        queue_list = self.server[server_num].q_list

        q_title = queue_list[index]['title']
        q_duration = queue_list[index]['duration']
        q_url = queue_list[index]['url']
        q_author = queue_list[index]['author']
        
        queue_list.pop(index)

        embed=discord.Embed(title='Deleted', description=f'[{q_title}]({q_url})', color=discord.Color.from_rgb(255, 0, 0))
        embed.add_field(name='Position', value=f'{index}')
        embed.add_field(name='Duration', value=f'{q_duration}', inline=True)
        embed.add_field(name='Requested by', value=f'{q_author}', inline=True)
        await ctx.send(embed=embed)
    

        


    ###########################################
    ###########################################

    @commands.command(name="nowplaying", aliases=["np", "Np", "NP", "ㅞ"])
    async def now_playing(self, ctx):

        try:
            a_voice = ctx.author.voice.channel
        except:
            await ctx.reply("You are not in voice channel")
            return

        server_num = server_check(self, a_voice)
        
        nowplaying = self.server[server_num].q_list

        if len(nowplaying) >= 1:
            title = nowplaying[0]['title']
            url = nowplaying[0]['url']
            author = nowplaying[0]['author']
            duration = nowplaying[0]['duration']
            np_time = self.server[server_num].np_time
            nowplaying_time = time.time()
            playing_time = datetime.timedelta(seconds=nowplaying_time - np_time)
            playing_time = str(playing_time).split('.')[0]

            embed=discord.Embed(title='Now Playing', description=f'[{title}]({url})', color=discord.Color.from_rgb(255, 0, 0))
            embed.add_field(name='Duration', value=f'{playing_time} / {duration}', inline=True)
            embed.add_field(name='Requested by', value=f'{author}', inline=True)
            await ctx.send(embed=embed)

        else:
            await ctx.send("Nothing is playing")
            
    




    ###########################################
    ###########################################

    @commands.command(name="quicknumber", aliases=["qn", "Qn", "부"])
    async def quick_number(self, ctx, num:int = 1):
        
        quicklist_page = []
        playlist = ""
        count = 0

        embed = discord.Embed(title="Quick Numbers")
        
        for i in range(0, len(url_quick)):
        
            playlist += f"{i+1}. {url_quick[i]}\n"
            count += 1
                
            #페이지당 7곡, 임베드 용량 초과하지 않도록 잘라냄
            if len(playlist) > 800 or count == 7:
                quicklist_page.append(playlist)
                playlist = ""
                count = 0
            #마지막 곡
            elif i+1 == len(url_quick):
                quicklist_page.append(playlist)
        
        embed.add_field(name=f'Lists', value=f"{quicklist_page[num-1]}\n{num} / {len(quicklist_page)}")

        await ctx.send(embed=embed)





    ###########################################
    ###########################################

    @commands.command(name="pause", aliases=["ps", "Ps", "ㅔㄴ"])
    async def pause(self, ctx):

        try:
            a_voice = ctx.author.voice.channel
        except:
            await ctx.reply("You are not in voice channel")
            return

        server_num = server_check(self, a_voice)

        self.bot.voice_clients[server_num].pause()
        

        await ctx.send("Paused")





    ###########################################
    ###########################################

    @commands.command(name="resume", aliases=["rs", "Rs", "ㄱㄴ"])
    async def resume(self, ctx):

        try:
            a_voice = ctx.author.voice.channel
        except:
            await ctx.reply("You are not in voice channel")
            return

        server_num = server_check(self, a_voice)

        self.bot.voice_clients[server_num].resume()
        

        await ctx.send("Resume")







    


async def setup(bot):
    await bot.add_cog(DJ(bot))

