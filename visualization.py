# visualization.py
import streamlit as st
import json
import streamlit.components.v1 as components
from prompt import HP_model

# Sample.jpgに基づく、全18要素の接続関係 (Source -> Target)
# すべてを「ノード」として扱うため、すべての矢印を描画します。
FULL_TOPOLOGY = [
    # UX起点
    (5, 18), # UX -> Art
    (5, 17), # UX -> BizEco
    
    # Art系フロー
    (18, 1), # Art -> AdvProb
    (1, 9),  # AdvProb -> Culture
    (9, 2),  # Culture -> Values
    
    # Community系フロー
    (1, 8),  # AdvProb -> Community
    (8, 3),  # Community -> SocProb
    (3, 11), # SocProb -> Comm
    (11, 2), # Comm -> Values
    
    # Institution系フロー
    (17, 6), # BizEco -> Inst
    (6, 7),  # Inst -> Media
    (7, 3),  # Media -> SocProb
    (3, 12), # SocProb -> Org
    (12, 4), # Org -> Tech
    
    # Tech系フロー
    (6, 10), # Inst -> Std
    (10, 4), # Std -> Tech
    (4, 16), # Tech -> Paradigm
    # (16) -> Next AdvProb (世代間接続)
    
    # Values起点後半
    (2, 15), # Values -> Habit
    (15, 6), # Habit -> Next Inst (世代間接続的だが、同世代図内では右側へ)
    
    (2, 13), # Values -> Meaning
    (13, 5), # Meaning -> Next UX (世代間接続)
    
    (4, 14), # Tech -> Product
    (14, 5), # Product -> Next UX
]

# 世代を超えて接続する矢印の定義 (SourceType, TargetType)
INTER_GEN_CONNECTIONS = [
    ("慣習化", "制度"),          # Habit -> Next Inst
    ("意味付け", "日常の空間とユーザー体験"), # Meaning -> Next UX
    ("パラダイム", "前衛的社会問題"),    # Paradigm -> Next AdvProb
    ("製品・サービス", "日常の空間とユーザー体験") # Product -> Next UX (図ではTech->Prod->UX)
]

# 全18要素のID
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

        # 1. 全18要素をノードとして作成
        for nid in NODE_IDS:
            node_name = HP_model[nid]
            # データがない場合も空文字でノード作成
            definition = raw_data.get(node_name, "...")
            nodes.append({
                "type": node_name,
                "definition": definition
            })

        # 2. 矢印データ作成 (世代内接続)
        for src_id, tgt_id in FULL_TOPOLOGY:
            src_name = HP_model[src_id]
            tgt_name = HP_model[tgt_id]
            
            # 世代またぎの判定 (簡易的に名前で判定)
            is_inter = False
            if (src_name, tgt_name) in INTER_GEN_CONNECTIONS:
                is_inter = True
            
            # 図の構造上、パラダイム->前衛、習慣->制度、意味->UX、製品->UX は「次の」世代へ伸びる線として描画したいが、
            # D3/HTML配置ロジックでは「右端」に配置することで視覚的に接続させる。
            # ここでは単純にSource->Targetの情報を渡す。
            
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
        return

    vis_data_list = transform_data_for_vis(hp_json)
    json_str = json.dumps(vis_data_list, ensure_ascii=False)

    html_content = f'''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: "Helvetica Neue", Arial, sans-serif; background-color: transparent; margin: 0; padding: 0; }}
        .vis-wrapper {{ overflow-x: auto; border: 1px solid #eee; border-radius: 8px; background: white; padding-bottom: 30px; }}
        .visualization {{ position: relative; width: 1800px; height: 600px; background: #fff; margin: 0 auto; }}
        
        .node {{
            position: absolute; width: 90px; height: 90px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; font-weight: bold; text-align: center;
            cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1); border: 2px solid #fff;
            padding: 2px; box-sizing: border-box; color: #444; z-index: 10;
            line-height: 1.2; background: #f0f0f0;
        }}
        .node:hover {{ transform: scale(1.1); z-index: 100; box-shadow: 0 6px 16px rgba(0,0,0,0.2); }}
        
        /* Node Colors by Category (Sample.jpg based) */
        .node-前衛的社会問題, .node-社会問題 {{ background: #ffffba; border-color: #e6e600; }}
        .node-技術や資源, .node-製品・サービス {{ background: #baffc9; border-color: #00cc44; }}
        .node-日常の空間とユーザー体験 {{ background: #bae1ff; border-color: #3399ff; }}
        .node-制度, .node-標準化 {{ background: #e1baff; border-color: #9933ff; }}
        .node-人々の価値観, .node-意味付け {{ background: #ffdfba; border-color: #ffb366; }}
        .node-アート\(社会批評\), .node-文化芸術振興 {{ background: #ffb3b3; border-color: #ff8080; }}
        
        .arrow {{ position: absolute; height: 1px; background: #aaa; transform-origin: left center; z-index: 1; pointer-events: none; }}
        .arrow::after {{
            content: ''; position: absolute; right: 0px; top: -3px;
            border-left: 6px solid #aaa; border-top: 3px solid transparent; border-bottom: 3px solid transparent;
        }}
        
        .tooltip {{
            position: fixed; background: rgba(40, 40, 40, 0.95); color: #fff;
            padding: 10px; border-radius: 4px; font-size: 12px;
            max-width: 300px; pointer-events: none; opacity: 0; z-index: 9999;
        }}
        .tooltip.show {{ opacity: 1; }}
        
        .stage-label {{
            position: absolute; bottom: 10px; font-size: 20px; font-weight: bold; color: #ddd;
            border-bottom: 2px solid #eee; width: 500px; text-align: center;
        }}
    </style>
</head>
<body>
    <div class="vis-wrapper">
        <div class="visualization" id="visualization"></div>
    </div>
    <div class="tooltip" id="tooltip"></div>

    <script>
        const container = document.getElementById('visualization');
        const tooltip = document.getElementById('tooltip');
        let allNodes = {{}};
        const data = {json_str};

        // ダイヤモンド・ラティス構造の座標計算
        // stageIdx: 0(Mt-1), 1(Mt), 2(Mt+1)
        function getNodePosition(stageIdx, nodeType) {{
            const stageWidth = 550; // 1世代の幅
            const startX = 50;
            const offsetX = startX + (stageIdx * stageWidth);
            
            // Y座標 (Top to Bottom)
            const y1 = 50;  // Top
            const y2 = 120;
            const y3 = 190;
            const y4 = 260; // Center
            const y5 = 330;
            const y6 = 400;
            const y7 = 470; // Bottom

            // X座標 (Left to Right within stage)
            const x1 = 0;   // Start (Prev UX)
            const x2 = 80;
            const x3 = 160;
            const x4 = 240; // Center (SocProb/Values)
            const x5 = 320;
            const x6 = 400;
            const x7 = 480; // End (Next UX)

            // Sample.jpgの配置を模倣
            // 左端: UX (前の世代の終わり = 今の世代の始まり)
            // 右端: UX (今の世代の終わり)
            
            switch(nodeType) {{
                case '日常の空間とユーザー体験': return {{ x: offsetX + x7, y: y4 }}; // End UX
                
                // --- Upper Stream ---
                case 'アート(社会批評)':     return {{ x: offsetX + x2, y: y2 }};
                case '前衛的社会問題':       return {{ x: offsetX + x3, y: y1 }};
                case '文化芸術振興':         return {{ x: offsetX + x5, y: y1 }};
                case '人々の価値観':         return {{ x: offsetX + x6, y: y2 }}; // Actually center-ish right
                
                case 'コミュニティ化':       return {{ x: offsetX + x3, y: y3 }};
                case '社会問題':             return {{ x: offsetX + x4, y: y4 }}; // Center Node
                case 'コミュニケーション':     return {{ x: offsetX + x5, y: y3 }};
                
                // --- Lower Stream ---
                case 'ビジネスエコシステム': return {{ x: offsetX + x2, y: y6 }};
                case '制度':                 return {{ x: offsetX + x3, y: y7 }};
                case '標準化':               return {{ x: offsetX + x5, y: y7 }};
                case '技術や資源':           return {{ x: offsetX + x6, y: y6 }};
                
                case 'メディア':             return {{ x: offsetX + x3, y: y5 }};
                case '組織化':               return {{ x: offsetX + x5, y: y5 }};
                
                // --- Transitions to Next ---
                case '慣習化':               return {{ x: offsetX + x6 + 30, y: y1 + 30 }}; // High Right
                case '意味付け':             return {{ x: offsetX + x6 + 30, y: y6 - 30 }}; // Low Right (Values -> UX)
                case '製品・サービス':       return {{ x: offsetX + x6 + 40, y: y5 + 20 }}; // Tech -> UX
                case 'パラダイム':           return {{ x: offsetX + x6 + 40, y: y2 - 20 }}; // Tech -> AdvProb (Next)
                
                default: return null;
            }}
        }}

        // Mtの開始UXは、Mt-1の終了UXと同じ位置に描画する必要がある
        // 特殊ロジック: 各ステージの「左端のUX」を描画する
        function render() {{
            container.innerHTML = '';
            allNodes = {{}};
            
            // Labels
            ['Mt-1: 過去', 'Mt: 現在', 'Mt+1: 未来'].forEach((label, i) => {{
                const div = document.createElement('div');
                div.className = 'stage-label';
                div.innerText = label;
                div.style.left = (i * 550 + 70) + 'px';
                container.appendChild(div);
            }});

            // Nodes
            data.forEach(d => {{
                // 1. 通常ノード
                d.ap_model.nodes.forEach(n => {{
                    // UXは「右端」として定義されているが、
                    // Mtの「左端」には「Mt-1の右端UX」が来るべき。
                    // ここではシンプルに、全ノードをオフセット通り描画する。
                    // 視覚的に連続させるため、前の世代のUXと重なるように座標調整してもよいが、
                    // わかりやすくするために全ノードを描く。
                    
                    const pos = getNodePosition(d.stage, n.type);
                    if (pos) {{
                        const el = document.createElement('div');
                        el.className = `node node-${{n.type}}`;
                        el.style.left = pos.x + 'px';
                        el.style.top = pos.y + 'px';
                        el.textContent = n.type;
                        el.dataset.text = n.definition || '';
                        
                        el.onmouseenter = (e) => showTip(e, n.type, el.dataset.text);
                        el.onmousemove = moveTip;
                        el.onmouseleave = hideTip;
                        
                        container.appendChild(el);
                        // Store with stage key
                        allNodes[`s${{d.stage}}-${{n.type}}`] = el;
                    }}
                }});
                
                // 2. 左端のUX (Start UX) を補完描画 (Mt, Mt+1のみ)
                // 前の世代のUXノードの場所と同じ場所に「Start UX」という概念がある
                if (d.stage > 0) {{
                     // 前のステージのデータを参照
                     const prevStage = data[d.stage - 1];
                     const prevUX = prevStage.ap_model.nodes.find(n => n.type === '日常の空間とユーザー体験');
                     if (prevUX) {{
                         // 前の世代のUXノードを、この世代の「開始点」として論理的に扱う
                         // ビジュアル上はすでに描画されている (prevStageのEnd UXとして)
                         // なので、矢印のソースとして参照できるようにエイリアスを作る
                         const prevEl = allNodes[`s${{d.stage-1}}-日常の空間とユーザー体験`];
                         if (prevEl) {{
                             allNodes[`s${{d.stage}}-StartUX`] = prevEl;
                         }}
                     }}
                }}
            }});

            // Arrows
            data.forEach(d => {{
                d.ap_model.arrows.forEach(a => {{
                    let src = allNodes[`s${{d.stage}}-${{a.source}}`];
                    let tgt = allNodes[`s${{d.stage}}-${{a.target}}`];
                    
                    // UXがソースの場合、それは「世代の開始点」としてのUXを指す
                    if (a.source === '日常の空間とユーザー体験') {{
                        // 通常のUXノード(End)ではなく、StartUX(前世代のEnd)を使う
                        if (d.stage > 0) {{
                            src = allNodes[`s${{d.stage}}-StartUX`];
                        }} else {{
                            // Mt-1の開始UXは存在しない(画面外)ので描画しない、あるいは仮想的に左に作る
                            // ここでは省略
                            src = null; 
                        }}
                    }}
                    
                    // 世代間接続 (Inter-gen)
                    // パラダイム -> 次の前衛的社会問題
                    // 慣習化 -> 次の制度 など
                    if (a.is_inter) {{
                        // ターゲットは次のステージのノード
                        const nextStageIdx = d.stage + 1;
                        if (nextStageIdx < 3) {{
                            tgt = allNodes[`s${{nextStageIdx}}-${{a.target}}`];
                            // 例外: UXへの接続(意味付け->UX, 製品->UX)は、次の世代のEnd UXではなくStart UX(つまり現在のEnd UX)へ
                            if (a.target === '日常の空間とユーザー体験') {{
                                tgt = allNodes[`s${{d.stage}}-日常の空間とユーザー体験`]; 
                            }}
                        }} else {{
                            tgt = null;
                        }}
                    }}

                    if (src && tgt) {{
                        drawArrow(src, tgt);
                    }}
                }});
            }});
        }}

        function drawArrow(n1, n2) {{
            const x1 = parseFloat(n1.style.left) + 45;
            const y1 = parseFloat(n1.style.top) + 45;
            const x2 = parseFloat(n2.style.left) + 45;
            const y2 = parseFloat(n2.style.top) + 45;
            
            const dx = x2 - x1;
            const dy = y2 - y1;
            const dist = Math.sqrt(dx*dx + dy*dy);
            const angle = Math.atan2(dy, dx) * 180 / Math.PI;
            
            const arrow = document.createElement('div');
            arrow.className = 'arrow';
            arrow.style.width = dist + 'px';
            arrow.style.left = x1 + 'px';
            arrow.style.top = y1 + 'px';
            arrow.style.transform = `rotate(${{angle}}deg)`;
            container.appendChild(arrow);
        }}

        function showTip(e, title, text) {{
            if (!text || text === '...') return;
            tooltip.innerHTML = `<strong>${{title}}</strong><br>${{text.substring(0, 200)}}...`;
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