import streamlit as st
import json
import streamlit.components.v1 as components
from prompt import HP_model

# ==========================================
# 1. 定義: ノード（対象）と矢印（プロセス）
# ==========================================

# ノードになるID (6要素)
NODE_IDS = {1, 2, 3, 4, 5, 6}

# 矢印定義 (sample.jpgのダイヤモンド・ラティス構造に基づく)
ARROW_MAP = [
    # --- 世代内接続 (左から右へ) ---
    # 起点(UX)からの分岐
    {"src": 5, "arr": 18, "tgt": 1},  # UX -> アート -> 前衛
    {"src": 5, "arr": 17, "tgt": 6},  # UX -> ビジネス -> 制度
    
    # 上段ルート
    {"src": 1, "arr": 9,  "tgt": 2},  # 前衛 -> 文化芸術 -> 価値観
    {"src": 1, "arr": 8,  "tgt": 3},  # 前衛 -> コミュニティ -> 社会問題
    
    # 下段ルート
    {"src": 6, "arr": 10, "tgt": 4},  # 制度 -> 標準化 -> 技術
    {"src": 6, "arr": 7,  "tgt": 3},  # 制度 -> メディア -> 社会問題
    
    # 中央(社会問題)からの拡散
    {"src": 3, "arr": 11, "tgt": 2},  # 社会問題 -> コミュニケーション -> 価値観
    {"src": 3, "arr": 12, "tgt": 4},  # 社会問題 -> 組織化 -> 技術
    
    # --- 次世代への接続 (右端への流出) ---
    # 同世代図の右端にあるノード(価値観/技術)から、次の世代のノードへ
    # 実際には次のステージのノードIDを指すが、描画上は「右への矢印」として処理
    {"src": 2, "arr": 15, "tgt": 6, "is_next": True}, # 価値観 -> 習慣化 -> (次)制度
    {"src": 2, "arr": 13, "tgt": 5, "is_next": True}, # 価値観 -> 意味付け -> (次)UX
    {"src": 4, "arr": 14, "tgt": 5, "is_next": True}, # 技術 -> 製品 -> (次)UX
    {"src": 4, "arr": 16, "tgt": 1, "is_next": True}, # 技術 -> パラダイム -> (次)前衛
]

def transform_data_for_vis(hp_json: dict) -> list:
    stages = [
        {"key": "hp_mt_0", "stage_idx": 0}, # Mt-1 (過去) - Up
        {"key": "hp_mt_1", "stage_idx": 1}, # Mt (現在) - Down (反転)
        {"key": "hp_mt_2", "stage_idx": 2}, # Mt+1 (未来) - Up
    ]
    
    vis_data = []

    for stage in stages:
        raw_data = hp_json.get(stage["key"], {})
        nodes = []
        arrows = []

        # 1. ノード (6つの対象)
        for nid in NODE_IDS:
            node_name = HP_model[nid]
            definition = raw_data.get(node_name, "...")
            nodes.append({
                "id": nid,
                "type": node_name,
                "definition": definition
            })

        # 2. 矢印 (12のプロセス)
        for rule in ARROW_MAP:
            arrow_id = rule["arr"]
            arrow_name = HP_model[arrow_id]
            definition = raw_data.get(arrow_name, "...")
            
            arrows.append({
                "arrow_id": arrow_id,
                "label": arrow_name,
                "definition": definition,
                "src_node_id": rule["src"],
                "tgt_node_id": rule["tgt"],
                "is_next": rule.get("is_next", False)
            })

        vis_data.append({
            "stage": stage["stage_idx"],
            "nodes": nodes,
            "arrows": arrows
        })
        
    return vis_data

def render_hp_visualization(hp_json: dict):
    if not hp_json:
        st.warning("可視化データがありません")
        return

    vis_data_list = transform_data_for_vis(hp_json)
    json_str = json.dumps(vis_data_list, ensure_ascii=False)

    html_content = f'''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: "Helvetica Neue", Arial, sans-serif; margin: 0; padding: 0; background: transparent; }}
        
        .vis-container {{
            width: 100%; overflow-x: auto; background: #fff;
            border: 1px solid #eee; border-radius: 8px; padding-bottom: 30px;
        }}
        
        .visualization {{
            position: relative;
            width: 2600px; /* 3世代分 */
            height: 650px;
            background: #fff;
            margin: 0;
        }}

        /* ノード (円) */
        .node {{
            position: absolute; width: 100px; height: 100px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            text-align: center; font-size: 12px; font-weight: bold; color: #333;
            border: 3px solid #ccc; box-shadow: 0 3px 6px rgba(0,0,0,0.1);
            z-index: 10; cursor: pointer; background: #f9f9f9;
            transition: transform 0.2s; padding: 5px; box-sizing: border-box;
            line-height: 1.2;
        }}
        .node:hover {{ transform: scale(1.1); z-index: 100; }}

        /* 色分け */
        .node-前衛的社会問題 {{ background: #ffcccc; border-color: #ff9999; }}
        .node-社会問題 {{ background: #ffffcc; border-color: #e6e600; }}
        .node-人々の価値観 {{ background: #ffebcc; border-color: #ffcc99; }}
        .node-技術や資源 {{ background: #ccffcc; border-color: #66cc66; }}
        .node-制度 {{ background: #e6ccff; border-color: #cc99ff; }}
        .node-日常の空間とユーザー体験 {{ background: #ccebff; border-color: #66b3ff; }}

        /* 矢印の線 */
        .arrow-line {{
            position: absolute; height: 2px; background: #999;
            transform-origin: 0 50%; z-index: 1; pointer-events: none;
        }}
        .arrow-line::after {{
            content: ""; position: absolute; right: 0; top: -4px;
            border-left: 8px solid #999; border-top: 5px solid transparent; border-bottom: 5px solid transparent;
        }}
        /* 世代間接続の線（破線） */
        .arrow-dashed {{ border-top: 2px dashed #999; background: transparent; height: 0; }}
        .arrow-dashed::after {{ border-left-color: #999; top: -6px; }}

        /* 矢印のラベル */
        .arrow-label {{
            position: absolute; background: #fff; padding: 2px 6px;
            border: 1px solid #ddd; border-radius: 4px; font-size: 10px; color: #555;
            z-index: 5; cursor: help; transform: translate(-50%, -50%);
            white-space: nowrap;
        }}
        .arrow-label:hover {{ background: #eee; color: #000; z-index: 50; }}

        .stage-label {{
            position: absolute; bottom: 10px; font-size: 20px; font-weight: bold; color: #ddd;
            border-bottom: 4px solid #f0f0f0; text-transform: uppercase;
        }}

        .tooltip {{
            position: fixed; background: rgba(30,30,30,0.9); color: #fff;
            padding: 10px; border-radius: 5px; font-size: 12px; max-width: 250px;
            pointer-events: none; opacity: 0; z-index: 9999;
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
        
        // DOM要素キャッシュ key: s{{stage}}-n{{node_id}}
        let nodeEls = {{}};

        // --- 座標定義 (ダイヤモンド型) ---
        function getNodeCoord(stageIdx, nodeId) {{
            const W = 800; // 1世代の幅
            const H_CENTER = 300;
            const V_GAP = 200; // 垂直方向の広がり
            
            // 基準X (世代ごとにシフト)
            const baseX = 50 + (stageIdx * W);

            // ★【反転ロジック】: Stage 1 (Mt) の場合のみ上下を入れ替える
            // invert = -1 (反転: 上が下に、下が上に), 1 (通常)
            const invert = (stageIdx === 1) ? -1 : 1;
            
            // ID別配置:
            // 5:UX(左端), 3:社会(中央) -> Yはセンター固定
            // 1:前衛, 2:価値 -> 通常は上(Y小)、反転時は下(Y大)
            // 6:制度, 4:技術 -> 通常は下(Y大)、反転時は上(Y小)
            
            switch(nodeId) {{
                case 5: return {{ x: baseX,          y: H_CENTER }};
                
                // 1: 前衛的社会問題
                // 通常: 300 - 200 = 100 (上)
                // 反転: 300 - (-200) = 500 (下)
                case 1: return {{ x: baseX + 200,    y: H_CENTER - (V_GAP * invert) }};
                
                // 6: 制度
                // 通常: 300 + 200 = 500 (下)
                // 反転: 300 + (-200) = 100 (上)
                case 6: return {{ x: baseX + 200,    y: H_CENTER + (V_GAP * invert) }};
                
                case 3: return {{ x: baseX + 400,    y: H_CENTER }};
                
                // 2: 価値観 (同 1)
                case 2: return {{ x: baseX + 600,    y: H_CENTER - (V_GAP * invert) }};
                
                // 4: 技術 (同 6)
                case 4: return {{ x: baseX + 600,    y: H_CENTER + (V_GAP * invert) }};
                
                default: return {{ x: 0, y: 0 }};
            }}
        }}

        function render() {{
            container.innerHTML = '';
            nodeEls = {{}};
            
            // 1. 世代ラベル
            ['Mt-1: 過去', 'Mt: 現在 (上下反転)', 'Mt+1: 未来'].forEach((txt, i) => {{
                const d = document.createElement('div');
                d.className = 'stage-label';
                d.innerText = txt;
                d.style.left = (50 + i * 800) + 'px';
                d.style.width = '700px';
                container.appendChild(d);
            }});

            // 2. ノード描画 (全世代分)
            data.forEach(d => {{
                d.nodes.forEach(n => {{
                    const pos = getNodeCoord(d.stage, n.id);
                    
                    const el = document.createElement('div');
                    el.className = `node node-${{n.type}}`;
                    el.textContent = n.type;
                    el.dataset.desc = n.definition;
                    
                    // 中心合わせ
                    el.style.left = (pos.x - 50) + 'px';
                    el.style.top = (pos.y - 50) + 'px';
                    
                    el.onmouseenter = (e) => showTip(e, n.type, el.dataset.desc);
                    el.onmousemove = moveTip;
                    el.onmouseleave = hideTip;
                    
                    container.appendChild(el);
                    nodeEls[`s${{d.stage}}-n${{n.id}}`] = el;
                }});
                
                // 次の世代へつなぐための「右端のEnd UX」ポイントを作成
                // これは次の世代のStart UXと同じ座標になる (x=baseX+800, y=300)
                const endUxX = (50 + (d.stage * 800)) + 800;
                const endUxY = 300;
                
                const dummy = document.createElement('div');
                dummy.style.position = 'absolute';
                dummy.style.left = (endUxX - 50) + 'px';
                dummy.style.top = (endUxY - 50) + 'px';
                dummy.style.width = '100px'; 
                dummy.style.height = '100px';
                // 描画はしないが、矢印のターゲットとしてDOMに追加しておく
                container.appendChild(dummy);
                
                nodeEls[`s${{d.stage}}-endUX`] = dummy;
            }});

            // 3. 矢印描画
            data.forEach(d => {{
                d.arrows.forEach(a => {{
                    let srcEl = nodeEls[`s${{d.stage}}-n${{a.src_node_id}}`];
                    let tgtEl = null;

                    if (a.is_next) {{
                        // 次世代への接続
                        const nextStage = d.stage + 1;
                        
                        // UX(5)への接続の場合、それは「この世代のEnd UX」へつなぐ
                        if (a.tgt_node_id === 5) {{
                            tgtEl = nodeEls[`s${{d.stage}}-endUX`];
                        }} else if (nextStage <= 2) {{
                            // それ以外は次世代の通常のノードへ
                            tgtEl = nodeEls[`s${{nextStage}}-n${{a.tgt_node_id}}`];
                        }}
                    }} else {{
                        // 同世代内接続
                        tgtEl = nodeEls[`s${{d.stage}}-n${{a.tgt_node_id}}`];
                    }}

                    if (srcEl && tgtEl) {{
                        drawArrow(srcEl, tgtEl, a.label, a.definition, a.is_next);
                    }}
                }});
            }});
        }}

        function drawArrow(el1, el2, label, desc, isDashed) {{
            const x1 = parseFloat(el1.style.left) + 50;
            const y1 = parseFloat(el1.style.top) + 50;
            const x2 = parseFloat(el2.style.left) + 50;
            const y2 = parseFloat(el2.style.top) + 50;
            
            const dx = x2 - x1;
            const dy = y2 - y1;
            const dist = Math.sqrt(dx*dx + dy*dy);
            const angle = Math.atan2(dy, dx) * 180 / Math.PI;
            
            // 線 (Node半径50px分空ける)
            const pad = 50; 
            const realDist = Math.max(0, dist - (pad * 2));
            
            const line = document.createElement('div');
            line.className = isDashed ? 'arrow-line arrow-dashed' : 'arrow-line';
            line.style.width = realDist + 'px';
            
            const startX = x1 + (Math.cos(angle * Math.PI/180) * pad);
            const startY = y1 + (Math.sin(angle * Math.PI/180) * pad);
            
            line.style.left = startX + 'px';
            line.style.top = startY + 'px';
            line.style.transform = `rotate(${{angle}}deg)`;
            container.appendChild(line);
            
            // ラベル
            const lbl = document.createElement('div');
            lbl.className = 'arrow-label';
            lbl.textContent = label;
            lbl.dataset.desc = desc;
            
            const midX = (x1 + x2) / 2;
            const midY = (y1 + y2) / 2;
            lbl.style.left = midX + 'px';
            lbl.style.top = midY + 'px';
            
            lbl.onmouseenter = (e) => showTip(e, label, lbl.dataset.desc);
            lbl.onmousemove = moveTip;
            lbl.onmouseleave = hideTip;
            
            container.appendChild(lbl);
        }}

        function showTip(e, title, desc) {{
            if (!desc || desc === '...') return;
            tooltip.innerHTML = `<strong>${{title}}</strong><br>${{desc.substring(0, 200)}}...`;
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
    components.html(html_content, height=700, scrolling=True)