"""Add reviewed short runtime labels/templates observed in the text trace."""
import json
from pathlib import Path

root=Path(__file__).resolve().parent.parent
path=root/'translation/curation.json'
config=json.loads(path.read_text(encoding='utf-8'))
labels={
    '項目%d':'Item %d','内容%d':'Details %d','選択肢%d':'Option %d',
    'シフト%d':'Shift %d','デ%d':'Data %d',
    '%d勝%d敗%dＳ':'%d W / %d L / %d SV',
    '%d勝%d敗':'%d W / %d L','%d勝':'%d W','%d敗':'%d L',
    '右上投：':'R Overhand:','左上投：':'L Overhand:',
    '右横投：':'R Sidearm:','左横投：':'L Sidearm:',
    '右ス投：':'R Three-quarter:','左ス投：':'L Three-quarter:',
    '右下投：':'R Underhand:','左下投：':'L Underhand:',
    'リリーフ調整中':'Warming Up (Relief)','先発準備完了':'Starter Ready',
    '走塁無視':'Ignore Baserunners','汎用16フォント':'Standard 16 Font',
    '球種名10文字':'Pitch Name (10 chars)','ＳＦＦ':'Splitter',
    '加藤':'Kato','高木':'Takagi','川井':'Kawai','ベニー':'Benny',
    '中村':'Nakamura','鈴木':'Suzuki',
    'コンバート：先発':'Convert to Starter','コンバート：リリーフ':'Convert to Reliever',
    'コンバート : 先発':'Convert to Starter','コンバート : リリーフ':'Convert to Reliever',
    '対象':'Target','期間':'Duration','エクストラ':'Extra',
    '勝':'W','負':'L','表':'Top','裏':'Bot','神':'T','ロ':'M',
    '昨シーズン':'Last Season','昨年成績':'Last Season',
    '防御率':'ERA','試合':'Games','試合数':'Games','打率':'AVG',
    '本塁打':'HR','打点':'RBI','安打':'Hits','盗塁':'SB',
    '出塁率':'OBP','長打率':'SLG','被打率':'Opp. AVG','奪三振':'SO',
    '勝率':'Win %','セーブ':'Saves','ホールド':'Holds',
    '四球':'BB','死球':'HBP','失点':'Runs','自責点':'ER',
    '先発':'Starter','リリーフ':'Reliever','投球回':'IP',
    'ライト':'RF','センター':'CF','レフト':'LF',
    'ファースト':'1B','セカンド':'2B','サード':'3B','ショート':'SS',
    'キャッチャー':'C','ピッチャー':'P','指名打者':'DH',
    '右':'R','左':'L','両':'S','%s投%s打':'Throws %s / Bats %s',
    '先　攻':'Away','後　攻':'Home','投　手':'Pitcher','打　者':'Batter',
    '先攻':'Away','後攻':'Home','試合時間':'Game Time',
    '飛距離':'Distance','パネル':'Panel','球団名':'Team',
    '球団名称':'Team','チーム名':'Team','開催地':'Venue',
    '所持金':'Funds','名前':'Name','年俸':'Salary','立場':'Role',
    '要求活躍':'Performance Target','基本VP':'Base VP',
    'COM難易度レート':'CPU Difficulty Multiplier',
    '最初から':'New Game','続きから':'Continue',
    'フリープレイ':'Free Play','VPチャレンジ':'VP Challenge',
    'ＶＰを稼ぐチャンス！':'Earn more VP!',
    'シーズン公式戦':'Regular Season','真剣ペナント':'Real Pennant',
    '球団切替':'Switch Team','左右切替':'Switch Side','獲得':'Earned',
    '獲得VP':'VP Earned','見出し':'Heading','盗塁企図':'SB Attempts',
    '定位置(標準)':'Normal Alignment','一塁走者':'Runner on 1st',
    '二塁走者':'Runner on 2nd','三塁走者':'Runner on 3rd',
    '右打者':'Right-handed Batter','左打者':'Left-handed Batter',
    '指示できる作戦はありません':'No strategies available.',
    'コマンド%d':'Command %d','ヘルプ説明%d行目':'Help Line %d',
    '個別役割説明%d行目':'Role Description %d',
    '%d時間 %d分':'%dh %dm','%d回戦 %d勝 %d敗 %d分':'Game %d: %d W / %d L / %d T',
    '%d回戦 %d敗 ':'Game %d: %d L','対戦成績%d勝':'Head-to-head: %d W',
    '%d万':'%d x 10,000 yen','%d月':'Month %d','%d日':'Day %d',
    '%s勝利を呼ぶ%d発！':'%s powers the win with %d HR!',
    '本塁打含む%d発%d打点の大当たり　　　　　　':'%d HR and %d RBI!',
    '　　　　　　　　%sを助ける見事な活躍':'Great support for %s!',
    'テキスト%d段目':'Text Row %d',
    '１シーズンの推定プレイ時間：　%d時間':'Estimated season: %d hours',
    '１シーズンの推定プレイ時間：　　%d時間':'Estimated season: %d hours',
    'オリジナル選手一覧':'Created Players','実在ドラフト選手一覧':'Real Draft Prospects',
    '自由に指名':'Free Draft','指名を再現':'Historical Draft',
    '先発タイプ':'Starter','中継ぎタイプ':'Reliever','抑えタイプ':'Closer',
}
config.setdefault('word_overrides',{}).update({s:e for s,e in labels.items() if '%' not in s})
for throws in ('右','左'):
    for bats in ('右','左','両'):
        hand=f'{throws}投{bats}打 '
        english=f'Throws {labels[throws]} / Bats {labels[bats]}'
        labels[hand]=english
        for position,abbr in {'外野手':'OF','一塁手':'1B','二塁手':'2B','三塁手':'3B','遊撃手':'SS','捕手':'C','投手':'P'}.items():
            for spaces in ('\u3000\u3000','\u3000\u3000\u3000'):
                labels[hand+spaces+position]=english+' / '+abbr
for hand in ('右','左'):
    for motion in ('上','横','ス','下'):
        prefix=f'{hand}{motion}投：'
        labels['休息中']='Resting'
        for state in ('リリーフ調整中','先発準備完了','休息中','先発タイプ','中継ぎタイプ','抑えタイプ'):
            labels[prefix+state]=labels[prefix]+' '+labels[state]
existing={r['source']:r for r in config['additional_strings']}
added=0
for source,english in labels.items():
    if source in existing:
        existing[source]['english']=english
        continue
    config['additional_strings'].append(dict(address='0x00000000',source=source,english=english,status='reviewed'))
    added+=1
path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Added {added} runtime labels/templates.')
