# generate.py
import json
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, List, Optional

from prompt import (
    HP_model,
    list_up_gpt,
    single_gpt,
    generate_question_for_tavily,
    tavily_generate_answer,
)

class HPGenerationSession:
    def __init__(self, max_workers: int = 8):
        self.hp_mt_0: Dict[str, str] = {}  # Mt-1 (過去)
        self.hp_mt_1: Dict[str, str] = {}  # Mt (現在)
        self.hp_mt_2: Dict[str, str] = {}  # Mt+1 (未来)

        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.all_futures: List[Future] = []
        
        # ユーザー入力を保持（再生成や文脈強化に使用）
        self.user_inputs = {
            "q1_ux": "",
            "q2_product": "",
            "q3_meaning": "",
            "q4_value": ""
        }

        self.future_candidates_adv: Optional[Future] = None
        self.mtplus1_candidates = {
            "goals": None,
            "values": None,
            "habits": None,
            "ux_future": None,
        }

    def tavily_from_nodes(self, input_id: int, input_text: str, output_id: int, time_state: int) -> str:
        return tavily_generate_answer(
            generate_question_for_tavily(HP_model[input_id], input_text, HP_model[output_id], time_state)
        )

    # ============ Input Handling ============

    def handle_input1(self, ux_text: str):
        #  Mt UX (Input) starts here.
        self.hp_mt_1[HP_model[5]] = ux_text 
        self.user_inputs["q1_ux"] = ux_text

        # 1) UX -> Mt Art (18)
        def job_art():
            art = self.tavily_from_nodes(5, ux_text, 18, 1)
            self.hp_mt_1[HP_model[18]] = art
            return art
        
        # 2) UX -> Mt Business Ecosystem (17) -> Institution (6)
        def job_be_and_inst():
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

        # Product -> Tech (Mt)
        def job_tech_mt():
            tech = self.tavily_from_nodes(14, product_text, 4, 1)
            self.hp_mt_1[HP_model[4]] = tech
            return tech
        self.all_futures.append(self.executor.submit(job_tech_mt))

    def handle_input3(self, mean_text: str):
        self.hp_mt_1[HP_model[13]] = mean_text
        self.user_inputs["q3_meaning"] = mean_text

    def start_from_values_and_trigger_future(self, values_text: str):
        """
        Q4入力後に呼ばれる。
        1. Mt/Mt-1 の残りを生成
        2. Mt+1 の候補（前衛的社会問題）を生成
        """
        self.hp_mt_1[HP_model[2]] = values_text
        self.user_inputs["q4_value"] = values_text

        # Background: Mt & Past Chain
        self.all_futures.append(self.executor.submit(self.job_mt_and_past_from_values, values_text))

        # Future: Generate Candidates for Mt+1 Adv Problem
        #  ユーザー入力(Q1, Q4)を強く反映させるために再設計
        self.trigger_adv_candidates_generation()

    def trigger_adv_candidates_generation(self):
        """
        Mt+1 前衛的社会問題の候補生成。
        「アート」だけでなく「ユーザーの価値観」「UX」をコンテキストとして渡す。
        """
        def job_candidates():
            # アート生成が終わっているか確認（なければUXから直接生成するようフォールバック）
            art_text = self.hp_mt_1.get(HP_model[18], "")
            
            # コンテキストの構築
            context = f"""
ユーザーの現在の行動(UX): {self.user_inputs['q1_ux']}
ユーザーの価値観: {self.user_inputs['q4_value']}
現在のアート/社会批評: {art_text}
これらの要素が突き詰められた結果、あるいは反動として生まれる未来の問題を予測してください。
"""
            # 入力ノードは形式的に「アート」または「パラダイム」だが、実質はコンテキスト重視
            candidates = list_up_gpt(
                input_node="現在のアートおよびユーザー体験",
                input_content=f"{art_text} / {self.user_inputs['q1_ux']}",
                output_node=HP_model[1], # Mt+1 前衛的社会問題
                context=context
            )
            return candidates

        self.future_candidates_adv = self.executor.submit(job_candidates)
        self.all_futures.append(self.future_candidates_adv)

    # ============ Logic: Mt / Mt-1 Chain ============

    def job_mt_and_past_from_values(self, values_text: str):
        # Mt Loop
        self.hp_mt_1[HP_model[9]] = self.tavily_from_nodes(2, values_text, 9, 1)
        self.hp_mt_1[HP_model[11]] = self.tavily_from_nodes(2, values_text, 11, 1)
        self.hp_mt_1[HP_model[3]] = self.tavily_from_nodes(2, values_text, 3, 1)
        self.hp_mt_1[HP_model[15]] = self.tavily_from_nodes(2, values_text, 15, 1)
        
        # Mt SocProblem -> Community -> AdvProblem (Mt)
        self.hp_mt_1[HP_model[8]] = self.tavily_from_nodes(3, self.hp_mt_1[HP_model[3]], 8, 1)
        self.hp_mt_1[HP_model[1]] = self.tavily_from_nodes(8, self.hp_mt_1[HP_model[8]], 1, 1)

        # Mt-1 Generation (Past)
        #  Mt starts from Mt-1 UX (AI inferred).
        # We assume Mt Paradigms (16) & Art (18) come from Mt AdvProb (1).
        
        # Mt(1) -> Mt-1(16) Paradigm, Mt-1(18) Art
        self.hp_mt_0[HP_model[16]] = self.tavily_from_nodes(1, self.hp_mt_1[HP_model[1]], 16, 0)
        self.hp_mt_0[HP_model[18]] = self.tavily_from_nodes(1, self.hp_mt_1[HP_model[1]], 18, 0)

        # Mt-1(16) -> Mt-1(4) Tech
        self.hp_mt_0[HP_model[4]] = self.tavily_from_nodes(16, self.hp_mt_0[HP_model[16]], 4, 0)

        # Mt-1(18) -> Mt-1(5) UX (Estimated Past UX)
        # [cite: 26, 28] 過去のUXを論理的に推定
        self.hp_mt_0[HP_model[5]] = self.tavily_from_nodes(18, self.hp_mt_0[HP_model[18]], 5, 0)
        
        # Mt-1(3) SocProb -> Mt-1(6) Institution
        # Assuming Mt SocProb comes from Mt-1 Inst.
        # Reverse search or infer:
        self.hp_mt_0[HP_model[6]] = self.tavily_from_nodes(3, self.hp_mt_1[HP_model[3]], 6, 0)

    # ============ Mt+1 Interaction ============

    def get_future_adv_candidates(self) -> List[str]:
        if self.future_candidates_adv:
            return self.future_candidates_adv.result()
        return []

    def set_future_adv_choice(self, choice: str):
        self.hp_mt_2[HP_model[1]] = choice

    def generate_mtplus1_candidates_chain(self):
        """
        Mt+1 の連鎖生成 (AdvProb -> Comm -> Goals -> Values -> Habits -> UX)
        """
        # 1) Mt+1 Community
        self.hp_mt_2[HP_model[8]] = single_gpt(
            HP_model[1], self.hp_mt_2[HP_model[1]], HP_model[8],
            context=f"過去からの文脈: {self.user_inputs['q4_value']}"
        )

        # 2) Candidates for Selection
        self.mtplus1_candidates["goals"] = list_up_gpt(
            HP_model[8], self.hp_mt_2[HP_model[8]], HP_model[3], 
            context="ユーザーが望む、あるいは恐れる未来の社会目標として"
        )
        # Default chain logic (will be refined by user selection)
        temp_goal = self.mtplus1_candidates["goals"][0]
        
        self.mtplus1_candidates["values"] = list_up_gpt(
            HP_model[3], temp_goal, HP_model[2]
        )
        temp_value = self.mtplus1_candidates["values"][0]

        self.mtplus1_candidates["habits"] = list_up_gpt(
            HP_model[2], temp_value, HP_model[15]
        )
        temp_habit = self.mtplus1_candidates["habits"][0]

        self.mtplus1_candidates["ux_future"] = list_up_gpt(
            HP_model[15], temp_habit, HP_model[5]
        )

    def apply_mtplus1_choices(self, idx_goals: int, idx_values: int, idx_habits: int, idx_ux_future: int):
        # ユーザー選択を適用
        self.hp_mt_2[HP_model[3]] = self.mtplus1_candidates["goals"][idx_goals]
        
        # 前の選択に基づいて次の候補を再生成するのが理想だが、ここでは高速化のためリスト生成時の整合性を信頼するか、
        # 厳密にするならここで再生成ロジックを入れる。今回は既存ロジックを踏襲しつつ適用。
        self.hp_mt_2[HP_model[2]] = self.mtplus1_candidates["values"][idx_values]
        self.hp_mt_2[HP_model[15]] = self.mtplus1_candidates["habits"][idx_habits]
        self.hp_mt_2[HP_model[5]] = self.mtplus1_candidates["ux_future"][idx_ux_future]

        # 残りの要素を生成 (Prod, Tech, Std)
        self.hp_mt_2[HP_model[14]] = single_gpt(HP_model[5], self.hp_mt_2[HP_model[5]], HP_model[14])
        self.hp_mt_2[HP_model[4]] = single_gpt(HP_model[14], self.hp_mt_2[HP_model[14]], HP_model[4])
        self.hp_mt_2[HP_model[10]] = single_gpt(HP_model[6], self.hp_mt_1.get(HP_model[6],""), HP_model[10])

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