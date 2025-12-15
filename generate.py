# generate.py
import json
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, List, Optional

from prompt import (
    HP_model,
    single_gpt,
    list_up_gpt,
    generate_question_for_tavily,
    tavily_generate_answer,
)
from agent_manager import AgentManager  # Import Multi-Agent Manager

class HPGenerationSession:
    def __init__(self, max_workers: int = 8):
        self.hp_mt_0: Dict[str, str] = {}  # Mt-1 (過去)
        self.hp_mt_1: Dict[str, str] = {}  # Mt (現在)
        self.hp_mt_2: Dict[str, str] = {}  # Mt+1 (未来)

        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.all_futures: List[Future] = []
        
        self.user_inputs = {
            "q1_ux": "",
            "q2_product": "",
            "q3_meaning": "",
            "q4_value": ""
        }

        self.future_candidates_adv: Optional[Future] = None
        
        self.mtplus1_candidates = {
            "goals": [],
            "values": [],
            "habits": [],
            "ux_future": [],
        }
        
        # New: Agent Manager for Step 2
        self.agent_manager = AgentManager()

    # ============ Utils ============
    def tavily_from_nodes(self, input_id: int, input_text: str, output_id: int, time_state: int) -> str:
        # time_state: 0=過去, 1=現在
        return tavily_generate_answer(
            generate_question_for_tavily(HP_model[input_id], input_text, HP_model[output_id], time_state)
        )

    def simple_fill(self, input_id: int, input_text: str, output_id: int) -> str:
        # GPTのみで高速に埋める（Tavilyなし）
        return single_gpt(HP_model[input_id], input_text, HP_model[output_id])
    
    # NEW: Wrapper to call AgentManager.run_multi_agent_generation
    def run_multi_agent(self, element_type, element_desc, topic, context):
        # 将 context 整合进 full_context_str
        full_context = f"現在の状況: {self.hp_mt_1}\nユーザー入力: {self.user_inputs}\n具体的な文脈: {context}"
        return self.agent_manager.run_multi_agent_generation(element_type, element_desc, topic, full_context)

    # ============ Step 1: User Input Handling ============

    def handle_input1(self, ux_text: str):
        # Mtのゴール地点としてのUX (HP:5)
        self.hp_mt_1[HP_model[5]] = ux_text 
        self.user_inputs["q1_ux"] = ux_text
        
        # UXから派生する「現在」の要素を検索
        def job_art():
            # UX -> Art (18)
            art = self.tavily_from_nodes(5, ux_text, 18, 1)
            self.hp_mt_1[HP_model[18]] = art
            return art
        
        def job_be_and_inst():
            # UX -> BizEco (17) -> Institution (6)
            be = self.tavily_from_nodes(5, ux_text, 17, 1)
            self.hp_mt_1[HP_model[17]] = be
            inst = self.tavily_from_nodes(17, be, 6, 1)
            self.hp_mt_1[HP_model[6]] = inst
            return inst

        self.all_futures.append(self.executor.submit(job_art))
        self.all_futures.append(self.executor.submit(job_be_and_inst))

    def handle_input2(self, product_text: str):
        self.hp_mt_1[HP_model[14]] = product_text
        self.user_inputs["q2_product"] = product_text
        
        def job_tech_mt():
            # Product -> Tech (4)
            tech = self.tavily_from_nodes(14, product_text, 4, 1)
            self.hp_mt_1[HP_model[4]] = tech
            return tech
        self.all_futures.append(self.executor.submit(job_tech_mt))

    def handle_input3(self, mean_text: str):
        self.hp_mt_1[HP_model[13]] = mean_text
        self.user_inputs["q3_meaning"] = mean_text

    def start_from_values_and_trigger_future(self, values_text: str):
        self.hp_mt_1[HP_model[2]] = values_text
        self.user_inputs["q4_value"] = values_text
        
        # 過去(Mt-1)と現在(Mt)の残りを埋めるジョブを開始
        self.all_futures.append(self.executor.submit(self.job_fill_past_and_present, values_text))

        # 未来(Mt+1)の候補生成を開始
        self.trigger_adv_candidates_generation()

    def trigger_adv_candidates_generation(self):
        def job_candidates():
            art_text = self.hp_mt_1.get(HP_model[18], "")
            context = f"""
現在のUX: {self.user_inputs['q1_ux']}
現在の価値観: {self.user_inputs['q4_value']}
この状況が行き着く先、あるいはこれに対する反動として生まれる未来の問題を予測してください。
"""
            # 【変更点】 Multi-Agentを使用
            # 先に Agent を生成（トピック：現在の状況からの未来変化）
            self.agent_manager.generate_agents(f"現在の状況（{self.user_inputs['q1_ux']}）と価値観（{self.user_inputs['q4_value']}）からの未来的進化")
            
            candidates = self.run_multi_agent(
                element_type=HP_model[1], # 前衛的社会問題
                element_desc="現在のUX/アートから生じる未来の前衛的な社会問題",
                topic=f"{art_text} からの進化",
                context=context
            )
            return candidates

        self.future_candidates_adv = self.executor.submit(job_candidates)
        self.all_futures.append(self.future_candidates_adv)

    # ============ Background: Fill Past (Mt-1) & Present (Mt) ============

    def job_fill_past_and_present(self, values_text: str):
        """
        Mtの完全化と、そこから逆算したMt-1の生成を行う
        """
        # 1. Mt (現在) の不足分を埋める
        # 価値観(2) -> 習慣(15), コミュニケーション(11), 文化芸術(9), 社会問題(3)
        self.hp_mt_1[HP_model[15]] = self.tavily_from_nodes(2, values_text, 15, 1)
        self.hp_mt_1[HP_model[11]] = self.simple_fill(2, values_text, 11)
        self.hp_mt_1[HP_model[9]] = self.simple_fill(2, values_text, 9)
        self.hp_mt_1[HP_model[3]] = self.tavily_from_nodes(2, values_text, 3, 1)

        # 社会問題(3) -> コミュニティ(8) -> 前衛的問題(1)
        self.hp_mt_1[HP_model[8]] = self.simple_fill(3, self.hp_mt_1[HP_model[3]], 8)
        self.hp_mt_1[HP_model[1]] = self.tavily_from_nodes(8, self.hp_mt_1[HP_model[8]], 1, 1)
        
        # 社会問題(3) -> 組織化(12) -> 技術(4, 既存確認)
        self.hp_mt_1[HP_model[12]] = self.simple_fill(3, self.hp_mt_1[HP_model[3]], 12)
        
        # 制度(6) -> 標準化(10), メディア(7)
        inst_text = self.hp_mt_1.get(HP_model[6], "現代の制度")
        self.hp_mt_1[HP_model[10]] = self.simple_fill(6, inst_text, 10)
        self.hp_mt_1[HP_model[7]] = self.simple_fill(6, inst_text, 7)

        # 技術(4) -> パラダイム(16)
        tech_text = self.hp_mt_1.get(HP_model[4], "現代の技術")
        self.hp_mt_1[HP_model[16]] = self.simple_fill(4, tech_text, 16)


        # 2. Mt-1 (過去) の生成
        
        mt_adv = self.hp_mt_1.get(HP_model[1], "")
        
        # Mt(1) -> Mt-1(16) パラダイム (過去の技術基盤)
        self.hp_mt_0[HP_model[16]] = self.tavily_from_nodes(1, mt_adv, 16, 0)
        
        # Mt-1(16) -> Mt-1(4) 技術
        self.hp_mt_0[HP_model[4]] = self.simple_fill(16, self.hp_mt_0[HP_model[16]], 4)

        # Mt(1) -> Mt-1(18) アート (過去の社会批評)
        self.hp_mt_0[HP_model[18]] = self.simple_fill(1, mt_adv, 18)
        
        # Mt-1(18) -> Mt-1(5) UX (【重要】過去のUX空間)
        self.hp_mt_0[HP_model[5]] = self.tavily_from_nodes(18, self.hp_mt_0[HP_model[18]], 5, 0)

        # Mt-1の残りをUX(5)から逆算的に埋める
        # UX(5) -> BizEco(17) -> Inst(6)
        self.hp_mt_0[HP_model[17]] = self.simple_fill(5, self.hp_mt_0[HP_model[5]], 17)
        self.hp_mt_0[HP_model[6]] = self.simple_fill(17, self.hp_mt_0[HP_model[17]], 6)
        
        # UX(5) -> Meaning(13) -> Value(2) (過去の価値観)
        self.hp_mt_0[HP_model[13]] = "製品を使用する理由" # 簡易
        self.hp_mt_0[HP_model[14]] = "過去の製品"
        # 逆算は難しいので、制度(6) -> メディア(7) -> 社会問題(3) -> 価値観(2) の順で推測
        self.hp_mt_0[HP_model[7]] = self.simple_fill(6, self.hp_mt_0[HP_model[6]], 7)
        self.hp_mt_0[HP_model[3]] = self.simple_fill(7, self.hp_mt_0[HP_model[7]], 3)
        self.hp_mt_0[HP_model[11]] = self.simple_fill(3, self.hp_mt_0[HP_model[3]], 11)
        self.hp_mt_0[HP_model[2]] = self.simple_fill(11, self.hp_mt_0[HP_model[11]], 2)
        
        # 残りの埋め合わせ
        self.hp_mt_0[HP_model[1]] = self.simple_fill(16, self.hp_mt_0[HP_model[16]], 1) 
        self.hp_mt_0[HP_model[8]] = self.simple_fill(3, self.hp_mt_0[HP_model[3]], 8)
        self.hp_mt_0[HP_model[9]] = self.simple_fill(1, self.hp_mt_0[HP_model[1]], 9)
        self.hp_mt_0[HP_model[10]] = self.simple_fill(6, self.hp_mt_0[HP_model[6]], 10)
        self.hp_mt_0[HP_model[12]] = self.simple_fill(3, self.hp_mt_0[HP_model[3]], 12)
        self.hp_mt_0[HP_model[15]] = self.simple_fill(2, self.hp_mt_0[HP_model[2]], 15)

    # ============ Step 2: Mt+1 Future Generation (With Multi-Agent) ============

    def get_future_adv_candidates(self) -> List[str]:
        if self.future_candidates_adv:
            return self.future_candidates_adv.result()
        return []

    def generate_goals_from_adv(self, adv_text: str) -> List[str]:
        self.hp_mt_2[HP_model[1]] = adv_text
        # Mt+1 コミュニティ(8)
        self.hp_mt_2[HP_model[8]] = single_gpt(
            HP_model[1], adv_text, HP_model[8],
            context=f"過去からの文脈: {self.user_inputs['q4_value']}"
        )
        # Mt+1 文化芸術(9)
        self.hp_mt_2[HP_model[9]] = self.simple_fill(1, adv_text, 9)

        # 社会の目標候補 (Multi-Agent)
        self.mtplus1_candidates["goals"] = self.run_multi_agent(
            element_type=HP_model[3], # 社会問題(Goal/Target)
            element_desc="コミュニティや前衛的問題によって駆動される未来の社会目標",
            topic=f"「{adv_text}」に対する目標",
            context=f"コミュニティの状況: {self.hp_mt_2[HP_model[8]]}"
        )
        return self.mtplus1_candidates["goals"]

    def generate_values_from_goal(self, goal_text: str) -> List[str]:
        self.hp_mt_2[HP_model[3]] = goal_text
        # Mt+1 組織化(12), コミュニケーション(11)
        self.hp_mt_2[HP_model[12]] = self.simple_fill(3, goal_text, 12)
        self.hp_mt_2[HP_model[11]] = self.simple_fill(3, goal_text, 11)

        # 価値観 (Multi-Agent)
        self.mtplus1_candidates["values"] = self.run_multi_agent(
            element_type=HP_model[2], 
            element_desc="社会目標を解決するために人々が持つ未来の価値観",
            topic=f"「{goal_text}」のための価値観",
            context="目標達成に必要な価値観。"
        )
        return self.mtplus1_candidates["values"]

    def generate_habits_from_value(self, value_text: str) -> List[str]:
        self.hp_mt_2[HP_model[2]] = value_text
        # Mt+1 意味付け(13)
        self.hp_mt_2[HP_model[13]] = self.simple_fill(2, value_text, 13)

        # 習慣 (Multi-Agent)
        self.mtplus1_candidates["habits"] = self.run_multi_agent(
            element_type=HP_model[15],
            element_desc="未来の価値観によって形成される日常的な習慣",
            topic=f"「{value_text}」に基づく習慣",
            context="制度化される日常の習慣。"
        )
        return self.mtplus1_candidates["habits"]

    def generate_ux_from_habit(self, habit_text: str) -> List[str]:
        self.hp_mt_2[HP_model[15]] = habit_text
        # Mt+1 制度(6)
        self.hp_mt_2[HP_model[6]] = single_gpt(HP_model[15], habit_text, HP_model[6])
        # Mt+1 標準化(10), メディア(7)
        self.hp_mt_2[HP_model[10]] = self.simple_fill(6, self.hp_mt_2[HP_model[6]], 10)
        self.hp_mt_2[HP_model[7]] = self.simple_fill(6, self.hp_mt_2[HP_model[6]], 7)

        # UX (Multi-Agent)
        self.mtplus1_candidates["ux_future"] = self.run_multi_agent(
            element_type=HP_model[5],
            element_desc="未来のUXと空間",
            topic=f"習慣「{habit_text}」のためのUX",
            context="習慣が行われる物理的/デジタル空間。"
        )
        return self.mtplus1_candidates["ux_future"]

    def finalize_mtplus1(self, ux_text: str):
        # Mt+1 UX(5)
        self.hp_mt_2[HP_model[5]] = ux_text
        
        # 残り: BizEco(17), Prod(14), Tech(4), Paradigm(16), Art(18)
        self.hp_mt_2[HP_model[17]] = self.simple_fill(5, ux_text, 17)
        self.hp_mt_2[HP_model[14]] = self.simple_fill(5, ux_text, 14)
        self.hp_mt_2[HP_model[18]] = self.simple_fill(5, ux_text, 18)
        self.hp_mt_2[HP_model[4]] = self.simple_fill(14, self.hp_mt_2[HP_model[14]], 4)
        self.hp_mt_2[HP_model[16]] = self.simple_fill(4, self.hp_mt_2[HP_model[4]], 16)

    def wait_all(self):
        for f in self.all_futures:
            try:
                f.result()
            except Exception:
                pass

    def to_dict(self) -> dict:
        return {
            "hp_mt_0": self.hp_mt_0,
            "hp_mt_1": self.hp_mt_1,
            "hp_mt_2": self.hp_mt_2,
        }