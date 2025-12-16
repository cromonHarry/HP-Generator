import concurrent.futures
from utils import parse_json_response
from prompt import client, SYSTEM_PROMPT 

class AgentManager:
    def __init__(self):
        self.client = client
        self.agents = []

    def generate_agents(self, topic: str) -> list:
        """
        基于话题生成 3 个不同的专家 Agent。
        """
        prompt = f"""
テーマ「{topic}」に関するHPモデル（アーキオロジカル・プロトタイピング）の要素を生成するために、全く異なる3人の専門家エージェントを生成してください。
各エージェントは異なる視点と専門知識を持ち、未来（Mt+1）に対して創造的かつ革新的な予測を提供できる必要があります。
以下のJSON形式で出力してください：
{{ "agents": [ {{ "name": "エージェント名", "expertise": "専門分野", "personality": "性格/特徴", "perspective": "独自の視点" }} ] }}
"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            temperature=1.0,
            response_format={"type": "json_object"}
        )
        result = parse_json_response(response.choices[0].message.content)
        self.agents = result.get("agents", [])
        return self.agents

    def _agent_think(self, agent, element_type, context_str, history):
        """单个 Agent 生成提案 - 50字以内限制"""
        history_text = "\n".join([f"- {h}" for h in history]) if history else "なし"
        
        prompt = f"""
あなたは{agent['name']}です（専門：{agent['expertise']}）。
{agent['perspective']}の視点で、未来（Mt+1）の要素「{element_type}」を予測してください。

## 文脈
{context_str}

## 過去の提案
{history_text}

【重要：出力ルール】
1. **50文字以内**で出力してください。これは絶対条件です。
2. 「未来の社会問題としては…」等の前置きは一切禁止です。体言止めなどで簡潔に。
3. HPモデルの定義説明は不要です。
4. 予測される**「現象」「状態」のみ**をズバリ書いてください。

【出力例】
（悪い）：未来の社会ではAIが発達し、人間が労働から解放されることで、生きがいを喪失する問題。（45文字）
（良い）：AIによる労働解放が招く「全人類的虚無感」と「生きがい喪失」。（30文字）

あなたの予測（テキストのみ、日本語、50文字以内）：
"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            temperature=1.2 # 高创造性
        )
        return response.choices[0].message.content.strip()

    def _judge_proposals(self, proposals, element_type, topic):
        """裁判选择最佳提案"""
        proposals_text = "\n".join([f"提案 {i+1} ({p['agent']}): {p['content']}" for i, p in enumerate(proposals)])
        prompt = f"""
トピック: {topic}
要素: {element_type} (未来 Mt+1)

以下の提案を評価してください。
{proposals_text}

最も創造的かつ簡潔な提案を1つ選択してください。
以下のJSON形式で出力してください:
{{ "selected_agent": "エージェント名", "selected_content": "提案内容（そのまま）", "reason": "選定理由（日本語）" }}
"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return parse_json_response(response.choices[0].message.content)

    def run_multi_agent_generation(self, element_type, element_desc, topic, full_context_str) -> list[str]:
        """
        运行 3 轮迭代
        """
        if not self.agents:
            self.generate_agents(topic)

        candidates = []
        agent_history = {agent['name']: [] for agent in self.agents}

        for i in range(1, 4):
            proposals = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_to_agent = {
                    executor.submit(self._agent_think, agent, f"{element_type} ({element_desc})", full_context_str, agent_history[agent['name']]): agent 
                    for agent in self.agents
                }
                for future in concurrent.futures.as_completed(future_to_agent):
                    agent = future_to_agent[future]
                    try:
                        content = future.result()
                        proposals.append({"agent": agent['name'], "content": content})
                        agent_history[agent['name']].append(content)
                    except Exception as e:
                        print(f"Agent failed: {e}")

            if not proposals:
                continue

            judgment = self._judge_proposals(proposals, element_type, topic)
            winner_content = judgment.get('selected_content', "")
            if winner_content:
                candidates.append(winner_content)

        return candidates if candidates else ["生成失敗"]