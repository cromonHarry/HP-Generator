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
        
        self.user_inputs = {
            "q1_ux": "",
            "q2_product": "",
            "q3_meaning": "",
            "q4_value": ""
        }

        self.future_candidates_adv: Optional[Future] = None
        
        # 候補リストを保持する辞書（逐次更新）
        self.mtplus1_candidates = {
            "goals": [],
            "values": [],
            "habits": [],
            "ux_future": [],
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
        def job_candidates():
            art_text = self.hp_mt_1.get(HP_model[18], "")
            context = f"""
ユーザーの現在の行動(UX): {self.user_inputs['q1_ux']}
ユーザーの価値観: {self.user_inputs['q4_value']}
現在のアート/社会批評: {art_text}
これらの要素が突き詰められた結果、あるいは反動として生まれる未来の問題を予測してください。
"""
            candidates = list_up_gpt(
                input_node="現在のアートおよびユーザー体験",
                input_content=f"{art_text} / {self.user_inputs['q1_ux']}",
                output_node=HP_model[1],
                context=context
            )
            return candidates
        self.future_candidates_adv = self.executor.submit(job_candidates)
        self.all_futures.append(self.future_candidates_adv)

    # ============ Logic: Mt / Mt-1 Chain ============

    def job_mt_and_past_from_values(self, values_text: str):
        self.hp_mt_1[HP_model[9]] = self.tavily_from_nodes(2, values_text, 9, 1)
        self.hp_mt_1[HP_model[11]] = self.tavily_from_nodes(2, values_text, 11, 1)
        self.hp_mt_1[HP_model[3]] = self.tavily_from_nodes(2, values_text, 3, 1)
        self.hp_mt_1[HP_model[15]] = self.tavily_from_nodes(2, values_text, 15, 1)
        self.hp_mt_1[HP_model[8]] = self.tavily_from_nodes(3, self.hp_mt_1[HP_model[3]], 8, 1)
        self.hp_mt_1[HP_model[1]] = self.tavily_from_nodes(8, self.hp_mt_1[HP_model[8]], 1, 1)

        self.hp_mt_0[HP_model[16]] = self.tavily_from_nodes(1, self.hp_mt_1[HP_model[1]], 16, 0)
        self.hp_mt_0[HP_model[18]] = self.tavily_from_nodes(1, self.hp_mt_1[HP_model[1]], 18, 0)
        self.hp_mt_0[HP_model[4]] = self.tavily_from_nodes(16, self.hp_mt_0[HP_model[16]], 4, 0)
        self.hp_mt_0[HP_model[5]] = self.tavily_from_nodes(18, self.hp_mt_0[HP_model[18]], 5, 0)
        self.hp_mt_0[HP_model[6]] = self.tavily_from_nodes(3, self.hp_mt_1[HP_model[3]], 6, 0)

    # ============ Mt+1 Interaction ============

    def get_future_adv_candidates(self) -> List[str]:
        if self.future_candidates_adv:
            return self.future_candidates_adv.result()
        return []

    # 1. 前衛的社会問題が決まったら -> コミュニティ化(自動) -> 社会の目標(候補)
    def generate_goals_from_adv(self, adv_text: str) -> List[str]:
        self.hp_mt_2[HP_model[1]] = adv_text
        
        # Mt+1 コミュニティ化 (自動生成)
        self.hp_mt_2[HP_model[8]] = single_gpt(
            HP_model[1], adv_text, HP_model[8],
            context=f"過去からの文脈: {self.user_inputs['q4_value']}"
        )
        
        # 社会の目標 (候補生成)
        self.mtplus1_candidates["goals"] = list_up_gpt(
            HP_model[8], self.hp_mt_2[HP_model[8]], HP_model[3], 
            context="ユーザーが望む、あるいは恐れる未来の社会目標として"
        )
        return self.mtplus1_candidates["goals"]

    # 2. 社会の目標が決まったら -> 人々の価値観(候補)
    def generate_values_from_goal(self, goal_text: str) -> List[str]:
        self.hp_mt_2[HP_model[3]] = goal_text
        self.mtplus1_candidates["values"] = list_up_gpt(
            HP_model[3], goal_text, HP_model[2]
        )
        return self.mtplus1_candidates["values"]

    # 3. 人々の価値観が決まったら -> 慣習化(候補)
    def generate_habits_from_value(self, value_text: str) -> List[str]:
        self.hp_mt_2[HP_model[2]] = value_text
        self.mtplus1_candidates["habits"] = list_up_gpt(
            HP_model[2], value_text, HP_model[15]
        )
        return self.mtplus1_candidates["habits"]

    # 4. 慣習化が決まったら -> UX空間(候補)
    def generate_ux_from_habit(self, habit_text: str) -> List[str]:
        self.hp_mt_2[HP_model[15]] = habit_text
        self.mtplus1_candidates["ux_future"] = list_up_gpt(
            HP_model[15], habit_text, HP_model[5]
        )
        return self.mtplus1_candidates["ux_future"]

    # 5. UX空間が決まったら -> 最終処理
    def finalize_mtplus1(self, ux_text: str):
        self.hp_mt_2[HP_model[5]] = ux_text
        
        # 残りの要素を生成 (Prod, Tech, Std)
        self.hp_mt_2[HP_model[14]] = single_gpt(HP_model[5], ux_text, HP_model[14])
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