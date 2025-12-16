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
        """单个 Agent 生成提案 - 已改良Prompt以去除废话"""
        history_text = "\n".join([f"- {h}" for h in history]) if history else "なし"
        
        # 改良后的 Prompt：增加“禁止事项”和“出力例”
        prompt = f"""
あなたは{agent['name']}です（専門：{agent['expertise']}）。
{agent['perspective']}の視点で、未来（Mt+1）の要素「{element_type}」を具体的に予測してください。

## 文脈
{context_str}

## 過去の提案（重複回避）
{history_text}

【重要：出力ルール】
1. **前置きは一切禁止**です。「未来の社会問題としては…」「…と考えられます」などの導入句は書かないでください。
2. HPモデルの定義説明（「前衛的社会問題とは…」）も不要です。
3. 予測される**「現象」「状態」「光景」そのもの**を、断定的に、かつ具体的に書き出してください。
4. 読者がその未来の情景を鮮明にイメージできるようなテキストにしてください。

【出力例】
（悪い例）：未来の前衛的社会問題としては、AIによる支配が考えられます。これは…
（良い例）：自律型AIが司法判断の9割を代行するようになり、人間の感情が法廷から排除されたことで生じる「計算された非人道的な正義」。

あなたの予測内容（テキストのみ、100文字〜150文字程度）を出力してください：
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

以下の提案を、創造性（最重要）、HPモデルとの整合性、論理的接続性に基づいて評価してください。
{proposals_text}

最も優れた提案を1つ選択してください。
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
        运行 3 轮迭代，返回 3 个最佳候选方案列表供用户选择。
        """
        # 1. 雇佣专家
        if not self.agents:
            self.generate_agents(topic)

        candidates = []
        agent_history = {agent['name']: [] for agent in self.agents}

        # 2. 运行 3 轮迭代 (Iterations)
        for i in range(1, 4):
            # 并行生成
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

            # 裁判评选本轮最佳
            judgment = self._judge_proposals(proposals, element_type, topic)
            winner_content = judgment.get('selected_content', "")
            if winner_content:
                candidates.append(winner_content)

        return candidates if candidates else ["生成に失敗しました。再試行してください。"]