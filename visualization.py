# visualization.py
import streamlit as st
import json
import streamlit.components.v1 as components
from prompt import HP_model

# ==========================================
# 1. トポロジー定義 (全18要素の接続関係)
# ==========================================
# (Source ID, Target ID)
FULL_TOPOLOGY = [
    # --- 起点: UX (5) ---
    (5, 18), # UX -> アート
    (5, 17), # UX -> ビジネスエコシステム
    
    # --- 上段ルート (文化・価値観系) ---
    (18, 1), # アート -> 前衛的社会問題
    (1, 8),  # 前衛的社会問題 -> コミュニティ化
    (1, 9),  # 前衛的社会問題 -> 文化芸術振興
    (9, 2),  # 文化芸術振興 -> 価値観
    (8, 3),  # コミュニティ化 -> 社会問題
    (11, 2), # コミュニケーション -> 価値観
    
    # --- 下段ルート (制度・技術系) ---
    (17, 6), # ビジネスエコシステム -> 制度
    (6, 7),  # 制度 -> メディア
    (6, 10), # 制度 -> 標準化
    (10, 4), # 標準化 -> 技術
    (7, 3),  # メディア -> 社会問題
    (12, 4), # 組織化 -> 技術
    
    # --- 中央収束 (社会問題) ---
    (3, 11), # 社会問題 -> コミュニケーション
    (3, 12), # 社会問題 -> 組織化
    
    # --- 終盤 (次世代への接続) ---
    (2, 15), # 価値観 -> 慣習化
    (2, 13), # 価値観 -> 意味付け
    (4, 14), # 技術 -> 製品
    (4, 16), # 技術 -> パラダイム
    
    # --- 世代間接続 (Inter-Generation) ---
    # これらは同世代図内では右端へ伸び、論理的には次の世代のノードを指す
    (15, 6), # 慣習化 -> (次)制度
    (13, 5), # 意味付け -> (次)UX
    (14, 5), # 製品 -> (次)UX
    (16, 1), # パラダイム -> (次)前衛的社会問題
]

# 世代を超えて接続する矢印の判定用セット
INTER_GEN_EDGES = {
    ("慣習化", "制度"),
    ("意味付け", "日常の空間とユーザー体験"),
    ("製品・サービス", "日常の空間とユーザー体験"),
    ("パラダイム", "前衛的社会問題")
}

NODE_IDS = list(range(1, 19))

def transform_data_for_vis(hp_json: dict) -> list:
    stages = [
        {"key": "hp_mt_0", "stage_idx": 0}, # Mt-1
        {"key": "hp_mt_1", "stage_idx": 1}, # Mt
        {"key": "hp_mt_2", "stage_idx": 2}, # Mt+1
    ]
    
    vis_data = []

    for stage in stages:
        raw_data = hp_json.get(stage["key"], {})
        nodes = []
        arrows = []

        # ノード生成
        for nid in NODE_IDS:
            node_name = HP_model[nid]
            definition = raw_data.get(node_name, "...")
            nodes.append({
                "type": node_name,
                "definition": definition
            })

        # 矢印生成
        for src_id, tgt_id in FULL_TOPOLOGY:
            src_name = HP_model[src_id]
            tgt_name = HP_model[tgt_id]
            
            is_inter = (src_name, tgt_name) in INTER_GEN_EDGES
            
            arrows.append({
                "source": src_name,
                "target": tgt_name,
                "is_inter": is_inter 
            })

        vis_data.append({
            "stage": stage["stage_idx"],
            "ap_model": {
                "nodes": nodes,
                "arrows": arrows
            }
        })
        
    return vis_data

def render_hp_visualization(hp_json: dict):
    if not hp_json:
        st.warning("可視化データがありません")
        return

    vis_data_list = transform_data_for_vis(hp_json)
    json_str = json.dumps(vis_data_list, ensure_ascii=False)

    # HTML/JS: 横スクロール可能な広大なキャンバスに、整理されたグリッド座標で配置
    html_content = f'''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: "Helvetica Neue", Arial, sans-serif; margin: 0; padding: 0; background: transparent; }}
        
        /* 横スクロールコンテナ */
        .vis-container {{
            width: 100%;
            overflow-x: auto;
            background: #fff;
            border: 1px solid #eee;
            border-radius: 8px;
            padding-bottom: 20px;
        }}
        
        /* 描画エリア (十分に広く取る) */
        .visualization {{
            position: relative;
            width: 3200px;  /* 3世代分を描画するのに十分な幅 */
            height: 600px;
            background: #fff;
            margin: 0;
        }}

        /* ノードスタイル */
        .node {{
            position: absolute;
            width: 100px;
            height: 100px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            font-size: 11px;
            font-weight: bold;
            color: #333;
            background: #f9f9f9;
            border: 2px solid #ccc;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            z-index: 10;
            cursor: pointer;
            transition: all 0.2s;
            padding: 4px;
            box-sizing: border-box;
            line-height: 1.25;
        }}
        .node:hover {{
            transform: scale(1.1);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            z-index: 100;
        }}

        /* ノードの色分け (カテゴリ別) */
        .node-前衛的社会問題, .node-社会問題 {{ background: #ffffcc; border-color: #cccc00; }}
        .node-人々の価値観, .node-意味付け, .node-習慣化 {{ background: #ffebcc; border-color: #ff9933; }}
        .node-技術や資源, .node-製品・サービス, .node-パラダイム {{ background: #d9ffcc; border-color: #33cc33; }}
        .node-制度, .node-標準化, .node-組織化 {{ background: #e6ccff; border-color: #9933ff; }}
        .node-日常の空間とユーザー体験 {{ background: #ccebff; border-color: #3399ff; font-weight: 800; }}
        .node-アート\(社会批評\), .node-文化芸術振興 {{ background: #ffcccc; border-color: #ff3333; }}

        /* 矢印 */
        .arrow {{
            position: absolute;
            height: 2px;
            background: #bbb;
            transform-origin: 0 50%;
            z-index: 1;
            pointer-events: none;
        }}
        .arrow::after {{
            content: "";
            position: absolute;
            right: 0;
            top: -4px;
            border-left: 8px solid #bbb;
            border-top: 5px solid transparent;
            border-bottom: 5px solid transparent;
        }}
        
        /* 世代ラベル */
        .stage-label {{
            position: absolute;
            bottom: 20px;
            font-size: 24px;
            font-weight: bold;
            color: #eee;
            border-bottom: 4px solid #f0f0f0;
            padding-bottom: 5px;
            text-transform: uppercase;
        }}

        /* ツールチップ */
        .tooltip {{
            position: fixed;
            background: rgba(30, 30, 30, 0.9);
            color: #fff;
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 12px;
            max-width: 300px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 10000;
        }}
        .tooltip.show {{ opacity: 1; }}
    </style>
</head>
<body>
    <div class="vis-container">
        <div class="visualization" id="vis"></div>
    </div>
    <div class="tooltip" id="tip"></div>

    <script>
        const container = document.getElementById('vis');
        const tooltip = document.getElementById('tip');
        const data = {json_str};
        
        // 全ノードのDOM要素を格納（矢印描画用）
        let nodeElements = {{}};

        // ---------------------------------------------------------
        // 座標計算ロジック (ダイヤモンド・ラティス配置)
        // ---------------------------------------------------------
        function getCoords(stageIdx, nodeType) {{
            // 1世代あたりの幅
            const W = 1000; 
            // 基準X座標 (世代ごとに右へずらす)
            // stageIdx: 0, 1, 2
            const baseX = 50 + (stageIdx * W);
            
            // Y座標の基準 (中心線: 300)
            const Y_CENTER = 300;
            const Y_STEP = 120; // 縦の間隔
            
            // Yレベル定義
            const y_top2 = Y_CENTER - (Y_STEP * 2); // 最上段 (60)
            const y_top1 = Y_CENTER - Y_STEP;       // 上段 (180)
            const y_mid  = Y_CENTER;                // 中段 (300)
            const y_bot1 = Y_CENTER + Y_STEP;       // 下段 (420)
            const y_bot2 = Y_CENTER + (Y_STEP * 2); // 最下段 (540)
            
            // Xオフセット定義 (左から右へ)
            // 流れ: UX(Start) -> [Art,Biz] -> [Adv,Inst] -> [Comm,Media] -> SocProb -> [Comm,Org] -> [Cul,Std] -> [Val,Tech] -> [Hab,Prod] -> UX(End)
            
            switch(nodeType) {{
                // --- 起点 ---
                // Start UX (各世代の左端)
                // ※ エンドUXは次の世代のスタートUXと重なる
                
                // --- 1. 分岐 (Art / BizEco) ---
                case 'アート(社会批評)':     return {{ x: baseX + 130, y: y_top1 }};
                case 'ビジネスエコシステム': return {{ x: baseX + 130, y: y_bot1 }};

                // --- 2. 第1ピーク (AdvProb / Inst) ---
                case '前衛的社会問題':       return {{ x: baseX + 260, y: y_top2 }};
                case '制度':                 return {{ x: baseX + 260, y: y_bot2 }};

                // --- 3. 収束へ向かう (Community / Media) ---
                case 'コミュニティ化':       return {{ x: baseX + 390, y: y_top1 + 40 }}; // 少し中心寄り
                case 'メディア':             return {{ x: baseX + 390, y: y_bot1 - 40 }};

                // --- 4. 中心 (SocProb) ---
                case '社会問題':             return {{ x: baseX + 500, y: y_mid }};

                // --- 5. 拡散 (Comm / Org) ---
                case 'コミュニケーション':     return {{ x: baseX + 610, y: y_top1 + 40 }};
                case '組織化':               return {{ x: baseX + 610, y: y_bot1 - 40 }};

                // --- 6. 第2ピーク (Culture / Std) ---
                case '文化芸術振興':         return {{ x: baseX + 740, y: y_top2 }};
                case '標準化':               return {{ x: baseX + 740, y: y_bot2 }};

                // --- 7. 価値観・技術 (Values / Tech) ---
                case '人々の価値観':         return {{ x: baseX + 840, y: y_top1 }};
                case '技術や資源':           return {{ x: baseX + 840, y: y_bot1 }};

                // --- 8. 次世代への移行 (Habit, Meaning / Prod, Para) ---
                case '慣習化':               return {{ x: baseX + 920, y: y_top2 + 40 }};
                case '意味付け':             return {{ x: baseX + 920, y: y_mid - 40 }};
                case '製品・サービス':       return {{ x: baseX + 920, y: y_mid + 40 }};
                case 'パラダイム':           return {{ x: baseX + 920, y: y_bot2 - 40 }};

                // --- 終点: UX (End) ---
                // 各世代の右端。これは視覚的には次の世代のStart UXと同じ位置になるべき。
                case '日常の空間とユーザー体験': 
                    // UXは世代の「結節点」。
                    // 基本位置は右端(End)とする。
                    // 矢印のSourceとして使われるときはEnd位置。
                    // Targetとして使われるときは...？
                    return {{ x: baseX + 1000, y: y_mid }};
                
                default: return null;
            }}
        }}

        // ---------------------------------------------------------
        // 描画実行
        // ---------------------------------------------------------
        function render() {{
            container.innerHTML = '';
            nodeElements = {{}};
            
            // 1. 世代ラベル
            ['Mt-1: 過去', 'Mt: 現在', 'Mt+1: 未来'].forEach((txt, i) => {{
                const div = document.createElement('div');
                div.className = 'stage-label';
                div.innerText = txt;
                div.style.left = (50 + i * 1000) + 'px';
                div.style.width = '900px';
                container.appendChild(div);
            }});

            // 2. ノード描画
            data.forEach(d => {{
                d.ap_model.nodes.forEach(n => {{
                    const pos = getCoords(d.stage, n.type);
                    if (pos) {{
                        const el = document.createElement('div');
                        el.className = `node node-${{n.type}}`;
                        el.textContent = n.type;
                        el.dataset.desc = n.definition || '';
                        
                        // 位置設定
                        el.style.left = (pos.x - 50) + 'px'; // 中心合わせ(幅100/2)
                        el.style.top = (pos.y - 50) + 'px';

                        // イベント
                        el.onmouseenter = (e) => showTip(e, n.type, el.dataset.desc);
                        el.onmousemove = moveTip;
                        el.onmouseleave = hideTip;
                        
                        container.appendChild(el);
                        
                        // ID登録: s{stage}-{type}
                        nodeElements[`s${{d.stage}}-${{n.type}}`] = el;

                        // 特別処理: UXの連続性
                        // UXノードは「この世代の終わり」に描画されている。
                        // 「次の世代の始まり」のUXは、視覚的にはこのノードと同じ場所であるべき。
                        // 次の世代のデータ処理時に、このノードを参照できるようにエイリアスを貼る。
                        const nextStage = d.stage + 1;
                        if (n.type === '日常の空間とユーザー体験') {{
                            // これを "s{next}-StartUX" として登録
                            nodeElements[`s${{nextStage}}-StartUX`] = el;
                        }}
                    }}
                }});
                
                // 第0世代(Mt-1)のStart UXを仮想的に作る（描画はしないが座標は定義）
                if (d.stage === 0) {{
                    // 必要なら追加。今回はMt-1の左端からの矢印はないので不要。
                }}
            }});

            // 3. 矢印描画
            data.forEach(d => {{
                d.ap_model.arrows.forEach(a => {{
                    // ソースとターゲットの要素を取得
                    let srcEl = nodeElements[`s${{d.stage}}-${{a.source}}`];
                    let tgtEl = nodeElements[`s${{d.stage}}-${{a.target}}`];

                    // --- 特殊ケース: UXの始点扱い ---
                    // 矢印のSourceがUXの場合、その世代のStart UX（＝前世代のEnd UX）から出るべき
                    if (a.source === '日常の空間とユーザー体験') {{
                        // "s{d.stage}-StartUX" を探す
                        // (Mt-1の場合はStartがないのでnullになる->描画されない、でOK)
                        srcEl = nodeElements[`s${{d.stage}}-StartUX`];
                    }}

                    // --- 特殊ケース: 世代間接続 ---
                    if (a.is_inter) {{
                        // Targetは次の世代
                        const nextStage = d.stage + 1;
                        if (nextStage <= 2) {{
                            tgtEl = nodeElements[`s${{nextStage}}-${{a.target}}`];
                            
                            // もしTargetがUXなら、それは次世代のEnd UXではなくStart UX（＝現世代のEnd UX）へ
                            if (a.target === '日常の空間とユーザー体験') {{
                                tgtEl = nodeElements[`s${{d.stage}}-日常の空間とユーザー体験`];
                            }}
                        }} else {{
                            tgtEl = null; // Mt+1より先はない
                        }}
                    }}

                    if (srcEl && tgtEl) {{
                        drawArrow(srcEl, tgtEl);
                    }}
                }});
            }});
        }}

        function drawArrow(el1, el2) {{
            // 要素の中心座標を取得
            const x1 = parseFloat(el1.style.left) + 50;
            const y1 = parseFloat(el1.style.top) + 50;
            const x2 = parseFloat(el2.style.left) + 50;
            const y2 = parseFloat(el2.style.top) + 50;

            const dx = x2 - x1;
            const dy = y2 - y1;
            const dist = Math.sqrt(dx*dx + dy*dy);
            
            // 角度
            const angle = Math.atan2(dy, dx) * 180 / Math.PI;

            // ノードの半径分(50px)だけ線を短くする（めり込み防止）
            const pad = 50;
            const realDist = Math.max(0, dist - (pad * 2));
            
            // 線を描く
            const arrow = document.createElement('div');
            arrow.className = 'arrow';
            arrow.style.width = realDist + 'px';
            
            // 位置合わせ: 中心からpad分ずらしたところから開始
            const startX = x1 + (Math.cos(angle * Math.PI/180) * pad);
            const startY = y1 + (Math.sin(angle * Math.PI/180) * pad);
            
            arrow.style.left = startX + 'px';
            arrow.style.top = startY + 'px';
            arrow.style.transform = `rotate(${{angle}}deg)`;
            
            container.appendChild(arrow);
        }}

        function showTip(e, title, desc) {{
            if (!desc || desc === '...') return;
            tooltip.innerHTML = `<strong>${{title}}</strong><br>${{desc.slice(0, 150)}}...`;
            tooltip.classList.add('show');
            moveTip(e);
        }}
        function moveTip(e) {{
            tooltip.style.left = (e.clientX + 15) + 'px';
            tooltip.style.top = (e.clientY + 15) + 'px';
        }}
        function hideTip() {{
            tooltip.classList.remove('show');
        }}

        render();
    </script>
</body>
</html>
    '''
    components.html(html_content, height=650, scrolling=True)