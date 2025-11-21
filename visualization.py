# visualization.py
import streamlit as st
import json
import streamlit.components.v1 as components
from prompt import HP_model

# HP模型的拓扑结构定义
# Key: Arrow ID (from prompt.py), Value: (Source Node ID, Target Node ID)
HP_TOPOLOGY = {
    7: (6, 3),   # メディア: 制度 -> 社会問題
    8: (1, 3),   # コミュニティ化: 前衛的社会問題 -> 社会問題
    9: (1, 2),   # 文化芸術振興: 前衛的社会問題 -> 人々の価値観
    10: (6, 4),  # 標準化: 制度 -> 技術・資源 (Inter-stage)
    11: (3, 2),  # コミュニケーション: 社会問題 -> 人々の価値観
    12: (3, 4),  # 組織化: 社会問題 -> 技術・資源 (Inter-stage)
    13: (2, 5),  # 意味付け: 人々の価値観 -> UX (Inter-stage)
    14: (4, 5),  # 製品・サービス: 技術・資源 -> UX
    15: (2, 6),  # 習慣化: 人々の価値観 -> 制度 (Inter-stage)
    16: (4, 1),  # パラダイム: 技術・資源 -> 前衛的社会問題 (Inter-stage)
    17: (5, 6),  # ビジネスエコシステム: UX -> 制度
    18: (5, 1)   # アート: UX -> 前衛的社会問題
}

NODE_IDS = [1, 2, 3, 4, 5, 6]

def transform_data_for_vis(hp_json: dict) -> list:
    """
    将 hp_json 转换为可视化数据结构
    """
    stages = [
        {"key": "hp_mt_0", "stage_idx": 0}, # 过去
        {"key": "hp_mt_1", "stage_idx": 1}, # 现在
        {"key": "hp_mt_2", "stage_idx": 2}, # 未来
    ]
    
    vis_data = []

    for stage in stages:
        raw_data = hp_json.get(stage["key"], {})
        nodes = []
        arrows = []

        # 1. 构建节点
        for nid in NODE_IDS:
            node_name = HP_model[nid]
            # 即使内容为空，为了保持结构完整，最好也生成节点，但在UI中可以标记为空
            if node_name in raw_data:
                nodes.append({
                    "type": node_name,
                    "definition": raw_data[node_name]
                })

        # 2. 构建连线
        for arrow_id, (src_id, tgt_id) in HP_TOPOLOGY.items():
            arrow_name = HP_model[arrow_id]
            src_name = HP_model[src_id]
            tgt_name = HP_model[tgt_id]
            
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
        .vis-wrapper {{ overflow-x: auto; border: 1px solid #eee; border-radius: 8px; background: white; padding-bottom: 20px; }}
        .visualization {{ position: relative; width: 1400px; height: 600px; background: #fff; margin: 0 auto; }}
        
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
        .arrow {{ position: absolute; height: 1px; background: #bbb; transform-origin: left center; z-index: 1; pointer-events: none; }}
        .arrow::after {{
            content: ''; position: absolute; right: -6px; top: -3px;
            border-left: 6px solid #bbb; border-top: 3px solid transparent; border-bottom: 3px solid transparent;
        }}
        .dotted-arrow {{ border-top: 1px dashed #999; background: transparent; }}
        
        /* Arrow Label */
        .arrow-label {{
            position: absolute; background: white; padding: 2px 6px;
            border: 1px solid #eee; border-radius: 10px; font-size: 9px; color: #666;
            transform: translate(-50%, -50%); z-index: 10; cursor: help; white-space: nowrap;
        }}
        .arrow-label:hover {{ background: #f0f0f0; color: #000; border-color: #ccc; z-index: 100; }}

        /* Tooltip */
        .tooltip {{
            position: fixed; background: rgba(30, 30, 30, 0.95); color: #fff;
            padding: 10px 14px; border-radius: 6px; font-size: 12px; line-height: 1.5;
            max-width: 280px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            opacity: 0; pointer-events: none; transition: opacity 0.2s; z-index: 9999;
        }}
        .tooltip.show {{ opacity: 1; }}
        
        .stage-label {{
            position: absolute; bottom: 10px; font-size: 16px; font-weight: bold; color: #ddd; text-transform: uppercase;
            border-bottom: 2px solid #eee; padding-bottom: 5px;
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

        // Position Logic (Fixed Layout)
        function getNodePosition(stageIdx, nodeType) {{
            const stageWidth = 450; 
            const offsetX = stageIdx * stageWidth;
            
            // Y Levels
            const yTop = 80;
            const yMid = 280;
            const yBot = 480;

            // Relative X within a stage (0 to 450)
            const xLeft = 30;
            const xMidL = 130;
            const xCenter = 225;
            const xMidR = 320;
            const xRight = 400;

            // Layout Pattern (Alternating to reduce overlaps)
            if (stageIdx % 2 === 0) {{ 
                // Even Stages (0, 2): Inst/Adv Centered
                if (nodeType === '制度') return {{ x: offsetX + xCenter, y: yTop }};
                if (nodeType === '日常の空間とユーザー体験') return {{ x: offsetX + xMidL, y: yMid }};
                if (nodeType === '社会問題') return {{ x: offsetX + xMidR, y: yMid }};
                if (nodeType === '技術や資源') return {{ x: offsetX + xLeft, y: yBot }};
                if (nodeType === '前衛的社会問題') return {{ x: offsetX + xCenter, y: yBot }};
                if (nodeType === '人々の価値観') return {{ x: offsetX + xRight, y: yBot }};
            }} else {{
                // Odd Stages (1): Inverted Y for some variety & easier connection
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
            
            // 1. Render Stage Labels
            ['Mt-1: 過去', 'Mt: 現在', 'Mt+1: 未来'].forEach((label, i) => {{
                const div = document.createElement('div');
                div.className = 'stage-label';
                div.innerText = label;
                div.style.left = (i * 450 + 180) + 'px';
                container.appendChild(div);
            }});

            // 2. Render Nodes FIRST (to populate allNodes)
            data.forEach(d => {{
                d.ap_model.nodes.forEach(n => {{
                    const pos = getNodePosition(d.stage, n.type);
                    if(pos) {{
                        const el = document.createElement('div');
                        el.className = `node node-${{n.type}}`;
                        el.style.left = pos.x + 'px';
                        el.style.top = pos.y + 'px';
                        el.textContent = n.type;
                        // Save definition for tooltip
                        el.dataset.text = n.definition || '';
                        
                        el.onmouseenter = (e) => showTip(e, n.type, el.dataset.text);
                        el.onmousemove = moveTip;
                        el.onmouseleave = hideTip;
                        
                        container.appendChild(el);
                        allNodes[`s${{d.stage}}-${{n.type}}`] = el;
                    }}
                }});
            }});

            // 3. Render Arrows (Logic Fix for Inter-stage)
            data.forEach((d, i) => {{
                const nextStage = data[i+1]; // define next stage object
                
                d.ap_model.arrows.forEach(a => {{
                    let src = allNodes[`s${{d.stage}}-${{a.source}}`];
                    let tgt = allNodes[`s${{d.stage}}-${{a.target}}`];
                    
                    // --- CRITICAL: Inter-stage Connection Logic ---
                    // This logic redirects the arrow target to the NEXT stage 
                    // for specific evolution arrows.
                    let isInter = false;
                    
                    if (nextStage) {{
                        // Paradigm: Tech (Current) -> Avant-garde (Next)
                        if (a.type === 'パラダイム') {{
                            tgt = allNodes[`s${{nextStage.stage}}-前衛的社会問題`];
                            isInter = true;
                        }}
                        // Standardization: Inst (Current) -> Tech (Next)
                        else if (a.type === '標準化') {{
                            tgt = allNodes[`s${{nextStage.stage}}-技術や資源`];
                            isInter = true;
                        }}
                        // Organization: SocProb (Current) -> Tech (Next)
                        else if (a.type === '組織化') {{
                            tgt = allNodes[`s${{nextStage.stage}}-技術や資源`];
                            isInter = true;
                        }}
                        // Meaning: Values (Current) -> UX (Next)
                        else if (a.type === '意味付け') {{
                            tgt = allNodes[`s${{nextStage.stage}}-日常の空間とユーザー体験`];
                            isInter = true;
                        }}
                        // Habituation: Values (Current) -> Institution (Next)
                        else if (a.type === '習慣化') {{
                            tgt = allNodes[`s${{nextStage.stage}}-制度`];
                            isInter = true;
                        }}
                    }}

                    // If it's the last stage, do not draw arrows that need a next stage
                    if (isInter && !nextStage) {{
                        return; 
                    }}

                    // Draw arrow if both ends exist
                    if (src && tgt) {{
                        const isDotted = ['アート(社会批評)', 'アート（社会批評）', 'メディア'].includes(a.type);
                        drawArrow(src, tgt, a.type, a.definition, isDotted);
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
            
            // Radius of node is 50px
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
            // Label position: 50% for normal, specialized for long arrows? No, 50% is fine.
            lbl.style.left = (x1 + dx/2) + 'px';
            lbl.style.top = (y1 + dy/2) + 'px';
            
            lbl.onmouseenter = (e) => showTip(e, labelText, content);
            lbl.onmousemove = moveTip;
            lbl.onmouseleave = hideTip;
            container.appendChild(lbl);
        }}

        function showTip(e, title, text) {{
            if (!text) return;
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
    
    # Fix for attribute error (v1.html -> html)
    components.html(html_content, height=650, scrolling=True)