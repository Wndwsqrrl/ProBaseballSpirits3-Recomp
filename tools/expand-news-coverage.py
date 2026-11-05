"""Apply concise baseball wording to composable match-report text."""
import json
from pathlib import Path

root=Path(__file__).resolve().parent.parent
path=root/'translation/curation.json';config=json.loads(path.read_text(encoding='utf-8'))
words={
    '%svs%sの試合は、':'%s vs %s:',
    '逆転に次ぐ逆転の激しいシーソーゲームの末、':'After a back-and-forth battle,',
    '両チームなかなか引き離せない苦しい展開の末、':'After a close contest,',
    '爆発的な破壊力を見せた%sが%d対%dで圧倒した。':'%s dominated with explosive hitting (final: %d-%d).',
    'わずかなリードを守り抜いた%sが%d対%dで逃げきった。':'%s held on to a narrow lead (final: %d-%d).',
    '終始リードを保った%sが%d対%dで完勝した。':'%s led throughout for a convincing win (final: %d-%d).',
    '豪快な打撃戦のすえ、':'After a high-scoring battle,',
    '引き締まった投手戦のすえ、':"After a pitchers' duel,",
    '%sが%d対%d':'%s (final: %d-%d)',
    'とか勝利をものにした。':'held on for the win.',
    '表、':'top,','裏、':'bottom,','ノーアウト':'no outs','1アウト':'1 out','2アウト':'2 outs',
    'から%sの':'%s hit a',
    'であげた得点を最後まで守り抜いた。':'provided the lead they held to the end.',
    'で豪快に試合を決めた。':'sealed the win.',
    'で熱い戦いに終止符をうった。':'ended the hard-fought contest.',
    'の間に得点し、からくも勝利をもぎ取った。':'brought home the decisive run.',
    'で試合を決めた。':'decided the game.',
    'の間に得点し勝利した。':'brought home the winning run.',
    'で貴重な勝ち越し点をあげた。':'drove in the go-ahead run.',
    'であげた得点が効果的だった。':'produced a crucial run.',
    'であげた得点が効いた。':'made the difference.',
    'で決勝点をあげた。':'drove in the winning run.',
    'であげた得点が最後まで効いた。':'provided the lead they held to the end.',
    '%sは':'%s:','%d安打':'%d hits','%d本塁打':'%d HR','%d打点':'%d RBI',
    'の大活躍':'in an outstanding performance','の活躍':'in a strong performance',
    'で勝利に貢献。':'helped secure the win.','で存在感を示した。':'made an impact.',
    '投げては、':'On the mound,','%sが%d回':'%s pitched %d innings',
    '%d回':'%d innings','を投げて':'pitched','1アウトも取れずに':'without recording an out',
    '%d失点と散々だった。':'struggled, allowing %d runs.',
    '投手陣は乱調で、大量%d点を失った。':'The pitching staff struggled, allowing %d runs.',
    '力投を見せ、セーブをあげた。':'earned the save with a strong outing.',
    'リリース時にもう一度':'At release, press','を押そう！':'again!',
    'スピリッツモードを最初からプレーします。':'Start a new Spirits game.',
    'スピリッツモードの中断データを読み込んで':'Load your Spirits save',
    '続きからプレーします。':'and continue playing.',
    'ユーティリティで“選手削除”を行ってください':'Use Delete Player in Utility.',
    'あと':'Remaining:','人作成可能':'player slots',
    'ペナントレースの最初からプレーを行います。':'Start a new Pennant season.',
    'ペナントレースの中断セーブデータを読み込んで':'Load your Pennant save',
    '公式戦を短くまとめた日程でプレイします。':'Play a shortened regular season.',
    'ペナントを気軽に楽しみたい方はこちら。':'A quicker, more casual Pennant season.',
    '１シーズンの推定プレイ時間：　　４０時間':'Estimated season length: 40 hours',
    '１シーズンの推定プレイ時間：　　１０時間':'Estimated season length: 10 hours',
    '・データはセーブされません。':'Data will not be saved.',
    'X回戦　X勝　X敗　X分':'Game X: X W / X L / X T','Ｘ勝':'X W','Ｘ敗':'X L','Ｘセーブ':'X SV','Ｘ号':'HR X',
    '山﨑　健':'Yamazaki Ken','後藤光':'Gotoh',
    'アレックス':'Alex','セントラルリーグ開幕！':'Central League Opening Day!',
}
config['word_overrides'].update(words)
path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'{len(words)} report/menu wording corrections applied.')
