# 🎵 파루코 봇 (PARUKO BOT)

![Image](https://github.com/user-attachments/assets/39feb63c-aa60-451d-aae9-5449f1e4802b)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11.6-blue?style=for-the-badge&logo=python&logoColor=white)
![Discord.py](https://img.shields.io/badge/Discord.py-2.3.2-7289da?style=for-the-badge&logo=discord&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Discord 음성 채널용 음악 봇**

*팔코! 절대적 센터 노리겠습니다!*

<sub>Forked from [skyeye1357/YO_Kan-Bot](https://github.com/skyeye1357/YO_Kan-Bot)</sub>

</div>

---

## 📋 목차

- [✨ 주요 기능](#-주요-기능)
- [🛠️ 설치 방법](#️-설치-방법)
- [📦 사용된 라이브러리](#-사용된-라이브러리)
- [🎮 명령어 목록](#-명령어-목록)
- [⚙️ 설정 방법](#️-설정-방법)
- [🚀 실행 방법](#-실행-방법)

---

## ✨ 주요 기능

- 🎵 **YouTube 음악 재생**: YouTube 링크로 음악 재생
- 🎶 **재생 목록 관리**: 큐 시스템으로 여러 음악 관리
- 🔔 **파루코 호출**: 지정된 음성 채널로 벨소리 전송
- 📊 **실시간 상태**: 현재 재생 중인 음악 정보 표시

---

## 🛠️ 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/PARUKO_BOT.git
cd PARUKO_BOT
```

### 2. Python 환경 설정
- **Python 3.11.6** 이상 필요
- 가상환경 생성 (권장):
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. FFmpeg 설치
**⚠️ 중요**: FFmpeg 실행 파일이 필요합니다!

#### Windows:
1. [FFmpeg 공식 사이트](https://ffmpeg.org/download.html)에서 다운로드
2. `ffmpeg/bin/` 폴더에 다음 파일들을 복사:
   - `ffmpeg.exe`
   - `ffplay.exe` 
   - `ffprobe.exe`

#### Linux/Mac:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### 5. 봇 토큰 설정
1. `token.txt` 파일을 생성후 실제 Discord 봇 토큰을 입력

---

## 📦 사용된 라이브러리

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| **discord.py** | 2.3.2 | Discord API 연동 |
| **aiohttp** | ≥3.8.4 | 비동기 HTTP 클라이언트 |
| **websockets** | ≥11.0.2 | WebSocket 통신 |
| **yt-dlp** | ≥2024.1.1 | YouTube 동영상 다운로드 |
| **mutagen** | ≥1.46.0 | 오디오 메타데이터 처리 |
| **ffmpeg-python** | ≥0.2.0 | FFmpeg Python 래퍼 |
| **requests** | ≥2.28.2 | HTTP 요청 처리 |
| **beautifulsoup4** | ≥4.12.2 | HTML 파싱 |
| **PyNaCl** | ≥1.5.0 | 암호화 라이브러리 |

---

## 🎮 명령어 목록

### 🎵 음악 재생 명령어

| 명령어 | 별칭 | 설명 |
|--------|------|------|
| `!play` | `!p`, `!P`, `!ㅔ` | YouTube 링크 또는 빠른 번호로 음악 재생 |
| `!skip` | `!s`, `!S`, `!ㄴ` | 다음 곡으로 건너뛰기 |
| `!pause` | `!ps`, `!Ps`, `!ㅔㄴ` | 재생 일시정지 |
| `!resume` | `!rs`, `!Rs`, `!ㄱㄴ` | 재생 재개 |
| `!leave` | `!l`, `!L`, `!ㅣ` | 음성 채널에서 퇴장 |

### 📋 재생 목록 관리

| 명령어 | 별칭 | 설명 |
|--------|------|------|
| `!queue` | `!q`, `!Q`, `!ㅂ` | 재생 대기열 확인 |
| `!delete` | `!d`, `!D`, `!ㅇ` | 대기열에서 특정 곡 제거 |
| `!nowplaying` | `!np`, `!Np`, `!NP`, `!ㅞ` | 현재 재생 중인 곡 정보 |

### 🔔 파루코 호출

| 명령어 | 설명 |
|--------|------|
| `!ringing` | 지정된 음성 채널로 벨소리 전송 |

### 📚 도움말

| 명령어 | 설명 |
|--------|------|
| `!help` | 전체 명령어 목록 표시 |

---

## ⚙️ 설정 방법

### 1. Discord 봇 생성
1. [Discord Developer Portal](https://discord.com/developers/applications) 접속
2. "New Application" 클릭하여 새 애플리케이션 생성
3. "Bot" 탭에서 봇 생성
4. "Token" 복사하여 `token.txt`에 저장

### 2. 봇 권한 설정
봇에 다음 권한이 필요합니다:
- ✅ **Send Messages** (메시지 전송)
- ✅ **Connect** (음성 채널 연결)
- ✅ **Speak** (음성 채널에서 말하기)
- ✅ **Use Voice Activity** (음성 활동 사용)

### 3. 오디오 파일 설정
- **입장음**: `mp3/entry/` 폴더에 MP3 파일 추가
- **벨소리**: `mp3/ringing/` 폴더에 MP3 파일 추가

---

## 🚀 실행 방법

### Windows
```bash
# 배치 파일 실행
start_bot.bat

# 또는 직접 실행
python main.py
```

### Linux/Mac
```bash
python main.py
```

---

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

<div align="center">

**🎵 스마트 팔콘과 함께 즐거운 음악 시간을 보내세요! 🎵**

Made with ❤️ by PARUKO BOT Team

</div>