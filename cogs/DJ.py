# -*- coding: utf-8 -*-

from discord.ext import tasks, commands
import discord
import asyncio
from yt_dlp import YoutubeDL
import datetime
import time
import glob
from mutagen.mp3 import MP3
import threading
from .Libs import FakeCtx, server_check, leave
from .GUI import MusicUIManager, MusicPlayerView

ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

import os
ffmpeg_location = os.path.abspath("./ffmpeg/bin/ffmpeg.exe") 

entry_path = "./mp3/entry/*.mp3"

url_quick = ["https://youtu.be/szxn42peP3M?si=vjBHCOHasX4O4BrA", "https://youtu.be/pNBB8DnoanU?si=3fYVi0NnXEGSYKnd", "https://youtu.be/_LPRluTeSxw?si=Dw1_e9nxeuuJvDG9"]

entry = 0  # 입장음 비활성화 (연결 불안정 해결)


class player():
    def __init__(self):
        
        self.q_list = []
        self.np_time = time.time()
        self.repeat_mode = False  # 반복 모드 상태 추가

    def queue_insert(self, y_link, y_title, y_duration, o_url, o_author, insert_num):
        q_dic = {'link':'', 'title':'', 'duration':'', 'url':'', 'author':''}
        q_dic['link'] = y_link
        q_dic['title'] = y_title
        # duration이 None인 경우 처리
        if y_duration is not None:
            q_dic['duration'] = datetime.timedelta(seconds=y_duration)
        else:
            q_dic['duration'] = datetime.timedelta(seconds=0)
        q_dic['url'] = o_url
        q_dic['author'] = o_author
        self.q_list.insert(insert_num, q_dic)

        return self.q_list
        

    def queue_set(self, y_link, y_title, y_duration, o_url, o_author):
        q_dic = {'link':'', 'title':'', 'duration':'', 'url':'', 'author':''}
        q_dic['link'] = y_link
        q_dic['title'] = y_title
        # duration이 None인 경우 처리
        if y_duration is not None:
            q_dic['duration'] = datetime.timedelta(seconds=y_duration)
        else:
            q_dic['duration'] = datetime.timedelta(seconds=0)
        q_dic['url'] = o_url
        q_dic['author'] = o_author
        self.q_list.append(q_dic)

        return self.q_list
    
    
    def channel_set(self, channel: discord.TextChannel):
        self.channel = channel

        return self.channel


################## DJ #####################
###########################################
class DJ(commands.Cog):

    
    
    def __init__(self, bot):
        self.bot = bot
        option = {
                'format': 'bestaudio/best', 
                'noplaylist': True,
                'skip_download': True,
                'extract_flat': False,
                'no_warnings': True,
                'default_search': 'auto',
                'source_address': '0.0.0.0',
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'tv_embedded', 'web'],
                        'skip': ['dash', 'hls'],
                        'lang': ['ko', 'en']
                    }
                }
                }
        self.DL = YoutubeDL(option)
        self.server = []
        self.ui_manager = MusicUIManager()  # UI 관리자 추가



    

    ################# Methods #################
    ###########################################
    
    def create_track_info(self, title, url, duration, author):
        """트랙 정보 딕셔너리를 생성하는 헬퍼 메서드"""
        return {
            'title': title,
            'url': url,
            'duration': duration,
            'author': author
        }
    
    def get_voice_client(self, ctx, server_num):
        """voice_client를 가져오는 헬퍼 메서드"""
        if hasattr(ctx, '_voice_client'):
            # 슬래시 명령어인 경우
            return ctx.voice_client if ctx.voice_client is not None else (self.bot.voice_clients[server_num] if server_num is not None else None)
        else:
            # 레거시 명령어인 경우
            return self.bot.voice_clients[server_num] if server_num is not None else None
    
    async def check_voice_channel(self, ctx):
        """음성 채널 확인 및 서버 번호 반환"""
        try:
            a_voice = ctx.author.voice.channel
        except:
            await ctx.reply("보이스 채널 경기장에 입장해 주세요!")
            return None, None

        server_num = server_check(self.bot, a_voice)
        
        if server_num is None:
            await ctx.reply("봇이 음성 채널에 연결되어 있지 않습니다!")
            return None, None
            
        return a_voice, server_num
    
    def create_queue_embed(self, title, description, position, duration, author, color):
        """큐 관련 임베드 생성 헬퍼 메서드"""
        embed = discord.Embed(title=title, description=description, color=color)
        embed.add_field(name='Position', value=f'{position}')
        embed.add_field(name='Duration', value=f'{duration}', inline=True)
        embed.add_field(name='Requested by', value=f'{author}', inline=True)
        return embed
    
    def create_ffmpeg_track(self, url, seek_seconds=0):
        """FFmpeg 트랙 생성 헬퍼 메서드"""
        if seek_seconds > 0:
            seek_ffmpeg_options = {
                'before_options': f'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {seek_seconds}',
                'options': '-vn'
            }
            return discord.FFmpegPCMAudio(url, **seek_ffmpeg_options, executable=ffmpeg_location)
        else:   
            return discord.FFmpegPCMAudio(url, **ffmpeg_options, executable=ffmpeg_location)    
    
    async def check_voice_permissions(self, ctx, channel):
        """음성 채널 권한 확인 헬퍼 메서드"""
        permissions = channel.permissions_for(ctx.guild.me)
        
        # 필수 권한만 확인
        if not permissions.connect or not permissions.speak or not permissions.view_channel:
            await ctx.reply(f"❌ **{channel.name}** 채널에서 권한이 부족합니다. 다른 음성 채널에서 시도해주세요.")
            return False
        
        return True
    
    async def send_embed_with_view(self, ctx, embed, view, use_default_image=False):
        """임베드와 뷰를 함께 전송하는 헬퍼 메서드"""
        if use_default_image:
            default_image_path = "default_player.png"
            return await ctx.send(embed=embed, view=view, file=discord.File(default_image_path))
        else:
            return await ctx.send(embed=embed, view=view)
    
    async def create_and_send_music_ui(self, bot, server_num, voice_client, track_info, ctx):
        """음악 UI 생성 및 전송 헬퍼 메서드"""
        # UI 생성
        ui = MusicPlayerView(bot, server_num, voice_client, track_info)
        
        # 임베드 생성
        embed = ui.create_music_embed()
        
        # Context 타입에 따른 메시지 전송 방식 구분
        if hasattr(ctx, 'interaction') and ctx.interaction is not None:
            # 슬래시 명령어인 경우 (FakeCtx)
            message = await ctx.interaction.followup.send(embed=embed, view=ui)
        else:
            # 일반 명령어인 경우 (discord.ext.commands.Context)
            message = await self.send_embed_with_view(ctx, embed, ui)
        
        # UI에 메시지 설정
        ui.message = message
        
        return ui, message
    
    async def create_and_send_empty_queue_ui(self, bot, server_num, voice_client, ctx):
        """빈 큐 상태 UI 생성 및 전송 헬퍼 메서드"""
        # 빈 큐 상태의 트랙 정보 생성
        empty_track_info = {
            'title': '재생 목록이 없어요',
            'url': '',
            'duration': 0,
            'author': '',
            'is_empty': True
        }
        
        # UI 생성
        ui = MusicPlayerView(bot, server_num, voice_client, empty_track_info)
        
        # 임베드 생성
        embed = ui.create_music_embed()
        
        # 메시지 전송 (기본 이미지 포함)
        default_image_path = "default_player.png"
        if os.path.exists(default_image_path):
            with open(default_image_path, 'rb') as f:
                file = discord.File(f, filename="default_player.png")
                # Context 타입에 따른 메시지 전송 방식 구분
                if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                    message = await ctx.interaction.followup.send(embed=embed, view=ui, file=file)
                else:
                    message = await ctx.send(embed=embed, view=ui, file=file)
        else:
            # Context 타입에 따른 메시지 전송 방식 구분
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                message = await ctx.interaction.followup.send(embed=embed, view=ui)
            else:
                message = await ctx.send(embed=embed, view=ui)
        
        # UI에 메시지 설정
        ui.message = message
        
        return ui, message
    
    async def left(self):
        try:
            for i in range(0, len(self.bot.voice_clients)):
                if self.bot.voice_clients[i].is_connected() is True and len(self.bot.voice_clients[i].channel.members) == 1:
                    await self.server[i].channel.send("*기숙사로 돌아갑니다...*")
                    await leave(self.bot, i, self.ui_manager, self.server)
                        
        except:
            pass
    ###########################################
    ###########################################





    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog: DJ is ready")
        self.out.start()


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


        
        # 음성 채널 확인
        try:
            channel = ctx.author.voice.channel
        except:
            await ctx.reply("보이스 채널 경기장에 입장해 주세요!")
            return

        # 봇이 이미 연결되어 있는지 확인
        server_num = server_check(self.bot, channel)
        
        if server_num is None:
            # 연결되지 않았으면 연결 시도
            if not await self.check_voice_permissions(ctx, channel):
                return
            
            await channel.connect(timeout=10.0, self_deaf=True)
            await asyncio.sleep(0.5)  # 연결 안정화 대기
            
            # 서버 설정
            server_num = len(self.bot.voice_clients) - 1
            self.server.append(server_0)
            self.server[server_num].channel_set(ctx.channel)
            
            # ctx.voice_client 설정 (슬래시 명령어인 경우에만)
            if hasattr(ctx, '_voice_client'):
                ctx.voice_client = self.bot.voice_clients[server_num]
        else:
            # 이미 연결되어 있으면 기존 연결 사용
            if hasattr(ctx, '_voice_client'):
                ctx.voice_client = self.bot.voice_clients[server_num]

            
            
  
        
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
        else:
            self.server[server_num].queue_insert(q_info['url'], q_info['title'], q_info['duration'], url, author, insert_num)
            queue_list = self.server[server_num].q_list
            q_num = insert_num

        # 큐에 추가된 경우 메시지 전송 후 종료
        if len(queue_list) > 1 or insert_num > 0:
            embed = self.create_queue_embed(
                '레이스 대기열에 추가됨',
                f'[{queue_list[q_num]["title"]}]({queue_list[q_num]["url"]})',
                q_num,
                queue_list[q_num]["duration"],
                queue_list[q_num]["author"],
                discord.Color.from_rgb(255, 215, 0)
            )
            
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await ctx.send(embed=embed)
            return
        

        

        # 첫 번째 곡 재생
        link = queue_list[0]['link']
        title = queue_list[0]['title']
        o_url = queue_list[0]['url'] 
        o_author = queue_list[0]['author']
        o_duration = queue_list[0]['duration']

        # 트랙 생성 및 재생
        track = self.create_ffmpeg_track(link)
        voice_client = self.get_voice_client(ctx, server_num)
        
        voice_client.play(track)
        self.server[server_num].np_time = time.time()


        # 음악 재생 GUI 생성
        track_info = self.create_track_info(title, o_url, o_duration, o_author)
        
        result = await self.ui_manager.get_or_create_ui(
            self.bot, server_num, voice_client, track_info, ctx
        )
        
        # 반환값 처리
        if len(result) == 3:
            music_view, message, was_empty_to_new = result
        else:
            music_view, message = result
            was_empty_to_new = False
        
        # 프로그레스 바 자동 업데이트 시작
        music_view.update_task = asyncio.create_task(music_view.start_progress_updates())
        
        # 봇 상태 업데이트
        if hasattr(self.bot, 'update_music_status'):
            self.bot.update_music_status(title)
                    
        
        
        while True:

            try:
                # voice_client 사용 (레거시는 직접 접근, 슬래시는 설정된 값 사용)
                voice_client = self.get_voice_client(ctx, server_num)
                
                # voice_client가 None인지 확인
                if voice_client is None:
                    print("Voice client is None, breaking loop")
                    break
                
                if not voice_client.is_playing() and voice_client.is_paused() is False:
                    # seek 중인지 확인 - seek 중이면 큐에서 제거하지 않음
                    is_seeking = False
                    try:
                        if hasattr(self, 'ui_manager') and self.ui_manager:
                            if server_num in self.ui_manager.server_uis:
                                music_view = self.ui_manager.server_uis[server_num]
                                if music_view and hasattr(music_view, '_seeking'):
                                    is_seeking = music_view._seeking
                                    print(f"Debug - Seeking flag status: {is_seeking}")
                                    if is_seeking:
                                        print("Seek in progress, skipping queue removal")
                    except Exception as e:
                        print(f"Error checking seek status: {e}")
                    
                    if not is_seeking:
                        print("Debug - Checking repeat mode before removing song")
                        # 반복 모드 확인
                        if self.server[server_num].repeat_mode and len(queue_list) > 0:
                            print("Debug - Repeat mode ON, keeping current song in queue")
                            # 반복 모드가 켜져있으면 현재 곡을 큐의 맨 뒤로 이동
                            current_song = queue_list.pop(0)
                            queue_list.append(current_song)
                        else:
                            print("Debug - Removing current song from queue")
                            queue_list.pop(0)
                    else:
                        # seek 중이면 잠시 대기 후 다시 체크
                        print("Debug - Seek in progress, waiting...")
                        await asyncio.sleep(0.1)
                        continue

                    # 큐가 비어있으면 빈 큐 UI 표시
                    if len(queue_list) == 0:
                        if hasattr(self.bot, 'update_music_status'):
                            self.bot.update_music_status(None)
                        
                        # 빈 큐 UI 표시
                        try:
                            await self.ui_manager.show_empty_queue_ui(self.bot, server_num, ctx)
                        except Exception as e:
                            print(f"Failed to show empty queue UI: {e}")
                        
                        break

                    link = queue_list[0]['link']
                    title = queue_list[0]['title']
                    o_url = queue_list[0]['url'] 
                    o_author = queue_list[0]['author']
                    o_duration = queue_list[0]['duration']

                    # 스트리밍 방식으로 트랙 생성
                    print(f"Creating streaming track from URL: {link}")
                    try:
                        track = self.create_ffmpeg_track(link)
                        print("FFmpeg track created successfully from streaming")
                    except Exception as e:
                        print(f"FFmpeg track creation failed: {type(e).__name__}: {e}")
                        await ctx.reply(f"음악 스트리밍 중 오류가 발생했습니다: {str(e)}")
                        return
                    
                    # voice_client 사용 (레거시는 직접 접근, 슬래시는 설정된 값 사용)
                    voice_client = self.get_voice_client(ctx, server_num)
                    
                    # voice_client가 None인지 확인
                    if voice_client is None:
                        print("Voice client is None, breaking loop")
                        break
                    
                    # 음악 재생 전에 잠시 대기하여 스트림이 준비되도록 함
                    await asyncio.sleep(0.05)  # 0.1초에서 0.05초로 단축
                    
                    # voice_client 연결 상태 재확인
                    if not voice_client.is_connected():
                        print("Voice client disconnected during playback, breaking loop")
                        break
                    
                    # 재생 전 권한 재확인
                    channel = voice_client.channel
                    if not channel.permissions_for(ctx.guild.me).speak:
                        print("Bot lost speak permission during playback, breaking loop")
                        await ctx.send("음성 채널에서 말할 권한이 없습니다! 관리자에게 권한을 요청해주세요.")
                        await voice_client.disconnect()
                        break
                    
                    # 큐 재생 전에도 더미 오디오로 활성화 (스트리밍 충돌 방지)
                    try:
                        dummy_audio = discord.FFmpegPCMAudio("silence.mp3", executable=ffmpeg_location)
                        voice_client.play(dummy_audio)
                        await asyncio.sleep(0.02)  # 0.05초에서 0.02초로 단축
                        voice_client.stop()
                        print("Dummy audio played before queue track")
                    except Exception as e:
                        print(f"Queue dummy audio play failed: {e}")
                    
                    try:
                        voice_client.play(track)
                        self.server[server_num].np_time = time.time()
                    except discord.ClientException as e:
                        if "Not connected to voice" in str(e):
                            print("Voice client connection lost during playback, breaking loop")
                            break
                        elif "You do not have permission" in str(e) or "Missing Permissions" in str(e):
                            print("Bot lost permission during playback, breaking loop")
                            await ctx.send("음성 채널에서 말할 권한이 없습니다! 관리자에게 권한을 요청해주세요.")
                            await voice_client.disconnect()
                            break
                        else:
                            print(f"Queue playback error: {type(e).__name__}: {e}")
                            break

                    # 음악 재생 GUI 생성 (큐에서 다음 곡 - UI 관리자 사용)
                    track_info = self.create_track_info(title, o_url, o_duration, o_author)
                    
                    try:
                        result = await self.ui_manager.get_or_create_ui(
                            self.bot, server_num, voice_client, track_info, ctx
                        )
                        
                        # 반환값 처리 (ui, message, was_empty_to_new)
                        if len(result) == 3:
                            music_view, message, was_empty_to_new = result
                        else:
                            music_view, message = result
                            was_empty_to_new = False
                            
                        print(f"Queue UI created/updated for server {server_num}")
                    except Exception as e:
                        print(f"ERROR: Queue UI creation failed: {e}")
                        await ctx.reply("UI 생성에 실패했습니다.")
                        continue
                    
                    # 프로그레스 바 자동 업데이트 시작 (message 설정 후)
                    # 기존 태스크가 있으면 중지하고 새로 시작
                    try:
                        if music_view.update_task and not music_view.update_task.done():
                            music_view.update_task.cancel()
                        music_view.update_task = asyncio.create_task(music_view.start_progress_updates())
                    except Exception as e:
                        print(f"Failed to start progress updates: {e}")
                    
                    # 봇 상태 업데이트 (다음 음악 재생 중)
                    if hasattr(self.bot, 'update_music_status'):
                        self.bot.update_music_status(title)
                    
                else:
                    await asyncio.sleep(0.1)
            
            except:
                track.cleanup()
                break





    ###########################################
    ###########################################

    @commands.command(name="queue", aliases=["q", "Q", "ㅂ"])
    async def queue(self, ctx, num:int = 1):
        a_voice, server_num = await self.check_voice_channel(ctx)
        if server_num is None:
            return

        embed = discord.Embed(title="레이스 대기열 정보", color=discord.Color.from_rgb(255, 20, 147))
        q_num = len(self.server[server_num].q_list)
        playlist = ""
        playlist_page = []
        play_time = datetime.timedelta(seconds=0)
        index = num-1
        count = 0

        # 디버그 정보 추가

        if q_num == 0:
            embed.add_field(name='Empty', value='큐가 비어있습니다.')
        
        else:
            for i in range(0, q_num):
                p_title = self.server[server_num].q_list[i]['title']
                p_url = self.server[server_num].q_list[i]['url']
                p_author = self.server[server_num].q_list[i]['author']
                p_duration = self.server[server_num].q_list[i]['duration']

                # 현재 재생 중인 곡 표시
                if i == 0:
                    playlist += f"🎵 **{i+1}. [{p_title}]({p_url})** | {p_duration} | {p_author}\n"
                else:
                    playlist += f"{i+1}. [{p_title}]({p_url}) | {p_duration} | {p_author}\n"
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
        a_voice, server_num = await self.check_voice_channel(ctx)
        if server_num is None:
            return
        
        # voice_client 확인
        voice_client = self.get_voice_client(ctx, server_num)
        
        if voice_client is None:
            await ctx.send("음성 채널에 연결되어 있지 않습니다!")
            return
        
        if not voice_client.is_playing():
            await ctx.send("스킵할 레이스가 없어요!")
            return
        
        await ctx.send("다음 레이스로!")
        
        # 현재 재생 중지
        voice_client.stop()
        
        # 봇 상태 업데이트
        if hasattr(self.bot, 'update_music_status'):
            self.bot.update_music_status(None)
        
        # 큐가 비어있으면 빈 큐 UI 표시
        if len(self.server[server_num].q_list) == 0:
            try:
                await self.ui_manager.show_empty_queue_ui(self.bot, server_num, ctx)
            except Exception as e:
                print(f"Failed to show empty queue UI: {e}")
        else:
            # 다음 곡이 있으면 UI 업데이트
            try:
                next_track = self.server[server_num].q_list[0]
                track_info = self.create_track_info(
                    next_track['title'],
                    next_track['url'],
                    next_track['duration'],
                    next_track.get('author', 'Unknown')
                )
                await self.ui_manager.update_ui(server_num, track_info)
            except Exception as e:
                print(f"Failed to update UI: {e}")
        




    ###########################################
    ###########################################
    
    @commands.command(name="leave", aliases=["l", "L", "ㅣ"])
    async def leave(self, ctx):
        a_voice, server_num = await self.check_voice_channel(ctx)
        if server_num is None:
            return

        channel_id = self.bot.voice_clients[server_num].channel.id
        
        await leave(self.bot, server_num, self.ui_manager, self.server)
        await ctx.send(f"스마트 팔콘이 <#{channel_id}>에서 퇴장했어요!")
        
        # 봇 상태 초기화 (음성 채널 퇴장)
        if hasattr(self.bot, 'update_music_status'):
            self.bot.update_music_status(None)
    

        


    ###########################################
    ###########################################

    @commands.command(name="delete", aliases=["d", "D", "ㅇ"]) 
    async def delete(self, ctx, index:int):
        
        if index <= 0: 
            await ctx.reply("index error")
            return
            
        a_voice, server_num = await self.check_voice_channel(ctx)
        if server_num is None:
            return

        queue_list = self.server[server_num].q_list

        q_title = queue_list[index]['title']
        q_duration = queue_list[index]['duration']
        q_url = queue_list[index]['url']
        q_author = queue_list[index]['author']
        
        queue_list.pop(index)

        embed = self.create_queue_embed(
            '레이스에서 제외됨',
            f'[{q_title}]({q_url})',
            index,
            q_duration,
            q_author,
            discord.Color.from_rgb(255, 100, 100)
        )
        await ctx.send(embed=embed)
    

        


    ###########################################
    ###########################################

    @commands.command(name="nowplaying", aliases=["np", "Np", "NP", "ㅞ"])
    async def now_playing(self, ctx):
        a_voice, server_num = await self.check_voice_channel(ctx)
        if server_num is None:
            return
        
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

            embed=discord.Embed(title='현재 레이스 중', description=f'[{title}]({url})', color=discord.Color.from_rgb(0, 200, 100))
            embed.add_field(name='Duration', value=f'{playing_time} / {duration}', inline=True)
            embed.add_field(name='Requested by', value=f'{author}', inline=True)
            await ctx.send(embed=embed)

        else:
            await ctx.send("현재 레이스 중인 음악이 없어요!")
            
    




    ###########################################
    ###########################################

    @commands.command(name="quicknumber", aliases=["qn", "Qn", "부"])
    async def quick_number(self, ctx, num:int = 1):
        
        quicklist_page = []
        playlist = ""
        count = 0

        embed = discord.Embed(title="빠른 레이스 번호", color=discord.Color.from_rgb(255, 215, 0))
        
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
        a_voice, server_num = await self.check_voice_channel(ctx)
        if server_num is None:
            return

        # voice_client 확인
        voice_client = self.get_voice_client(ctx, server_num)
        
        if voice_client is None:
            await ctx.send("음성 채널에 연결되어 있지 않습니다!")
            return

        voice_client.pause()
        

        await ctx.send("휴식 시간!")
        
        # 봇 상태 업데이트 (일시정지)
        if hasattr(self.bot, 'update_music_status'):
            self.bot.update_music_status(None)





    ###########################################
    ###########################################

    @commands.command(name="resume", aliases=["rs", "Rs", "ㄱㄴ"])
    async def resume(self, ctx):
        a_voice, server_num = await self.check_voice_channel(ctx)
        if server_num is None:
            return

        # voice_client 확인
        voice_client = self.get_voice_client(ctx, server_num)
        
        if voice_client is None:
            await ctx.send("음성 채널에 연결되어 있지 않습니다!")
            return

        voice_client.resume()
        

        await ctx.send("레이스 재개!")
        
        # 봇 상태 업데이트 (재생 재개)
        if hasattr(self.bot, 'update_music_status'):
            if len(self.server[server_num].q_list) > 0:
                self.bot.update_music_status(self.server[server_num].q_list[0]['title'])







    


    ################ Slash Commands ############
    ###########################################

    @discord.app_commands.command(name="play", description="음악을 재생합니다")
    @discord.app_commands.describe(url="유튜브 URL 또는 빠른 번호 (1-3)", insert_num="대기열에 삽입할 위치 (기본값: 0)")
    async def slash_play(self, interaction: discord.Interaction, url: str, insert_num: int = 0):
        await interaction.response.defer()
        ctx = FakeCtx(interaction)
        await self.play(ctx, url, insert_num)

    @discord.app_commands.command(name="queue", description="음악 대기열을 확인합니다")
    @discord.app_commands.describe(num="페이지 번호 (기본값: 1)")
    async def slash_queue(self, interaction: discord.Interaction, num: int = 1):
        await interaction.response.defer()
        ctx = FakeCtx(interaction)
        await self.queue(ctx, num)

    @discord.app_commands.command(name="skip", description="다음 곡으로 넘어갑니다")
    async def slash_skip(self, interaction: discord.Interaction):
        await interaction.response.defer()
        ctx = FakeCtx(interaction)
        await self.skip(ctx)

    @discord.app_commands.command(name="leave", description="음성 채널에서 나갑니다")
    async def slash_leave(self, interaction: discord.Interaction):
        await interaction.response.defer()
        ctx = FakeCtx(interaction)
        await self.leave(ctx)

    @discord.app_commands.command(name="delete", description="대기열에서 곡을 제거합니다")
    @discord.app_commands.describe(index="제거할 곡의 번호")
    async def slash_delete(self, interaction: discord.Interaction, index: int):
        await interaction.response.defer()
        ctx = FakeCtx(interaction)
        await self.delete(ctx, index)

    @discord.app_commands.command(name="nowplaying", description="현재 재생 중인 곡을 확인합니다")
    async def slash_nowplaying(self, interaction: discord.Interaction):
        ctx = FakeCtx(interaction)
        await self.now_playing(ctx)

    @discord.app_commands.command(name="quicknumber", description="빠른 번호 목록을 확인합니다")
    @discord.app_commands.describe(num="페이지 번호 (기본값: 1)")
    async def slash_quicknumber(self, interaction: discord.Interaction, num: int = 1):
        ctx = FakeCtx(interaction)
        await self.quick_number(ctx, num)

    @discord.app_commands.command(name="pause", description="음악을 일시정지합니다")
    async def slash_pause(self, interaction: discord.Interaction):
        await interaction.response.defer()
        ctx = FakeCtx(interaction)
        await self.pause(ctx)

    @discord.app_commands.command(name="resume", description="일시정지된 음악을 재생합니다")
    async def slash_resume(self, interaction: discord.Interaction):
        await interaction.response.defer()
        ctx = FakeCtx(interaction)
        await self.resume(ctx)

    @discord.app_commands.command(name="gui", description="플레이어 GUI를 채팅 맨 아래로 가져옵니다")
    async def slash_bring_gui(self, interaction: discord.Interaction):
        await interaction.response.defer()
        ctx = FakeCtx(interaction)
        await self.bring_gui(ctx)

    @commands.command(name="gui", aliases=["player", "플레이어"])
    async def bring_gui(self, ctx):
        """플레이어 GUI를 채팅 맨 아래로 가져오기"""
        # 음성 채널 확인
        if not ctx.author.voice:
            await ctx.reply("❌ 음성 채널에 먼저 들어가주세요!")
            return
        
        voice_channel = ctx.author.voice.channel
        
        # 서버 번호 찾기
        server_num = server_check(self.bot, voice_channel)
        if server_num is None:
            await ctx.reply("❌ 봇이 음성 채널에 연결되어 있지 않습니다!")
            return
        
        # UI가 존재하는지 확인
        if server_num not in self.ui_manager.server_uis:
            await ctx.reply("❌ 현재 재생 중인 음악이 없습니다!")
            return
        
        # UI를 채팅 맨 아래로 가져오기
        ui, message = await self.ui_manager.bring_ui_to_bottom(self.bot, server_num, ctx)
        
        if ui and message:
            await ctx.reply("✅ 플레이어 GUI를 채팅 맨 아래로 가져왔습니다!", delete_after=3)
        else:
            await ctx.reply("❌ GUI를 가져오는 중 오류가 발생했습니다!")

    @commands.command(name="test")
    async def test_seek(self, ctx, url):
        """간단한 seek 테스트 명령어"""
        # 음성 채널 연결 확인
        if not ctx.author.voice:
            await ctx.send("음성 채널에 먼저 들어가주세요!")
            return
        
        voice_channel = ctx.author.voice.channel
        voice_client = ctx.voice_client
        
        # 봇이 음성 채널에 없으면 연결
        if not voice_client:
            voice_client = await voice_channel.connect()
        
        # URL에서 오디오 정보 추출
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'skip_download': True,
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            audio_url = info.get('url')
        
        # 첫 번째 재생 (0초부터 시작)
        initial_track = self.create_ffmpeg_track(audio_url)
        voice_client.play(initial_track)
        
        await ctx.send(f"🎵 **{title}** 재생 시작! 5초 후 30초 위치로 이동합니다...")
        
        # 5초 대기
        await asyncio.sleep(5)
        
        # 30초 위치로 seek
        seek_track = self.create_ffmpeg_track(audio_url, 30)
        
        # 기존 트랙 중지 후 새 트랙 재생
        voice_client.stop()
        await asyncio.sleep(1)  # stop 완료 대기
        
        voice_client.play(seek_track, after=lambda e: print(f"Test seek track ended: {e}"))
        
        await ctx.send("⏩ **30초 위치로 이동 완료!**")

async def setup(bot):
    """Cog를 봇에 로드하는 함수"""
    await bot.add_cog(DJ(bot))
