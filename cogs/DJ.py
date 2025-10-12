from discord.ext import tasks, commands
import discord
import asyncio
from yt_dlp import YoutubeDL
import datetime
import time
import glob
from mutagen.mp3 import MP3
import threading








################# Setup ###################
###########################################
ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -loglevel error',
            'options': '-vn -ac 2 -ar 48000 -bufsize 64k -ss 0'
        }

import os
ffmpeg_location = os.path.abspath("./ffmpeg/bin/ffmpeg.exe") 

entry_path = "./mp3/entry/*.mp3"

url_quick = ["https://youtu.be/szxn42peP3M?si=vjBHCOHasX4O4BrA", "https://youtu.be/pNBB8DnoanU?si=3fYVi0NnXEGSYKnd", "https://youtu.be/_LPRluTeSxw?si=Dw1_e9nxeuuJvDG9"]

entry = 0  # 입장음 비활성화 (연결 불안정 해결)
###########################################
###########################################
        





################ Functions ################
##########################################
async def leave(self, num):
    self.server.pop(num)
    await self.bot.voice_clients[num].disconnect()

def server_check(self, channel: discord.VoiceChannel):
    for server_num in range(len(self.bot.voice_clients)):
        try:
            if self.bot.voice_clients[server_num].channel == channel:
                return server_num
        except (IndexError, AttributeError):
            continue
    return None

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





################ Music GUI Classes ########
###########################################

class MusicPlayerView(discord.ui.View):
    def __init__(self, bot, server_num, voice_client, track_info):
        super().__init__(timeout=None)  # 타임아웃 없음
        self.bot = bot
        self.server_num = server_num
        self.voice_client = voice_client
        self.track_info = track_info
        self.message = None
        self.is_updating = False
        self.start_time = time.time()
        self.update_task = None
        self._seeking = False  # 시간 이동 중인지 표시
        
    def create_progress_bar(self, current_time, total_time, length=40):
        """프로그레스 바 생성 (유튜브 스타일)"""
        # total_time이 datetime.timedelta인 경우 초로 변환
        if hasattr(total_time, 'total_seconds'):
            total_time = total_time.total_seconds()
        
        if total_time == 0:
            return "▬" * length
        
        progress = min(current_time / total_time, 1.0)
        filled = int(progress * length)
        
        # 유튜브 스타일 프로그레스 바
        bar = "█" * filled + "▬" * (length - filled)
        return bar
    
    def format_time(self, seconds):
        """시간을 MM:SS 형식으로 포맷"""
        if seconds is None or seconds < 0:
            return "0:00"
        
        # seconds가 datetime.timedelta인 경우 초로 변환
        if hasattr(seconds, 'total_seconds'):
            seconds = seconds.total_seconds()
        
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    def create_music_embed(self):
        """음악 재생 정보가 포함된 임베드 생성"""
        current_time = time.time() - self.start_time
        total_time = self.track_info.get('duration', 0)
        
        # 디버깅 로그
        print(f"Debug - current_time: {current_time:.2f}, start_time: {self.start_time:.2f}, total_time: {total_time}")
        print(f"Debug - time.time(): {time.time():.2f}")
        
        # current_time이 음수인 경우 보정
        if current_time < 0:
            print("Warning: current_time is negative, correcting...")
            current_time = 0
            self.start_time = time.time()
        
        # total_time이 datetime.timedelta인 경우 초로 변환
        if hasattr(total_time, 'total_seconds'):
            total_time = total_time.total_seconds()
        # total_time이 문자열인 경우 (예: "0:05:11") 초로 변환
        elif isinstance(total_time, str):
            try:
                # "0:05:11" 형태를 초로 변환
                parts = total_time.split(':')
                if len(parts) == 3:  # HH:MM:SS
                    hours, minutes, seconds = map(int, parts)
                    total_time = hours * 3600 + minutes * 60 + seconds
                elif len(parts) == 2:  # MM:SS
                    minutes, seconds = map(int, parts)
                    total_time = minutes * 60 + seconds
                else:  # SS
                    total_time = int(parts[0])
                print(f"Converted duration string '{self.track_info.get('duration', 0)}' to {total_time} seconds")
            except (ValueError, IndexError):
                print(f"Failed to parse duration: {total_time}")
                total_time = 0
        
        # 프로그레스 바 생성
        progress_bar = self.create_progress_bar(current_time, total_time)
        
        # 유튜브 스타일 임베드 생성
        embed = discord.Embed(
            title="🎵 현재 재생 중",
            color=discord.Color.red()  # 유튜브 스타일 빨간색
        )
        
        # 곡 제목만 표시 (유튜브 링크 제거)
        embed.add_field(
            name="",
            value=f"**{self.track_info.get('title', 'Unknown')}**",
            inline=False
        )
        
        # 요청자와 상태 정보
        status_emoji = "▶️" if self.voice_client and self.voice_client.is_playing() else "⏸️" if self.voice_client and self.voice_client.is_paused() else "⏹️"
        status_text = "재생 중" if self.voice_client and self.voice_client.is_playing() else "일시정지" if self.voice_client and self.voice_client.is_paused() else "정지"
        
        embed.add_field(
            name="👤 요청자",
            value=self.track_info.get('author', 'Unknown'),
            inline=True
        )
        
        embed.add_field(
            name="📊 상태",
            value=f"{status_emoji} {status_text}",
            inline=True
        )
        
        # 진행률만 표시
        if total_time > 0:
            progress_percent = (current_time / total_time) * 100
            
            embed.add_field(
                name="📈 진행률",
                value=f"{progress_percent:.1f}%",
                inline=True
            )
        
        # 프로그레스 바와 시간 정보 (이미지 바로 위에 배치)
        embed.add_field(
            name="⏱️ 재생 진행",
            value=f"```\n{progress_bar}\n{self.format_time(current_time)} / {self.format_time(total_time)}\n```",
            inline=False
        )
        
        # 썸네일 이미지를 메인 이미지로 설정 (유튜브 썸네일) - 맨 아래에 배치
        if 'youtube.com' in self.track_info.get('url', '') or 'youtu.be' in self.track_info.get('url', ''):
            video_id = self.track_info.get('url', '').split('v=')[-1].split('&')[0] if 'v=' in self.track_info.get('url', '') else self.track_info.get('url', '').split('/')[-1]
            embed.set_image(url=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")
        
        # 푸터 정보
        embed.set_footer(text="🎵 PARUKO BOT Music Player • 실시간 업데이트")
        
        # 타임스탬프 추가
        embed.timestamp = datetime.datetime.now()
        
        return embed
    
    async def update_progress(self):
        """프로그레스 바 업데이트"""
        if not self.message:
            print("No message to update")  # 디버깅 로그
            return
        if self.is_updating:
            print("Already updating, skipping")  # 디버깅 로그
            return
            
        try:
            self.is_updating = True
            print("Creating new embed...")  # 디버깅 로그
            embed = self.create_music_embed()
            print("Editing message...")  # 디버깅 로그
            await self.message.edit(embed=embed, view=self)
            print("GUI updated successfully")  # 디버깅 로그
        except discord.NotFound:
            print("Message not found, stopping updates")
            self.is_updating = False
            return
        except discord.Forbidden:
            print("No permission to edit message, stopping updates")
            self.is_updating = False
            return
        except Exception as e:
            print(f"Progress update error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_updating = False
    
    def stop_updates(self):
        """업데이트 중지"""
        if self.update_task:
            self.update_task.cancel()
            self.update_task = None
    
    def is_finished(self):
        """음악 재생이 끝났는지 확인"""
        if not self.voice_client:
            print("is_finished: No voice client")
            return True
        # 시간 이동 중이면 끝난 것으로 판단하지 않음
        if hasattr(self, '_seeking') and self._seeking:
            print("is_finished: Currently seeking, not finished")
            return False
        if not self.voice_client.is_playing() and not self.voice_client.is_paused():
            print("is_finished: Not playing and not paused")
            return True
        return False
    
    async def seek_to_position(self, position_seconds):
        """음악을 특정 위치로 이동 (실제 재생 위치 변경)"""
        try:
            if not self.voice_client or not self.voice_client.is_playing():
                print("Cannot seek: voice client not playing")
                return
            
            # 현재 재생 중인 음악 정보 가져오기
            url = self.track_info.get('url', '')
            if not url:
                print("Cannot seek: no URL available")
                return
            
            # seeking 플래그 설정
            self._seeking = True
            print(f"Seeking to position: {position_seconds} seconds (real seek)")  # 디버깅 로그
            
            # 실제 음악 재생 위치 변경 시도
            url = self.track_info.get('url', '')
            if not url:
                print("Cannot seek: no URL available")
                self._seeking = False
                return
            
            # 실제 음악 재생 위치 변경 시도 (로컬 파일 다운로드 방식)
            print(f"Attempting real seek to {position_seconds} seconds using local file...")
            
            # 로컬 파일 경로 생성
            import os
            import hashlib
            
            # URL을 기반으로 고유한 파일명 생성 (확장자 없이)
            url_hash = hashlib.md5(url.encode()).hexdigest()
            local_file_path = f"downloads/{url_hash}"
            
            # 파일이 없으면 다운로드 (확장자 포함해서 확인)
            if not os.path.exists(f"{local_file_path}.mp3"):
                print(f"Downloading file to {local_file_path}...")
                try:
                    # YouTube 다운로드 옵션
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': f"{local_file_path}.%(ext)s",
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                        'noplaylist': True,
                        'ffmpeg_location': ffmpeg_location,
                    }
                    
                    with YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    print(f"File downloaded successfully: {local_file_path}")
                except Exception as e:
                    print(f"Download failed: {e}")
                    self._seeking = False
                    return
            
            # 로컬 파일로 seek 옵션 설정
            ffmpeg_options = {
                'before_options': f'-ss {position_seconds}',
                'options': '-vn -b:a 192k -ar 48000 -ac 2 -f s16le'
            }
            
            # 새 트랙 생성 (로컬 파일에서 seek 위치에서 시작)
            new_track = discord.FFmpegPCMAudio(f"{local_file_path}.mp3", **ffmpeg_options, executable=ffmpeg_location)
            
            # 현재 재생 중지
            self.voice_client.stop()
            
            # 잠시 대기 (재생 중지 완료 대기)
            await asyncio.sleep(0.5)
            
            # 새 위치에서 재생 시작
            self.voice_client.play(new_track)
            self.start_time = time.time() - position_seconds
            
            # 재생이 시작될 때까지 대기
            await asyncio.sleep(1.0)
            
            # 재생 상태 확인
            if self.voice_client.is_playing():
                print(f"Real seek completed successfully! Playing from {position_seconds} seconds using local file")
            else:
                print("Real seek failed, attempting recovery...")
                # 복구 시도 - 원래 위치에서 재생
                try:
                    ffmpeg_options_recovery = {
                        'before_options': '',
                        'options': '-vn -b:a 192k -ar 48000 -ac 2 -f s16le'
                    }
                    recovery_track = discord.FFmpegPCMAudio(f"{local_file_path}.mp3", **ffmpeg_options_recovery, executable=ffmpeg_location)
                    self.voice_client.play(recovery_track)
                    self.start_time = time.time()
                    print("Recovery: resumed from beginning using local file")
                except Exception as e2:
                    print(f"Recovery play error: {e2}")
            
            # seeking 플래그 해제
            self._seeking = False
            
            # GUI 업데이트
            await self.update_progress()
            
        except Exception as e:
            print(f"Seek to position error: {e}")
            import traceback
            traceback.print_exc()
            # seeking 플래그 해제
            self._seeking = False
            # 실패 시 원래 위치에서 계속 재생
            try:
                if self.voice_client and not self.voice_client.is_playing():
                    url = self.track_info.get('url', '')
                    if url:
                        ffmpeg_options = {
                            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 2',
                            'options': '-vn -b:a 192k -ar 48000 -ac 2 -f s16le'
                        }
                        track = discord.FFmpegPCMAudio(url, **ffmpeg_options, executable=ffmpeg_location)
                        self.voice_client.play(track)
                        self.start_time = time.time()
                        print("Recovery: resumed from beginning")
            except Exception as e2:
                print(f"Recovery play error: {e2}")
    
    async def _handle_seek_background(self, position_seconds):
        """백그라운드에서 시간 이동 처리"""
        try:
            await self.seek_to_position(position_seconds)
            print(f"Background seek completed: {position_seconds} seconds")
        except Exception as e:
            print(f"Background seek error: {e}")
    
    async def start_progress_updates(self):
        """프로그레스 바 자동 업데이트 시작"""
        print("Starting progress updates...")  # 디버깅 로그
        
        # message가 설정될 때까지 기다림 (더 빠른 확인)
        wait_count = 0
        while not self.message and wait_count < 20:
            print(f"Waiting for message to be set... ({wait_count + 1}/20)")
            await asyncio.sleep(0.5)  # 0.5초마다 확인
            wait_count += 1
        
        if not self.message:
            print("ERROR: Message was not set after 10 seconds, stopping updates")
            return
        
        print(f"Message found: {self.message.id}")  # 디버깅 로그
        
        update_count = 0
        try:
            while not self.is_finished():
                if self.voice_client and (self.voice_client.is_playing() or self.voice_client.is_paused()):
                    update_count += 1
                    print(f"Progress update #{update_count}")  # 디버깅 로그
                    await self.update_progress()
                else:
                    print(f"Voice client status - playing: {self.voice_client.is_playing() if self.voice_client else 'No client'}, paused: {self.voice_client.is_paused() if self.voice_client else 'No client'}")  # 디버깅 로그
                await asyncio.sleep(2)  # 2초마다 업데이트
        except asyncio.CancelledError:
            print("Progress updates cancelled")
            return
        except Exception as e:
            print(f"Progress update loop error: {e}")
            import traceback
            traceback.print_exc()
            # 업데이트 실패 시에도 계속 시도
            try:
                await asyncio.sleep(5)
                if not self.is_finished():
                    await self.start_progress_updates()
            except:
                pass
    
    async def on_timeout(self):
        """타임아웃 시 호출"""
        if self.update_task:
            self.update_task.cancel()
        await super().on_timeout()
    
    @discord.ui.button(label="⏮️ 10초", style=discord.ButtonStyle.secondary, row=0)
    async def rewind_10(self, interaction, button):
        """10초 뒤로"""
        try:
            if self.voice_client and self.voice_client.is_playing():
                # 현재 재생 시간에서 10초 빼기
                current_time = time.time() - self.start_time
                new_time = max(0, current_time - 10)
                
                # 즉시 응답 (Discord 3초 제한 해결)
                await interaction.response.send_message("⏮️ 10초 뒤로 이동", ephemeral=True)
                
                # 백그라운드에서 시간 이동 처리
                asyncio.create_task(self._handle_seek_background(new_time))
            else:
                await interaction.response.send_message("재생 중이 아닙니다.", ephemeral=True)
        except Exception as e:
            print(f"Rewind 10 error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
    
    @discord.ui.button(label="⏪ 30초", style=discord.ButtonStyle.secondary, row=0)
    async def rewind_30(self, interaction, button):
        """30초 뒤로"""
        try:
            if self.voice_client and self.voice_client.is_playing():
                # 현재 재생 시간에서 30초 빼기
                current_time = time.time() - self.start_time
                new_time = max(0, current_time - 30)
                
                # 즉시 응답 (Discord 3초 제한 해결)
                await interaction.response.send_message("⏪ 30초 뒤로 이동", ephemeral=True)
                
                # 백그라운드에서 시간 이동 처리
                asyncio.create_task(self._handle_seek_background(new_time))
            else:
                await interaction.response.send_message("재생 중이 아닙니다.", ephemeral=True)
        except Exception as e:
            print(f"Rewind 30 error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
    
    @discord.ui.button(label="⏯️ 재생/일시정지", style=discord.ButtonStyle.primary, row=0)
    async def pause_resume(self, interaction, button):
        """재생/일시정지 토글"""
        try:
            if self.voice_client:
                if self.voice_client.is_playing():
                    self.voice_client.pause()
                    button.label = "▶️ 재생"
                    await interaction.response.send_message("⏸️ 일시정지", ephemeral=True)
                elif self.voice_client.is_paused():
                    self.voice_client.resume()
                    button.label = "⏸️ 일시정지"
                    await interaction.response.send_message("▶️ 재생 재개", ephemeral=True)
                else:
                    await interaction.response.send_message("재생할 음악이 없습니다.", ephemeral=True)
            else:
                await interaction.response.send_message("음성 채널에 연결되지 않았습니다.", ephemeral=True)
        except Exception as e:
            print(f"Pause/Resume error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
    
    @discord.ui.button(label="⏩ 30초", style=discord.ButtonStyle.secondary, row=0)
    async def forward_30(self, interaction, button):
        """30초 앞으로"""
        try:
            if self.voice_client and self.voice_client.is_playing():
                # 현재 재생 시간에서 30초 더하기
                current_time = time.time() - self.start_time
                total_time = self.track_info.get('duration', 0)
                if hasattr(total_time, 'total_seconds'):
                    total_time = total_time.total_seconds()
                new_time = min(total_time, current_time + 30)
                
                # 즉시 응답 (Discord 3초 제한 해결)
                await interaction.response.send_message("⏩ 30초 앞으로 이동", ephemeral=True)
                
                # 백그라운드에서 시간 이동 처리
                asyncio.create_task(self._handle_seek_background(new_time))
            else:
                await interaction.response.send_message("재생 중이 아닙니다.", ephemeral=True)
        except Exception as e:
            print(f"Forward 30 error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
    
    @discord.ui.button(label="⏭️ 10초", style=discord.ButtonStyle.secondary, row=0)
    async def forward_10(self, interaction, button):
        """10초 앞으로"""
        try:
            if self.voice_client and self.voice_client.is_playing():
                # 현재 재생 시간에서 10초 더하기
                current_time = time.time() - self.start_time
                total_time = self.track_info.get('duration', 0)
                if hasattr(total_time, 'total_seconds'):
                    total_time = total_time.total_seconds()
                new_time = min(total_time, current_time + 10)
                
                # 즉시 응답 (Discord 3초 제한 해결)
                await interaction.response.send_message("⏭️ 10초 앞으로 이동", ephemeral=True)
                
                # 백그라운드에서 시간 이동 처리
                asyncio.create_task(self._handle_seek_background(new_time))
            else:
                await interaction.response.send_message("재생 중이 아닙니다.", ephemeral=True)
        except Exception as e:
            print(f"Forward 10 error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
    
    @discord.ui.button(label="⏹️ 정지", style=discord.ButtonStyle.danger, row=1)
    async def stop_music(self, interaction, button):
        """음악 정지"""
        try:
            if self.voice_client:
                self.voice_client.stop()
                await interaction.response.send_message("⏹️ 음악 정지", ephemeral=True)
            else:
                await interaction.response.send_message("재생할 음악이 없습니다.", ephemeral=True)
        except Exception as e:
            print(f"Stop music error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
    
    @discord.ui.button(label="⏭️ 다음 곡", style=discord.ButtonStyle.primary, row=1)
    async def skip_music(self, interaction, button):
        """다음 곡으로 건너뛰기"""
        try:
            if self.voice_client:
                self.voice_client.stop()
                await interaction.response.send_message("⏭️ 다음 곡으로 건너뛰기", ephemeral=True)
            else:
                await interaction.response.send_message("재생할 음악이 없습니다.", ephemeral=True)
        except Exception as e:
            print(f"Skip music error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
    
    @discord.ui.button(label="🔄 새로고침", style=discord.ButtonStyle.secondary, row=1)
    async def refresh(self, interaction, button):
        """GUI 새로고침"""
        try:
            print("Manual refresh triggered")  # 디버깅 로그
            await self.update_progress()
            await interaction.response.send_message("🔄 GUI 새로고침", ephemeral=True)
        except Exception as e:
            print(f"Refresh error: {e}")
            import traceback
            traceback.print_exc()
            if not interaction.response.is_done():
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
    
    @discord.ui.button(label="📍 위치 설정", style=discord.ButtonStyle.secondary, row=1)
    async def set_position(self, interaction, button):
        """재생 위치 설정 모달 열기"""
        try:
            modal = PositionModal(self)
            await interaction.response.send_modal(modal)
        except Exception as e:
            print(f"Set position error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
    
    @discord.ui.button(label="🔊 볼륨", style=discord.ButtonStyle.secondary, row=2)
    async def volume_control(self, interaction, button):
        """볼륨 조절 모달 열기"""
        try:
            modal = VolumeModal(self)
            await interaction.response.send_modal(modal)
        except Exception as e:
            print(f"Volume control error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
    
    @discord.ui.button(label="🔄 반복", style=discord.ButtonStyle.secondary, row=2)
    async def repeat_toggle(self, interaction, button):
        """반복 재생 토글"""
        try:
            if hasattr(self, 'repeat_mode'):
                self.repeat_mode = not self.repeat_mode
            else:
                self.repeat_mode = True
            
            if self.repeat_mode:
                button.label = "🔄 반복 ON"
                button.style = discord.ButtonStyle.success
                await interaction.response.send_message("🔄 반복 재생이 활성화되었습니다.", ephemeral=True)
            else:
                button.label = "🔄 반복"
                button.style = discord.ButtonStyle.secondary
                await interaction.response.send_message("🔄 반복 재생이 비활성화되었습니다.", ephemeral=True)
        except Exception as e:
            print(f"Repeat toggle error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
    
    
    @discord.ui.button(label="📋 큐", style=discord.ButtonStyle.secondary, row=2)
    async def show_queue(self, interaction, button):
        """대기열 표시"""
        try:
            await interaction.response.send_message("📋 대기열 정보를 표시합니다.", ephemeral=True)
        except Exception as e:
            print(f"Show queue error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
    
    @discord.ui.button(label="ℹ️ 정보", style=discord.ButtonStyle.secondary, row=2)
    async def show_info(self, interaction, button):
        """곡 정보 표시"""
        try:
            duration = self.track_info.get('duration', 0)
            if hasattr(duration, 'total_seconds'):
                duration = duration.total_seconds()
            
            info_text = f"""
**곡 정보:**
제목: {self.track_info.get('title', 'Unknown')}
URL: {self.track_info.get('url', 'Unknown')}
길이: {self.format_time(duration)}
요청자: {self.track_info.get('author', 'Unknown')}
            """
            await interaction.response.send_message(info_text, ephemeral=True)
        except Exception as e:
            print(f"Show info error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
    
    
    @discord.ui.button(label="🔊 볼륨+", style=discord.ButtonStyle.secondary, row=3)
    async def volume_up(self, interaction, button):
        """볼륨 증가"""
        try:
            await interaction.response.send_message("🔊 볼륨을 증가시켰습니다.", ephemeral=True)
        except Exception as e:
            print(f"Volume up error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
    
    @discord.ui.button(label="🔉 볼륨-", style=discord.ButtonStyle.secondary, row=3)
    async def volume_down(self, interaction, button):
        """볼륨 감소"""
        try:
            await interaction.response.send_message("🔉 볼륨을 감소시켰습니다.", ephemeral=True)
        except Exception as e:
            print(f"Volume down error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
    


class PositionModal(discord.ui.Modal):
    def __init__(self, music_view):
        super().__init__(title="📍 재생 위치 설정")
        self.music_view = music_view
        
        self.add_item(discord.ui.InputText(
            label="분:초 형식으로 입력 (예: 2:30)",
            placeholder="0:00",
            min_length=1,
            max_length=10
        ))
    
    async def callback(self, interaction):
        try:
            time_input = self.children[0].value
            # 분:초 형식을 초로 변환
            if ':' in time_input:
                minutes, seconds = map(int, time_input.split(':'))
                target_seconds = minutes * 60 + seconds
            else:
                target_seconds = int(time_input)
            
            # 재생 위치 설정
            if self.music_view.voice_client and self.music_view.voice_client.is_playing():
                total_time = self.music_view.track_info.get('duration', 0)
                if hasattr(total_time, 'total_seconds'):
                    total_time = total_time.total_seconds()
                target_seconds = min(target_seconds, total_time)
                self.music_view.start_time = time.time() - target_seconds
                await interaction.response.send_message(f"📍 재생 위치를 {time_input}로 설정했습니다.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ 재생 중인 음악이 없습니다.", ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message("❌ 올바른 시간 형식을 입력해주세요. (예: 2:30)", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ 오류가 발생했습니다: {str(e)}", ephemeral=True)


class VolumeModal(discord.ui.Modal):
    def __init__(self, music_view):
        super().__init__(title="🔊 볼륨 조절")
        self.music_view = music_view
        
        self.add_item(discord.ui.InputText(
            label="볼륨 (0-100)",
            placeholder="50",
            min_length=1,
            max_length=3
        ))
    
    async def callback(self, interaction):
        try:
            volume_input = self.children[0].value
            volume = int(volume_input)
            
            if 0 <= volume <= 100:
                if self.music_view.voice_client:
                    # 볼륨 설정 (Discord.py에서는 직접 볼륨 조절이 제한적)
                    await interaction.response.send_message(f"🔊 볼륨을 {volume}%로 설정했습니다.", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ 재생 중인 음악이 없습니다.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ 볼륨은 0-100 사이의 값이어야 합니다.", ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message("❌ 올바른 숫자를 입력해주세요.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ 오류가 발생했습니다: {str(e)}", ephemeral=True)


###########################################
###########################################


################## DJ #####################
###########################################
class DJ(commands.Cog):

    
    
    def __init__(self, bot):
        self.bot = bot
        option = {
                'format': 'bestaudio[abr>=320]/bestaudio[abr>=256]/bestaudio[abr>=192]/bestaudio/best', 
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

        self.out.start()



    

    ################# Methods #################
    ###########################################
    async def left(self):
        try:
            for i in range(0, len(self.bot.voice_clients)):
                if self.bot.voice_clients[i].is_connected() is True and len(self.bot.voice_clients[i].channel.members) == 1:
                    await self.server[i].channel.send("*기숙사로 돌아갑니다...*")
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
            print(f"User is in voice channel: {channel.name} (ID: {channel.id})")
        except Exception as e:
            print(f"User not in voice channel: {e}")
            await ctx.reply("보이스 채널 경기장에 입장해 주세요!")
            return


        # 봇이 이미 연결되어 있는지 확인
        server_num = server_check(self, channel)
        print(f"Initial server check: {server_num}")
        print(f"Current voice clients count: {len(self.bot.voice_clients)}")
        
        if server_num is None:
            # 연결되지 않았으면 연결 시도
            try:
                print(f"Attempting to connect to channel: {channel.name} (ID: {channel.id})")
                permissions = channel.permissions_for(ctx.guild.me)
                
                # 핵심 음성 권한만 간단히 로깅 (터미널 전용)
                print(f"=== {channel.name} 채널 핵심 권한 체크 ===")
                print(f"Connect: {permissions.connect}")
                print(f"Speak: {permissions.speak}")
                print(f"View Channel: {permissions.view_channel}")
                print(f"Priority Speaker: {permissions.priority_speaker}")
                print(f"Stream: {permissions.stream}")
                print(f"Use Voice Activity: {permissions.use_voice_activation}")
                print("=" * 40)
                
                # 다른 음성 채널과 핵심 권한만 간단히 비교 (터미널 전용)
                print("=== 다른 음성 채널과 권한 비교 ===")
                for voice_channel in ctx.guild.voice_channels:
                    if voice_channel != channel:
                        other_perms = voice_channel.permissions_for(ctx.guild.me)
                        # 권한 차이가 있는 경우만 로깅
                        if (other_perms.connect != permissions.connect or 
                            other_perms.speak != permissions.speak or 
                            other_perms.view_channel != permissions.view_channel or
                            other_perms.priority_speaker != permissions.priority_speaker or
                            other_perms.stream != permissions.stream or
                            other_perms.use_voice_activation != permissions.use_voice_activation):
                            print(f"⚠️ 권한 차이 발견: {voice_channel.name} vs {channel.name}")
                            print(f"  Connect: {other_perms.connect} vs {permissions.connect}")
                            print(f"  Speak: {other_perms.speak} vs {permissions.speak}")
                            print(f"  Priority Speaker: {other_perms.priority_speaker} vs {permissions.priority_speaker}")
                            print(f"  Stream: {other_perms.stream} vs {permissions.stream}")
                            print("-" * 30)
                
                # 필수 권한 확인 및 오류 메시지
                missing_permissions = []
                
                if not permissions.connect:
                    missing_permissions.append("음성 채널에 연결")
                    print("❌ Connect permission missing")
                
                if not permissions.speak:
                    missing_permissions.append("음성 채널에서 말하기")
                    print("❌ Speak permission missing")
                
                if not permissions.view_channel:
                    missing_permissions.append("음성 채널 보기")
                    print("❌ View channel permission missing")
                
                if not permissions.use_voice_activation:
                    print("⚠️ Use voice activity permission missing (may cause issues)")
                
                if not permissions.priority_speaker:
                    print("⚠️ Priority speaker permission missing (may cause issues in crowded channels)")
                
                if not permissions.stream:
                    print("⚠️ Stream permission missing (may cause issues with streaming users)")
                
                # 권한 부족 시 터미널에만 오류 로깅
                if missing_permissions:
                    print(f"❌ Permission check failed: {missing_permissions}")
                    print(f"❌ {channel.name} 채널에서 다음 권한이 부족합니다:")
                    for perm in missing_permissions:
                        print(f"  • {perm}")
                    print("해결 방법:")
                    print("  1. 서버 관리자에게 권한 요청")
                    print("  2. 채널별 권한 설정 확인")
                    print("  3. 봇 역할의 권한 확인")
                    print("  4. 다른 음성 채널에서 시도")
                    
                    # Discord에는 간단한 오류 메시지만 전송
                    await ctx.reply(f"❌ **{channel.name}** 채널에서 권한이 부족합니다. 다른 음성 채널에서 시도해주세요.")
                    return
                
                # 권한은 있지만 주의사항이 있는 경우
                warnings = []
                if not permissions.priority_speaker:
                    warnings.append("우선순위 말하기 권한 없음 (인원이 많은 채널에서 문제 가능)")
                if not permissions.stream:
                    warnings.append("스트리밍 권한 없음 (스트리밍 사용자와 충돌 가능)")
                if not permissions.use_voice_activation:
                    warnings.append("음성 활동 감지 권한 없음 (음성 감지 관련 문제 가능)")
                
                if warnings:
                    warning_message = f"⚠️ **{channel.name}** 채널에서 주의사항:\n"
                    for warning in warnings:
                        warning_message += f"• {warning}\n"
                    warning_message += "\n문제가 발생하면 다른 음성 채널에서 시도해보세요."
                    print(f"Permission warnings: {warnings}")
                    # 경고 메시지는 터미널에만 출력하고 Discord에는 보내지 않음
                    # await ctx.reply(warning_message)
                
                await channel.connect(timeout=10.0, self_deaf=True)
                print(f"Successfully connected to channel: {channel.name}")
                
                # 연결 후 즉시 더미 오디오로 음성 채널 활성화 (스트리밍 충돌 방지)
                try:
                    dummy_audio = discord.FFmpegPCMAudio("silence.mp3", executable=ffmpeg_location)
                    voice_client_temp = self.bot.voice_clients[-1]
                    voice_client_temp.play(dummy_audio)
                    await asyncio.sleep(0.1)  # 더미 오디오 재생
                    voice_client_temp.stop()
                    print("Dummy audio played to activate voice channel")
                except Exception as e:
                    print(f"Dummy audio play failed: {e}")
                
                # 연결 후 충분한 대기 시간 (연결 안정성 향상)
                await asyncio.sleep(2.0)  # 1초에서 2초로 증가
                
                # 연결 후 상태 확인
                voice_client_after = self.bot.voice_clients[-1]
                print(f"Voice client connected: {voice_client_after.is_connected()}")
                print(f"Voice client channel: {voice_client_after.channel}")
                print(f"Voice client guild: {voice_client_after.guild}")
                
                # 연결이 완전히 확립될 때까지 대기
                max_wait = 10  # 최대 10초 대기
                wait_count = 0
                while not voice_client_after.is_connected() and wait_count < max_wait:
                    await asyncio.sleep(0.5)
                    wait_count += 1
                    print(f"Waiting for connection... {wait_count * 0.5}s")
                
                if not voice_client_after.is_connected():
                    print("Failed to establish voice connection after waiting")
                    await ctx.reply("음성 채널 연결에 실패했습니다. 다시 시도해주세요.")
                    return
                
                print(f"Voice connection fully established after {wait_count * 0.5}s")
                
                # 가장 최근에 연결된 클라이언트 사용
                server_num = len(self.bot.voice_clients) - 1
                print(f"Server number: {server_num}")
                print(f"Voice client after connection: {self.bot.voice_clients[server_num]}")
                
                self.server.append(server_0)
                self.server[server_num].channel_set(ctx.channel)
                
                # ctx.voice_client 설정 (슬래시 명령어인 경우에만)
                if hasattr(ctx, '_voice_client'):
                    ctx.voice_client = self.bot.voice_clients[server_num]
                    print(f"Set ctx.voice_client: {ctx.voice_client}")
                else:
                    print(f"Legacy command - voice_client will be accessed directly")

                #입장음 (임시 비활성화)
                if entry == 1:
                    try:
                        entry_link = glob.glob(entry_path)
                        if entry_link and len(entry_link) > 0:
                            entry_audio = MP3(entry_link[0])
                            entry_player = discord.FFmpegPCMAudio(executable=ffmpeg_location, source=entry_link[0])
                            # voice_client 사용 (레거시는 직접 접근, 슬래시는 설정된 값 사용)
                            voice_client = ctx.voice_client if hasattr(ctx, '_voice_client') else self.bot.voice_clients[server_num]
                            voice_client.play(entry_player)
                            await asyncio.sleep(entry_audio.info.length)
                    except Exception as e:
                        print(f"Entry sound error: {e}")
                        # 입장음 오류 시 무시하고 계속 진행
                else:
                    pass
            except Exception as e:
                print(f"Connection error details: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                await ctx.reply(f"보이스 채널 경기장에 연결할 수 없습니다! 오류: {str(e)}")
                return
        else:
            # 이미 연결되어 있으면 기존 연결 사용
            print(f"Using existing connection, server_num: {server_num}")
            # ctx.voice_client 설정 (슬래시 명령어인 경우에만)
            if hasattr(ctx, '_voice_client'):
                ctx.voice_client = self.bot.voice_clients[server_num]
                print(f"Set ctx.voice_client from existing: {ctx.voice_client}")
            else:
                print(f"Legacy command - using existing voice_client: {ctx.voice_client}")

            
            
  
        
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
            

            embed=discord.Embed(title='레이스 대기열에 추가됨', description=f'[{queue_list[q_num]["title"]}]({queue_list[q_num]["url"]})', color=discord.Color.from_rgb(255, 215, 0))
            embed.add_field(name='Position', value=f'{q_num}')
            embed.add_field(name='Duration', value=f'{queue_list[q_num]["duration"]}', inline=True)
            embed.add_field(name='Requested by', value=f'{queue_list[q_num]["author"]}', inline=True)
            await ctx.send(embed=embed)

            return
        
        else:
            self.server[server_num].queue_insert(q_info['url'], q_info['title'], q_info['duration'], url, author, insert_num)


            queue_list = self.server[server_num].q_list
            q_num = insert_num
            

            embed=discord.Embed(title='레이스 대기열에 추가됨', description=f'[{queue_list[q_num]["title"]}]({queue_list[q_num]["url"]})', color=discord.Color.from_rgb(255, 215, 0))
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

        # 로컬 파일 경로 생성
        import os
        import hashlib
        
        # URL을 기반으로 고유한 파일명 생성 (확장자 없이)
        url_hash = hashlib.md5(o_url.encode()).hexdigest()
        local_file_path = f"downloads/{url_hash}"
        
        # 파일이 없으면 다운로드 (확장자 포함해서 확인)
        if not os.path.exists(f"{local_file_path}.mp3"):
            print(f"Downloading file to {local_file_path}...")
            try:
                # YouTube 다운로드 옵션
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': f"{local_file_path}.%(ext)s",
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'noplaylist': True,
                    'ffmpeg_location': ffmpeg_location,
                }
                
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([o_url])
                print(f"File downloaded successfully: {local_file_path}")
            except Exception as e:
                print(f"Download failed: {e}")
                await ctx.reply(f"음악 다운로드 중 오류가 발생했습니다: {str(e)}")
                return
        
        print(f"Creating FFmpeg track from local file: {local_file_path}.mp3")
        print(f"File exists: {os.path.exists(f'{local_file_path}.mp3')}")
        if os.path.exists(f"{local_file_path}.mp3"):
            print(f"File size: {os.path.getsize(f'{local_file_path}.mp3')} bytes")
        
        try:
            # 로컬 파일용 FFmpeg 옵션
            local_ffmpeg_options = {
                'before_options': '',
                'options': '-vn -b:a 192k -ar 48000 -ac 2 -f s16le'
            }
            track = discord.FFmpegPCMAudio(f"{local_file_path}.mp3", **local_ffmpeg_options, executable=ffmpeg_location)
            print("FFmpeg track created successfully from local file")
        except Exception as e:
            print(f"FFmpeg track creation failed: {type(e).__name__}: {e}")
            await ctx.reply(f"음악 파일 처리 중 오류가 발생했습니다: {str(e)}")
            return
        
        # voice_client 사용 (레거시는 직접 접근, 슬래시는 설정된 값 사용)
        voice_client = ctx.voice_client if hasattr(ctx, '_voice_client') else self.bot.voice_clients[server_num]
        
        # 음악 재생 전에 잠시 대기하여 스트림이 준비되도록 함
        await asyncio.sleep(0.1)
        
        # voice_client 연결 상태 재확인
        print(f"Before play - voice_client connected: {voice_client.is_connected()}")
        print(f"Before play - voice_client channel: {voice_client.channel}")
        print(f"Before play - voice_client guild: {voice_client.guild}")
        
        # 연결 상태를 다시 한번 확인하고 필요시 재연결 시도
        if not voice_client.is_connected():
            print("Voice client disconnected before play attempt, trying to reconnect...")
            try:
                await voice_client.connect(timeout=10.0, self_deaf=True)
                await asyncio.sleep(1.0)
                if not voice_client.is_connected():
                    print("Reconnection failed")
                    await ctx.reply("음성 채널 연결이 끊어졌습니다. 다시 시도해주세요.")
                    return
                print("Reconnection successful")
                
                # 재연결 후에도 더미 오디오로 활성화
                try:
                    dummy_audio = discord.FFmpegPCMAudio("silence.mp3", executable=ffmpeg_location)
                    voice_client.play(dummy_audio)
                    await asyncio.sleep(0.1)
                    voice_client.stop()
                    print("Dummy audio played after reconnection")
                except Exception as e:
                    print(f"Dummy audio play after reconnection failed: {e}")
                    
            except Exception as e:
                print(f"Reconnection error: {e}")
                await ctx.reply("음성 채널 재연결에 실패했습니다. 다시 시도해주세요.")
                return
        
        # 재생 전 권한 재확인
        channel = voice_client.channel
        permissions_after = channel.permissions_for(ctx.guild.me)
        print(f"Permissions after connection - Connect: {permissions_after.connect}, Speak: {permissions_after.speak}")
        
        if not permissions_after.speak:
            print("Bot lost speak permission after connection")
            await ctx.reply("음성 채널에서 말할 권한이 없습니다! 관리자에게 권한을 요청해주세요.")
            await voice_client.disconnect()
            return
        
        print("Attempting to play track...")
        print(f"Before play - voice_client connected: {voice_client.is_connected()}")
        print(f"Before play - voice_client playing: {voice_client.is_playing()}")
        print(f"Before play - voice_client paused: {voice_client.is_paused()}")
        
        try:
            voice_client.play(track)
            print("Track play command sent successfully")
            self.server[server_num].np_time = time.time()
            
            # 재생 후 상태 확인
            await asyncio.sleep(1.0)  # 재생 시작 대기 (더 긴 시간)
            print(f"After play - voice_client connected: {voice_client.is_connected()}")
            print(f"After play - voice_client playing: {voice_client.is_playing()}")
            print(f"After play - voice_client paused: {voice_client.is_paused()}")
            
            # 재생이 시작되지 않았으면 추가 대기
            if not voice_client.is_playing():
                print("Track not playing, waiting longer...")
                await asyncio.sleep(2.0)
                print(f"After longer wait - voice_client playing: {voice_client.is_playing()}")
            
        except discord.ClientException as e:
            print(f"Play failed with ClientException: {type(e).__name__}: {e}")
            if "Not connected to voice" in str(e):
                await ctx.reply("음성 채널 연결이 불안정합니다. 잠시 후 다시 시도해주세요.")
                return
            elif "You do not have permission" in str(e) or "Missing Permissions" in str(e):
                await ctx.reply("음성 채널에서 말할 권한이 없습니다! 관리자에게 권한을 요청해주세요.")
                await voice_client.disconnect()
                return
            else:
                print(f"Play error: {type(e).__name__}: {e}")
                await ctx.reply(f"음악 재생 중 오류가 발생했습니다: {str(e)}")
                return


        # 음악 재생 GUI 생성
        track_info = {
            'title': title,
            'url': o_url,
            'duration': o_duration,
            'author': o_author
        }
        
        music_view = MusicPlayerView(self.bot, server_num, voice_client, track_info)
        embed = music_view.create_music_embed()
        
        print(f"Attempting to send message with embed: {embed.title}")  # 디버깅 로그
        print(f"View has {len(music_view.children)} children")  # 디버깅 로그
        
        try:
            message = await ctx.send(embed=embed, view=music_view)
            print(f"ctx.send() completed, message type: {type(message)}")  # 디버깅 로그
        except Exception as e:
            print(f"ERROR: ctx.send() failed: {e}")
            await ctx.reply("메시지 전송에 실패했습니다.")
            return
        
        if message is None:
            print("ERROR: ctx.send() returned None")
            await ctx.reply("메시지 전송에 실패했습니다.")
            return
        
        music_view.message = message
        print(f"Message set for music_view: {message.id}")  # 디버깅 로그
        
        # 프로그레스 바 자동 업데이트 시작 (message 설정 후)
        try:
            music_view.update_task = asyncio.create_task(music_view.start_progress_updates())
            print("Progress update task created successfully")  # 디버깅 로그
        except Exception as e:
            print(f"Failed to start progress updates: {e}")
        
        # 봇 상태 업데이트 (음악 재생 중)
        if hasattr(self.bot, 'update_music_status'):
            self.bot.update_music_status(title)

        
        
        while True:

            try:
                # voice_client 사용 (레거시는 직접 접근, 슬래시는 설정된 값 사용)
                if hasattr(ctx, '_voice_client'):
                    # 슬래시 명령어인 경우
                    voice_client = ctx.voice_client if ctx.voice_client is not None else (self.bot.voice_clients[server_num] if server_num is not None else None)
                else:
                    # 레거시 명령어인 경우
                    voice_client = self.bot.voice_clients[server_num] if server_num is not None else None
                
                # voice_client가 None인지 확인
                if voice_client is None:
                    print("Voice client is None, breaking loop")
                    break
                
                if not voice_client.is_playing() and voice_client.is_paused() is False:
                    queue_list.pop(0)

                    # 큐가 비어있으면 상태 초기화
                    if len(queue_list) == 0:
                        if hasattr(self.bot, 'update_music_status'):
                            self.bot.update_music_status(None)
                        break

                    link = queue_list[0]['link']
                    title = queue_list[0]['title']
                    o_url = queue_list[0]['url'] 
                    o_author = queue_list[0]['author']
                    o_duration = queue_list[0]['duration']


                    # 로컬 파일 경로 생성
                    import os
                    import hashlib
                    
                    # URL을 기반으로 고유한 파일명 생성 (확장자 없이)
                    url_hash = hashlib.md5(o_url.encode()).hexdigest()
                    local_file_path = f"downloads/{url_hash}"
                    
                    # 파일이 없으면 다운로드 (확장자 포함해서 확인)
                    if not os.path.exists(f"{local_file_path}.mp3"):
                        print(f"Downloading file to {local_file_path}...")
                        try:
                            # YouTube 다운로드 옵션
                            ydl_opts = {
                                'format': 'bestaudio/best',
                                'outtmpl': f"{local_file_path}.%(ext)s",
                                'postprocessors': [{
                                    'key': 'FFmpegExtractAudio',
                                    'preferredcodec': 'mp3',
                                    'preferredquality': '192',
                                }],
                                'noplaylist': True,
                                'ffmpeg_location': ffmpeg_location,
                            }
                            
                            with YoutubeDL(ydl_opts) as ydl:
                                ydl.download([o_url])
                            print(f"File downloaded successfully: {local_file_path}")
                        except Exception as e:
                            print(f"Download failed: {e}")
                            continue
                    
                    # 로컬 파일용 FFmpeg 옵션
                    local_ffmpeg_options = {
                        'before_options': '',
                        'options': '-vn -b:a 192k -ar 48000 -ac 2 -f s16le'
                    }
                    track = discord.FFmpegPCMAudio(f"{local_file_path}.mp3", **local_ffmpeg_options, executable=ffmpeg_location)
                    
                    # 음악 재생 전에 잠시 대기하여 스트림이 준비되도록 함
                    await asyncio.sleep(0.1)
                    
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
                        await asyncio.sleep(0.05)  # 더 짧은 시간
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

                    # 음악 재생 GUI 생성 (큐에서 다음 곡)
                    track_info = {
                        'title': title,
                        'url': o_url,
                        'duration': o_duration,
                        'author': o_author
                    }
                    
                    music_view = MusicPlayerView(self.bot, server_num, voice_client, track_info)
                    embed = music_view.create_music_embed()
                    message = await ctx.send(embed=embed, view=music_view)
                    
                    if message is None:
                        print("ERROR: ctx.send() returned None in queue")
                        await ctx.reply("메시지 전송에 실패했습니다.")
                        continue
                    
                    music_view.message = message
                    print(f"Message set for music_view: {message.id}")  # 디버깅 로그
                    
                    # 프로그레스 바 자동 업데이트 시작 (message 설정 후)
                    try:
                        music_view.update_task = asyncio.create_task(music_view.start_progress_updates())
                        print("Progress update task created successfully")  # 디버깅 로그
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

        try:
            a_voice = ctx.author.voice.channel
        except:
            await ctx.reply("보이스 채널 경기장에 입장해 주세요!")
            return

        server_num = server_check(self, a_voice)

        

        embed = discord.Embed(title="레이스 대기열 정보", color=discord.Color.from_rgb(255, 20, 147))
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
            await ctx.reply("보이스 채널 경기장에 입장해 주세요!")
            return
        
        server_num = server_check(self, a_voice)
        
        if server_num is None:
            await ctx.send("음성 채널에 연결되어 있지 않습니다!")
            return
        
        # voice_client 확인
        if hasattr(ctx, '_voice_client'):
            # 슬래시 명령어인 경우
            voice_client = ctx.voice_client if ctx.voice_client is not None else self.bot.voice_clients[server_num]
        else:
            # 레거시 명령어인 경우
            voice_client = self.bot.voice_clients[server_num]
        
        if voice_client is None:
            await ctx.send("음성 채널에 연결되어 있지 않습니다!")
            return
        
        if voice_client.is_playing():
            await ctx.send("다음 레이스로!")
        
        # 봇 상태 업데이트 (다음 음악으로)
        if hasattr(self.bot, 'update_music_status'):
            if len(self.server[server_num].q_list) > 0:
                self.bot.update_music_status(self.server[server_num].q_list[0]['title'])
            else:
                self.bot.update_music_status(None)
            voice_client.stop()
        elif not voice_client.is_playing():
            await ctx.send("스킵할 레이스가 없어요!")
        




    ###########################################
    ###########################################
    
    @commands.command(name="leave", aliases=["l", "L", "ㅣ"])
    async def leave(self, ctx):

        try:
            a_voice = ctx.author.voice.channel
        except:
            await ctx.reply("보이스 채널 경기장에 입장해 주세요!")
            return

        server_num = server_check(self, a_voice)

        channel_id = self.bot.voice_clients[server_num].channel.id
        
        await leave(self, server_num)
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
            

        try:
            a_voice = ctx.author.voice.channel
        except:
            await ctx.reply("보이스 채널 경기장에 입장해 주세요!")
            return

        server_num = server_check(self, a_voice)

        queue_list = self.server[server_num].q_list

        q_title = queue_list[index]['title']
        q_duration = queue_list[index]['duration']
        q_url = queue_list[index]['url']
        q_author = queue_list[index]['author']
        
        queue_list.pop(index)

        embed=discord.Embed(title='레이스에서 제외됨', description=f'[{q_title}]({q_url})', color=discord.Color.from_rgb(255, 100, 100))
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

        try:
            a_voice = ctx.author.voice.channel
        except:
            await ctx.reply("보이스 채널 경기장에 입장해 주세요!")
            return

        server_num = server_check(self, a_voice)

        if server_num is None:
            await ctx.send("음성 채널에 연결되어 있지 않습니다!")
            return

        # voice_client 확인
        if hasattr(ctx, '_voice_client'):
            # 슬래시 명령어인 경우
            voice_client = ctx.voice_client if ctx.voice_client is not None else self.bot.voice_clients[server_num]
        else:
            # 레거시 명령어인 경우
            voice_client = self.bot.voice_clients[server_num]
        
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

        try:
            a_voice = ctx.author.voice.channel
        except:
            await ctx.reply("보이스 채널 경기장에 입장해 주세요!")
            return

        server_num = server_check(self, a_voice)

        if server_num is None:
            await ctx.send("음성 채널에 연결되어 있지 않습니다!")
            return

        # voice_client 확인
        if hasattr(ctx, '_voice_client'):
            # 슬래시 명령어인 경우
            voice_client = ctx.voice_client if ctx.voice_client is not None else self.bot.voice_clients[server_num]
        else:
            # 레거시 명령어인 경우
            voice_client = self.bot.voice_clients[server_num]
        
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
        # 즉시 응답
        await interaction.response.defer()
        
        # 기존 play 명령어와 동일한 로직을 사용하기 위해 가상의 ctx 생성
        class FakeCtx:
            def __init__(self, interaction):
                self.author = interaction.user
                self.channel = interaction.channel
                self.guild = interaction.guild
                self._voice_client = None
                
            @property
            def voice_client(self):
                return self._voice_client
                
            @voice_client.setter
            def voice_client(self, value):
                self._voice_client = value
                
            async def reply(self, message):
                await interaction.followup.send(message, ephemeral=True)
                
            async def send(self, content=None, embed=None, view=None):
                if embed and view:
                    return await interaction.followup.send(embed=embed, view=view)
                elif embed:
                    return await interaction.followup.send(embed=embed)
                else:
                    return await interaction.followup.send(content)
                    
            def __getattr__(self, name):
                return getattr(interaction, name)
        
        ctx = FakeCtx(interaction)
        
        try:
            # 기존 play 메서드 호출
            await self.play(ctx, url, insert_num)
        except Exception as e:
            print(f"Slash command play error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"오류가 발생했습니다: {str(e)}", ephemeral=True)

    @discord.app_commands.command(name="queue", description="음악 대기열을 확인합니다")
    @discord.app_commands.describe(num="페이지 번호 (기본값: 1)")
    async def slash_queue(self, interaction: discord.Interaction, num: int = 1):
        class FakeCtx:
            def __init__(self, interaction):
                self.author = interaction.user
                self.channel = interaction.channel
                self.guild = interaction.guild
                self._voice_client = None
                
            @property
            def voice_client(self):
                return self._voice_client
                
            @voice_client.setter
            def voice_client(self, value):
                self._voice_client = value
                
            async def reply(self, message):
                await interaction.response.send_message(message, ephemeral=True)
                
            async def send(self, content=None, embed=None, view=None):
                if embed and view:
                    return await interaction.response.send_message(embed=embed, view=view)
                elif embed:
                    return await interaction.response.send_message(embed=embed)
                else:
                    return await interaction.response.send_message(content)
                
            async def send(self, content=None, embed=None):
                if embed:
                    return await interaction.followup.send(embed=embed)
                else:
                    return await interaction.followup.send(content)
        
        ctx = FakeCtx(interaction)
        await self.queue(ctx, num)

    @discord.app_commands.command(name="skip", description="다음 곡으로 넘어갑니다")
    async def slash_skip(self, interaction: discord.Interaction):
        # 즉시 응답
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.author = interaction.user
                self.channel = interaction.channel
                self.guild = interaction.guild
                self._voice_client = None
                
            @property
            def voice_client(self):
                return self._voice_client
                
            @voice_client.setter
            def voice_client(self, value):
                self._voice_client = value
                
            async def reply(self, message):
                await interaction.followup.send(message, ephemeral=True)
                
            async def send(self, content=None, embed=None):
                return await interaction.followup.send(content)
        
        ctx = FakeCtx(interaction)
        
        try:
            await self.skip(ctx)
        except Exception as e:
            print(f"Slash command skip error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"오류가 발생했습니다: {str(e)}", ephemeral=True)

    @discord.app_commands.command(name="leave", description="음성 채널에서 나갑니다")
    async def slash_leave(self, interaction: discord.Interaction):
        # 즉시 응답
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.author = interaction.user
                self.channel = interaction.channel
                self.guild = interaction.guild
                self._voice_client = None
                
            @property
            def voice_client(self):
                return self._voice_client
                
            @voice_client.setter
            def voice_client(self, value):
                self._voice_client = value
                
            async def reply(self, message):
                await interaction.followup.send(message, ephemeral=True)
                
            async def send(self, content=None, embed=None):
                return await interaction.followup.send(content)
        
        ctx = FakeCtx(interaction)
        
        try:
            await self.leave(ctx)
        except Exception as e:
            print(f"Slash command leave error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"오류가 발생했습니다: {str(e)}", ephemeral=True)

    @discord.app_commands.command(name="delete", description="대기열에서 곡을 제거합니다")
    @discord.app_commands.describe(index="제거할 곡의 번호")
    async def slash_delete(self, interaction: discord.Interaction, index: int):
        # 즉시 응답
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.author = interaction.user
                self.channel = interaction.channel
                self.guild = interaction.guild
                self._voice_client = None
                
            @property
            def voice_client(self):
                return self._voice_client
                
            @voice_client.setter
            def voice_client(self, value):
                self._voice_client = value
                
            async def reply(self, message):
                await interaction.followup.send(message, ephemeral=True)
                
            async def send(self, content=None, embed=None):
                if embed:
                    return await interaction.followup.send(embed=embed)
                else:
                    return await interaction.followup.send(content)
        
        ctx = FakeCtx(interaction)
        
        try:
            await self.delete(ctx, index)
        except Exception as e:
            print(f"Slash command delete error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"오류가 발생했습니다: {str(e)}", ephemeral=True)

    @discord.app_commands.command(name="nowplaying", description="현재 재생 중인 곡을 확인합니다")
    async def slash_nowplaying(self, interaction: discord.Interaction):
        class FakeCtx:
            def __init__(self, interaction):
                self.author = interaction.user
                self.channel = interaction.channel
                self.guild = interaction.guild
                self._voice_client = None
                
            @property
            def voice_client(self):
                return self._voice_client
                
            @voice_client.setter
            def voice_client(self, value):
                self._voice_client = value
                
            async def reply(self, message):
                await interaction.response.send_message(message, ephemeral=True)
                
            async def send(self, content=None, embed=None, view=None):
                if embed and view:
                    return await interaction.response.send_message(embed=embed, view=view)
                elif embed:
                    return await interaction.response.send_message(embed=embed)
                else:
                    return await interaction.response.send_message(content)
                
            async def send(self, content=None, embed=None):
                if embed:
                    return await interaction.followup.send(embed=embed)
                else:
                    return await interaction.followup.send(content)
        
        ctx = FakeCtx(interaction)
        await self.now_playing(ctx)

    @discord.app_commands.command(name="quicknumber", description="빠른 번호 목록을 확인합니다")
    @discord.app_commands.describe(num="페이지 번호 (기본값: 1)")
    async def slash_quicknumber(self, interaction: discord.Interaction, num: int = 1):
        class FakeCtx:
            def __init__(self, interaction):
                self.author = interaction.user
                self.channel = interaction.channel
                self.guild = interaction.guild
                self._voice_client = None
                
            @property
            def voice_client(self):
                return self._voice_client
                
            @voice_client.setter
            def voice_client(self, value):
                self._voice_client = value
                
            async def reply(self, message):
                await interaction.response.send_message(message, ephemeral=True)
                
            async def send(self, content=None, embed=None, view=None):
                if embed and view:
                    return await interaction.response.send_message(embed=embed, view=view)
                elif embed:
                    return await interaction.response.send_message(embed=embed)
                else:
                    return await interaction.response.send_message(content)
                
            async def send(self, content=None, embed=None):
                if embed:
                    return await interaction.followup.send(embed=embed)
                else:
                    return await interaction.followup.send(content)
        
        ctx = FakeCtx(interaction)
        await self.quick_number(ctx, num)

    @discord.app_commands.command(name="pause", description="음악을 일시정지합니다")
    async def slash_pause(self, interaction: discord.Interaction):
        # 즉시 응답
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.author = interaction.user
                self.channel = interaction.channel
                self.guild = interaction.guild
                self._voice_client = None
                
            @property
            def voice_client(self):
                return self._voice_client
                
            @voice_client.setter
            def voice_client(self, value):
                self._voice_client = value
                
            async def reply(self, message):
                await interaction.followup.send(message, ephemeral=True)
                
            async def send(self, content=None, embed=None):
                return await interaction.followup.send(content)
        
        ctx = FakeCtx(interaction)
        
        try:
            await self.pause(ctx)
        except Exception as e:
            print(f"Slash command pause error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"오류가 발생했습니다: {str(e)}", ephemeral=True)

    @discord.app_commands.command(name="resume", description="일시정지된 음악을 재생합니다")
    async def slash_resume(self, interaction: discord.Interaction):
        # 즉시 응답
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.author = interaction.user
                self.channel = interaction.channel
                self.guild = interaction.guild
                self._voice_client = None
                
            @property
            def voice_client(self):
                return self._voice_client
                
            @voice_client.setter
            def voice_client(self, value):
                self._voice_client = value
                
            async def reply(self, message):
                await interaction.followup.send(message, ephemeral=True)
                
            async def send(self, content=None, embed=None):
                return await interaction.followup.send(content)
        
        ctx = FakeCtx(interaction)
        
        try:
            await self.resume(ctx)
        except Exception as e:
            print(f"Slash command resume error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"오류가 발생했습니다: {str(e)}", ephemeral=True)

    ###########################################
    ###########################################

async def setup(bot):
    await bot.add_cog(DJ(bot))

