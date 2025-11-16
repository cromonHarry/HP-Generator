# app.py
import json
import streamlit as st

from generate import HPGenerationSession
from outline import generate_outline, modify_outline

# ===== ページ設定 =====
st.set_page_config(
    page_title="HPモデル SFプロット生成ツール",
    page_icon="🛰️",
    layout="wide",
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
if "hp_session" not in st.session_state:
    st.session_state.hp_session = HPGenerationSession()

if "adv_candidates" not in st.session_state:
    st.session_state.adv_candidates = None

if "mtplus1_candidates" not in st.session_state:
    st.session_state.mtplus1_candidates = None

if "hp_json" not in st.session_state:
    st.session_state.hp_json = None

if "outline_text" not in st.session_state:
    st.session_state.outline_text = None

# 各ステップの表示管理
for key in ["show_q2", "show_q3", "show_q4", "show_step2", "show_step3", "show_step4"]:
    if key not in st.session_state:
        st.session_state[key] = False

hp_session: HPGenerationSession = st.session_state.hp_session

# ===== 左右レイアウト =====
col_left, col_right = st.columns([1.3, 1.0])

# ---------------------------------------------------------
# ---------------------- 左側：Q1〜Q4 ---------------------
# ---------------------------------------------------------
with col_left:
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

                if adv_candidates:
                    st.success("第1フェーズが完了しました！ステップ2に進んでください。")
                else:
                    st.error("Mt+1 の前衛的社会問題候補の生成に失敗しました。")

# ---------------------------------------------------------
# ---------------------- ステップ2 -------------------------
# ---------------------------------------------------------
with col_left:
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
            with st.spinner("Mt+1 の他の候補（目標・価値観・慣習・UX）を生成しています…"):
                hp_session.generate_mtplus1_candidates()

            st.session_state.mtplus1_candidates = hp_session.mtplus1_candidates
            st.session_state.show_step3 = True
            st.success("Mt+1 の候補生成が完了しました。ステップ3に進んでください。")

# ---------------------------------------------------------
# ---------------------- ステップ3 -------------------------
# ---------------------------------------------------------
with col_left:
    if st.session_state.show_step3 and st.session_state.mtplus1_candidates:
        st.header("ステップ 3：Mt+1 の4要素を選ぶ（5択）", divider="grey")

        cands = st.session_state.mtplus1_candidates
        idx_goals = st.radio("Mt+1：社会の目標", list(range(len(cands["goals"]))), format_func=lambda i: cands["goals"][i])
        idx_values = st.radio("Mt+1：人々の価値観", list(range(len(cands["values"]))), format_func=lambda i: cands["values"][i])
        idx_habits = st.radio("Mt+1：慣習化", list(range(len(cands["habits"]))), format_func=lambda i: cands["habits"][i])
        idx_ux = st.radio("Mt+1：日常の空間とユーザー体験", list(range(len(cands["ux_future"]))), format_func=lambda i: cands["ux_future"][i])

        if st.button("三世代HPモデルを完成させる", key="btn_step3"):
            with st.spinner("Mt+1 の連鎖生成と Mt/Mt-1 の最終処理を待っています…"):
                hp_session.apply_mtplus1_choices(idx_goals, idx_values, idx_habits, idx_ux)
                hp_session.wait_all()
                hp_json = hp_session.to_dict()

            st.session_state.hp_json = hp_json
            st.session_state.show_step4 = True
            st.success("HPモデル（三世代）が完成しました！ステップ4へ進んでください。")

# ---------------------------------------------------------
# ---------------------- ステップ4：右側 -------------------
# ---------------------------------------------------------
with col_right:
    if st.session_state.show_step4 and st.session_state.hp_json:
        st.header("ステップ 4：HPモデルをもとにSF物語のアウトライン生成", divider="grey")

        if st.button("✨ アウトラインを生成する", use_container_width=True):
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

            if st.button("🔁 修正意見を反映して再生成", use_container_width=True):
                if not mod.strip():
                    st.warning("修正内容を入力してください。")
                else:
                    with st.spinner("修正意見に基づきアウトラインを更新しています…"):
                        new_outline = modify_outline(st.session_state.outline_text, mod)
                    st.session_state.outline_text = new_outline
                    st.success("アウトラインが更新されました。")

            # ダウンロード
            hp_json_str = json.dumps(st.session_state.hp_json, ensure_ascii=False, indent=2)
            st.download_button("⬇️ HPモデル（json）をダウンロード", hp_json_str, "hp_output.json", "application/json", use_container_width=True)
            st.download_button("⬇️ 物語アウトラインをダウンロード", st.session_state.outline_text, "outline.txt", "text/plain", use_container_width=True)
