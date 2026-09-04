import re
p = 'build_metre.py'
s = open(p, encoding='utf-8').read()
# Add BOLD alias
old = 'ALIGN_LEFT_NOWRAP = Alignment(horizontal="left", wrap_text=False)'
new = 'ALIGN_LEFT_NOWRAP = Alignment(horizontal="left", wrap_text=False)\nBOLD = FONT_DATA_BOLD'
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
import ast; ast.parse(s); print('OK')
