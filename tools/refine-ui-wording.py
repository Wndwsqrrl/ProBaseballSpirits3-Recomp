"""Keep concise, consistent English for common baseball UI labels."""
import json
from pathlib import Path
p=Path(__file__).resolve().parent.parent/'translation/curation.json'
c=json.loads(p.read_text(encoding='utf-8'))
corrections={
    '球威':'Stuff','球速':'Velocity','制球':'Control','変化球':'Breaking Pitches',
    '走力':'Speed','パワー':'Power','ミート':'Contact','スタミナ':'Stamina',
    '守備力':'Fielding','守備適性':'Positions','捕球':'Catching','スローイング':'Throwing',
    '肩力':'Arm Strength','走塁力':'Baserunning','盗塁力':'Stealing','長打力':'Power',
    '疲労回復力':'Recovery','守備フォーメーション':'Defensive Alignment',
    '外野前進守備':'Shallow Outfield','外野後退守備':'Deep Outfield',
    '中間守備':'Halfway In','前進守備':'Infield In','通常守備':'Normal Alignment',
    '中継にボールを投げる':'Throw to the Cutoff Man','守備カーソルの固定':'Lock Fielder Cursor',
    '球速レベル':'Pitch Speed','キャッチャー返球':'Catcher Return Throw',
    '起用設定':'Player Roles','全力ピッチシステム':'Power Pitch System',
    '強振とミート打ち':'Power and Contact Swings','全力ピッチング！':'Power Pitching!',
    '上投：':'Overhand:','ス投：':'Three-quarter:','横投：':'Sidearm:','下投：':'Underhand:',
    '両投':'Ambidextrous','オーバースロー':'Overhand','サイドスロー':'Sidearm','アンダースロー':'Underhand',
    '高速スライダー':'Hard Slider','カットボール':'Cutter','高速シンカー':'Hard Sinker',
    '高速スクリュー':'Hard Screwball','超高速スクリュー':'Extra-hard Screwball','高速シュート':'Hard Shuuto',
    '変化球主体配球':'Breaking Ball Focus','直球主体配球':'Fastball Focus',
    '変化球中心':'Breaking Ball Focus','速球中心':'Fastball Focus','決め球':'Out Pitch',
    '積極起用':'Aggressive Usage','ベテラン起用':'Favor Veterans','若手起用':'Favor Young Players',
    '慎重守備':'Conservative Fielding','積極守備':'Aggressive Fielding','積極走塁':'Aggressive Baserunning',
    '慎重スイング':'Patient Approach','積極スイング':'Aggressive Approach',
    'シュート回転':'Arm-side Run','球速安定':'Consistent Velocity','逃げ球':'Keep It Down',
    'ジャイロボール':'Gyroball','打球反応':'Pitcher Reflexes','目切り背走':'Track Fly Balls',
    'バックハンドトス':'Backhand Toss','座り送球':'Seated Throw','パワーヒッター':'Power Hitter',
    '調子安定':'Consistent Form','走塁':'Baserunning','グリーンライト':'Green Light',
    '次の一球は待ちます':'Take the Next Pitch','守備練習':'Fielding Practice',
    '右投げ':'Throws R','左投げ':'Throws L','グラウンド':'Surface','人工芝':'Artificial Turf',
    '天然芝':'Natural Grass','両翼':'LF/RF','フェンス':'Fence','デーゲーム':'Day Game','ナイトゲーム':'Night Game',
    '決定する':'Confirm','決定しました':'Confirmed','きめる':'Confirm',
    '本拠地':'Home Stadium','本拠地球場':'Home Stadium','前年成績':'Previous Season',
    '勝率':'Win %','%d勝、%d敗、%d分':'%d W / %d L / %d T',
    '%d勝%d敗%d分':'%d W / %d L / %d T','%d勝 %d敗 %d分':'%d W / %d L / %d T',
    '%d回表':'Top %d','%d回ウラ':'Bottom %d','%d回表攻撃終了':'End of Top %d','%d回裏攻撃終了':'End of Bottom %d',
}
c['word_overrides'].update(corrections)
p.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'{len(corrections)} concise UI corrections applied.')
