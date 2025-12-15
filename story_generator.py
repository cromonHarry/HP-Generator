import json
from prompt import SYSTEM_PROMPT, client
from utils import parse_json_response

# 仅供写作 Agent 使用的创意 Prompt (日语版)
CREATIVE_SYSTEM_PROMPT = "あなたは受賞歴のあるSF作家兼編集者です。詳細な社会学データ（HPモデル）に基づき、説得力があり、論理的かつ創造的な物語を作成することを目標としています。"

class StoryGenerator:
    def __init__(self):
        self.client = client

    # ==========================================
    # 0. Global Overseer: Briefing Director
    # ==========================================
    def _overseer_prepare_brief(self, full_ap_data, target_type):
        """
        Overseer (Director) 准备简报。
        """
        ap_context_str = json.dumps(full_ap_data, indent=2, ensure_ascii=False)

        if target_type == "setting":
            focus_instruction = "世界観構築（World Building）に関連する静的な要素（技術、日常空間、制度、雰囲気など）のみを抽出してください。"
        else:
            focus_instruction = "プロットと対立（Plot & Conflict）に関連する動的な要素（社会問題、メディア、アート、前衛的運動、変化を引き起こす矢印など）のみを抽出してください。"

        prompt = f"""
あなたは**総監督（Global Overseer）**です。あなたは完全な社会モデル（HPモデル）を保持しています。
あなたの任務は、SF小説を完成させるために、エージェントに必要な情報を与えることです。

## マスターファイル（HPモデル）
{ap_context_str}

## タスク
{target_type} エージェントのための **コンセプト・ブリーフ（指示書）** を作成してください。
{focus_instruction}

## 出力形式 (JSON)
{{
    "briefing_theme": "短いテーマタイトル",
    "relevant_data_points": "このエージェントが注目すべき具体的なHPモデルの要素（ノード/矢印）の要約。すべてを含めず、関連するものだけを記述すること。"
}}
"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.5 
        )
        return parse_json_response(response.choices[0].message.content)


    # ==========================================
    # 1. Global Overseer: The Critic
    # ==========================================
    def _global_check(self, content_type, content_data, context_data, full_ap_data, specific_criteria):
        """
        Global Agent 审核内容，确保符合 HP 模型。
        """
        ap_master_str = json.dumps(full_ap_data, indent=2, ensure_ascii=False)

        prompt = f"""
あなたは厳格な**総監督（Global Overseer）**です。
あなたの仕事は、生成されたコンテンツがHPモデルの論理および具体的な指示（ブリーフ）に従っているかを確認することです。

## 資料1：マスター社会モデル（正解データ）
{ap_master_str}

## 資料2：エージェントへの指示（ブリーフ）
{context_data}

## 審査基準
{specific_criteria}

## 審査対象コンテンツ ({content_type})
{json.dumps(content_data, indent=2, ensure_ascii=False)}

## 出力形式 (JSON)
{{
    "approved": true/false,
    "feedback": "承認(true)の場合は空欄。拒否(false)の場合は、HPモデルやブリーフとの矛盾点を具体的に指摘し、修正方法を助言してください。"
}}
"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        return parse_json_response(response.choices[0].message.content)

    # ==========================================
    # 2. Setting Agent (World & Characters)
    # ==========================================
    def _agent_build_settings(self, setting_brief, feedback=""):
        brief_str = json.dumps(setting_brief, indent=2, ensure_ascii=False)

        prompt = f"""
あなたは**設定制作エージェント（Setting Agent）**です。SF小説のための魅力的で創造的な世界設定とキャラクターをデザインしてください。

## 総監督からのブリーフ（基盤情報）
{brief_str}

## 指示
このブリーフを統合し、生き生きとした世界を作り上げてください。

1. **世界観 (World View)**: 年代、雰囲気、技術レベル、社会の機能などを詳細に記述してください。
2. **キャラクター (Characters)**: この世界に住む主要なキャラクターを作成してください。名前、役割、背景、動機を設定してください。

## 以前のフィードバック（ある場合、必ず修正すること）
{feedback}

## 出力形式 (JSON)
{{
    "world_view": "世界観の詳細な記述",
    "characters": [
        {{ "name": "名前", "role": "役割", "background": "背景", "motivation": "動機" }}
    ]
}}
"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": CREATIVE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return parse_json_response(response.choices[0].message.content)

    # ==========================================
    # 3. Outline Agent (Plot Architect)
    # ==========================================
    def _agent_build_outline_step(self, step_name, step_goal, settings, plot_brief, current_outline_history, feedback=""):
        history_text = "\n".join([f"{k}: {v['summary']}" for k, v in current_outline_history.items()])
        settings_str = json.dumps(settings, indent=2, ensure_ascii=False)
        brief_str = json.dumps(plot_brief, indent=2, ensure_ascii=False)
        
        prompt = f"""
あなたは**プロット構成エージェント（Outline Agent）**です。物語の **{step_name}** 部分を作成してください。

## 物語の設定
{settings_str}

## 総監督のプロット指示
以下の要素を使ってプロットイベントを推進してください：
{brief_str}

## 現在のプロット履歴（これまでの出来事）
{history_text if history_text else "ここから物語が始まります。"}

## このステップの目標
{step_goal}

## 以前のフィードバック（ある場合、修正してください）
{feedback}

## 出力形式 (JSON)
{{
    "title": "シーンのタイトル",
    "summary": "何が起こるかの詳細な説明（約150〜300文字）。キャラクターの行動とプロットの進行に焦点を当ててください。",
    "notes": "監督のブリーフとどのように関連しているかのメモ。"
}}
"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": CREATIVE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return parse_json_response(response.choices[0].message.content)

    # ==========================================
    # 4. Main Workflow Orchestrator
    # ==========================================
    def generate_story_outline(self, ap_data_dict: dict) -> str:
        # --- PHASE 0: Director prepares Briefs ---
        setting_brief = self._overseer_prepare_brief(ap_data_dict, "setting")

        # --- PHASE 1: Build & Verify Settings ---
        settings = None
        feedback = ""
        max_retries = 2 # 試行回数
        
        for i in range(max_retries + 1):
            settings = self._agent_build_settings(setting_brief, feedback)
            
            criteria = "「世界観」と「キャラクター」が、提供された監督のブリーフを論理的に反映しており、かつマスターHPモデルと矛盾していないか確認してください。"
            context_data = json.dumps(setting_brief, ensure_ascii=False)
            
            review = self._global_check("Story Settings", settings, context_data, ap_data_dict, criteria)
            
            if review.get('approved'):
                break
            else:
                feedback = review.get('feedback', '')
        
        if not settings:
             return "エラー: 設定の生成に失敗しました。"

        # --- PHASE 0.5: Director prepares Plot Brief ---
        plot_brief = self._overseer_prepare_brief(ap_data_dict, "outline")

        # --- PHASE 2: Build Outline Step-by-Step ---
        steps_config = [
            {"name": "1. Inciting Incident (発端)", "goal": "物語は設定の中で始まり、キャラクターと舞台が紹介されます。"},
            {"name": "2. Rising Action (葛藤)", "goal": "事件や対立が導入され、キャラクターは一連の課題や紛争に直面し始めます。緊張が高まります。"},
            {"name": "3. Climax (クライマックス)", "goal": "物語の最も盛り上がる瞬間、または転換点です。"},
            {"name": "4. Resolution (結末)", "goal": "物語の結末です。"}
        ]

        final_outline_steps = {}

        for step in steps_config:
            step_content = None
            feedback = ""
            
            for i in range(max_retries + 1):
                step_content = self._agent_build_outline_step(
                    step['name'], 
                    step['goal'], 
                    settings, 
                    plot_brief,
                    final_outline_steps, 
                    feedback
                )
                
                context_for_review = f"""
                PLOT BRIEF: {json.dumps(plot_brief, ensure_ascii=False)}
                PREVIOUS PLOT: {json.dumps(final_outline_steps, ensure_ascii=False)}
                """
                criteria = "一貫性チェック: このプロットステップは監督のプロット指示に従っており、かつマスターHPモデルと整合性が取れていますか？"
                
                review = self._global_check(step['name'], step_content, context_for_review, ap_data_dict, criteria)
                
                if review.get('approved'):
                    final_outline_steps[step['name']] = step_content
                    break
                else:
                    feedback = review.get('feedback', '')
            
            if step['name'] not in final_outline_steps:
                 final_outline_steps[step['name']] = step_content

        # --- PHASE 3: Compile Final Output ---
        chars_text = ""
        for c in settings.get('characters', []):
            chars_text += f"* **{c.get('name', '不明')}** ({c.get('role', 'N/A')}): {c.get('motivation', 'N/A')}\n"

        raw_conflict = plot_brief.get('relevant_data_points', "N/A")
        if isinstance(raw_conflict, list):
            conflict_str = ", ".join([str(x) for x in raw_conflict])
        else:
            conflict_str = str(raw_conflict)
            
        full_text = f"""# SFストーリー概要 (Generated by Multi-Agent)

## 1. 世界観とキャラクター
**テーマ:** {setting_brief.get('briefing_theme', 'N/A')}

**世界観:**
{settings.get('world_view', 'N/A')}

**主要キャラクター:**
{chars_text}

## 2. プロットアウトライン
**対立の源:** {conflict_str[:300]}...

### I. 発端 (Inciting Incident)
**タイトル:** {final_outline_steps.get('1. Inciting Incident (発端)', {}).get('title', 'N/A')}
{final_outline_steps.get('1. Inciting Incident (発端)', {}).get('summary', 'N/A')}

### II. 葛藤 (Rising Action)
**タイトル:** {final_outline_steps.get('2. Rising Action (葛藤)', {}).get('title', 'N/A')}
{final_outline_steps.get('2. Rising Action (葛藤)', {}).get('summary', 'N/A')}

### III. クライマックス (Climax)
**タイトル:** {final_outline_steps.get('3. Climax (クライマックス)', {}).get('title', 'N/A')}
{final_outline_steps.get('3. Climax (クライマックス)', {}).get('summary', 'N/A')}

### IV. 結末 (Resolution)
**タイトル:** {final_outline_steps.get('4. Resolution (結末)', {}).get('title', 'N/A')}
{final_outline_steps.get('4. Resolution (結末)', {}).get('summary', 'N/A')}
"""
        return full_text