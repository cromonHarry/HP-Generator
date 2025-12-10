# visualization.py
import streamlit as st
import json
import streamlit.components.v1 as components
from prompt import HP_model

# HPモデルのトポロジー定義
HP_TOPOLOGY = {
    # Intra-generation
    16: (4, 1, False),
    9:  (1, 2, False),
    11: (3, 2, False),
    7:  (6, 3, False),
    8:  (1, 3, False),
    12: (3, 4, False),
    14: (4, 5, False),
    17: (5, 6, False),
    18: (5, 1, False),
    
    # Inter-generation (Next Generation)
    10: (6, 4, True),   # 制度 -> (次)技術
    13: (2, 5, True),   # 価値観 -> (次)UX
    15: (2, 6, True),   # 価値観 -> (次)制度
}

NODE_IDS = [1, 2, 3, 4, 5, 6]

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

        #  入力がない要素も描写する（完全なHPモデルの描写）
        # データがない場合は "（未定義）" または空文字を入れるが、ノード自体は生成する
        for nid in NODE_IDS:
            node_name = HP_model[nid]
            definition = raw_data.get(node_name, "...") # データがなくてもノード作成
            nodes.append({
                "type": node_name,
                "definition": definition
            })

        # 矢印構築
        for arrow_id, (src_id, tgt_id, is_inter) in HP_TOPOLOGY.items():
            arrow_name = HP_model[arrow_id]
            src_name = HP_model[src_id]
            tgt_name = HP_model[tgt_id]
            
            definition = raw_data.get(arrow_name, "")
            
            arrows.append({
                "type": arrow_name,
                "definition": definition,
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

    # (HTML/JS部分は既存のものを維持しつつ、ノードが必ず存在することを前提に動作)
    # ここでは既存コードの長いHTML文字列を再利用します。
    # 変更点: ノードのデータが空でもクリックできるようにする等はJS側でよしなに処理される
    
    html_content = f'''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: "Helvetica Neue", Arial, sans-serif; background-color: transparent; margin: 0; padding: 0; }}
        .vis-wrapper {{ overflow-x: auto; border: 1px solid #eee; border-radius: 8px; background: white; padding-bottom: 30px; }}
        .visualization {{ position: relative; width: 1450px; height: 680px; background: #fff; margin: 0 auto; }}
        
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
        
        /* Node Colors */
        .node-前衛的社会問題 {{ background: #ffb3b3; border-color: #ff8080; }}
        .node-人々の価値観 {{ background: #ffdfba; border-color: #ffb366; }}
        .node-社会問題 {{ background: #ffffba; border-color: #e6e600; }}
        .node-技術や資源 {{ background: #baffc9; border-color: #00cc44; }}
        .node-日常の空間とユーザー体験 {{ background: #bae1ff; border-color: #3399ff; }}
        .node-制度 {{ background: #e1baff; border-color: #9933ff; }}
        
        /* Empty Node Style (Optional) */
        .node[data-text="..."] {{ opacity: 0.6; border-style: dashed; }}

        .arrow {{ position: absolute; height: 2px; background: #999; transform-origin: left center; z-index: 1; pointer-events: none; }}
        .arrow::after {{
            content: ''; position: absolute; right: -8px; top: -4px;
            border-left: 8px solid #999; border-top: 4px solid transparent; border-bottom: 4px solid transparent;
        }}
        .dotted-arrow {{ border-top: 2px dashed #999; background: transparent; height: 0px; }}
        .dotted-arrow::after {{ border-left-color: #999; }}
        
        .arrow-label {{
            position: absolute; background: white; padding: 2px 8px;
            border: 1px solid #ccc; border-radius: 12px; font-size: 10px; color: #555;
            transform: translate(-50%, -50%); z-index: 5; cursor: help; white-space: nowrap;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .arrow-label:hover {{ background: #f9f9f9; color: #000; border-color: #888; z-index: 100; }}

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

        function getNodePosition(stageIdx, nodeType) {{
            const stageWidth = 460;
            const startX = 40;
            const offsetX = startX + (stageIdx * stageWidth);
            
            const yTop = 60;
            const yMid = 260;
            const yBot = 480;

            const xLeft = 20;
            const xMidLeft = 120;
            const xCenter = 205;
            const xMidRight = 290;
            const xRight = 370;

            if (stageIdx % 2 === 0) {{
                if (nodeType === '制度')                      return {{ x: offsetX + xCenter, y: yTop }};
                if (nodeType === '日常の空間とユーザー体験')  return {{ x: offsetX + xMidLeft, y: yMid }};
                if (nodeType === '社会問題')                  return {{ x: offsetX + xMidRight, y: yMid }};
                if (nodeType === '技術や資源')              return {{ x: offsetX + xLeft,  y: yBot }};
                if (nodeType === '前衛的社会問題')            return {{ x: offsetX + xCenter, y: yBot }};
                if (nodeType === '人々の価値観')              return {{ x: offsetX + xRight, y: yBot }};
            }} 
            else {{
                if (nodeType === '技術や資源')              return {{ x: offsetX + xLeft,  y: yTop }};
                if (nodeType === '前衛的社会問題')            return {{ x: offsetX + xCenter, y: yTop }};
                if (nodeType === '人々の価値観')              return {{ x: offsetX + xRight, y: yTop }};
                if (nodeType === '日常の空間とユーザー体験')  return {{ x: offsetX + xMidLeft, y: yMid }};
                if (nodeType === '社会問題')                  return {{ x: offsetX + xMidRight, y: yMid }};
                if (nodeType === '制度')                      return {{ x: offsetX + xCenter, y: yBot }};
            }}
            return null;
        }}

        function render() {{
            container.innerHTML = '';
            allNodes = {{}};
            
            ['Mt-1: 過去', 'Mt: 現在', 'Mt+1: 未来'].forEach((label, i) => {{
                const div = document.createElement('div');
                div.className = 'stage-label';
                div.innerText = label;
                div.style.left = (i * 460 + 170) + 'px';
                container.appendChild(div);
            }});

            data.forEach(d => {{
                d.ap_model.nodes.forEach(n => {{
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
                        allNodes[`s${{d.stage}}-${{n.type}}`] = el;
                    }}
                }});
            }});

            data.forEach((d, i) => {{
                const nextStage = data[i+1];
                
                d.ap_model.arrows.forEach(a => {{
                    let src = allNodes[`s${{d.stage}}-${{a.source}}`];
                    let tgt = allNodes[`s${{d.stage}}-${{a.target}}`];
                    
                    if (a.is_inter && nextStage) {{
                         tgt = allNodes[`s${{nextStage.stage}}-${{a.target}}`];
                    }}
                    
                    if (a.is_inter && !nextStage) return;

                    if (src && tgt) {{
                        drawArrow(src, tgt, a.type, a.definition, a.is_inter);
                    }}
                }});
            }});
        }}

        function drawArrow(n1, n2, labelText, content, isDashed) {{
            const x1 = parseFloat(n1.style.left) + 55;
            const y1 = parseFloat(n1.style.top) + 55;
            const x2 = parseFloat(n2.style.left) + 55;
            const y2 = parseFloat(n2.style.top) + 55;
            
            const dx = x2 - x1;
            const dy = y2 - y1;
            const dist = Math.sqrt(dx*dx + dy*dy);
            const angle = Math.atan2(dy, dx) * 180 / Math.PI;
            
            const pad = 55; 
            const len = Math.max(0, dist - pad * 2);
            
            const arrow = document.createElement('div');
            arrow.className = isDashed ? 'arrow dotted-arrow' : 'arrow';
            arrow.style.width = len + 'px';
            arrow.style.left = (x1 + (dx/dist)*pad) + 'px';
            arrow.style.top = (y1 + (dy/dist)*pad) + 'px';
            arrow.style.transform = `rotate(${{angle}}deg)`;
            container.appendChild(arrow);
            
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
    components.html(html_content, height=700, scrolling=True)