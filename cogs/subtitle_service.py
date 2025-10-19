"""
YouTube 자막 서비스
youtube-transcript-api를 사용하여 자막을 가져옵니다.
"""

import asyncio
import logging
from typing import Optional, Dict, List
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled, 
    NoTranscriptFound, 
    VideoUnavailable
)

logger = logging.getLogger(__name__)

class SubtitleService:
    """YouTube 자막 서비스"""
    
    def __init__(self):
        self.subtitle_cache = {}  # video_id -> subtitle_data
        self.language_priority = ['ko', 'en', 'ja']  # 한글 > 영어 > 일본어
        self.cache_max_size = 50
        
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        URL에서 비디오 ID 추출
        플레이리스트 URL의 경우 첫 번째 비디오 ID만 추출
        """
        try:
            # youtu.be 짧은 URL 형식
            if 'youtu.be/' in url:
                video_id = url.split('youtu.be/')[1].split('?')[0].split('&')[0]
                return video_id
            
            # youtube.com/watch 형식
            elif 'youtube.com/watch' in url:
                # v= 파라미터에서 비디오 ID 추출
                if 'v=' in url:
                    video_id = url.split('v=')[1].split('&')[0]
                    return video_id
            
            # youtube.com/playlist 형식 (플레이리스트 URL)
            # 플레이리스트에서는 비디오 ID를 추출할 수 없으므로 None 반환
            elif 'youtube.com/playlist' in url:
                logger.info(f"[Subtitle] Playlist URL detected, cannot extract single video ID: {url}")
                return None
            
            return None
        except Exception as e:
            logger.warning(f"[Subtitle] Failed to extract video ID from URL: {url}, error: {e}")
            return None
    
    async def get_subtitles_for_video(self, video_url: str, video_title: str) -> Optional[Dict]:
        """
        YouTube 자막을 가져옵니다
        
        Args:
            video_url: YouTube 비디오 URL
            video_title: 비디오 제목
            
        Returns:
            dict: 자막 데이터 또는 None
        """
        video_id = self.extract_video_id(video_url)
        if not video_id:
            logger.warning(f"[Subtitle] Could not extract video ID from URL: {video_url}")
            return None
        
        # 캐시 확인
        if video_id in self.subtitle_cache:
            logger.info(f"[Subtitle] Using cached subtitle for video {video_id}")
            return self.subtitle_cache[video_id]
        
        try:
            # asyncio로 감싸서 비동기 실행
            subtitle_data = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._fetch_subtitles_sync, 
                video_id
            )
            
            if subtitle_data:
                # 캐시에 저장
                self._add_to_cache(video_id, subtitle_data)
                logger.info(f"[Subtitle] Successfully fetched {subtitle_data['language']} subtitle for video {video_id} ({len(subtitle_data['subtitles'])} entries)")
                return subtitle_data
            else:
                logger.info(f"[Subtitle] No suitable subtitle found for video {video_id}")
                return None
                
        except Exception as e:
            logger.warning(f"[Subtitle] Failed to fetch subtitle for video {video_id}: {e}")
            return None
    
    def _fetch_subtitles_sync(self, video_id: str) -> Optional[Dict]:
        """
        동기적으로 자막을 가져옵니다 (executor에서 실행)
        최신 youtube-transcript-api 사용 (v1.2.3+)
        
        Args:
            video_id: YouTube 비디오 ID
            
        Returns:
            dict: 자막 데이터 또는 None
        """
        try:
            ytt_api = YouTubeTranscriptApi()
            
            # 우선순위 언어로 자막 가져오기 시도
            for lang_code in self.language_priority:
                try:
                    # fetch() 메서드로 자막 가져오기 (언어 우선순위 지정)
                    fetched_transcript = ytt_api.fetch(video_id, languages=[lang_code])
                    
                    # FetchedTranscript 객체를 dict 형식으로 변환
                    subtitles = [
                        {
                            'text': snippet.text,
                            'start': snippet.start,
                            'duration': snippet.duration
                        }
                        for snippet in fetched_transcript.snippets
                    ]
                    
                    return {
                        'language': fetched_transcript.language_code,
                        'subtitles': subtitles,
                        'video_id': video_id,
                        'is_generated': fetched_transcript.is_generated
                    }
                    
                except NoTranscriptFound:
                    # 해당 언어의 자막이 없으면 다음 언어 시도
                    continue
            
            # 우선순위 언어가 모두 없으면 기본 언어(영어)로 시도
            try:
                fetched_transcript = ytt_api.fetch(video_id)
                
                subtitles = [
                    {
                        'text': snippet.text,
                        'start': snippet.start,
                        'duration': snippet.duration
                    }
                    for snippet in fetched_transcript.snippets
                ]
                
                logger.info(f"[Subtitle] Fallback to default language: {fetched_transcript.language_code}")
                
                return {
                    'language': fetched_transcript.language_code,
                    'subtitles': subtitles,
                    'video_id': video_id,
                    'is_generated': fetched_transcript.is_generated
                }
                
            except NoTranscriptFound:
                logger.info(f"[Subtitle] No transcript found for video {video_id}")
                return None
            
        except TranscriptsDisabled:
            logger.info(f"[Subtitle] Subtitles are disabled for video {video_id}")
            return None
        except VideoUnavailable:
            logger.warning(f"[Subtitle] Video {video_id} is unavailable")
            return None
        except Exception as e:
            # TooManyRequests나 기타 모든 에러를 여기서 처리
            error_msg = str(e)
            if "too many requests" in error_msg.lower() or "429" in error_msg:
                logger.warning(f"[Subtitle] Too many requests - YouTube is rate limiting: {e}")
            else:
                logger.error(f"[Subtitle] Error fetching subtitle: {e}")
            return None
    
    def _add_to_cache(self, video_id: str, subtitle_data: Dict):
        """캐시에 자막 데이터 추가"""
        if len(self.subtitle_cache) >= self.cache_max_size:
            # 가장 오래된 항목 제거 (FIFO)
            oldest_key = next(iter(self.subtitle_cache))
            del self.subtitle_cache[oldest_key]
        
        self.subtitle_cache[video_id] = subtitle_data
        logger.debug(f"[Subtitle] Added to cache: {video_id}, cache size: {len(self.subtitle_cache)}")
    
    def get_current_subtitle(self, subtitle_data: Dict, current_time: float) -> Optional[str]:
        """
        현재 시간에 해당하는 자막 텍스트를 가져옵니다
        
        Args:
            subtitle_data: 자막 데이터
            current_time: 현재 재생 시간 (초)
            
        Returns:
            str: 자막 텍스트 또는 None
        """
        if not subtitle_data or 'subtitles' not in subtitle_data:
            return None
        
        subtitles = subtitle_data['subtitles']
        
        # 현재 시간에 해당하는 자막 찾기
        for subtitle in subtitles:
            start_time = subtitle['start']
            duration = subtitle['duration']
            end_time = start_time + duration
            
            if start_time <= current_time < end_time:
                return subtitle['text']
        
        return None
    
    def clear_cache(self):
        """캐시 초기화"""
        self.subtitle_cache.clear()
        logger.info("[Subtitle] Cache cleared")

# 전역 인스턴스
subtitle_service = SubtitleService()
