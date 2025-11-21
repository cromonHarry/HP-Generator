# visualization.py
import streamlit as st
import json
import streamlit.components.v1 as components
from prompt import HP_model

# HPモデルのトポロジー定義（PDF資料に基づく厳密な定義）
# Key: Arrow ID, Value: (Source Node ID, Target Node ID, Is_Inter_Generation)
# Is_Inter_Generation=True の場合は点線で次世代（Mt+1）に接続する
HP_TOPOLOGY = {
    # === 同世代 (Intra-generation / 実線) ===
    7:  (6, 3, False),  # メディア: 制度 -> 社会問題
    8:  (1, 3, False),  # コミュニティ化: 前衛的社会問題 -> 社会問題
    12: (3, 4, False),  # 組織化: 社会問題 -> 技術・資源
    14: (4, 5, False),  # 製品・サービス: 技術・資源 -> UX
    17: (5, 6, False),  # ビジネスエコシステム: UX -> 制度
    18: (5, 1, False),  # アート: UX -> 前衛的社会問題

    # === 次世代 (Inter-generation / 点線 / 時間的差異あり) ===
    9:  (1, 2, True),   # 文化芸術振興: 前衛的社会問題 -> (次)人々の価値観
    10: (6, 4, True),   # 標準化: 制度 -> (次)技術・資源
    11: (3, 2, True),   # コミュニケーション: 社会問題 -> (次)人々の価値観
    13: (2, 5, True),   # 意味付け: 人々の価値観 -> (次)UX
    15: (2, 6, True),   # 習慣化: 人々の価値観 -> (次)制度
    16: (4, 1, True)    # パラダイム: 技術・資源 -> (次)前衛的社会問題
}

NODE_IDS = [1, 2, 3, 4, 5, 6]

def transform_data_for_vis(hp_json: dict) -> list:
    """
    hp_jsonを可視化用に変換。トポロジー定義に基づき、
    同世代・次世代のフラグ(is_inter)を付与する。
    """
    stages = [
        {"key": "hp_mt_0", "stage_idx": 0}, # Mt-1: 過去
        {"key": "hp_mt_1", "stage_idx": 1}, # Mt: 現在
        {"key": "hp_mt_2", "stage_idx": 2}, # Mt+1: 未来
    ]
    
    vis_data = []

    for stage in stages:
        raw_data = hp_json.get(stage["key"], {})
        nodes = []
        arrows = []

        # 1. ノード構築
        for nid in NODE_IDS:
            node_name = HP_model[nid]
            if node_name in raw_data:
                nodes.append({
                    "type": node_name,
                    "definition": raw_data[node_name]
                })

        # 2. 矢印構築
        for arrow_id, (src_id, tgt_id, is_inter) in HP_TOPOLOGY.items():
            arrow_name = HP_model[arrow_id]
            src_name = HP_model[src_id]
            tgt_name = HP_model[tgt_id]
            
            if arrow_name in raw_data:
                arrows.append({
                    "type": arrow_name,
                    "definition": raw_data[arrow_name],
                    "source": src_name,
                    "target": tgt_name,
                    "is_inter": is_inter  # JS側で次世代への接続を判断するために使用
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
        st.warning("可視化するデータがありません。")
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
        /* コンテナ幅を少し広げて、各世代間の矢印を見やすくする */
        .visualization {{ position: relative; width: 1500px; height: 650px; background: #fff; margin: 0 auto; }}
        
        /* Node Styles */
        .node {{
            position: absolute; width: 110px; height: 110px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 12px; font-weight: bold; text-align: center;
            cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 3px 8px rgba(0,0,0,0.1); border: 3px solid #fff;
            padding: 5px; box-sizing: border-box; color: #444; z-index: 10;
            line-height: 1.3;
        }}
        .node:hover {{ transform: scale(1.1); z-index: 100; box-shadow: 0 6px 16px rgba(0,0,0,0.2); }}
        
        /* Node Colors (Pastel) */
        .node-前衛的社会問題 {{ background: #ffb3b3; border-color: #ff8080; }} /* Red-ish */
        .node-人々の価値観 {{ background: #ffdfba; border-color: #ffb366; }} /* Orange-ish */
        .node-社会問題 {{ background: #ffffba; border-color: #e6e600; }} /* Yellow-ish */
        .node-技術や資源 {{ background: #baffc9; border-color: #00cc44; }} /* Green-ish */
        .node-日常の空間とユーザー体験 {{ background: #bae1ff; border-color: #3399ff; }} /* Blue-ish */
        .node-制度 {{ background: #e1baff; border-color: #9933ff; }} /* Purple-ish */
        
        /* Arrow Styles */
        .arrow {{ position: absolute; height: 2px; background: #999; transform-origin: left center; z-index: 1; pointer-events: none; }}
        .arrow::after {{
            content: ''; position: absolute; right: -8px; top: -4px;
            border-left: 8px solid #999; border-top: 4px solid transparent; border-bottom: 4px solid transparent;
        }}
        /* Inter-generation arrows are dashed (Dotted in PDF terminology) */
        .dotted-arrow {{ border-top: 2px dashed #999; background: transparent; height: 0px; }}
        .dotted-arrow::after {{ border-left-color: #999; }}
        
        /* Arrow Label */
        .arrow-label {{
            position: absolute; background: white; padding: 2px 8px;
            border: 1px solid #ccc; border-radius: 12px; font-size: 10px; color: #555;
            transform: translate(-50%, -50%); z-index: 5; cursor: help; white-space: nowrap;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .arrow-label:hover {{ background: #f9f9f9; color: #000; border-color: #888; z-index: 100; }}

        /* Tooltip */
        .tooltip {{
            position: fixed; background: rgba(40, 40, 40, 0.95); color: #fff;
            padding: 12px 16px; border-radius: 6px; font-size: 13px; line-height: 1.6;
            max-width: 320px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            opacity: 0; pointer-events: none; transition: opacity 0.2s; z-index: 9999;
        }}
        .tooltip.show {{ opacity: 1; }}
        
        .stage-label {{
            position: absolute; bottom: 20px; font-size: 18px; font-weight: bold; color: #ccc; text-transform: uppercase;
            border-bottom: 3px solid #eee; padding-bottom: 5px; width: 200px; text-align: center;
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

        // === 座標計算ロジック ===
        // 3世代を左から右へ配置
        function getNodePosition(stageIdx, nodeType) {{
            const stageWidth = 480; // 世代間の幅
            const startX = 50;
            const offsetX = startX + (stageIdx * stageWidth);
            
            // Y座標 (Top, Middle, Bottom)
            const yTop = 50;
            const yMid = 270;
            const yBot = 490;

            // 各世代内のX相対座標
            // PDFの図のダイヤモンド型/六角形配置を意識
            const xLeft = 0;
            const xMidL = 100;
            const xCenter = 200;
            const xMidR = 300;
            const xRight = 400;

            // === レイアウト定義 ===
            // PDFの図を見ると、技術(左下)・UX(左上)・社会問題(右上)・制度(右下)のような配置が多いが
            // 世代間の接続を見やすくするため、標準的な六角形配置を採用します。
            
            // 偶数世代 (Mt-1, Mt+1)
            if (stageIdx % 2 === 0) {{
                if (nodeType === '日常の空間とユーザー体験') return {{ x: offsetX + xLeft,   y: yTop }}; // 左上
                if (nodeType === '技術や資源')              return {{ x: offsetX + xLeft,   y: yBot }}; // 左下
                if (nodeType === '前衛的社会問題')          return {{ x: offsetX + xCenter, y: yMid }}; // 中央 (または左中)
                if (nodeType === '制度')                    return {{ x: offsetX + xRight,  y: yBot }}; // 右下
                if (nodeType === '社会問題')                return {{ x: offsetX + xRight,  y: yTop }}; // 右上
                if (nodeType === '人々の価値観')            return {{ x: offsetX + xCenter + 160, y: yMid }}; // 最右
                
                // 調整: 前衛的社会問題は少し左寄りに
                if (nodeType === '前衛的社会問題')          return {{ x: offsetX + xMidL, y: yMid }};
            }} 
            // 奇数世代 (Mt: 現在) - 少しずらして重なり防止 & リズム感
            else {{
                if (nodeType === '日常の空間とユーザー体験') return {{ x: offsetX + xLeft,   y: yTop }};
                if (nodeType === '技術や資源')              return {{ x: offsetX + xLeft,   y: yBot }};
                if (nodeType === '前衛的社会問題')          return {{ x: offsetX + xMidL,   y: yMid }};
                if (nodeType === '社会問題')                return {{ x: offsetX + xRight,  y: yTop }};
                if (nodeType === '制度')                    return {{ x: offsetX + xRight,  y: yBot }};
                if (nodeType === '人々の価値観')            return {{ x: offsetX + xCenter + 160, y: yMid }};
            }}
            
            // デフォルト配置 (念のため)
            return {{ x: offsetX, y: yMid }};
        }}

        function render() {{
            container.innerHTML = '';
            allNodes = {{}};
            
            // 1. ステージラベル
            ['Mt-1: 過去', 'Mt: 現在', 'Mt+1: 未来'].forEach((label, i) => {{
                const div = document.createElement('div');
                div.className = 'stage-label';
                div.innerText = label;
                div.style.left = (i * 480 + 150) + 'px';
                container.appendChild(div);
            }});

            // 2. ノード描画
            data.forEach(d => {{
                d.ap_model.nodes.forEach(n => {{
                    const pos = getNodePosition(d.stage, n.type);
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
                    allNodes[`s${{d.stage}}-${{n.type}}`] = el;
                }});
            }});

            // 3. 矢印描画
            data.forEach((d, i) => {{
                const nextStage = data[i+1];
                
                d.ap_model.arrows.forEach(a => {{
                    let src = allNodes[`s${{d.stage}}-${{a.source}}`];
                    let tgt = allNodes[`s${{d.stage}}-${{a.target}}`];
                    
                    // === 重要: 世代間接続ロジック ===
                    // is_inter フラグが True の場合、強制的に次の世代のノードを探す
                    if (a.is_inter && nextStage) {{
                         tgt = allNodes[`s${{nextStage.stage}}-${{a.target}}`];
                    }}
                    
                    // 最後の世代で、さらに次へ行こうとする矢印は描画しない
                    if (a.is_inter && !nextStage) {{
                        return;
                    }}

                    if (src && tgt) {{
                        // is_inter が True なら点線 (Dotted/Dashed)
                        drawArrow(src, tgt, a.type, a.definition, a.is_inter);
                    }}
                }});
            }});
        }}

        function drawArrow(n1, n2, labelText, content, isDashed) {{
            const x1 = parseFloat(n1.style.left) + 55; // node center (110/2)
            const y1 = parseFloat(n1.style.top) + 55;
            const x2 = parseFloat(n2.style.left) + 55;
            const y2 = parseFloat(n2.style.top) + 55;
            
            const dx = x2 - x1;
            const dy = y2 - y1;
            const dist = Math.sqrt(dx*dx + dy*dy);
            const angle = Math.atan2(dy, dx) * 180 / Math.PI;
            
            const pad = 55; // node radius
            const len = Math.max(0, dist - pad * 2);
            
            const arrow = document.createElement('div');
            arrow.className = isDashed ? 'arrow dotted-arrow' : 'arrow';
            arrow.style.width = len + 'px';
            arrow.style.left = (x1 + (dx/dist)*pad) + 'px';
            arrow.style.top = (y1 + (dy/dist)*pad) + 'px';
            arrow.style.transform = `rotate(${{angle}}deg)`;
            container.appendChild(arrow);
            
            // Label
            const lbl = document.createElement('div');
            lbl.className = 'arrow-label';
            lbl.innerText = labelText;
            lbl.style.left = (x1 + dx/2) + 'px';
            lbl.style.top = (y1 + dy/2) + 'px';
            
            lbl.onmouseenter = (e) => showTip(e, labelText, content);
            lbl.onmousemove = moveTip;
            lbl.onmouseleave = hideTip;
            container.appendChild(lbl);
        }}

        function showTip(e, title, text) {{
            if (!text) return;
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
    
    # 正しいメソッドを使用
    components.html(html_content, height=700, scrolling=True)