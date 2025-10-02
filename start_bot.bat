@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 파루코 봇 시작 중...
echo 현재 디렉토리: %CD%
echo Python 버전 확인 중...
python --version
echo.
echo 봇 시작...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo 오류가 발생했습니다. 오류 코드: %errorlevel%
    echo Python이 설치되어 있는지 확인해주세요.
    echo requirements.txt의 패키지들이 설치되어 있는지 확인해주세요.
)
echo.
pause
