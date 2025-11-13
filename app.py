from prompt import *
import json
from concurrent.futures import ThreadPoolExecutor, Future

# ============================
# 全局状态：Mt-1 / Mt / Mt+1
# ============================
hp_mt_0: dict[str, str] = {}  # Mt-1
hp_mt_1: dict[str, str] = {}  # Mt
hp_mt_2: dict[str, str] = {}  # Mt+1

# Tavily / GPT 用线程池
executor = ThreadPoolExecutor(max_workers=8)

# 记录所有后台任务（方便最后等待）
all_futures: list[Future] = []

# 与 Mt+1 前衛的社会問題 候補生成相关的 future
future_art_mt: Future | None = None
future_candidates_adv: Future | None = None


# ============================
# 工具函数
# ============================
def tavily_from_nodes(input_id: int, input_text: str, output_id: int, time_state: int) -> str:
    """
    封装一次 Tavily 调用：
    input_id:  输入 HP 节点 id
    input_text: 该节点的内容
    output_id: 输出 HP 节点 id
    time_state: 1 = Mt (現在), 0 = Mt-1 (過去)
    """
    return tavily_generate_answer(
        generate_question_for_tavily(
            HP_model[input_id],
            input_text,
            HP_model[output_id],
            time_state,
        )
    )


# ============================
# Input1: Mt の UX空間 (HP:5)
# ============================
def handle_input1(ux_text: str):
    global future_art_mt, future_candidates_adv

    print("▶ Input1: MtのUX空間 を受け取りました")
    hp_mt_1[HP_model[5]] = ux_text  # Mt UX

    # 1) UX → Mt のアート(18) （現代UXへの批評）
    def job_art():
        art = tavily_from_nodes(5, ux_text, 18, 1)
        hp_mt_1[HP_model[18]] = art
        return art

    future_art_mt = executor.submit(job_art)
    all_futures.append(future_art_mt)

    # 2) UX → Mt のビジネスエコシステム(17) → 制度(6)（第一版）
    def job_be_and_inst():
        be = tavily_from_nodes(5, ux_text, 17, 1)
        hp_mt_1[HP_model[17]] = be

        inst = tavily_from_nodes(17, be, 6, 1)  # ビジネスエコシステム → 制度
        hp_mt_1[HP_model[6]] = inst
        return inst

    future_inst_from_be = executor.submit(job_be_and_inst)
    all_futures.append(future_inst_from_be)

    # 3) Mt のアート → Mt+1 前衛的社会問題（候補列表）
    def job_candidates_from_art():
        art_text = future_art_mt.result()
        candidates = list_up_gpt(
            HP_model[18],  # アート(社会批評)
            art_text,
            HP_model[1],   # 前衛的社会問題 (Mt+1 候補)
        )
        return candidates

    future_candidates_adv = executor.submit(job_candidates_from_art)
    all_futures.append(future_candidates_adv)


# ============================
# Input2: Mt の 製品・サービス (HP:14)
# ============================
def handle_input2(product_text: str):
    print("▶ Input2: Mtの製品・サービス を受け取った")
    hp_mt_1[HP_model[14]] = product_text

    def job_tech_mt():
        tech = tavily_from_nodes(14, product_text, 4, 1)
        hp_mt_1[HP_model[4]] = tech
        return tech

    future_tech_mt = executor.submit(job_tech_mt)
    all_futures.append(future_tech_mt)


# ============================
# Input3: Mt の 意味付け (HP:13)
# ============================
def handle_input3(mean_text: str):
    print("▶ Input3: Mtの意味付け を受け取った（現時点では記録のみ）")
    hp_mt_1[HP_model[13]] = mean_text


# ============================
# 后台任务：从 Mt の人々の価値観 生成 Mt / Mt-1 全链
# （在单独线程中顺序执行，避免阻塞主线程）
# ============================
def job_mt_and_past_from_values(values_text: str):
    """
    在后台线程里执行：
      2 → 9,11,3,15
      3 → 8 → 1
      15 → 6 (Mt 制度 最终版)
      1 → 16,18
      16 → 4 (Mt-1 技術・資源)
      18 → 5 (Mt-1 UX)
      3 → 6 (Mt-1 制度)
    """
    # 2 → 9,11,3,15 可以并行做，也可以顺序做，这里为简化写顺序，如果你想再并行也可以在里面再开 executor
    hp_mt_1[HP_model[9]] = tavily_from_nodes(2, values_text, 9, 1)
    hp_mt_1[HP_model[11]] = tavily_from_nodes(2, values_text, 11, 1)
    hp_mt_1[HP_model[3]] = tavily_from_nodes(2, values_text, 3, 1)
    hp_mt_1[HP_model[15]] = tavily_from_nodes(2, values_text, 15, 1)

    # 3 → 8 → 1 (Mt 版 前衛的社会問題)
    hp_mt_1[HP_model[8]] = tavily_from_nodes(3, hp_mt_1[HP_model[3]], 8, 1)
    hp_mt_1[HP_model[1]] = tavily_from_nodes(8, hp_mt_1[HP_model[8]], 1, 1)

    # 15 → 6 (Mt 制度，覆盖 UX→BE→6 的一版)
    hp_mt_1[HP_model[6]] = tavily_from_nodes(15, hp_mt_1[HP_model[15]], 6, 1)

    # 1 → 16,18 (Mt-1 パラダイム, アート)
    hp_mt_0[HP_model[16]] = tavily_from_nodes(1, hp_mt_1[HP_model[1]], 16, 0)
    hp_mt_0[HP_model[18]] = tavily_from_nodes(1, hp_mt_1[HP_model[1]], 18, 0)

    # 16 → 4 (Mt-1 技術・資源)
    hp_mt_0[HP_model[4]] = tavily_from_nodes(16, hp_mt_0[HP_model[16]], 4, 0)
    # 18 → 5 (Mt-1 UX)
    hp_mt_0[HP_model[5]] = tavily_from_nodes(18, hp_mt_0[HP_model[18]], 5, 0)
    # 3 → 6 (Mt-1 制度)
    hp_mt_0[HP_model[6]] = tavily_from_nodes(3, hp_mt_1[HP_model[3]], 6, 0)

    print("◎ バックグラウンド: Mt / Mt-1 の生成が完了しました")


# ============================
# Input4: Mt の 人々の価値観 (HP:2)
# 这里只做：
#  - 记录 values_text
#  - 启动 job_mt_and_past_from_values 在线程池中跑（Mt / Mt-1 全链）
#  - 做 Mt+1 前衛的社会問題 的 5選1
# ============================
def handle_input4(values_text: str):
    print("▶ Input4: Mtの人々の価値観 を受け取った")
    hp_mt_1[HP_model[2]] = values_text  # Mt 人々の価値観

    # 1) 启动后台任务：生成 Mt / Mt-1 全链（不会阻塞主线程）
    f_mt_chain = executor.submit(job_mt_and_past_from_values, values_text)
    all_futures.append(f_mt_chain)

    # 2) Mt+1 前衛的社会問題：5選1（候補は Input1 後に生成済み）
    global future_candidates_adv
    if future_candidates_adv is not None:
        try:
            candidates = future_candidates_adv.result()  # 只等候选，本身一个任务而已
            print("\n=== Mt+1 の前衛的社会問題（候補リスト） ===\n")
            chosen = user_choose_answer(candidates)
            hp_mt_2[HP_model[1]] = chosen  # Mt+1 前衛的社会問題（決定版）
        except Exception as e:
            print("⚠ Mt+1 前衛的社会問題の5選1中にエラー:", e)
    else:
        print("⚠ Mt+1 前衛的社会問題 候補が存在しません")


# ============================
# Mt+1 侧的 5选1 + 连锁生成
# ============================
def run_future_mtplus1_chain():
    """
    基于：
      - Mt+1 前衛的社会問題 (hp_mt_2[1])  ← 在 handle_input4 中决定
    生成：
      - Mt+1 コミュニティ化 / 社会の目標 / 人々の価値観 / 慣習化 / UX空間 / 製品・サービス / 技術資源 等
    其中 5 个关键节点通过 5選1 决定：
      1) 前衛的社会問題 (已完成)
      2) 社会の目標
      3) 人々の価値観
      4) 慣習化
      5) UX空間
    """
    if HP_model[1] not in hp_mt_2:
        print("⚠ Mt+1 前衛的社会問題 が未決定のため、Mt+1 連鎖をスキップします")
        return

    print("\n▶ Mt+1 の5選1と連鎖生成を開始します")

    # 1) Mt+1 コミュニティ化：前衛的社会問題 → コミュニティ化（single_gpt）
    hp_mt_2[HP_model[8]] = single_gpt(
        HP_model[1],
        hp_mt_2[HP_model[1]],
        HP_model[8],
    )

    # 2) Mt+1 社会の目標：コミュニティ化(Mt+1) → 5選1
    candidates_goals = list_up_gpt(
        HP_model[8],
        hp_mt_2[HP_model[8]],   # 用 Mt+1 コミュニティ化，不依赖 Mt の 8
        HP_model[3],
    )
    print("\n=== Mt+1 の社会の目標（候補リスト） ===\n")
    hp_mt_2[HP_model[3]] = user_choose_answer(candidates_goals)

    # 3) Mt+1 人々の価値観：社会の目標 → 5選1
    candidates_values = list_up_gpt(
        HP_model[3],
        hp_mt_2[HP_model[3]],
        HP_model[2],
    )
    print("\n=== Mt+1 の人々の価値観（候補リスト） ===\n")
    hp_mt_2[HP_model[2]] = user_choose_answer(candidates_values)

    # 4) Mt+1 慣習化：価値観 → 5選1
    candidates_habits = list_up_gpt(
        HP_model[2],
        hp_mt_2[HP_model[2]],
        HP_model[15],
    )
    print("\n=== Mt+1 の慣習化（候補リスト） ===\n")
    hp_mt_2[HP_model[15]] = user_choose_answer(candidates_habits)

    # 5) Mt+1 UX空間：慣習化 → 5選1
    candidates_ux_future = list_up_gpt(
        HP_model[15],
        hp_mt_2[HP_model[15]],
        HP_model[5],
    )
    print("\n=== Mt+1 のUX空間（候補リスト） ===\n")
    hp_mt_2[HP_model[5]] = user_choose_answer(candidates_ux_future)

    # 6) Mt+1 製品・サービス：UX空間 → single_gpt
    hp_mt_2[HP_model[14]] = single_gpt(
        HP_model[5],
        hp_mt_2[HP_model[5]],
        HP_model[14],
    )

    # 7) Mt+1 技術資源：製品・サービス → single_gpt
    hp_mt_2[HP_model[4]] = single_gpt(
        HP_model[14],
        hp_mt_2[HP_model[14]],
        HP_model[4],
    )

    # 8) Mt の制度 → Mt+1 標準化 → Mt+1 技術資源（再整理）
    #    制度(Mt) → 標準化(Mt+1)
    hp_mt_2[HP_model[10]] = single_gpt(
        HP_model[6],
        hp_mt_1.get(HP_model[6], ""),  # 如果后台还没算完，就用空字符串；不会阻塞
        HP_model[10],
    )
    #    標準化 → 技術資源（补充 / 覆盖）
    hp_mt_2[HP_model[4]] = single_gpt(
        HP_model[10],
        hp_mt_2[HP_model[10]],
        HP_model[4],
    )

    print("✔ Mt+1 の5選1と連鎖生成が完了しました")


# ============================
# 主流程
# ============================
def main():
    # --- Input1 ---
    input1 = input("Q1. 最近、自分が他の人と違うと感じた行動はありますか？\n").strip()
    handle_input1(input1)

    # --- Input2 ---
    input2 = input("Q2. その行動を実現するために、どんな製品やサービスを使っていますか？\n").strip()
    handle_input2(input2)

    # --- Input3 ---
    input3 = input("Q3. なぜそのような製品やサービスを使用するのだと思いますか？\n").strip()
    handle_input3(input3)

    # --- Input4 ---
    input4 = input("Q4. その行動や選択を通じて、どんな自分でありたいと思っていますか？\n").strip()
    handle_input4(input4)

    # ⚠ 这里不等待 all_futures，直接进入 Mt+1 的连锁 5选1，
    #    此时 Mt / Mt-1 的生成在后台线程中继续执行，不阻塞
    run_future_mtplus1_chain()

    # 现在 Mt+1 的 5选1 全部走完了，再统一等后台任务，保证 JSON 完备
    print("\n⏳ バックグラウンド処理を最終確認中…\n")
    for f in all_futures:
        try:
            f.result()
        except Exception as e:
            print("⚠ バックグラウンドタスクでエラー:", e)

    # 输出 json
    output_data = {
        "hp_mt_0": hp_mt_0,
        "hp_mt_1": hp_mt_1,
        "hp_mt_2": hp_mt_2,
    }

    with open("hp_output.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

    print("\n🎉 HPモデルの3世代データを 'hp_output.json' に保存しました。")

    # 关闭线程池
    executor.shutdown(wait=True)


if __name__ == "__main__":
    main()
