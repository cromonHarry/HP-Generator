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
st.markdown('<div class="sub-title">あなたの経験をもとに三世代のHPモデルとSF物語アウトラインを共創します。</div>', unsafe_allow_html=True)


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

        # Step1
        "show_q2": False,
        "show_q3": False,
        "show_q4": False,

        # Step2～Step4
        "step2": False,
        "step3": False,
        "step4": False,

        # Step3 段階
        "s3_goal": False,
        "s3_value": False,
        "s3_habit": False,
        "s3_ux": False,

        # Step3 用户选择
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
    "最近、『自分は他の人と違うかもしれない』と感じた行動は？",
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
        "その行動を実現するために使用している製品・サービスは？",
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
        "なぜ、その製品・サービスを使っていると思いますか？",
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

    if st.button("Q4 を送信して HPモデル生成開始", key="btn_q4"):
        if not q4.strip():
            st.warning("Q4に回答してください。")
        else:
            with st.spinner("Mt・Mt-1・Mt+1 の初期情報を生成中…"):
                hp_session.start_from_values(q4)
                state.adv_candidates = hp_session.get_future_adv_candidates()

            state.step2 = True
            st.success("第1フェーズ完了！ステップ2へ。")


# ============================================================
#   🟩 ステップ2：Mt+1 前衛的社会問題
# ============================================================

if state.step2 and state.adv_candidates:
    st.header("ステップ 2：Mt+1 の前衛的社会問題を選ぶ", divider="grey")

    adv = state.adv_candidates
    idx_adv = st.radio(
        "未来社会の根本となる『前衛的社会問題』を選択：",
        list(range(len(adv))), format_func=lambda i: adv[i],
        key="adv_select"
    )

    if st.button("前衛的社会問題を確定", key="btn_adv"):
        hp_session.set_future_adv_choice(adv[idx_adv])

        with st.spinner("Mt+1 の『社会の目標』候補を生成しています…"):
            state.mtplus1 = {
                "goals": list_up_gpt("前衛的社会問題", adv[idx_adv], "社会の目標")
            }

        state.step3 = True
        state.s3_goal = True
        st.success("次へ：『社会の目標』を選んでください。")


# ============================================================
#   🟧 ステップ3：Mt+1 の4要素（逐步式）
# ============================================================

if state.step3:
    cands = state.mtplus1

    # ---------- ① 社会の目標 ----------
    if state.s3_goal:
        st.header("ステップ 3：Mt+1 の4要素を段階的に選択", divider="grey")
        st.subheader("① 社会の目標")

        idx_goal = st.radio(
            "未来社会が目指すゴール：",
            list(range(len(cands["goals"]))),
            format_func=lambda i: cands["goals"][i],
            key="goal_radio"
        )

        if st.button("① 社会の目標を確定", key="btn_goal"):
            state.choice_goal = idx_goal

            with st.spinner("『人々の価値観』候補を生成中…"):
                goal_text = cands["goals"][idx_goal]
                cands["values"] = list_up_gpt("社会の目標", goal_text, "人々の価値観")

            state.s3_value = True
            st.success("②『人々の価値観』を選択してください。")


    # ---------- ② 人々の価値観 ----------
    if state.s3_value:
        st.subheader("② 人々の価値観")

        idx_value = st.radio(
            "未来の人々が共有する価値観：",
            list(range(len(cands["values"]))),
            format_func=lambda i: cands["values"][i],
            key="value_radio"
        )

        if st.button("② 人々の価値観を確定", key="btn_value"):
            state.choice_value = idx_value

            with st.spinner("『慣習化』および『日常の空間とUX』候補を生成中…"):
                value_text = cands["values"][idx_value]
                cands["habits"] = list_up_gpt("人々の価値観", value_text, "慣習化")

                base_habit = cands["habits"][0] if cands["habits"] else ""
                cands["ux_future"] = list_up_gpt("慣習化", base_habit, "日常の空間とユーザー体験")

            state.s3_habit = True
            st.success("③『慣習化』を選択してください。")


    # ---------- ③ 慣習化 ----------
    if state.s3_habit:
        st.subheader("③ 慣習化")

        idx_habit = st.radio(
            "価値観がどのように日常へ定着するか：",
            list(range(len(cands["habits"]))),
            format_func=lambda i: cands["habits"][i],
            key="habit_radio"
        )

        if st.button("③ 慣習化を確定", key="btn_habit"):
            state.choice_habit = idx_habit
            state.s3_ux = True
            st.success("④『日常の空間とUX』を選択してください。")


    # ---------- ④ UX ----------
    if state.s3_ux:
        st.subheader("④ 日常の空間とユーザー体験")

        idx_ux = st.radio(
            "未来の日常空間・ユーザー体験：",
            list(range(len(cands["ux_future"]))),
            format_func=lambda i: cands["ux_future"][i],
            key="ux_radio"
        )

        if st.button("三世代HPモデルを完成させる", key="btn_finish", type="primary"):
            state.choice_ux = idx_ux

            # 🚨 修复：把 Step3 的候选同步给 hp_session
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
            st.success("HPモデルが完成しました！ステップ4へ。")


# ============================================================
#   🟪 ステップ4：SF物語アウトライン生成
# ============================================================

if state.step4 and state.hp_json:
    st.header("ステップ 4：SF物語アウトライン生成", divider="grey")

    if st.button("✨ アウトラインを生成", key="btn_outline"):
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

    if state.outline:
        st.text_area("現在のアウトライン：", state.outline, height=300, key="outline_display")

        mod = st.text_area("修正したい点があれば入力：", height=100, key="outline_modify")

        if st.button("🔁 修正意見を反映", key="btn_outline_fix"):
            if not mod.strip():
                st.warning("修正内容を入力してください。")
            else:
                with st.spinner("アウトライン修正中…"):
                    state.outline = modify_outline(state.outline, mod)
                st.success("アウトラインを更新しました。")

        st.download_button(
            "⬇️ HPモデルをダウンロード（hp_output.json）",
            json.dumps(state.hp_json, ensure_ascii=False, indent=2),
            "hp_output.json",
            "application/json",
            key="download_hp"
        )

        st.download_button(
            "⬇️ アウトラインをダウンロード（outline.txt）",
            state.outline,
            "outline.txt",
            "text/plain",
            key="download_outline"
        )
