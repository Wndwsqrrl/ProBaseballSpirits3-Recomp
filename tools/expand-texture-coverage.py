"""Add English replacements for shared card, input and home/away labels."""
import json
from pathlib import Path
p=Path(__file__).resolve().parent.parent/'translation/texture-labels.json'
c=json.loads(p.read_text(encoding='utf-8'))
c.setdefault('BBMENU.CHK',{})['MENU_ETC_nblock_deco2.tsr']=[
    dict(rect=[0,0,36,16],text='vs L',padding=2,foreground=[0,0,0,255]),
    dict(rect=[0,16,36,16],text='vs R',padding=2,foreground=[0,0,0,255]),
]
c.setdefault('TMSEL.CHK',{})['MENU_EXtesele.tsr']=[
    dict(rect=[298,16,70,28],text='Away',padding=2,foreground=[68,68,68,255]),
    dict(rect=[370,16,70,28],text='Home',padding=2,foreground=[68,68,68,255]),
]
c.setdefault('SELECT.CHK',{})['MENU_MAT_pw03.tsr']=[
    dict(rect=[0,64,64,24],text='Back',padding=2,outline_width=1),
]
p.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(sum(len(labels) for member in c.values() for labels in member.values()),'texture labels configured.')
