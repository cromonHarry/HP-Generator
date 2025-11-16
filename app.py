# app.py
import json
import streamlit as st

from generate import HPGenerationSession
from outline import generate_outline, modify_outline

# ===== ページ設定 =====
st.set_page_config(
    page_title="HPモデル SFプロット生成ツール",
    page_icon="🛰️",
    layout="centered",
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.0rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .sub-title {
        font-size: 0.9rem;
        color: #666666;
        margin-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">HPモデル × GPT × Tavily によるSFプロット生成ツール</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">あなたの経験をもとに、三世代のHPモデルとSF物語のアウトラインを共創します。</div>', unsafe_allow_html=True)

# ===== セッション状態の初期化 =====
session_defaults = {
    "hp_session": HPGenerationSession(),
    "adv_candidates": None,
    "mtplus1_candidates": None,
    "hp_json": None,
    "outline_text": None,

    # UI フラグ
    "show_q2": False,
    "show_q3": False,
    "show_q4": False,
    "show_step2": False,
    "show_step3": False,
    "show_step4": False,

    # Step3 の段階
    "show_step3_goal": False,
    "show_step3_value": False,
    "show_step3_habit": False,
    "show_step3_ux": False,

    # Step3 の選択内容
    "step3_goal_choice": None,
    "step3_value_choice": None,
    "step3_habit_choice": None,
    "step3_ux_choice": None,
}
for key, val in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

hp_session: HPGenerationSession = st.session_state.hp_session

# ---------------------------------------------------------
# ---------------------- ステップ1：Q1〜Q4 ----------------
# ---------------------------------------------------------

st.header("ステップ 1：あなたの経験についての4つの質問", divider="grey")

# ------------------- Q1 -------------------
st.markdown("### Q1（Mt：日常の空間とユーザー体験）")
q1 = st.text_area("最近、「自分は他の人と違うかもしれない」と感じた行動はありますか？", key="q1", height=60)

if st.button("Q1 を送信する", key="btn_q1"):
    if not q1.strip():
        st.warning("Q1に回答してください。")
    else:
        st.session_state.show_q2 = True
        hp_session.handle_input1(q1)
        st.success("Q1 を受け取りました。続いて Q2 にお答えください。")

# ------------------- Q2 -------------------
if st.session_state.show_q2:
    st.markdown("### Q2（Mt：製品・サービス）")
    q2 = st.text_area("その行動を実現するために、どのような製品・サービスを使っていますか？", key="q2", height=60)

    if st.button("Q2 を送信する", key="btn_q2"):
        if not q2.strip():
            st.warning("Q2に回答してください。")
        else:
            st.session_state.show_q3 = True
            hp_session.handle_input2(q2)
            st.success("Q2 を受け取りました。続いて Q3 にお答えください。")

# ------------------- Q3 -------------------
if st.session_state.show_q3:
    st.markdown("### Q3（Mt：意味付け）")
    q3 = st.text_area("なぜ、そのような製品・サービスを選ぶのだと思いますか？", key="q3", height=60)

    if st.button("Q3 を送信する", key="btn_q3"):
        if not q3.strip():
            st.warning("Q3に回答してください。")
        else:
            st.session_state.show_q4 = True
            hp_session.handle_input3(q3)
            st.success("Q3 を受け取りました。続いて Q4 にお答えください。")

# ------------------- Q4 -------------------
if st.session_state.show_q4:
    st.markdown("### Q4（Mt：人々の価値観）")
    q4 = st.text_area("その行動を通じて、どんな自分でありたいと思っていますか？", key="q4", height=60)

    if st.button("Q4 を送信して HP モデル生成（第1フェーズ）開始", key="btn_q4"):
        if not q4.strip():
            st.warning("Q4に回答してください。")
        else:
            with st.spinner("Tavily と GPT を用いて Mt・Mt-1・Mt+1 の情報を生成しています…"):
                hp_session.start_from_values(q4)
                adv_candidates = hp_session.get_future_adv_candidates()

            st.session_state.adv_candidates = adv_candidates
            st.session_state.show_step2 = True

            st.success("第1フェーズが完了しました！ステップ2に進んでください。")

# ---------------------------------------------------------
# ---------------------- ステップ2 -------------------------
# ---------------------------------------------------------
if st.session_state.show_step2 and st.session_state.adv_candidates:
    st.header("ステップ 2：Mt+1 の前衛的社会問題を選ぶ", divider="grey")

    adv_candidates = st.session_state.adv_candidates

    selected_adv_idx = st.radio(
        "未来社会（Mt+1）の根本的な『前衛的社会問題』として適切なものを1つ選んでください：",
        options=list(range(len(adv_candidates))),
        format_func=lambda i: adv_candidates[i],
    )

    if st.button("前衛的社会問題を確定し、次へ進む", key="btn_step2"):
        hp_session.set_future_adv_choice(adv_candidates[selected_adv_idx])
        with st.spinner("Mt+1 の目標候補を生成しています…"):
            # ここでは目標だけを生成する（後続の項目は後から生成）
            hp_session.mtplus1_candidates = {}
            hp_session.mtplus1_candidates["goals"] = hp_session.list_up_gpt(
                "前衛的社会問題",
                adv_candidates[selected_adv_idx],
                "社会の目標",
            )

        st.session_state.mtplus1_candidates = hp_session.mtplus1_candidates
        st.session_state.show_step3 = True
        st.session_state.show_step3_goal = True
        st.success("ステップ3に進んでください。")

# ---------------------------------------------------------
# ---------------------- ステップ3：段階的 -----------------
# ---------------------------------------------------------
if st.session_state.show_step3 and st.session_state.mtplus1_candidates:
    st.header("ステップ 3：Mt+1 の4要素を段階的に選ぶ", divider="grey")

    cands = st.session_state.mtplus1_candidates

    # --- (1) 社会の目標 ---
    if st.session_state.show_step3_goal:
        st.subheader("① Mt+1：社会の目標")
        idx_goals = st.radio(
            "未来社会が目指すゴールを1つ選んでください：",
            list(range(len(cands["goals"]))),
            format_func=lambda i: cands["goals"][i],
            key="idx_goals",
        )

        if st.button("社会の目標を確定する", key="btn_goal"):
            st.session_state.step3_goal_choice = idx_goals

            # ここで「人々の価値観」の候補生成
            with st.spinner("Mt+1 の『人々の価値観』候補を生成しています…"):
                chosen_goal = cands["goals"][idx_goals]
                cands["values"] = hp_session.list_up_gpt(
                    "社会の目標",
                    chosen_goal,
                    "人々の価値観",
                )

            st.session_state.show_step3_value = True
            st.success("②『人々の価値観』を選択してください。")

    # --- (2) 人々の価値観 ---
    if st.session_state.show_step3_value:
        st.subheader("② Mt+1：人々の価値観")

        idx_values = st.radio(
            "未来の人々が共有する価値観を1つ選んでください：",
            list(range(len(cands["values"]))),
            format_func=lambda i: cands["values"][i],
            key="idx_values_step3",
        )

        if st.button("価値観を確定する", key="btn_values"):
            st.session_state.step3_value_choice = idx_values

            # 価値観を選んだら慣習化とUX候補を生成
            with st.spinner("『慣習化』と『日常の空間とUX』の候補を生成しています…"):
                chosen_value = cands["values"][idx_values]

                cands["habits"] = hp_session.list_up_gpt(
                    "人々の価値観",
                    chosen_value,
                    "慣習化",
                )
                cands["ux_future"] = hp_session.list_up_gpt(
                    "慣習化",
                    cands["habits"][0],
                    "日常の空間とユーザー体験",
                )

            st.session_state.show_step3_habit = True
            st.success("③『慣習化』を選択してください。")

    # --- (3) 慣習化 ---
    if st.session_state.show_step3_habit:
        st.subheader("③ Mt+1：慣習化")

        idx_habits = st.radio(
            "価値観がどのように日常に根付いているか、最も近いものを選んでください：",
            list(range(len(cands["habits"]))),
            format_func=lambda i: cands["habits"][i],
            key="idx_habits_step3",
        )

        if st.button("慣習化を確定する", key="btn_habits"):
            st.session_state.step3_habit_choice = idx_habits
            st.session_state.show_step3_ux = True
            st.success("④『日常の空間とUX』を選択してください。")

    # --- (4) 日常の空間とユーザー体験 ---
    if st.session_state.show_step3_ux:
        st.subheader("④ Mt+1：日常の空間とユーザー体験")

        idx_ux = st.radio(
            "未来の典型的な日常空間・UXを選んでください：",
            list(range(len(cands["ux_future"]))),
            format_func=lambda i: cands["ux_future"][i],
            key="idx_ux_step3",
        )

        if st.button("三世代HPモデルを完成させる", key="btn_complete_hp", type="primary"):
            st.session_state.step3_ux_choice = idx_ux

            with st.spinner("Mt+1 の連鎖生成と Mt・Mt-1 の最終処理を待っています…"):
                hp_session.apply_mtplus1_choices(
                    st.session_state.step3_goal_choice,
                    st.session_state.step3_value_choice,
                    st.session_state.step3_habit_choice,
                    st.session_state.step3_ux_choice,
                )
                hp_session.wait_all()
                st.session_state.hp_json = hp_session.to_dict()

            st.session_state.show_step4 = True
            st.success("HPモデル（三世代）が完成しました！ステップ4へ進んでください。")

# ---------------------------------------------------------
# ---------------------- ステップ4：アウトライン ----------
# ---------------------------------------------------------
if st.session_state.show_step4 and st.session_state.hp_json:
    st.header("ステップ 4：HPモデルをもとにSF物語のアウトライン生成", divider="grey")

    if st.button("✨ アウトラインを生成する"):
        with st.spinner("GPT による物語アウトライン生成中…"):
            outline_text = generate_outline(
                theme="未来社会",
                scene="（ユーザー入力なし）",
                ap_model_history=[
                    {"ap_model": st.session_state.hp_json.get("hp_mt_0", {})},
                    {"ap_model": st.session_state.hp_json.get("hp_mt_1", {})},
                    {"ap_model": st.session_state.hp_json.get("hp_mt_2", {})},
                ],
            )
        st.session_state.outline_text = outline_text
        st.success("アウトラインが生成されました。")

    if st.session_state.outline_text:
        st.markdown("**現在のアウトライン：**")
        st.text_area("", st.session_state.outline_text, height=300)

        mod = st.text_area("修正したい点があれば入力してください：", height=100)

        if st.button("🔁 修正意見を反映して再生成"):
            if not mod.strip():
                st.warning("修正内容を入力してください。")
            else:
                with st.spinner("修正意見に基づきアウトラインを更新しています…"):
                    new_outline = modify_outline(st.session_state.outline_text, mod)
                st.session_state.outline_text = new_outline
                st.success("アウトラインが更新されました。")

        # ダウンロード
        hp_json_str = json.dumps(st.session_state.hp_json, ensure_ascii=False, indent=2)
        st.download_button("⬇️ HPモデル（json）をダウンロード", hp_json_str, "hp_output.json", "application/json")
        st.download_button("⬇️ 物語アウトラインをダウンロード", st.session_state.outline_text, "outline.txt", "text/plain")