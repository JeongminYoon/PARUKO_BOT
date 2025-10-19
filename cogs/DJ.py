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
import os
from .Libs import FakeCtx, server_check, leave
from .GUI import MusicUIManager, MusicPlayerView
from .subtitle_service import subtitle_service

# ============================================================================
# Configuration Constants
# ============================================================================

class MusicBotConfig:
    """음악 봇 설정 상수"""
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }
    
    FFMPEG_LOCATION = os.path.abspath("./ffmpeg/bin/ffmpeg.exe")
    ENTRY_PATH = "./mp3/entry/*.mp3"
    
    QUICK_URLS = [
        "https://youtu.be/szxn42peP3M?si=vjBHCOHasX4O4BrA",
        "https://youtu.be/pNBB8DnoanU?si=3fYVi0NnXEGSYKnd", 
        "https://youtu.be/_LPRluTeSxw?si=Dw1_e9nxeuuJvDG9"
    ]
    
    YOUTUBE_DL_OPTIONS = {
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

# ============================================================================
# Player Class
# ============================================================================

class Player:
    """음악 재생을 위한 플레이어 클래스"""
    
    def __init__(self):
        self.q_list = []
        self.np_time = time.time()
        self.repeat_mode = False
        self.channel = None

    def queue_insert(self, y_link, y_title, y_duration, o_url, o_author, insert_num):
        """큐에 음악을 특정 위치에 삽입"""
        q_dic = self._create_queue_item(y_link, y_title, y_duration, o_url, o_author)
        self.q_list.insert(insert_num, q_dic)
        return self.q_list

    def queue_set(self, y_link, y_title, y_duration, o_url, o_author):
        """큐에 음악을 추가"""
        q_dic = self._create_queue_item(y_link, y_title, y_duration, o_url, o_author)
        self.q_list.append(q_dic)
        return self.q_list
    
    def channel_set(self, channel: discord.TextChannel):
        """채널 설정"""
        self.channel = channel
        return self.channel

    def _create_queue_item(self, y_link, y_title, y_duration, o_url, o_author):
        """큐 아이템 딕셔너리 생성"""
        return {
            'link': y_link,
            'title': y_title,
            'duration': datetime.timedelta(seconds=y_duration) if y_duration else datetime.timedelta(seconds=0),
            'url': o_url,
            'author': o_author
        }

# ============================================================================
# Main DJ Cog
# ============================================================================

class DJ(commands.Cog):
    """Discord 음악 봇의 핵심 기능을 담당하는 클래스"""
    
    def __init__(self, bot):
        self.bot = bot
        self.DL = YoutubeDL(MusicBotConfig.YOUTUBE_DL_OPTIONS)
        self.server = []
        self.ui_manager = MusicUIManager()
        self.entry = 0  # 입장음 비활성화
        self.skip_in_progress = {}  # 서버별 스킵 진행 상태

    # ============================================================================
    # Event Handlers
    # ============================================================================
    
    @commands.Cog.listener()
    async def on_ready(self):
        """봇이 준비되었을 때 실행"""
        print("Cog: DJ is ready")
        self.out.start()

    @tasks.loop(seconds=0.1)
    async def out(self):
        """음성 채널 자동 퇴장 체크"""
        await self._check_auto_leave()

    # ============================================================================
    # Private Helper Methods
    # ============================================================================
    
    async def _check_auto_leave(self):
        """음성 채널 자동 퇴장 체크"""
        try:
            for i in range(len(self.bot.voice_clients)):
                voice_client = self.bot.voice_clients[i]
                if (voice_client.is_connected() and 
                    len(voice_client.channel.members) == 1):
                    await self.server[i].channel.send("*기숙사로 돌아갑니다...*")
                    await leave(self.bot, i, self.ui_manager, self.server)
        except Exception:
            pass

    def _create_track_info(self, title, url, duration, author, original_url=None):
        """트랙 정보 딕셔너리 생성"""
        return {
            'title': title,
            'url': url,
            'duration': duration,
            'author': author,
            'original_url': original_url or url
        }
    
    def _get_voice_client(self, ctx, server_num):
        """voice_client를 가져오는 헬퍼 메서드"""
        if hasattr(ctx, '_voice_client'):
            return (ctx.voice_client if ctx.voice_client is not None 
                   else (self.bot.voice_clients[server_num] if server_num is not None else None))
        else:
            return self.bot.voice_clients[server_num] if server_num is not None else None
    
    async def _check_voice_channel(self, ctx):
        """음성 채널 확인 및 서버 번호 반환"""
        try:
            a_voice = ctx.author.voice.channel
        except AttributeError:
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send("보이스 채널 경기장에 입장해 주세요!", ephemeral=True)
            else:
                await ctx.reply("보이스 채널 경기장에 입장해 주세요!")
            return None, None

        server_num = server_check(self.bot, a_voice)
        
        if server_num is None:
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send("봇이 음성 채널에 연결되어 있지 않습니다!", ephemeral=True)
            else:
                await ctx.reply("봇이 음성 채널에 연결되어 있지 않습니다!")
            return None, None
            
        return a_voice, server_num
    
    def _create_queue_embed(self, title, description, position, duration, author, color):
        """큐 관련 임베드 생성"""
        embed = discord.Embed(title=title, description=description, color=color)
        embed.add_field(name='Position', value=f'{position}')
        embed.add_field(name='Duration', value=f'{duration}', inline=True)
        embed.add_field(name='Requested by', value=f'{author}', inline=True)
        return embed
    
    def _create_ffmpeg_track(self, url, seek_seconds=0):
        """FFmpeg 트랙 생성"""
        if seek_seconds > 0:
            seek_options = {
                'before_options': f'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {seek_seconds}',
                'options': '-vn'
            }
            return discord.FFmpegPCMAudio(url, **seek_options, executable=MusicBotConfig.FFMPEG_LOCATION)
        else:   
            return discord.FFmpegPCMAudio(url, **MusicBotConfig.FFMPEG_OPTIONS, executable=MusicBotConfig.FFMPEG_LOCATION)
    
    async def _check_voice_permissions(self, ctx, channel):
        """음성 채널 권한 확인"""
        permissions = channel.permissions_for(ctx.guild.me)
        
        if not (permissions.connect and permissions.speak and permissions.view_channel):
            await ctx.reply(f"❌ **{channel.name}** 채널에서 권한이 부족합니다. 다른 음성 채널에서 시도해주세요.")
            return False
        
        return True

    async def create_and_send_music_ui(self, bot, server_num, voice_client, track_info, ctx):
        """음악 UI 생성 및 전송 헬퍼 메서드"""
        from .GUI import MusicPlayerView
        
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
            message = await ctx.send(embed=embed, view=ui)
        
        # UI에 메시지 설정
        ui.message = message
        
        return ui, message
    
    async def create_and_send_empty_queue_ui(self, bot, server_num, voice_client, ctx):
        """빈 큐 상태 UI 생성 및 전송 헬퍼 메서드"""
        from .GUI import MusicPlayerView
        
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

    async def send_embed_with_view(self, ctx, embed, view, use_default_image=False):
        """임베드와 뷰를 포함한 메시지 전송 헬퍼 메서드"""
        import os
        
        # 기본 이미지가 필요한 경우에만 첨부
        if use_default_image or (embed.image and "attachment://default_player.png" in str(embed.image.url)):
            default_image_path = "default_player.png"
            if os.path.exists(default_image_path):
                with open(default_image_path, 'rb') as f:
                    file = discord.File(f, filename="default_player.png")
                    if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                        return await ctx.interaction.followup.send(embed=embed, view=view, file=file)
                    else:
                        return await ctx.send(embed=embed, view=view, file=file)
        
        # 일반 메시지 전송
        if hasattr(ctx, 'interaction') and ctx.interaction is not None:
            return await ctx.interaction.followup.send(embed=embed, view=view)
        else:
            return await ctx.send(embed=embed, view=view)

    # ============================================================================
    # Music Control Commands
    # ============================================================================
    
    @commands.command(name="play", aliases=["p", "P", "ㅔ"])
    async def play(self, ctx, url, insert_num: int = 0):
        """음악을 재생합니다."""
        # 입력 검증
        if not await self._validate_play_input(ctx, url, insert_num):
            return
        
        # 음성 채널 연결 처리
        voice_channel, server_num = await self._handle_voice_connection(ctx)
        if server_num is None:
            return
        
        # 음악 정보 추출
        track_info = await self._extract_track_info(url, ctx)
        if not track_info:
            return
        
        # 큐 관리
        queue_result = await self._manage_queue(ctx, server_num, track_info, insert_num)
        if queue_result == "queued":
            return
        
        # 재생 시작
        await self._start_playback(ctx, server_num)

    async def _validate_play_input(self, ctx, url, insert_num):
        """play 명령어 입력값 검증"""
        if insert_num < 0:
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send("index error", ephemeral=True)
            else:
                await ctx.reply("index error")
            return False
        return True

    async def _handle_voice_connection(self, ctx):
        """음성 채널 연결 처리"""
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send("보이스 채널 경기장에 입장해 주세요!", ephemeral=True)
            else:
                await ctx.reply("보이스 채널 경기장에 입장해 주세요!")
            return None, None

        server_num = server_check(self.bot, channel)
        
        if server_num is None:
            if not await self._check_voice_permissions(ctx, channel):
                return None, None
            
            await channel.connect(timeout=10.0, self_deaf=True)
            await asyncio.sleep(0.5)
            
            server_num = len(self.bot.voice_clients) - 1
            self.server.append(Player())
            self.server[server_num].channel_set(ctx.channel)
            
            if hasattr(ctx, '_voice_client'):
                ctx.voice_client = self.bot.voice_clients[server_num]
        else:
            if hasattr(ctx, '_voice_client'):
                ctx.voice_client = self.bot.voice_clients[server_num]

        return channel, server_num

    async def _extract_track_info(self, url, ctx):
        """음악 정보 추출"""
        # 단축키 처리
        url = self._process_quick_url(url)
        
        try:
            q_info = self.DL.extract_info(url, download=False)
        except Exception:
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send("ERROR: URL invalid", ephemeral=True)
            else:
                await ctx.reply("ERROR: URL invalid")
            return None
        
        author = ctx.author.nick or ctx.author.name
        
        return {
            'info': q_info,
            'author': author,
            'original_url': url
        }

    def _process_quick_url(self, url):
        """빠른 URL 처리"""
        for i, quick_url in enumerate(MusicBotConfig.QUICK_URLS):
            if url == str(i + 1):
                return quick_url
        return url

    async def _manage_queue(self, ctx, server_num, track_info, insert_num):
        """큐 관리"""
        q_info = track_info['info']
        author = track_info['author']
        
        # yt-dlp가 추출한 실제 비디오 URL (webpage_url 또는 original_url 사용)
        actual_video_url = q_info.get('webpage_url') or q_info.get('original_url') or track_info['original_url']
        
        if len(self.server[server_num].q_list) == 0:
            self.server[server_num].queue_set(q_info['url'], q_info['title'], q_info['duration'], actual_video_url, author)
            queue_list = self.server[server_num].q_list
        elif insert_num == 0:
            self.server[server_num].queue_set(q_info['url'], q_info['title'], q_info['duration'], actual_video_url, author)
            queue_list = self.server[server_num].q_list
            q_num = len(queue_list) - 1
        else:
            self.server[server_num].queue_insert(q_info['url'], q_info['title'], q_info['duration'], actual_video_url, author, insert_num)
            queue_list = self.server[server_num].q_list
            q_num = insert_num

        # 큐에 추가된 경우 메시지 전송 후 종료
        if len(queue_list) > 1 or insert_num > 0:
            embed = self._create_queue_embed(
                '레이스 대기열에 추가됨',
                f'[{queue_list[q_num]["title"]}]({queue_list[q_num]["url"]})',
                q_num,
                queue_list[q_num]["duration"],
                queue_list[q_num]["author"],
                discord.Color.from_rgb(255, 215, 0)
            )
            
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send(embed=embed, ephemeral=True)
            else:
                await ctx.reply(embed=embed)
            return "queued"
        
        return "play"

    async def _start_playback(self, ctx, server_num):
        """재생 시작"""
        queue_list = self.server[server_num].q_list
        
        # 첫 번째 곡 재생
        track_data = queue_list[0]
        
        # 자막 다운로드 (완전히 비동기로 처리, 노래 재생 블로킹 방지)
        print(f"[Subtitle] Starting subtitle download for: {track_data['title']}")
        asyncio.create_task(self._download_subtitle_async(track_data, server_num))
        
        track = self._create_ffmpeg_track(track_data['link'])
        voice_client = self._get_voice_client(ctx, server_num)
        
        voice_client.play(track)
        self.server[server_num].np_time = time.time()

        # 첫 번째 곡 재생 시작 메시지 전송
        embed = self._create_queue_embed(
            '레이스 시작!',
            f'[{track_data["title"]}]({track_data["url"]})',
            0,
            track_data["duration"],
            track_data["author"],
            discord.Color.from_rgb(0, 200, 100)
        )
        
        if hasattr(ctx, 'interaction') and ctx.interaction is not None:
            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.reply(embed=embed)

        # 음악 재생 GUI 생성
        track_info = self._create_track_info(
            track_data['title'], 
            track_data['url'], 
            track_data['duration'], 
            track_data['author']
        )
        # 자막 데이터 추가
        if 'subtitle_data' in track_data:
            track_info['subtitle_data'] = track_data['subtitle_data']
        
        result = await self.ui_manager.get_or_create_ui(
            self.bot, server_num, voice_client, track_info, ctx
        )
        
        if len(result) == 3:
            music_view, message, was_empty_to_new = result
        else:
            music_view, message = result
            was_empty_to_new = False
        
        music_view.update_task = asyncio.create_task(music_view.start_progress_updates())
        
        if hasattr(self.bot, 'update_music_status'):
            self.bot.update_music_status(track_data['title'])
        
        # 재생 루프
        await self._playback_loop(ctx, server_num, queue_list)

    async def _playback_loop(self, ctx, server_num, queue_list):
        """재생 루프"""
        while True:
            try:
                voice_client = self._get_voice_client(ctx, server_num)
                
                if voice_client is None:
                    print("Voice client is None, breaking loop")
                    break
                
                if not voice_client.is_playing() and not voice_client.is_paused():
                    # 스킵 진행 중인지 확인
                    if self.skip_in_progress.get(server_num, False):
                        await asyncio.sleep(0.1)
                        continue
                    
                    # seek 중인지 확인
                    is_seeking = await self._check_seek_status(server_num)
                    
                    if not is_seeking:
                        # 마지막 노래인 경우 큐에서 제거
                        if len(queue_list) == 1:
                            queue_list.pop(0)
                            await self._handle_empty_queue(ctx, server_num)
                            break
                        
                        await self._handle_queue_advancement(server_num, queue_list)
                        
                        if len(queue_list) == 0:
                            await self._handle_empty_queue(ctx, server_num)
                            break
                        
                        await self._play_next_track(ctx, server_num, queue_list)
                    else:
                        await asyncio.sleep(0.1)
                        continue
                else:
                    await asyncio.sleep(0.1)
            
            except Exception as e:
                print(f"Playback loop error: {e}")
                break

    async def _check_seek_status(self, server_num):
        """seek 상태 확인"""
        try:
            if (hasattr(self, 'ui_manager') and self.ui_manager and 
                server_num in self.ui_manager.server_uis):
                music_view = self.ui_manager.server_uis[server_num]
                if music_view and hasattr(music_view, '_seeking'):
                    return music_view._seeking
        except Exception as e:
            print(f"Error checking seek status: {e}")
        return False

    async def _handle_queue_advancement(self, server_num, queue_list):
        """큐 진행 처리"""
        if self.server[server_num].repeat_mode and len(queue_list) > 0:
            current_song = queue_list.pop(0)
            queue_list.append(current_song)
        else:
            # 마지막 노래인 경우 큐에서 제거하지 않음 (재생 완료 후 제거)
            if len(queue_list) > 1:
                queue_list.pop(0)

    async def _handle_empty_queue(self, ctx, server_num):
        """빈 큐 처리"""
        if hasattr(self.bot, 'update_music_status'):
            self.bot.update_music_status(None)
        
        try:
            await self.ui_manager.show_empty_queue_ui(self.bot, server_num, ctx)
        except Exception as e:
            print(f"Failed to show empty queue UI: {e}")

        # bring_ui_to_bottom 호출 제거 - 중복 UI 생성 방지
        # try:
        #     await self.ui_manager.bring_ui_to_bottom(self.bot, server_num, ctx)
        # except Exception as e:
        #     print(f"GUI 자동 이동 중 오류 발생: {e}")

    async def _play_next_track(self, ctx, server_num, queue_list):
        """다음 트랙 재생"""
        track_data = queue_list[0]
        
        # 자막 다운로드 (완전히 비동기로 처리, 노래 재생 블로킹 방지)
        print(f"[Subtitle] Starting subtitle download for: {track_data['title']}")
        asyncio.create_task(self._download_subtitle_async(track_data, server_num))
        
        try:
            track = self._create_ffmpeg_track(track_data['link'])
            voice_client = self._get_voice_client(ctx, server_num)
            
            if voice_client is None:
                return
            
            await asyncio.sleep(0.05)
            
            if not voice_client.is_connected():
                return
            
            # 더미 오디오로 활성화
            await self._play_dummy_audio(voice_client)
            
            voice_client.play(track)
            self.server[server_num].np_time = time.time()
            
            # UI 업데이트
            track_info = self._create_track_info(
                track_data['title'], 
                track_data['url'], 
                track_data['duration'], 
                track_data['author'],
                track_data.get('original_url', track_data['url'])
            )
            # 자막 데이터 추가
            if 'subtitle_data' in track_data:
                track_info['subtitle_data'] = track_data['subtitle_data']

            await self.ui_manager.bring_ui_to_bottom(self.bot, server_num, ctx)
            await self._update_music_ui(ctx, server_num, voice_client, track_info)
            
            if hasattr(self.bot, 'update_music_status'):
                self.bot.update_music_status(track_data['title'])
                
        except Exception as e:
            print(f"Error playing next track: {e}")

    async def _download_subtitle_async(self, track_data, server_num=None):
        """자막 다운로드를 비동기로 처리"""
        try:
            subtitle_data = await subtitle_service.get_subtitles_for_video(
                track_data['url'], 
                track_data['title']
            )
            
            if subtitle_data:
                track_data['subtitle_data'] = subtitle_data
                print(f"[Subtitle] Subtitle ready: {subtitle_data.get('language', 'unknown')}")
                
                # 자막이 준비되면 GUI 업데이트 트리거
                if server_num is not None and hasattr(self, 'ui_manager'):
                    try:
                        if server_num in self.ui_manager.server_uis:
                            music_view = self.ui_manager.server_uis[server_num]
                            if music_view and hasattr(music_view, 'track_info'):
                                music_view.track_info['subtitle_data'] = subtitle_data
                                print(f"[Subtitle] GUI updated with subtitle data for server {server_num}")
                    except Exception as e:
                        print(f"[Subtitle] Failed to update GUI: {e}")
            else:
                print("[Subtitle] No subtitle available")
                
        except Exception as e:
            print(f"[Subtitle] Subtitle download failed: {e}")

    async def _play_dummy_audio(self, voice_client):
        """더미 오디오 재생"""
        try:
            dummy_audio = discord.FFmpegPCMAudio("silence.mp3", executable=MusicBotConfig.FFMPEG_LOCATION)
            voice_client.play(dummy_audio)
            await asyncio.sleep(0.02)
            voice_client.stop()
        except Exception as e:
            print(f"Dummy audio play failed: {e}")

    async def _update_music_ui(self, ctx, server_num, voice_client, track_info):
        """음악 UI 업데이트"""
        try:
            result = await self.ui_manager.get_or_create_ui(
                self.bot, server_num, voice_client, track_info, ctx
            )
            
            if len(result) == 3:
                music_view, message, was_empty_to_new = result
            else:
                music_view, message = result
                was_empty_to_new = False
            
            if music_view.update_task and not music_view.update_task.done():
                music_view.update_task.cancel()
            music_view.update_task = asyncio.create_task(music_view.start_progress_updates())
            
        except Exception as e:
            print(f"ERROR: UI update failed: {e}")

    # ============================================================================
    # Additional Commands
    # ============================================================================
    
    @commands.command(name="queue", aliases=["q", "Q", "ㅂ"])
    async def queue(self, ctx, num: int = 1):
        """음악 대기열을 확인합니다."""
        a_voice, server_num = await self._check_voice_channel(ctx)
        if server_num is None:
            return

        embed = discord.Embed(title="레이스 대기열 정보", color=discord.Color.from_rgb(255, 20, 147))
        q_num = len(self.server[server_num].q_list)
        
        if q_num == 0:
            embed.add_field(name='Empty', value='큐가 비어있습니다.')
        else:
            playlist_data = self._format_queue_playlist(server_num, num)
            embed.add_field(name=f'Lists {playlist_data["total_time"]}', 
                          value=f"{playlist_data['content']}\n{num} / {playlist_data['total_pages']}")

        if hasattr(ctx, 'interaction') and ctx.interaction is not None:
            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.reply(embed=embed)

    def _format_queue_playlist(self, server_num, page_num):
        """큐 플레이리스트 포맷팅"""
        q_list = self.server[server_num].q_list
        playlist_page = []
        playlist = ""
        play_time = datetime.timedelta(seconds=0)
        count = 0

        for i, track in enumerate(q_list):
            prefix = "🎵 **" if i == 0 else ""
            suffix = "**" if i == 0 else ""
            
            playlist += f"{prefix}{i+1}. [{track['title']}]({track['url']}) | {track['duration']} | {track['author']}{suffix}\n"
            count += 1
            play_time += track['duration']
            
            if len(playlist) > 800 or count == 7:
                playlist_page.append(playlist)
                playlist = ""
                count = 0
            elif i + 1 == len(q_list):
                playlist_page.append(playlist)

        return {
            'content': playlist_page[page_num - 1] if page_num <= len(playlist_page) else "페이지가 없습니다.",
            'total_pages': len(playlist_page),
            'total_time': play_time
        }

    @commands.command(name="skip", aliases=["s", "S", "ㄴ"])
    async def skip(self, ctx):
        """다음 곡으로 넘어갑니다."""
        a_voice, server_num = await self._check_voice_channel(ctx)
        if server_num is None:
            return
        
        voice_client = self._get_voice_client(ctx, server_num)
        
        if voice_client is None:
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send("음성 채널에 연결되어 있지 않습니다!", ephemeral=True)
            else:
                await ctx.reply("음성 채널에 연결되어 있지 않습니다!")
            return
        
        # 큐에 곡이 있는지 확인
        if len(self.server[server_num].q_list) == 0:
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send("스킵할 레이스가 없어요!", ephemeral=True)
            else:
                await ctx.reply("스킵할 레이스가 없어요!")
            return
        
        # 스킵 진행 플래그 설정
        self.skip_in_progress[server_num] = True
        
        if hasattr(ctx, 'interaction') and ctx.interaction is not None:
            await ctx.send("다음 레이스로!", ephemeral=True)
        else:
            await ctx.reply("다음 레이스로!")
        
        # 현재 재생 중지
        if voice_client.is_playing():
            voice_client.stop()
        
        # 큐에서 첫 번째 곡 제거
        if len(self.server[server_num].q_list) > 0:
            self.server[server_num].q_list.pop(0)
        
        if hasattr(self.bot, 'update_music_status'):
            self.bot.update_music_status(None)
        
        # 다음 곡이 있으면 재생
        if len(self.server[server_num].q_list) > 0:
            try:
                await self._play_next_track(ctx, server_num, self.server[server_num].q_list)
            except Exception as e:
                print(f"Error playing next track after skip: {e}")
        else:
            # skip 명령어로 인한 빈 큐 - 기존 UI를 빈 큐 상태로 업데이트
            try:
                if server_num in self.ui_manager.server_uis:
                    ui = self.ui_manager.server_uis[server_num]
                    # 빈 큐 상태로 트랙 정보 업데이트
                    ui.track_info = {
                        'title': '재생 목록이 없어요',
                        'url': '',
                        'duration': 0,
                        'author': '',
                        'is_empty': True
                    }
                    ui.start_time = time.time()
                    
                    # 업데이트 태스크 중지
                    if ui.update_task and not ui.update_task.done():
                        ui.update_task.cancel()
                    
                    # UI 업데이트
                    await ui.update_progress()
            except Exception as e:
                print(f"Failed to update UI to empty state after skip: {e}")
        
        # 스킵 완료 후 플래그 해제
        self.skip_in_progress[server_num] = False

    @commands.command(name="leave", aliases=["l", "L", "ㅣ"])
    async def leave(self, ctx):
        """음성 채널에서 나갑니다."""
        a_voice, server_num = await self._check_voice_channel(ctx)
        if server_num is None:
            return

        channel_id = self.bot.voice_clients[server_num].channel.id
        
        await leave(self.bot, server_num, self.ui_manager, self.server)
        await ctx.send(f"스마트 팔콘이 <#{channel_id}>에서 퇴장했어요!")
        
        if hasattr(self.bot, 'update_music_status'):
            self.bot.update_music_status(None)

    @commands.command(name="delete", aliases=["d", "D", "ㅇ"]) 
    async def delete(self, ctx, index: int):
        """대기열에서 곡을 제거합니다."""
        if index <= 0: 
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send("index error", ephemeral=True)
            else:
                await ctx.reply("index error")
            return
            
        a_voice, server_num = await self._check_voice_channel(ctx)
        if server_num is None:
            return

        queue_list = self.server[server_num].q_list

        q_title = queue_list[index]['title']
        q_duration = queue_list[index]['duration']
        q_url = queue_list[index]['url']
        q_author = queue_list[index]['author']
        
        queue_list.pop(index)

        embed = self._create_queue_embed(
            '레이스에서 제외됨',
            f'[{q_title}]({q_url})',
            index,
            q_duration,
            q_author,
            discord.Color.from_rgb(255, 100, 100)
        )
        await ctx.send(embed=embed)

    @commands.command(name="nowplaying", aliases=["np", "Np", "NP", "ㅞ"])
    async def now_playing(self, ctx):
        """현재 재생 중인 곡을 확인합니다."""
        a_voice, server_num = await self._check_voice_channel(ctx)
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

            embed = discord.Embed(title='현재 레이스 중', description=f'[{title}]({url})', color=discord.Color.from_rgb(0, 200, 100))
            embed.add_field(name='Duration', value=f'{playing_time} / {duration}', inline=True)
            embed.add_field(name='Requested by', value=f'{author}', inline=True)
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send(embed=embed, ephemeral=True)
            else:
                await ctx.reply(embed=embed)
        else:
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send("현재 레이스 중인 음악이 없어요!", ephemeral=True)
            else:
                await ctx.reply("현재 레이스 중인 음악이 없어요!")

    @commands.command(name="quicknumber", aliases=["qn", "Qn", "부"])
    async def quick_number(self, ctx, num: int = 1):
        """빠른 번호 목록을 확인합니다."""
        quicklist_page = []
        playlist = ""
        count = 0

        embed = discord.Embed(title="빠른 레이스 번호", color=discord.Color.from_rgb(255, 215, 0))
        
        for i in range(len(MusicBotConfig.QUICK_URLS)):
            playlist += f"{i+1}. {MusicBotConfig.QUICK_URLS[i]}\n"
            count += 1
                
            if len(playlist) > 800 or count == 7:
                quicklist_page.append(playlist)
                playlist = ""
                count = 0
            elif i + 1 == len(MusicBotConfig.QUICK_URLS):
                quicklist_page.append(playlist)
        
        embed.add_field(name=f'Lists', value=f"{quicklist_page[num-1]}\n{num} / {len(quicklist_page)}")
        if hasattr(ctx, 'interaction') and ctx.interaction is not None:
            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.reply(embed=embed)

    @commands.command(name="pause", aliases=["ps", "Ps", "ㅔㄴ"])
    async def pause(self, ctx):
        """음악을 일시정지합니다."""
        a_voice, server_num = await self._check_voice_channel(ctx)
        if server_num is None:
            return

        voice_client = self._get_voice_client(ctx, server_num)
        
        if voice_client is None:
            await ctx.send("음성 채널에 연결되어 있지 않습니다!")
            return

        voice_client.pause()
        await ctx.send("휴식 시간!")
        
        if hasattr(self.bot, 'update_music_status'):
            self.bot.update_music_status(None)

    @commands.command(name="resume", aliases=["rs", "Rs", "ㄱㄴ"])
    async def resume(self, ctx):
        """일시정지된 음악을 재생합니다."""
        a_voice, server_num = await self._check_voice_channel(ctx)
        if server_num is None:
            return

        voice_client = self._get_voice_client(ctx, server_num)
        
        if voice_client is None:
            await ctx.send("음성 채널에 연결되어 있지 않습니다!")
            return

        voice_client.resume()
        await ctx.send("레이스 재개!")
        
        if hasattr(self.bot, 'update_music_status'):
            if len(self.server[server_num].q_list) > 0:
                self.bot.update_music_status(self.server[server_num].q_list[0]['title'])

    @commands.command(name="gui", aliases=["player", "플레이어"])
    async def bring_gui(self, ctx):
        """플레이어 GUI를 채팅 맨 아래로 가져오기"""
        if not ctx.author.voice:
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send("❌ 음성 채널에 먼저 들어가주세요!", ephemeral=True)
            else:
                await ctx.reply("❌ 음성 채널에 먼저 들어가주세요!")
            return
        
        voice_channel = ctx.author.voice.channel
        server_num = server_check(self.bot, voice_channel)
        
        if server_num is None:
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send("❌ 봇이 음성 채널에 연결되어 있지 않습니다!", ephemeral=True)
            else:
                await ctx.reply("❌ 봇이 음성 채널에 연결되어 있지 않습니다!")
            return
        
        if server_num not in self.ui_manager.server_uis:
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send("❌ 현재 재생 중인 음악이 없습니다!", ephemeral=True)
            else:
                await ctx.reply("❌ 현재 재생 중인 음악이 없습니다!")
            return
        
        ui, message = await self.ui_manager.bring_ui_to_bottom(self.bot, server_num, ctx)
        
        if ui and message:
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send("✅ 플레이어 GUI를 채팅 맨 아래로 가져왔습니다!", ephemeral=True, delete_after=3)
            else:
                await ctx.reply("✅ 플레이어 GUI를 채팅 맨 아래로 가져왔습니다!", delete_after=3)
        else:
            if hasattr(ctx, 'interaction') and ctx.interaction is not None:
                await ctx.send("❌ GUI를 가져오는 중 오류가 발생했습니다!", ephemeral=True)
            else:
                await ctx.reply("❌ GUI를 가져오는 중 오류가 발생했습니다!")

    @commands.command(name="test")
    async def test_seek(self, ctx, url):
        """간단한 seek 테스트 명령어"""
        if not ctx.author.voice:
            await ctx.send("음성 채널에 먼저 들어가주세요!")
            return
        
        voice_channel = ctx.author.voice.channel
        voice_client = ctx.voice_client
        
        if not voice_client:
            voice_client = await voice_channel.connect()
        
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
        
        initial_track = self._create_ffmpeg_track(audio_url)
        voice_client.play(initial_track)
        
        await ctx.send(f"🎵 **{title}** 재생 시작! 5초 후 30초 위치로 이동합니다...")
        
        await asyncio.sleep(5)
        
        seek_track = self._create_ffmpeg_track(audio_url, 30)
        
        voice_client.stop()
        await asyncio.sleep(1)
        
        voice_client.play(seek_track, after=lambda e: print(f"Test seek track ended: {e}"))
        
        await ctx.send("⏩ **30초 위치로 이동 완료!**")

    # ============================================================================
    # Slash Commands
    # ============================================================================
    
    @discord.app_commands.command(name="play", description="음악을 재생합니다")
    @discord.app_commands.describe(url="유튜브 URL 또는 빠른 번호 (1-3)", insert_num="대기열에 삽입할 위치 (기본값: 0)")
    async def slash_play(self, interaction: discord.Interaction, url: str, insert_num: int = 0):
        await interaction.response.defer(ephemeral=True)
        ctx = FakeCtx(interaction)
        await self.play(ctx, url, insert_num)

    @discord.app_commands.command(name="queue", description="음악 대기열을 확인합니다")
    @discord.app_commands.describe(num="페이지 번호 (기본값: 1)")
    async def slash_queue(self, interaction: discord.Interaction, num: int = 1):
        await interaction.response.defer(ephemeral=True)
        ctx = FakeCtx(interaction)
        await self.queue(ctx, num)

    @discord.app_commands.command(name="skip", description="다음 곡으로 넘어갑니다")
    async def slash_skip(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ctx = FakeCtx(interaction)
        await self.skip(ctx)

    @discord.app_commands.command(name="leave", description="음성 채널에서 나갑니다")
    async def slash_leave(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        ctx = FakeCtx(interaction)
        await self.leave(ctx)

    @discord.app_commands.command(name="delete", description="대기열에서 곡을 제거합니다")
    @discord.app_commands.describe(index="제거할 곡의 번호")
    async def slash_delete(self, interaction: discord.Interaction, index: int):
        await interaction.response.defer(ephemeral=True)
        ctx = FakeCtx(interaction)
        await self.delete(ctx, index)

    @discord.app_commands.command(name="nowplaying", description="현재 재생 중인 곡을 확인합니다")
    async def slash_nowplaying(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ctx = FakeCtx(interaction)
        await self.now_playing(ctx)

    @discord.app_commands.command(name="quicknumber", description="빠른 번호 목록을 확인합니다")
    @discord.app_commands.describe(num="페이지 번호 (기본값: 1)")
    async def slash_quicknumber(self, interaction: discord.Interaction, num: int = 1):
        await interaction.response.defer(ephemeral=True)
        ctx = FakeCtx(interaction)
        await self.quick_number(ctx, num)

    @discord.app_commands.command(name="pause", description="음악을 일시정지합니다")
    async def slash_pause(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        ctx = FakeCtx(interaction)
        await self.pause(ctx)

    @discord.app_commands.command(name="resume", description="일시정지된 음악을 재생합니다")
    async def slash_resume(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        ctx = FakeCtx(interaction)
        await self.resume(ctx)

    @discord.app_commands.command(name="gui", description="플레이어 GUI를 채팅 맨 아래로 가져옵니다")
    async def slash_bring_gui(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ctx = FakeCtx(interaction)
        await self.bring_gui(ctx)

async def setup(bot):
    """Cog를 봇에 로드하는 함수"""
    await bot.add_cog(DJ(bot))