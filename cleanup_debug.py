import re

# DJ.py 파일 읽기
with open('cogs/DJ.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 디버깅 메시지 제거
lines = content.split('\n')
filtered_lines = []

for line in lines:
    if 'print(' in line and any(debug_type in line for debug_type in ['PLAY DEBUG', 'UPDATE DEBUG']):
        continue
    elif 'print(' in line and '=' in line and '*' in line:  # 구분선 제거
        continue
    elif 'print(' in line and ('PLAY FUNCTION CALLED!' in line):
        continue
    else:
        filtered_lines.append(line)

# 파일 쓰기
with open('cogs/DJ.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(filtered_lines))

print('DJ.py 디버깅 메시지 제거 완료')
