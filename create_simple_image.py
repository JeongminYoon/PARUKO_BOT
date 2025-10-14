import os

def create_simple_default_image():
    """간단한 기본 이미지 생성 (SVG 형식)"""
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="1280" height="720" xmlns="http://www.w3.org/2000/svg">
  <!-- 배경 -->
  <rect width="1280" height="720" fill="#2C2F33"/>
  
  <!-- 중앙 원 -->
  <circle cx="640" cy="300" r="80" fill="none" stroke="#7289DA" stroke-width="8"/>
  
  <!-- 음표 -->
  <text x="640" y="320" text-anchor="middle" font-family="Arial, sans-serif" font-size="60" fill="#7289DA">♪</text>
  
  <!-- 메인 텍스트 -->
  <text x="640" y="450" text-anchor="middle" font-family="Arial, sans-serif" font-size="48" font-weight="bold" fill="#FFFFFF">🎵 PARUKO BOT</text>
  
  <!-- 서브 텍스트 -->
  <text x="640" y="500" text-anchor="middle" font-family="Arial, sans-serif" font-size="32" fill="#FFFFFF">재생 목록이 없어요</text>
  
  <!-- 안내 텍스트 -->
  <text x="640" y="550" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" fill="#99AAB5">!play [URL] 명령어로 음악을 재생하세요</text>
</svg>'''
    
    with open('default_player.svg', 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    print("기본 이미지가 생성되었습니다: default_player.svg")
    print("SVG 파일을 PNG로 변환하려면 온라인 변환기나 이미지 편집 프로그램을 사용하세요.")

if __name__ == "__main__":
    create_simple_default_image()

