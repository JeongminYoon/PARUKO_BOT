import discord
import asyncio
import time
import datetime
import os
from discord.ext import commands
from .Libs import FakeCtx



class MusicUIManager:

    """음악 플레이어 UI를 관리하는 클래스"""

    def __init__(self):

        self.server_uis = {}  # server_num -> MusicPlayerView

        self.server_messages = {}  # server_num -> discord.Message

    

    async def get_or_create_ui(self, bot, server_num, voice_client, track_info, ctx):

        """UI를 가져오거나 새로 생성"""
        print(f"DEBUG: get_or_create_ui called for server {server_num}")
        print(f"DEBUG: track_info = {track_info}")

        # 빈 큐에서 새 음악으로 전환된 경우인지 확인
        was_empty_to_new = False
        if server_num in self.server_uis:
            old_ui = self.server_uis[server_num]
            was_empty_to_new = old_ui.track_info.get('is_empty', False) and not track_info.get('is_empty', False)
            print(f"DEBUG: was_empty_to_new = {was_empty_to_new}")
            print(f"DEBUG: old_ui.track_info = {old_ui.track_info}")
            
            if was_empty_to_new:
                # 빈 큐 상태에서 새로운 음악을 재생하는 경우 - 기존 메시지 삭제 후 새로 생성
                print(f"Empty queue to new music transition detected for server {server_num}")
                
                # 기존 메시지 삭제 (첨부 파일과 응답 상태 정리를 위해)
                if server_num in self.server_messages and self.server_messages[server_num]:
                    try:
                        await self.server_messages[server_num].delete()
                        print(f"Deleted old empty queue message for server {server_num}")
                    except Exception as e:
                        print(f"Failed to delete old message: {e}")
                
                # 기존 UI 정리
                if old_ui.update_task and not old_ui.update_task.done():
                    old_ui.update_task.cancel()
                
                # 기존 UI와 메시지 참조 제거
                del self.server_uis[server_num]
                if server_num in self.server_messages:
                    del self.server_messages[server_num]
            else:
                # 일반적인 UI 업데이트
                ui = self.server_uis[server_num]
                ui.track_info = track_info
                ui.voice_client = voice_client
                ui.start_time = time.time()

                # 메시지가 있으면 업데이트
                if server_num in self.server_messages and self.server_messages[server_num]:
                    try:
                        await ui.update_progress()
                        return ui, self.server_messages[server_num], False  # 일반적인 업데이트
                    except (discord.NotFound, discord.Forbidden):
                        # 메시지가 삭제되었거나 권한이 없으면 새로 생성
                        pass
                else:
                    # 메시지가 없으면 새로 생성
                    pass

        # 새 UI 생성 및 전송

        ui, message = await bot.get_cog('DJ').create_and_send_music_ui(

            bot, server_num, voice_client, track_info, ctx

        )

        

        self.server_uis[server_num] = ui

        self.server_messages[server_num] = message

        

        return ui, message, was_empty_to_new  # 새로 생성된 UI

    

    async def update_ui(self, server_num, track_info):

        """특정 서버의 UI 업데이트"""

        if server_num in self.server_uis:

            ui = self.server_uis[server_num]

            ui.track_info = track_info

            ui.start_time = time.time()

            # 기존 업데이트 태스크가 있으면 중지
            if ui.update_task and not ui.update_task.done():
                ui.update_task.cancel()

            # 새로운 업데이트 태스크 시작
            ui.update_task = asyncio.create_task(ui.start_progress_updates())

            await ui.update_progress()

    

    async def cleanup_ui(self, server_num):

        """특정 서버의 UI 정리"""

        if server_num in self.server_uis:

            ui = self.server_uis[server_num]

            if ui.update_task and not ui.update_task.done():

                ui.update_task.cancel()

            del self.server_uis[server_num]

        

        if server_num in self.server_messages:

            del self.server_messages[server_num]

    

    async def cleanup_all(self):

        """모든 UI 정리"""

        for server_num in list(self.server_uis.keys()):

            await self.cleanup_ui(server_num)

    

    async def bring_ui_to_bottom(self, bot, server_num, ctx):

        """UI를 채팅 맨 아래로 가져오기"""

        if server_num not in self.server_uis:

            return None, None

        

        ui = self.server_uis[server_num]

        voice_client = bot.voice_clients[server_num] if server_num < len(bot.voice_clients) else None

        

        if not voice_client or not ui.track_info:

            return None, None

        

        # 기존 메시지 삭제 (선택사항)

        if server_num in self.server_messages and self.server_messages[server_num]:

            try:

                await self.server_messages[server_num].delete()

            except:

                pass  # 삭제 실패해도 계속 진행

        

        # 새 메시지 전송 (채팅 맨 아래에)

        embed = ui.create_music_embed()

        

        # 빈 큐 상태인지 확인하여 파일 전송

        use_default_image = ui.track_info.get('is_empty', False)

        message = await bot.get_cog('DJ').send_embed_with_view(ctx, embed, ui, use_default_image)

        

        ui.message = message

        self.server_messages[server_num] = message

        

        return ui, message

    

    async def show_empty_queue_ui(self, bot, server_num, ctx):

        """빈 큐 상태의 UI 표시"""

        voice_client = bot.voice_clients[server_num] if server_num < len(bot.voice_clients) else None

        

        # 기존 UI가 있으면 정리
        if server_num in self.server_uis:
            ui = self.server_uis[server_num]
            # 업데이트 태스크 중지
            if ui.update_task and not ui.update_task.done():
                ui.update_task.cancel()
        
        # 기존 메시지 삭제
        if server_num in self.server_messages and self.server_messages[server_num]:
            try:
                await self.server_messages[server_num].delete()
                print(f"Deleted old UI message for server {server_num}")
            except Exception as e:
                print(f"Failed to delete old UI message: {e}")

        # 빈 큐 상태 UI 생성 및 전송
        ui, message = await bot.get_cog('DJ').create_and_send_empty_queue_ui(
            bot, server_num, voice_client, ctx
        )

        self.server_uis[server_num] = ui
        self.server_messages[server_num] = message

        return ui, message



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

        # 빈 큐 상태 확인

        if self.track_info.get('is_empty', False):

            return self.create_empty_queue_embed()

        

        current_time = time.time() - self.start_time

        total_time = self.track_info.get('duration', 0)

        

        # 디버깅 로그

        # current_time이 음수인 경우 보정

        if current_time < 0:

            print("Warning: current_time is negative, correcting...")

            current_time = 0

            self.start_time = time.time()

        

        # total_time이 None인 경우 처리
        if total_time is None:
            total_time = 0

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

        

        # 반복 모드 상태 확인

        repeat_status = ""

        try:

            server_num = None

            for i, voice_client in enumerate(self.bot.voice_clients):

                if voice_client.channel == self.voice_client.channel:

                    server_num = i

                    break

            

            if server_num is not None:

                player_instance = self.bot.get_cog('DJ').server[server_num]

                if hasattr(player_instance, 'repeat_mode') and player_instance.repeat_mode:

                    repeat_status = " | 🔄 반복"

        except:

            pass

        

        embed.add_field(

            name="👤 요청자",

            value=self.track_info.get('author', 'Unknown'),

            inline=True

        )

        

        embed.add_field(

            name="📊 상태",

            value=f"{status_emoji} {status_text}{repeat_status}",

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

        embed.set_footer(text="🎵 PARUKO GUI W.I.P • 실시간 업데이트")

        

        # 타임스탬프 추가

        embed.timestamp = datetime.datetime.now()

        

        return embed

    

    def create_empty_queue_embed(self):

        """빈 큐 상태의 임베드 생성"""

        embed = discord.Embed(

            title="🎵 현재 재생 중",

            color=discord.Color.greyple()  # 회색으로 변경

        )

        

        # 빈 큐 메시지

        embed.add_field(

            name="",

            value="**재생 목록이 없어요**",

            inline=False

        )

        

        # 빈 정보 필드들

        embed.add_field(

            name="👤 요청자",

            value="",

            inline=True

        )

        

        embed.add_field(

            name="📊 상태",

            value="⏹️ 정지",

            inline=True

        )

        

        embed.add_field(

            name="📈 진행률",

            value="0.0%",

            inline=True

        )

        

        # 빈 프로그레스 바

        empty_progress_bar = "▬" * 40

        embed.add_field(

            name="⏱️ 재생 진행",

            value=f"```\n{empty_progress_bar}\n0:00 / 0:00\n```",

            inline=False

        )

        

        # 기본 이미지를 메인 이미지로 설정 (캐릭터 이미지) - 맨 아래에 배치
        if os.path.exists("default_player.png"):
            embed.set_image(url="attachment://default_player.png")
        else:
            # 기본 이미지가 없을 때만 텍스트 추가
            embed.add_field(
                name="",
                value="🎵 음악을 재생하려면 `!play [URL]` 명령어를 사용하세요!",
                inline=False
            )

        # 푸터 정보
        embed.set_footer(text="🎵 PARUKO GUI W.I.P • 대기 중")

        

        # 타임스탬프 추가

        embed.timestamp = datetime.datetime.now()

        

        return embed

    

    async def update_progress(self):

        """프로그레스 바 업데이트"""

        if not self.message:

            return

        if self.is_updating:

            return

            

        try:

            self.is_updating = True

            embed = self.create_music_embed()

            await self.message.edit(embed=embed, view=self)

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

        # 빈 큐 상태면 업데이트 중지

        if self.track_info.get('is_empty', False):

            print("is_finished: Empty queue state")

            return True

            

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

        """음악을 특정 위치로 이동 (스트리밍 방식)"""

        try:

            if not self.voice_client or not self.voice_client.is_playing():

                print("Cannot seek: voice client not playing")

                return

            

            # 현재 재생 중인 음악 정보 가져오기

            original_url = self.track_info.get('url', '')

            if not original_url:

                print("Cannot seek: no URL available")

                return

            

            print(f"Debug - Original URL: {original_url}")

            

            # URL에서 직접 오디오 URL 추출 (테스트 명령어와 동일한 방식)

            from yt_dlp import YoutubeDL

            ydl_opts = {

                'format': 'bestaudio/best',

                'noplaylist': True,

                'skip_download': True,

            }

            

            try:

                with YoutubeDL(ydl_opts) as ydl:

                    info = ydl.extract_info(original_url, download=False)

                    url = info.get('url')

                    print(f"Debug - Extracted audio URL: {url}")

            except Exception as e:

                print(f"Debug - Failed to extract audio URL: {e}")

                url = original_url  # 실패 시 원본 URL 사용

            

            # seeking 플래그 설정

            self._seeking = True

            

            print(f"Seeking to {position_seconds} seconds...")

            

            # 새 트랙 생성 (seek 기능 포함)

            seek_track = self.bot.get_cog('DJ').create_ffmpeg_track(url, position_seconds)

            

            # 기존 트랙 중지 후 새 트랙 재생 (테스트 방식)

            print("Debug - Stopping current track...")

            self.voice_client.stop()

            print("Debug - Waiting for stop to complete...")

            await asyncio.sleep(1)  # 1초 대기 (테스트와 동일)

            print("Debug - Stop completed, starting new track...")

            

            # np_time 설정 (재생 시작 시간 기록)

            if hasattr(self, 'server') and hasattr(self, 'server_num'):

                self.server[self.server_num].np_time = time.time()

                print(f"Debug - np_time set to: {self.server[self.server_num].np_time}")

            

            # GUI의 start_time 설정 (seek된 위치에서 시작하도록)

            self.start_time = time.time() - position_seconds

            print(f"Debug - GUI start_time set to: {self.start_time} (for position {position_seconds}s)")

            

            # 재생 전 상태 확인

            print(f"Debug - Before play - connected: {self.voice_client.is_connected()}")

            print(f"Debug - Before play - playing: {self.voice_client.is_playing()}")

            print(f"Debug - Before play - paused: {self.voice_client.is_paused()}")

            

            self.voice_client.play(seek_track, after=lambda e: print(f"Seek track ended: {e}"))

            

            # 재생 후 상태 확인

            await asyncio.sleep(0.5)  # 재생 시작 대기

            print(f"Debug - After play - connected: {self.voice_client.is_connected()}")

            print(f"Debug - After play - playing: {self.voice_client.is_playing()}")

            print(f"Debug - After play - paused: {self.voice_client.is_paused()}")

            

            print(f"Seek completed! Playing from {position_seconds} seconds")

            

            # seeking 플래그 해제

            self._seeking = False

            print("Debug - Seeking flag cleared")

            

        except Exception as e:

            print(f"Streaming seek error: {e}")

            import traceback

            traceback.print_exc()

            # seeking 플래그 해제

            self._seeking = False

            # 실패 시 원래 위치에서 계속 재생

            try:

                if self.voice_client and not self.voice_client.is_playing():

                    url = self.track_info.get('url', '')

                    if url:

                        track = self.bot.get_cog('DJ').create_ffmpeg_track(url)

                        self.voice_client.play(track)

                        self.start_time = time.time()

                        print("Recovery: resumed from beginning using streaming")

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

        

        # message가 설정될 때까지 기다림 (더 빠른 확인)

        wait_count = 0

        while not self.message and wait_count < 20:

            print(f"Waiting for message to be set... ({wait_count + 1}/20)")

            await asyncio.sleep(0.1)  # 0.1초마다 확인 (최대 2초)

            wait_count += 1

        

        if not self.message:

            print("ERROR: Message was not set after 2 seconds, stopping updates")

            return

        

        update_count = 0

        try:

            while not self.is_finished():

                if self.voice_client and (self.voice_client.is_playing() or self.voice_client.is_paused()):

                    update_count += 1

                    await self.update_progress()

                await asyncio.sleep(1)  # 1초마다 업데이트

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

    

    @discord.ui.button(label="🔄 반복", style=discord.ButtonStyle.secondary, row=1)

    async def repeat_toggle(self, interaction, button):

        """반복 재생 토글"""

        try:

            # 서버 번호 찾기

            server_num = None

            for i, voice_client in enumerate(self.bot.voice_clients):

                if voice_client.channel == interaction.user.voice.channel:

                    server_num = i

                    break

            

            if server_num is None:

                await interaction.response.send_message("❌ 봇이 음성 채널에 연결되어 있지 않습니다!", ephemeral=True)

                return

            

            # 반복 모드 토글

            player_instance = self.bot.get_cog('DJ').server[server_num]

            player_instance.repeat_mode = not player_instance.repeat_mode

            

            if player_instance.repeat_mode:

                button.label = "🔄 반복 ON"

                button.style = discord.ButtonStyle.success

                await interaction.response.send_message("🔄 반복 재생이 활성화되었습니다.", ephemeral=True)

            else:

                button.label = "🔄 반복"

                button.style = discord.ButtonStyle.secondary

                await interaction.response.send_message("🔄 반복 재생이 비활성화되었습니다.", ephemeral=True)

                

        except Exception as e:

            print(f"Repeat toggle error: {e}")

            import traceback

            traceback.print_exc()

            if not interaction.response.is_done():

                await interaction.response.send_message("❌ 반복 모드 설정 중 오류가 발생했습니다.", ephemeral=True)

    

    @discord.ui.button(label="📋 큐", style=discord.ButtonStyle.secondary, row=1)

    async def show_queue(self, interaction, button):

        """대기열 표시"""

        try:

            # 서버 번호 찾기

            server_num = None

            for i, voice_client in enumerate(self.bot.voice_clients):

                if voice_client.channel == interaction.user.voice.channel:

                    server_num = i

                    break

            

            if server_num is None:

                await interaction.response.send_message("❌ 봇이 음성 채널에 연결되어 있지 않습니다!", ephemeral=True)

                return

            

            # 대기열 정보 가져오기

            queue_list = self.bot.get_cog('DJ').server[server_num].q_list

            

            if len(queue_list) == 0:

                embed = discord.Embed(

                    title="📋 대기열 정보",

                    description="대기열이 비어있습니다.",

                    color=discord.Color.blue()

                )

            else:

                embed = discord.Embed(

                    title="📋 대기열 정보",

                    color=discord.Color.blue()

                )

                

                # 현재 재생 중인 곡과 대기 중인 곡들 표시

                queue_text = ""

                total_duration = datetime.timedelta(seconds=0)

                

                for i, track in enumerate(queue_list):

                    title = track['title']

                    duration = track['duration']

                    author = track['author']

                    url = track['url']

                    

                    total_duration += duration

                    

                    if i == 0:

                        # 현재 재생 중인 곡

                        queue_text += f"🎵 **{i+1}. [{title}]({url})** | {duration} | {author}\n"

                    else:

                        # 대기 중인 곡들

                        queue_text += f"{i+1}. [{title}]({url}) | {duration} | {author}\n"

                    

                    # 임베드 필드 길이 제한 (2000자)

                    if len(queue_text) > 1800:

                        queue_text += f"\n... 및 {len(queue_list) - i - 1}곡 더"

                        break

                

                embed.add_field(

                    name=f"총 {len(queue_list)}곡 | 총 재생시간: {total_duration}",

                    value=queue_text or "대기열이 비어있습니다.",

                    inline=False

                )

            

            await interaction.response.send_message(embed=embed, ephemeral=True)

            

        except Exception as e:

            print(f"Show queue error: {e}")

            import traceback

            traceback.print_exc()

            if not interaction.response.is_done():

                await interaction.response.send_message("❌ 대기열 정보를 가져오는 중 오류가 발생했습니다.", ephemeral=True)

    

    @discord.ui.button(label="ℹ️ 정보", style=discord.ButtonStyle.secondary, row=1)

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

    

    @discord.ui.button(label="⬇️ GUI 아래로", style=discord.ButtonStyle.secondary, row=2)

    async def move_gui_down(self, interaction, button):

        """GUI를 채팅 맨 아래로 이동"""

        try:

            # 서버 번호 찾기

            server_num = None

            for i, voice_client in enumerate(self.bot.voice_clients):

                if voice_client.channel == interaction.user.voice.channel:

                    server_num = i

                    break

            

            if server_num is None:

                await interaction.response.send_message("❌ 봇이 음성 채널에 연결되어 있지 않습니다!", ephemeral=True)

                return

            

            # UI 관리자 가져오기

            ui_manager = self.bot.get_cog('DJ').ui_manager

            

            # UI가 존재하는지 확인

            if server_num not in ui_manager.server_uis:

                await interaction.response.send_message("❌ 현재 재생 중인 음악이 없습니다!", ephemeral=True)

                return

            

            # FakeCtx 생성 (기존 bring_ui_to_bottom 메서드 사용)

            ctx = FakeCtx(interaction)

            

            # 즉시 응답 (3초 제한 해결)

            await interaction.response.send_message("⏳ GUI를 이동하는 중...", ephemeral=True, delete_after=1)

            

            # UI를 채팅 맨 아래로 가져오기

            ui, message = await ui_manager.bring_ui_to_bottom(self.bot, server_num, ctx)

            

            if ui and message:

                # followup으로 성공 메시지 전송

                await interaction.followup.send("✅ GUI를 채팅 맨 아래로 이동했습니다!", ephemeral=True)

            else:

                # followup으로 오류 메시지 전송

                await interaction.followup.send("❌ GUI 이동 중 오류가 발생했습니다!", ephemeral=True)

                

        except Exception as e:

            print(f"Move GUI down error: {e}")

            import traceback

            traceback.print_exc()

            try:

                if not interaction.response.is_done():

                    await interaction.response.send_message("❌ 오류가 발생했습니다!", ephemeral=True)

                else:

                    await interaction.followup.send("❌ 오류가 발생했습니다!", ephemeral=True)

            except Exception as followup_error:

                print(f"Followup error: {followup_error}")

                # 최후의 수단: 채널에 직접 전송

                try:

                    await interaction.channel.send("❌ GUI 이동 중 오류가 발생했습니다!")

                except:

                    print("Failed to send error message to channel")

async def setup(bot):
    """GUI 모듈을 위한 setup 함수 (Cog가 아니므로 빈 함수)"""
    pass

