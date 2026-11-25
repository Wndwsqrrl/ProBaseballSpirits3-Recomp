"""Apply the maintained English UI review to the translation curation table."""
import json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
p=root/'translation/curation.json'
config=json.loads(p.read_text(encoding='utf-8'))
review=json.loads((root/'translation/reviewed-ui.json').read_text(encoding='utf-8'))
config['overrides'].update(review)
skills=json.loads((root/'translation/reviewed-abilities.json').read_text(encoding='utf-8'))
config['overrides'].update(skills['descriptions'])
config['word_overrides'].update(skills['labels'])
ability_fragments=json.loads((root/'translation/reviewed-ability-fragments.json').read_text(encoding='utf-8'))
config['word_overrides'].update({row['source']:row['english'] for row in ability_fragments})
headlines=json.loads((root/'translation/reviewed-headlines.json').read_text(encoding='utf-8'))
config['overrides'].update(headlines['overrides'])
config['word_overrides'].update(headlines['patterns'])
settings=json.loads((root/'translation/reviewed-settings.json').read_text(encoding='utf-8'))
config['overrides'].update(settings['overrides'])
config['word_overrides'].update(settings['labels'])
settings_fragments=json.loads((root/'translation/reviewed-settings-fragments.json').read_text(encoding='utf-8'))
config['word_overrides'].update({row['source']:row['english'] for row in settings_fragments})
modes=json.loads((root/'translation/reviewed-modes.json').read_text(encoding='utf-8'))
config['overrides'].update(modes['overrides'])
config['word_overrides'].update(modes['labels'])
management=json.loads((root/'translation/reviewed-management.json').read_text(encoding='utf-8'))
config['overrides'].update(management['overrides'])
config['word_overrides'].update(management['labels'])
names=json.loads((root/'translation/reviewed-player-names.json').read_text(encoding='utf-8'))
config['overrides'].update(names)
graded_labels={'球速安定','打たれ強さ','対ピンチ','クイック','対左打者',
               'ショートバウンド','バントダッシュ','打球反応','ベースカバー',
               '走塁','盗塁','ケガしにくさ','バント','チャンス'}
for source,english in skills['labels'].items():
    for level in range(1,6):
        for digit in (str(level),chr(0xff10+level)):
            key=source+digit
            if source in graded_labels:
                config['word_overrides'][key]=english+' '+str(level)
            elif config['word_overrides'].get(key)==english+' '+str(level):
                config['word_overrides'].pop(key)
additional=config['additional_strings']
for row in management.get('runtime_patterns',[]):
    previous=next((r for r in additional if r.get('address')==row['address'] and r.get('source')==row['source']),None)
    if previous is None:
        additional.append(row)
    else:
        previous.update(row)
if not any(int(r['address'],0)==0x8205F504 for r in additional):
    additional.append(dict(address='0x8205F504',source='清原選手に対して警戒します。',english='Guard against Kiyohara.',status='reviewed'))
p.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Applied {len(review)} UI, {len(skills["descriptions"])} ability, {len(headlines["overrides"])+len(headlines["patterns"])} newspaper, {len(settings["overrides"])} settings, {len(modes["overrides"])} mode/menu, {len(management["overrides"])} management, and {len(names)} player name reviews.')
