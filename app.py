from prompt import *
import json

hp_mt_0 = {}
hp_mt_1 = {}
hp_mt_2 = {}

# -----------------------------
# 1. 用户输入（和原来完全一样）
# -----------------------------
input_prompts = [
    ("最近自分が別人と違う感じになった行動はありますか", 5),
    ("それを実現するために、どんな製品やサービスを使っていますか", 14),
    ("なぜそのような製品やサービスを使用するか", 13),
    ("その行動を基づいて、どんな自分になりたいですか", 2),
]

for question, node_id in input_prompts:
    hp_mt_1[HP_model[node_id]] = input(question + "\n").strip()


tavily_tasks = [
    (2, "1", 9, "1"),
    (2, "1", 11, "1"),
    (2, "1", 3, "1"),
    (3, "1", 8, "1"),
    (8, "1", 1, "1"),

    (1, "1", 16, "0"),
    (16, "0", 4, "0"),
    (1, "1", 18, "0"),
    (18, "0", 5, "0"),
    (3, "1", 6, "0"),

    (14, "1", 4, "1"),
    (5, "1", 17, "1"),
    (2, "1", 15, "1"),
    (17, "1", 6, "1"),
    (15, "1", 6, "1"),

    (5, "1", 18, "1"),
]


def run_tavily_tasks():
    for input_id, src_mt, output_id, tgt_mt in tavily_tasks:
        input_node = HP_model[input_id]
        output_node = HP_model[output_id]

        source_dict = hp_mt_1 if src_mt == "1" else hp_mt_0
        target_dict = hp_mt_1 if tgt_mt == "1" else hp_mt_0
        time_state = 1 if tgt_mt == "1" else 0

        question = generate_question_for_tavily(
            input_node,
            source_dict[input_node],
            output_node,
            time_state
        )
        target_dict[output_node] = tavily_generate_answer(question)


run_tavily_tasks()


user_choice_tasks = [
    (5, 1),   # 5先导 -> 前衛的社会問題
    (8, 3),   # コミュニティ化 -> 社会問題
    (3, 2),   # 社会問題 -> 価値観
    (2, 15),  # 価値観 -> 習慣化
    (2, 5),   # 価値観 -> UX 空間
]


def run_user_choice_tasks():
    for input_id, output_id in user_choice_tasks:
        input_node = HP_model[input_id]
        output_node = HP_model[output_id]

        input_content = hp_mt_1[input_node]

        candidates = list_up_gpt(input_node, input_content, output_node)
        hp_mt_2[output_node] = user_choose_answer(candidates)


run_user_choice_tasks()


single_gpt_tasks = [
    (6, 10, "1", "2"),
    (10, 4, "2", "2"),
    (1, 8, "2", "2"),
    (5, 14, "2", "2"),
    (14, 4, "2", "2"),
]


def run_single_gpt_tasks():
    for input_id, output_id, src_mt, tgt_mt in single_gpt_tasks:
        input_node = HP_model[input_id]
        output_node = HP_model[output_id]

        src_dict = hp_mt_1 if src_mt == "1" else hp_mt_2
        dst_dict = hp_mt_2 if tgt_mt == "2" else hp_mt_1  # 目前只有 mt2 作为目标

        dst_dict[output_node] = single_gpt(
            input_node,
            src_dict[input_node],
            output_node
        )


run_single_gpt_tasks()


# -----------------------------
# 5. 输出 JSON
# -----------------------------
output_data = {
    "hp_mt_0": hp_mt_0,
    "hp_mt_1": hp_mt_1,
    "hp_mt_2": hp_mt_2
}

with open("hp_output.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print("\n✅ HPモデルの3段階データを 'hp_output.json' に保存しました。")
