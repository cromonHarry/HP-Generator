# app.py
import json
import streamlit as st

from generate import HPGenerationSession
from outline import generate_outline, modify_outline
from prompt import list_up_gpt


# ===== ページ設定 =====
st.set_page_config(
    page_title="HPモデル SFプロット生成ツール",
    page_icon="🛰️",
    layout="centered",
)

st.markdown(
    """
    <style>
    .main-title { font-size: 2.0rem; font-weight: 700; margin-bottom: 0.3rem; }
    .sub-title  { font-size: 0.9rem; color: #666; margin-bottom: 1.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">HPモデル × GPT × Tavily によるSFプロット生成ツール</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">あなたの経験をもとに三世代HPモデルとSF物語アウトラインを共創します。</div>', unsafe_allow_html=True)


# ============================================================
#   🧠 セッション初期化
# ============================================================
def init_state():
    defaults = {
        "hp_session": HPGenerationSession(),
        "adv_candidates": None,
        "mtplus1": {},
        "hp_json": None,
        "outline": None,
        "final_confirmed": False,

        # Step1 状態
        "show_q2": False,
        "show_q3": False,
        "show_q4": False,

        # Mt+1 5つの選択 全体フラグ
        "step2": False,

        # HPモデル完成後 → アウトライン生成に進むフラグ
        "step4": False,

        # Step2 内部段階
        "s2_adv": False,
        "s2_goal": False,
        "s2_value": False,
        "s2_habit": False,
        "s2_ux": False,

        # ユーザー選択
        "choice_adv": None,
        "choice_goal": None,
        "choice_value": None,
        "choice_habit": None,
        "choice_ux": None,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()
state = st.session_state
hp_session: HPGenerationSession = state.hp_session


# ============================================================
#   🟦 ステップ1：Q1〜Q4
# ============================================================

st.header("ステップ 1：あなたの経験についての4つの質問", divider="grey")

# ---------- Q1 ----------
st.subheader("Q1（Mt：日常の空間とユーザー体験）")
q1 = st.text_area(
    "最近あなた自身がした行動の中で、誇りに思える、あるいは独創性があると感じるものを思い出してください。",
    key="input_q1",
    height=60
)

if st.button("Q1 を送信", key="btn_q1"):
    if not q1.strip():
        st.warning("Q1に回答してください。")
    else:
        hp_session.handle_input1(q1)
        state.show_q2 = True
        st.success("Q1 を受け取りました。続いて Q2 へ。")

# ---------- Q2 ----------
if state.show_q2:
    st.subheader("Q2（Mt：製品・サービス）")
    q2 = st.text_area(
        "その行動を実現するために使用している製品やサービスは？",
        key="input_q2", height=60
    )

    if st.button("Q2 を送信", key="btn_q2"):
        if not q2.strip():
            st.warning("Q2に回答してください。")
        else:
            hp_session.handle_input2(q2)
            state.show_q3 = True
            st.success("Q2 を受け取りました。続いて Q3 へ。")

# ---------- Q3 ----------
if state.show_q3:
    st.subheader("Q3（Mt：意味付け）")
    q3 = st.text_area(
        "なぜ、その製品やサービスを使っていると思いますか？",
        key="input_q3", height=60
    )

    if st.button("Q3 を送信", key="btn_q3"):
        if not q3.strip():
            st.warning("Q3に回答してください。")
        else:
            hp_session.handle_input3(q3)
            state.show_q4 = True
            st.success("Q3 を受け取りました。続いて Q4 へ。")

# ---------- Q4 ----------
if state.show_q4:
    st.subheader("Q4（Mt：人々の価値観）")
    q4 = st.text_area(
        "その行動を通じて、どんな自分でありたいですか？",
        key="input_q4", height=60
    )

    if st.button("Q4 を送信して Step2 開始", key="btn_q4"):
        if not q4.strip():
            st.warning("Q4に回答してください。")
        else:
            with st.spinner("Mt・Mt-1・Mt+1 の初期情報を生成中…"):
                hp_session.start_from_values(q4)
                state.adv_candidates = hp_session.get_future_adv_candidates()

            state.step2 = True
            state.s2_adv = True
            st.success("次へ：未来社会の『前衛的社会問題』を選んでください。")


# ============================================================
#   🟩 ステップ2：未来社会（Mt+1）5つの選択
# ============================================================

if state.step2:
    st.header("ステップ 2：未来社会（Mt+1）を構成する5つの選択", divider="grey")

    cands = state.mtplus1

    # ① 前衛的社会問題
    if state.s2_adv:
        st.subheader("① 前衛的社会問題")

        adv = state.adv_candidates or []
        if not adv:
            st.error("前衛的社会問題の候補が生成できませんでした。もう一度最初から試してください。")
        else:
            idx_adv = st.radio(
                "以下の選択肢の中から、最も共感する前衛的社会問題を一つ選んでください。",
                list(range(len(adv))),
                format_func=lambda i: adv[i],
                key="radio_adv"
            )

            if st.button("① 前衛的社会問題を確定", key="btn_adv"):
                state.choice_adv = idx_adv
                hp_session.set_future_adv_choice(adv[idx_adv])

                with st.spinner("『社会の目標』候補を生成中…"):
                    state.mtplus1["goals"] = list_up_gpt(
                        "前衛的社会問題", adv[idx_adv], "社会の目標"
                    )

                state.s2_goal = True
                st.success("②『社会の目標』を選択してください。")

    # ② 社会の目標
    if state.s2_goal:
        st.subheader("② 社会の目標")

        goals = state.mtplus1.get("goals", [])
        if not goals:
            st.error("『社会の目標』候補が存在しません。")
        else:
            idx_goal = st.radio(
                "以下の選択肢の中から、最も共感する社会の目標を一つ選んでください。",
                list(range(len(goals))),
                format_func=lambda i: goals[i],
                key="radio_goal"
            )

            if st.button("② 社会の目標を確定", key="btn_goal"):
                state.choice_goal = idx_goal
                goal_text = goals[idx_goal]

                with st.spinner("『人々の価値観』候補を生成中…"):
                    state.mtplus1["values"] = list_up_gpt(
                        "社会の目標", goal_text, "人々の価値観"
                    )

                state.s2_value = True
                st.success("③『人々の価値観』を選択してください。")

    # ③ 人々の価値観
    if state.s2_value:
        st.subheader("③ 人々の価値観")

        values = state.mtplus1.get("values", [])
        if not values:
            st.error("『人々の価値観』候補が存在しません。")
        else:
            idx_value = st.radio(
                "以下の選択肢の中から、最も共感する未来人が共有する価値観を一つ選んでください。",
                list(range(len(values))),
                format_func=lambda i: values[i],
                key="radio_value"
            )

            if st.button("③ 人々の価値観を確定", key="btn_value"):
                state.choice_value = idx_value
                value_text = values[idx_value]

                with st.spinner("『慣習化』および『日常の空間とUX』候補を生成中…"):
                    state.mtplus1["habits"] = list_up_gpt(
                        "人々の価値観", value_text, "慣習化"
                    )
                    habits = state.mtplus1["habits"]
                    base_habit = habits[0] if habits else ""
                    state.mtplus1["ux_future"] = list_up_gpt(
                        "慣習化", base_habit, "日常の空間とユーザー体験"
                    )

                state.s2_habit = True
                st.success("④『慣習化』を選択してください。")

    # ④ 慣習化
    if state.s2_habit:
        st.subheader("④ 慣習化")

        habits = state.mtplus1.get("habits", [])
        if not habits:
            st.error("『慣習化』候補が存在しません。")
        else:
            idx_habit = st.radio(
                "以下の選択肢の中から、最も共感する未来人が共有する習慣を一つ選んでください。",
                list(range(len(habits))),
                format_func=lambda i: habits[i],
                key="radio_habit"
            )

            if st.button("④ 慣習化を確定", key="btn_habit"):
                state.choice_habit = idx_habit
                state.s2_ux = True
                st.success("⑤『日常の空間とUX』を選択してください。")

    # ⑤ UX
    if state.s2_ux:
        st.subheader("⑤ 日常の空間とユーザー体験")

        ux_list = state.mtplus1.get("ux_future", [])
        if not ux_list:
            st.error("『日常の空間とUX』候補が存在しません。")
        else:
            idx_ux = st.radio(
                "以下の選択肢の中から、最も共感する未来人が共有するユーザー体験を一つ選んでください。",
                list(range(len(ux_list))),
                format_func=lambda i: ux_list[i],
                key="radio_ux"
            )

            if st.button("三世代HPモデルを完成させる", key="btn_finish", type="primary"):
                state.choice_ux = idx_ux

                # generate.py に候補を渡す
                hp_session.mtplus1_candidates = state.mtplus1

                with st.spinner("HPモデル（三世代）を最終生成中…"):
                    hp_session.apply_mtplus1_choices(
                        state.choice_goal,
                        state.choice_value,
                        state.choice_habit,
                        state.choice_ux,
                    )
                    hp_session.wait_all()
                    state.hp_json = hp_session.to_dict()

                state.step4 = True
                st.success("HPモデルが完成しました！ステップ 3 へ。")


# ============================================================
#   🟪 ステップ3：SF物語アウトライン生成（改進 / 確定）
# ============================================================

if state.step4 and state.hp_json:
    st.header("ステップ 3：SF物語アウトライン生成", divider="grey")

    # -------------------------------
    # ① 初次生成アウトライン
    # -------------------------------
    if state.outline is None:
        if st.button("✨ アウトラインを生成", key="btn_generate_outline"):
            with st.spinner("GPT によるアウトライン生成中…"):
                hp = state.hp_json
                state.outline = generate_outline(
                    theme="未来社会",
                    scene="（ユーザー設定なし）",
                    ap_model_history=[
                        {"ap_model": hp.get("hp_mt_0", {})},
                        {"ap_model": hp.get("hp_mt_1", {})},
                        {"ap_model": hp.get("hp_mt_2", {})},
                    ],
                )
            st.success("アウトラインが生成されました。")
            st.rerun()

    # -------------------------------
    # ② アウトライン表示 & 改進
    # -------------------------------
    if state.outline:

        # ⭐ 动态容器（text_area を毎回再描画するため）
        st.subheader("現在のアウトライン：")
        outline_container = st.empty()

        # 上下换行、只读显示最新内容
        outline_container.text_area(
            label="",
            value=state.outline,
            height=300,
            disabled=True
        )

        # 左右按钮
        col1, col2 = st.columns(2)

        # -------------------------------
        # 🟦 改進
        # -------------------------------
        with col1:
            mod = st.text_area("修正提案：", height=100, key="outline_modify")

            if st.button("🔁 改進", key="btn_modify"):
                if mod.strip():
                    with st.spinner("アウトライン修正中…"):
                        new_outline = modify_outline(state.outline, mod)
                        state.outline = new_outline

                    st.success("アウトラインが更新されました。")

                    # ⭐ 强制刷新 → 新内容立即显示在上方
                    st.rerun()

                else:
                    st.warning("修正内容を入力してください。")

        # -------------------------------
        # 🟩 確定
        # -------------------------------
        with col2:
            if st.button("✔️ 確定", key="btn_confirm"):
                state.final_confirmed = True
                st.success("確定しました！下にダウンロードボタンが表示されます。")


# ============================================================
#   🟫 STEP4：ダウンロード（確定後に表示）
# ============================================================

if state.final_confirmed and state.hp_json and state.outline:
    st.header("ダウンロード", divider="grey")

    st.download_button(
        "⬇️ HPモデル（hp_output.json）",
        json.dumps(state.hp_json, ensure_ascii=False, indent=2),
        "hp_output.json",
        "application/json",
        key="download_hp"
    )

    st.download_button(
        "⬇️ アウトライン（outline.txt）",
        state.outline,
        "outline.txt",
        "text/plain",
        key="download_outline"
    )
