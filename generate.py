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
    """
    一次完整 HP 生成会话（Mt-1 / Mt / Mt+1）。
    用于在 Streamlit 中多步交互地调用。
    """

    def __init__(self, max_workers: int = 8):
        # 三个时间层的 HP 模型
        self.hp_mt_0: Dict[str, str] = {}  # Mt-1
        self.hp_mt_1: Dict[str, str] = {}  # Mt
        self.hp_mt_2: Dict[str, str] = {}  # Mt+1

        # 线程池 & future 管理
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.all_futures: List[Future] = []

        # 和 Mt+1 前衛的社会問題候補相关的 future
        self.future_art_mt: Optional[Future] = None
        self.future_candidates_adv: Optional[Future] = None

        # Mt+1 连锁生成中的候选列表缓存（给 UI 选择）
        self.mtplus1_candidates = {
            "goals": None,      # 社会の目標
            "values": None,     # 人々の価値観
            "habits": None,     # 慣習化
            "ux_future": None,  # UX空間
        }

    # ============ Tavily 封装 ============

    def tavily_from_nodes(self, input_id: int, input_text: str, output_id: int, time_state: int) -> str:
        return tavily_generate_answer(
            generate_question_for_tavily(
                HP_model[input_id],
                input_text,
                HP_model[output_id],
                time_state,
            )
        )

    # ============ Input1: Mt の UX空間 (HP:5) ============

    def handle_input1(self, ux_text: str):
        """
        Q1: Mt の UX空間
        - 记录 Mt UX
        - 并发启动：
          1) UX → Mt アート(18)
          2) UX → Mt ビジネスエコシステム(17) → 制度(6)
          3) (等待アート结果后) アート → Mt+1 前衛的社会問題 候補リスト
        """
        self.hp_mt_1[HP_model[5]] = ux_text  # Mt UX

        # 1) UX → Mt のアート(18)
        def job_art():
            art = self.tavily_from_nodes(5, ux_text, 18, 1)
            self.hp_mt_1[HP_model[18]] = art
            return art

        self.future_art_mt = self.executor.submit(job_art)
        self.all_futures.append(self.future_art_mt)

        # 2) UX → Mt のビジネスエコシステム(17) → 制度(6)
        def job_be_and_inst():
            be = self.tavily_from_nodes(5, ux_text, 17, 1)
            self.hp_mt_1[HP_model[17]] = be

            inst = self.tavily_from_nodes(17, be, 6, 1)
            self.hp_mt_1[HP_model[6]] = inst
            return inst

        future_inst_from_be = self.executor.submit(job_be_and_inst)
        self.all_futures.append(future_inst_from_be)

        # 3) Mt のアート → Mt+1 前衛的社会問題 候補リスト
        def job_candidates_from_art():
            art_text = self.future_art_mt.result()
            candidates = list_up_gpt(
                HP_model[18],  # アート(社会批評)
                art_text,
                HP_model[1],   # 前衛的社会問題 (Mt+1 候補)
            )
            return candidates

        self.future_candidates_adv = self.executor.submit(job_candidates_from_art)
        self.all_futures.append(self.future_candidates_adv)

    # ============ Input2: Mt の 製品・サービス (HP:14) ============

    def handle_input2(self, product_text: str):
        self.hp_mt_1[HP_model[14]] = product_text

        def job_tech_mt():
            tech = self.tavily_from_nodes(14, product_text, 4, 1)
            self.hp_mt_1[HP_model[4]] = tech
            return tech

        future_tech_mt = self.executor.submit(job_tech_mt)
        self.all_futures.append(future_tech_mt)

    # ============ Input3: Mt の 意味付け (HP:13) ============

    def handle_input3(self, mean_text: str):
        self.hp_mt_1[HP_model[13]] = mean_text

    # ============ 后台：Mt / Mt-1 链 ============

    def job_mt_and_past_from_values(self, values_text: str):
        """
        在后台线程执行：
          2 → 9,11,3,15
          3 → 8 → 1
          15 → 6 (Mt 制度)
          1 → 16,18 (Mt-1)
          16 → 4, 18 → 5, 3 → 6 (Mt-1)
        """
        # 2 → 9, 11, 3, 15
        self.hp_mt_1[HP_model[9]] = self.tavily_from_nodes(2, values_text, 9, 1)
        self.hp_mt_1[HP_model[11]] = self.tavily_from_nodes(2, values_text, 11, 1)
        self.hp_mt_1[HP_model[3]] = self.tavily_from_nodes(2, values_text, 3, 1)
        self.hp_mt_1[HP_model[15]] = self.tavily_from_nodes(2, values_text, 15, 1)

        # 3 → 8 → 1 (Mt 版 前衛的社会問題)
        self.hp_mt_1[HP_model[8]] = self.tavily_from_nodes(3, self.hp_mt_1[HP_model[3]], 8, 1)
        self.hp_mt_1[HP_model[1]] = self.tavily_from_nodes(8, self.hp_mt_1[HP_model[8]], 1, 1)

        # 15 → 6 (Mt 制度 覆盖第一版)
        self.hp_mt_1[HP_model[6]] = self.tavily_from_nodes(15, self.hp_mt_1[HP_model[15]], 6, 1)

        # 1 → 16,18 (Mt-1 パラダイム, アート)
        self.hp_mt_0[HP_model[16]] = self.tavily_from_nodes(1, self.hp_mt_1[HP_model[1]], 16, 0)
        self.hp_mt_0[HP_model[18]] = self.tavily_from_nodes(1, self.hp_mt_1[HP_model[1]], 18, 0)

        # 16 → 4 (Mt-1 技術・資源)
        self.hp_mt_0[HP_model[4]] = self.tavily_from_nodes(16, self.hp_mt_0[HP_model[16]], 4, 0)
        # 18 → 5 (Mt-1 UX)
        self.hp_mt_0[HP_model[5]] = self.tavily_from_nodes(18, self.hp_mt_0[HP_model[18]], 5, 0)
        # 3 → 6 (Mt-1 制度)
        self.hp_mt_0[HP_model[6]] = self.tavily_from_nodes(3, self.hp_mt_1[HP_model[3]], 6, 0)

    def start_from_values(self, values_text: str):
        """
        对应原来的 handle_input4 里“启动后台任务”的部分，但不做 5选1。
        """
        self.hp_mt_1[HP_model[2]] = values_text  # Mt 人々の価値観
        f_mt_chain = self.executor.submit(self.job_mt_and_past_from_values, values_text)
        self.all_futures.append(f_mt_chain)

    # ============ Mt+1: 第一次 5选1（前衛的社会問題） ============

    def get_future_adv_candidates(self) -> List[str]:
        """
        等待由 Input1 启动的 future_candidates_adv 完成，返回 Mt+1 前衛的社会問題 候補。
        """
        if self.future_candidates_adv is None:
            return []
        return self.future_candidates_adv.result()

    def set_future_adv_choice(self, choice: str):
        """
        用户在 UI 中选定 Mt+1 前衛的社会問題。
        """
        self.hp_mt_2[HP_model[1]] = choice

    # ============ Mt+1: 其余 4 个 5选1 + 连锁生成 ============

    def generate_mtplus1_candidates(self):
        """
        基于已经确定的 Mt+1 前衛的社会問題：
          1) 生成 Mt+1 コミュニティ化（single_gpt）
          2) 生成 4 组候选（社会の目標 / 人々の価値観 / 慣習化 / UX空間）
        仅生成候选，不做选择。
        """
        if HP_model[1] not in self.hp_mt_2:
            raise ValueError("Mt+1 前衛的社会問題 尚未确定。")

        # 1) Mt+1 コミュニティ化
        self.hp_mt_2[HP_model[8]] = single_gpt(
            HP_model[1],
            self.hp_mt_2[HP_model[1]],
            HP_model[8],
        )

        # 2) 候选列表
        self.mtplus1_candidates["goals"] = list_up_gpt(
            HP_model[8], self.hp_mt_2[HP_model[8]], HP_model[3]
        )
        self.mtplus1_candidates["values"] = list_up_gpt(
            HP_model[3],
            # 暂时用“候选之一”的上位描述，真正的 value 选择在 UI 中决定
            self.mtplus1_candidates["goals"][0],
            HP_model[2],
        )
        self.mtplus1_candidates["habits"] = list_up_gpt(
            HP_model[2],
            self.mtplus1_candidates["values"][0],
            HP_model[15],
        )
        self.mtplus1_candidates["ux_future"] = list_up_gpt(
            HP_model[15],
            self.mtplus1_candidates["habits"][0],
            HP_model[5],
        )

    def apply_mtplus1_choices(self, idx_goals: int, idx_values: int, idx_habits: int, idx_ux_future: int):
        """
        根据 UI 中用户对 4 个候选组的选择，填入 Mt+1 的：
          - 社会の目標
          - 人々の価値観
          - 慣習化
          - UX空間
        然后依次生成：
          - Mt+1 製品・サービス
          - Mt+1 技術・資源（两步）
        """
        goals_list = self.mtplus1_candidates["goals"] or []
        values_list = self.mtplus1_candidates["values"] or []
        habits_list = self.mtplus1_candidates["habits"] or []
        ux_list = self.mtplus1_candidates["ux_future"] or []

        if not (goals_list and values_list and habits_list and ux_list):
            raise ValueError("Mt+1 候選リストが未生成です。")

        self.hp_mt_2[HP_model[3]] = goals_list[idx_goals]
        self.hp_mt_2[HP_model[2]] = values_list[idx_values]
        self.hp_mt_2[HP_model[15]] = habits_list[idx_habits]
        self.hp_mt_2[HP_model[5]] = ux_list[idx_ux_future]

        # 6) Mt+1 製品・サービス：UX空間 → single_gpt
        self.hp_mt_2[HP_model[14]] = single_gpt(
            HP_model[5],
            self.hp_mt_2[HP_model[5]],
            HP_model[14],
        )

        # 7) Mt+1 技術資源：製品・サービス → single_gpt
        self.hp_mt_2[HP_model[4]] = single_gpt(
            HP_model[14],
            self.hp_mt_2[HP_model[14]],
            HP_model[4],
        )

        # 8) Mt の制度 → Mt+1 標準化 → Mt+1 技術資源（再整理）
        self.hp_mt_2[HP_model[10]] = single_gpt(
            HP_model[6],
            self.hp_mt_1.get(HP_model[6], ""),
            HP_model[10],
        )
        self.hp_mt_2[HP_model[4]] = single_gpt(
            HP_model[10],
            self.hp_mt_2[HP_model[10]],
            HP_model[4],
        )

    # ============ 收尾 & 导出 ============

    def wait_all(self):
        """
        等待所有后台 future 完成（Mt / Mt-1 的 Tavily 调用等）。
        """
        for f in self.all_futures:
            try:
                f.result()
            except Exception as e:
                print("⚠ バックグラウンドタスクでエラー:", e)

    def to_dict(self) -> dict:
        return {
            "hp_mt_0": self.hp_mt_0,
            "hp_mt_1": self.hp_mt_1,
            "hp_mt_2": self.hp_mt_2,
        }

    def save_json(self, path: str = "hp_output.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)
