"""Check reviewed settings wrapping with approximate Arial pixel budgets."""
import argparse
import json
import re
from pathlib import Path
from PIL import ImageFont


def visible(text):
    text=re.sub(r'\\(?:c[0-9a-fA-F]|C[0-9a-fA-F]{6})','',text)
    text=re.sub(r'<BR\s*/?>','\n',text,flags=re.I)
    text=re.sub(r'<RGB[^>]*>','',text)
    # Reserve a full character cell for each native button icon.
    return re.sub(r'<[^>]*>','M',text)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('review',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--font',type=Path,default=Path('C:/Windows/Fonts/arial.ttf'))
    parser.add_argument('--font-size',type=int,default=16)
    parser.add_argument('--width',type=int,default=360)
    parser.add_argument('--lines',type=int,default=7)
    args=parser.parse_args()
    font=ImageFont.truetype(str(args.font),args.font_size)
    rows=json.loads(args.review.read_text(encoding='utf-8'))['overrides']
    failures=[];widest=0;most_lines=0
    for address,text in rows.items():
        lines=visible(text).splitlines()
        width=max((sum(font.getlength(c) for c in line) for line in lines),default=0)
        widest=max(widest,width);most_lines=max(most_lines,len(lines))
        if width>args.width or len(lines)>args.lines:
            failures.append(dict(address=address,width=round(width,2),lines=len(lines)))
    result=dict(checked_entries=len(rows),font='Arial',font_size=args.font_size,
                width_budget=args.width,line_budget=args.lines,
                widest_line=round(widest,2),maximum_lines=most_lines,
                failures=failures,
                scope='Offline estimate for reviewed settings help only. Actual game rectangles, native scaling, and placement still require visual testing.')
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f'{len(rows)} settings entries: widest {widest:.1f}px; at most {most_lines} lines; {len(failures)} budget failures.')
    if failures:raise SystemExit(1)


if __name__=='__main__':
    main()
