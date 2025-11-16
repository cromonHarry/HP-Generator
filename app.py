# app.py
import json
import streamlit as st

from generate import HPGenerationSession
from outline import generate_outline, modify_outline
from prompt import list_up_gpt  # 必须引入

# ===== ページ設定 =====
st.set_page_config(
    page_title="HPモデル SFプロット生成ツール",
    page_icon="🛰️",
    layout="centered",
)

# ===== タイトル =====
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
#   🧠 セッション初期化 (一次性管理，结构更干净)
# ============================================================
DEFAULT_STATE = {
    "hp_session": HPGenerationSession(),
    "adv_candidates": None,
    "mtplus1": {},  # Step3 の候補をここにまとめる

    # ステップ表示フラグ
    "q2": False, "q3": False, "q4": False,
    "step2": False, "step3": False, "step4": False,

    # Step3 段階フラグ
    "s3_goal": False,
    "s3_value": False,
    "s3_habit": False,
    "s3_ux": False,

    # Step3 選択
    "choice_goal": None,
    "choice_value": None,
    "choice_habit": None,
    "choice_ux": None,

    # 生成結果
    "hp_json": None,
    "outline": None,
}

for key, val in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = val


# 快速引用
state = st.session_state
hp_session: HPGenerationSession = state.hp_session


# ============================================================
#   🟦 ステップ1：Q1〜Q4（逐步式）
# ============================================================

st.header("ステップ 1：あなたの経験についての4つの質問", divider="grey")

# ----- Q1 -----
st.subheader("Q1（Mt：日常の空間とユーザー体験）")
q1 = st.text_area("最近、「自分は他の人と違うかもしれない」と感じた行動は？", key="q1", height=60)

if st.button("Q1 を送信", key="btn_q1"):
    if not q1.strip():
        st.warning("Q1に回答してください。")
    else:
        hp_session.handle_input1(q1)
        state.q2 = True
        st.success("Q1 を受け取りました。続いて Q2 へ。")

# ----- Q2 -----
if state.q2:
    st.subheader("Q2（Mt：製品・サービス）")
    q2 = st.text_area("その行動のために使用している製品・サービスは？", key="q2", height=60)

    if st.button("Q2 を送信", key="btn_q2"):
        if not q2.strip():
            st.warning("Q2に回答してください。")
        else:
            hp_session.handle_input2(q2)
            state.q3 = True
            st.success("Q2 を受け取りました。続いて Q3 へ。")

# ----- Q3 -----
if state.q3:
    st.subheader("Q3（Mt：意味付け）")
    q3 = st.text_area("なぜ、その製品・サービスを使っていると思いますか？", key="q3", height=60)

    if st.button("Q3 を送信", key="btn_q3"):
        if not q3.strip():
            st.warning("Q3に回答してください。")
        else:
            hp_session.handle_input3(q3)
            state.q4 = True
            st.success("Q3 を受け取りました。続いて Q4 へ。")

# ----- Q4 -----
if state.q4:
    st.subheader("Q4（Mt：人々の価値観）")
    q4 = st.text_area("その行動を通じて、どんな自分でありたいですか？", key="q4", height=60)

    if st.button("Q4 を送信して HPモデル生成開始", key="btn_q4"):
        if not q4.strip():
            st.warning("Q4に回答してください。")
        else:
            with st.spinner("Mt・Mt-1・Mt+1 の初期情報を生成中…"):
                hp_session.start_from_values(q4)
                adv = hp_session.get_future_adv_candidates()
            state.adv_candidates = adv
            state.step2 = True
            st.success("第1フェーズ完了。ステップ2へ。")


# ============================================================
#   🟩 ステップ2：Mt+1 前衛的社会問題（5択）
# ============================================================
if state.step2 and state.adv_candidates:
    st.header("ステップ 2：Mt+1 の前衛的社会問題を選ぶ", divider="grey")

    adv_list = state.adv_candidates
    idx_adv = st.radio("未来社会の根本的な『前衛的社会問題』を選択：",
                       options=list(range(len(adv_list))),
                       format_func=lambda i: adv_list[i])

    if st.button("前衛的社会問題を確定", key="btn_adv"):
        hp_session.set_future_adv_choice(adv_list[idx_adv])

        # Step3 の最初：社会の目標候補を生成
        with st.spinner("Mt+1『社会の目標』候補を生成中…"):
            state.mtplus1 = {"goals": list_up_gpt("前衛的社会問題", adv_list[idx_adv], "社会の目標")}

        state.step3 = True
        state.s3_goal = True
        st.success("次は『社会の目標』を選択してください。")


# ============================================================
#   🟧 ステップ3：Mt+1 の4要素（逐步式）
# ============================================================

if state.step3:

    cands = state.mtplus1

    # --- ① 社会の目標 ---
    if state.s3_goal:
        st.header("ステップ 3：Mt+1 の4要素を段階的に選択", divider="grey")
        st.subheader("① 社会の目標")

        idx_goal = st.radio(
            "未来社会が目指すゴール：",
            list(range(len(cands["goals"]))),
            format_func=lambda i: cands["goals"][i],
        )

        if st.button("① 社会の目標を確定", key="btn_goal"):
            state.choice_goal = idx_goal

            # 次の候補生成（価値観）
            with st.spinner("『人々の価値観』候補を生成中…"):
                chosen_goal = cands["goals"][idx_goal]
                cands["values"] = list_up_gpt("社会の目標", chosen_goal, "人々の価値観")

            state.s3_value = True
            st.success("②『人々の価値観』を選択してください。")

    # --- ② 人々の価値観 ---
    if state.s3_value:
        st.subheader("② 人々の価値観")

        idx_value = st.radio(
            "未来の人々が共有する価値観：",
            list(range(len(cands["values"]))),
            format_func=lambda i: cands["values"][i],
        )

        if st.button("② 人々の価値観を確定", key="btn_value"):
            state.choice_value = idx_value

            # 次の候補生成（慣習化 / UX）
            with st.spinner("『慣習化』と『日常の空間とUX』候補を生成中…"):
                chosen_value = cands["values"][idx_value]
                cands["habits"] = list_up_gpt("人々の価値観", chosen_value, "慣習化")
                cands["ux_future"] = list_up_gpt("慣習化", cands["habits"][0], "日常の空間とユーザー体験")

            state.s3_habit = True
            st.success("③『慣習化』を選択してください。")

    # --- ③ 慣習化 ---
    if state.s3_habit:
        st.subheader("③ 慣習化")

        idx_habit = st.radio(
            "価値観がどのように日常へ定着しているか：",
            list(range(len(cands["habits"]))),
            format_func=lambda i: cands["habits"][i],
        )

        if st.button("③ 慣習化を確定", key="btn_habit"):
            state.choice_habit = idx_habit
            state.s3_ux = True
            st.success("④『日常の空間とUX』を選択してください。")

    # --- ④ UX ---
    if state.s3_ux:
        st.subheader("④ 日常の空間とユーザー体験")

        idx_ux = st.radio(
            "未来の典型的な日常空間とUX：",
            list(range(len(cands["ux_future"]))),
            format_func=lambda i: cands["ux_future"][i],
        )

        if st.button("三世代HPモデルを完成", key="btn_finish", type="primary"):
            state.choice_ux = idx_ux

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
#   🟪 ステップ4：SFアウトライン生成
# ============================================================

if state.step4 and state.hp_json:
    st.header("ステップ 4：SF物語アウトライン生成", divider="grey")

    if st.button("✨ アウトラインを生成"):
        with st.spinner("GPT によるアウトライン生成中…"):
            data = state.hp_json
            outline = generate_outline(
                theme="未来社会",
                scene="（ユーザー入力なし）",
                ap_model_history=[
                    {"ap_model": data.get("hp_mt_0", {})},
                    {"ap_model": data.get("hp_mt_1", {})},
                    {"ap_model": data.get("hp_mt_2", {})},
                ],
            )
        state.outline = outline
        st.success("アウトラインが生成されました！")

    if state.outline:
        st.text_area("現在のアウトライン：", state.outline, height=280)

        mod = st.text_area("修正したい点があれば入力：", height=100)

        if st.button("🔁 修正意見を反映"):
            if not mod.strip():
                st.warning("修正内容を入力してください。")
            else:
                with st.spinner("アウトライン修正中…"):
                    state.outline = modify_outline(state.outline, mod)
                st.success("アウトラインを更新しました。")

        # ダウンロード
        st.download_button("⬇️ HPモデルをダウンロード（json）",
                           json.dumps(state.hp_json, ensure_ascii=False, indent=2),
                           "hp_output.json", "application/json")

        st.download_button("⬇️ アウトラインをダウンロード（txt）",
                           state.outline, "outline.txt", "text/plain")
