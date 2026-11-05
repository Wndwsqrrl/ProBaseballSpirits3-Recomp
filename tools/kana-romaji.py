"""Small deterministic Hepburn transliterator for kana readings from NAMEDIC."""
BASE={}
for kana,roman in [
    ('ぁあぃいぅうぇえぉお','a a i i u u e e o o'),
    ('かがきぎくぐけげこご','ka ga ki gi ku gu ke ge ko go'),
    ('さざしじすずせぜそぞ','sa za shi ji su zu se ze so zo'),
    ('ただちぢっつづてでとど','ta da chi ji * tsu zu te de to do'),
    ('なにぬねの','na ni nu ne no'),
    ('はばぱひびぴふぶぷへべぺほぼぽ','ha ba pa hi bi pi fu bu pu he be pe ho bo po'),
    ('まみむめも','ma mi mu me mo'),('ゃやゅゆょよ','ya ya yu yu yo yo'),
    ('らりるれろ','ra ri ru re ro'),('ゎわゐゑをん','wa wa i e o n')]:
    BASE.update(zip(kana,roman.split()))

def romanize(text):
    text=''.join(chr(ord(c)-0x60) if '\u30a1'<=c<='\u30f6' else c for c in text)
    syllables=[];at=0;double=False
    while at<len(text):
        c=text[at];at+=1
        if c=='っ':double=True;continue
        if c=='ー':continue
        value=BASE.get(c)
        if value is None:return None
        if at<len(text) and text[at] in 'ゃゅょ' and value.endswith('i'):
            tail={'ゃ':'a','ゅ':'u','ょ':'o'}[text[at]];at+=1
            value=(value[:-1] if value in ('shi','chi','ji') else value[:-1]+'y')+tail
        if at<len(text) and text[at] in 'ぁぃぅぇぉ' and len(value)>1:
            value=value[:-1]+BASE[text[at]];at+=1
        if double:
            value=('t' if value.startswith('ch') else value[0])+value;double=False
        # Standard ASCII name spellings omit a macron/extra vowel in ou/uu.
        if syllables and ((value=='u' and syllables[-1].endswith(('o','u'))) or
                          (value=='o' and syllables[-1].endswith('o'))):continue
        syllables.append(value)
    return ''.join(syllables).capitalize()
