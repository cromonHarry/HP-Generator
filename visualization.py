# visualization.py
import streamlit as st
import json
import streamlit.components.v1 as components
from prompt import HP_model

# HP模型的拓扑结构定义
# Key: Arrow ID (from prompt.py), Value: (Source Node ID, Target Node ID)
# 这里的ID对应 prompt.py 中的 HP_model keys
HP_TOPOLOGY = {
    7: (6, 3),   # メディア: 制度 -> 社会問題
    8: (1, 3),   # コミュニティ化: 前衛的社会問題 -> 社会問題
    9: (1, 2),   # 文化芸術振興: 前衛的社会問題 -> 人々の価値観
    10: (6, 4),  # 標準化: 制度 -> 技術・資源
    11: (3, 2),  # コミュニケーション: 社会問題 -> 人々の価値観
    12: (3, 4),  # 組織化: 社会問題 -> 技術・資源
    13: (2, 5),  # 意味付け: 人々の価値観 -> UX
    14: (4, 5),  # 製品・サービス: 技術・資源 -> UX
    15: (2, 6),  # 習慣化: 人々の価値観 -> 制度
    16: (4, 1),  # パラダイム: 技術・資源 -> 前衛的社会問題
    17: (5, 6),  # ビジネスエコシステム: UX -> 制度
    18: (5, 1)   # アート: UX -> 前衛的社会問題
}

# 节点ID列表 (1-6)
NODE_IDS = [1, 2, 3, 4, 5, 6]

def transform_data_for_vis(hp_json: dict) -> list:
    """
    将 hp_json (扁平字典) 转换为可视化所需的 Nodes/Arrows 结构列表。
    """
    stages = [
        {"key": "hp_mt_0", "stage_idx": 0},
        {"key": "hp_mt_1", "stage_idx": 1},
        {"key": "hp_mt_2", "stage_idx": 2},
    ]
    
    vis_data = []

    for stage in stages:
        raw_data = hp_json.get(stage["key"], {})
        nodes = []
        arrows = []

        # 1. 构建节点
        for nid in NODE_IDS:
            node_name = HP_model[nid]
            if node_name in raw_data:
                nodes.append({
                    "type": node_name,
                    "definition": raw_data[node_name]
                })

        # 2. 构建连线 (Arrows)
        for arrow_id, (src_id, tgt_id) in HP_TOPOLOGY.items():
            arrow_name = HP_model[arrow_id]
            src_name = HP_model[src_id]
            tgt_name = HP_model[tgt_id]
            
            # 只有当该层数据中包含这个 Arrow 的内容时才画线
            if arrow_name in raw_data:
                arrows.append({
                    "type": arrow_name,
                    "definition": raw_data[arrow_name],
                    "source": src_name,
                    "target": tgt_name
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
    """
    在 Streamlit 中渲染 HP 模型可视化组件
    """
    if not hp_json:
        st.warning("可視化するデータがありません。")
        return

    # 数据转换
    vis_data_list = transform_data_for_vis(hp_json)
    json_str = json.dumps(vis_data_list, ensure_ascii=False)

    # HTML/JS 模板 (基于你提供的代码，适配了容器大小)
    html_content = f'''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: "Helvetica Neue", Arial, sans-serif; background-color: transparent; margin: 0; padding: 0; }}
        .vis-wrapper {{ overflow-x: auto; border: 1px solid #eee; border-radius: 8px; background: white; padding-bottom: 10px; }}
        .visualization {{ position: relative; width: 1350px; height: 600px; background: #fff; margin: 0 auto; }}
        
        /* Node Styles */
        .node {{
            position: absolute; width: 100px; height: 100px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; font-weight: bold; text-align: center;
            cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1); border: 2px solid #fff;
            padding: 8px; box-sizing: border-box; color: #333; z-index: 5;
        }}
        .node:hover {{ transform: scale(1.1); z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }}
        
        /* Node Colors */
        .node-前衛的社会問題 {{ background: #ffcccc; border-color: #ff9999; }}
        .node-人々の価値観 {{ background: #ffe6cc; border-color: #ffcc99; }}
        .node-社会問題 {{ background: #ffffcc; border-color: #ffff99; }}
        .node-技術や資源 {{ background: #ccffcc; border-color: #99cc99; }}
        .node-日常の空間とユーザー体験 {{ background: #ccffff; border-color: #99cccc; }}
        .node-制度 {{ background: #e6ccff; border-color: #cc99ff; }}
        
        /* Arrow Styles */
        .arrow {{ position: absolute; height: 1px; background: #999; transform-origin: left center; z-index: 1; pointer-events: none; }}
        .arrow::after {{
            content: ''; position: absolute; right: -6px; top: -3px;
            border-left: 6px solid #999; border-top: 3px solid transparent; border-bottom: 3px solid transparent;
        }}
        .dotted-arrow {{ border-top: 1px dashed #999; background: transparent; }}
        
        /* Arrow Label */
        .arrow-label {{
            position: absolute; background: white; padding: 1px 6px;
            border: 1px solid #eee; border-radius: 10px; font-size: 9px; color: #666;
            transform: translate(-50%, -50%); z-index: 10; cursor: help; white-space: nowrap;
        }}
        .arrow-label:hover {{ background: #f0f0f0; color: #000; border-color: #ccc; }}

        /* Tooltip */
        .tooltip {{
            position: fixed; background: rgba(30, 30, 30, 0.95); color: #fff;
            padding: 10px 14px; border-radius: 6px; font-size: 12px; line-height: 1.5;
            max-width: 280px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            opacity: 0; pointer-events: none; transition: opacity 0.2s; z-index: 9999;
        }}
        .tooltip.show {{ opacity: 1; }}
        .stage-label {{
            position: absolute; bottom: 10px; font-size: 14px; font-weight: bold; color: #ccc; text-transform: uppercase;
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

        // Position Logic
        function getNodePosition(stageIdx, nodeType) {{
            const stageWidth = 420; 
            const startX = 40;
            const offsetX = stageIdx * stageWidth;
            
            // Y Levels
            const yTop = 60;
            const yMid = 260;
            const yBot = 460;

            // Relative X in a stage
            const xLeft = 20;
            const xMidL = 120;
            const xCenter = 200;
            const xMidR = 280;
            const xRight = 360;

            // Odd/Even stage inversion logic (Optional, keeping simple layout for now)
            // Mt-1 (0), Mt (1), Mt+1 (2)
            
            // Default layout pattern
            if (stageIdx % 2 === 0) {{ 
                // 0 & 2: Top=Inst, Bot=Adv
                if (nodeType === '制度') return {{ x: offsetX + xCenter, y: yTop }};
                if (nodeType === '日常の空間とユーザー体験') return {{ x: offsetX + xMidL, y: yMid }};
                if (nodeType === '社会問題') return {{ x: offsetX + xMidR, y: yMid }};
                if (nodeType === '技術や資源') return {{ x: offsetX + xLeft, y: yBot }};
                if (nodeType === '前衛的社会問題') return {{ x: offsetX + xCenter, y: yBot }};
                if (nodeType === '人々の価値観') return {{ x: offsetX + xRight, y: yBot }};
            }} else {{
                // 1: Inverted (Top=Adv, Bot=Inst)
                if (nodeType === '技術や資源') return {{ x: offsetX + xLeft, y: yTop }};
                if (nodeType === '前衛的社会問題') return {{ x: offsetX + xCenter, y: yTop }};
                if (nodeType === '人々の価値観') return {{ x: offsetX + xRight, y: yTop }};
                if (nodeType === '日常の空間とユーザー体験') return {{ x: offsetX + xMidL, y: yMid }};
                if (nodeType === '社会問題') return {{ x: offsetX + xMidR, y: yMid }};
                if (nodeType === '制度') return {{ x: offsetX + xCenter, y: yBot }};
            }}
            return null;
        }}

        function render() {{
            container.innerHTML = '';
            allNodes = {{}};
            
            // 1. Render Stage Labels (Optional Background)
            ['Mt-1: 過去', 'Mt: 現在', 'Mt+1: 未来'].forEach((label, i) => {{
                const div = document.createElement('div');
                div.className = 'stage-label';
                div.innerText = label;
                div.style.left = (i * 420 + 180) + 'px';
                container.appendChild(div);
            }});

            // 2. Render Nodes
            data.forEach(d => {{
                d.ap_model.nodes.forEach(n => {{
                    const pos = getNodePosition(d.stage, n.type);
                    if(pos) {{
                        const el = document.createElement('div');
                        el.className = `node node-${{n.type}}`;
                        el.style.left = pos.x + 'px';
                        el.style.top = pos.y + 'px';
                        el.textContent = n.type;
                        el.dataset.text = n.definition;
                        
                        el.onmouseenter = (e) => showTip(e, n.type, n.definition);
                        el.onmousemove = moveTip;
                        el.onmouseleave = hideTip;
                        
                        container.appendChild(el);
                        allNodes[`s${{d.stage}}-${{n.type}}`] = el;
                    }}
                }});
            }});

            // 3. Render Arrows
            data.forEach((d, i) => {{
                const nextStage = data[i+1];
                d.ap_model.arrows.forEach(a => {{
                    let src = allNodes[`s${{d.stage}}-${{a.source}}`];
                    let tgt = allNodes[`s${{d.stage}}-${{a.target}}`];
                    
                    // Inter-stage connections logic
                    // Some arrows jump to the next stage (e.g., Standardization -> Tech of next stage)
                    let isInter = false;
                    if (nextStage) {{
                        if (['標準化', '組織化'].includes(a.type)) {{
                            tgt = allNodes[`s${{nextStage.stage}}-技術や資源`]; isInter = true;
                        }} else if (a.type === '意味付け') {{
                            tgt = allNodes[`s${{nextStage.stage}}-日常の空間とユーザー体験`]; isInter = true;
                        }} else if (a.type === '習慣化') {{
                            tgt = allNodes[`s${{nextStage.stage}}-制度`]; isInter = true;
                        }}
                    }}
                    
                    // Draw if both endpoints exist
                    if (src && tgt) {{
                        drawArrow(src, tgt, a.type, a.definition, a.type.includes('アート') || a.type.includes('メディア'));
                    }}
                }});
            }});
        }}

        function drawArrow(n1, n2, labelText, content, isDotted) {{
            const x1 = parseFloat(n1.style.left) + 50;
            const y1 = parseFloat(n1.style.top) + 50;
            const x2 = parseFloat(n2.style.left) + 50;
            const y2 = parseFloat(n2.style.top) + 50;
            
            const dx = x2 - x1;
            const dy = y2 - y1;
            const dist = Math.sqrt(dx*dx + dy*dy);
            const angle = Math.atan2(dy, dx) * 180 / Math.PI;
            
            // Shorten line to stop at circle edge (radius ~50)
            const pad = 50;
            const len = Math.max(0, dist - pad * 2);
            
            const arrow = document.createElement('div');
            arrow.className = isDotted ? 'arrow dotted-arrow' : 'arrow';
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
            tooltip.innerHTML = `<strong>${{title}}</strong><br>${{text.substring(0, 150)}}...`;
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
    components.html(html_content, height=630, scrolling=True)