import ast
p = 'electron/src/app.js'
s = open(p, encoding='utf-8').read()
old = "document.querySelectorAll('.page').forEach(p => p.classList.remove('active');\n  document.querySelector('[data-page=\"results\"]').classList.add('active');"
new = "document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));\n  document.querySelector('[data-page=\"results\"]').classList.add('active');"
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
ast.parse(s)
print('fixed')
