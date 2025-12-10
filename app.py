# app.py
import json
import streamlit as st

from generate import HPGenerationSession
from outline import generate_outline, modify_outline
from prompt import list_up_gpt
from visualization import render_hp_visualization


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
st.markdown('<div class="sub-title">あなたの経験をもとに三世代HPモデルとSF物語ストーリー概要を共創します。</div>', unsafe_allow_html=True)


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

        # Step2 状態
        "step2": False,
        "s2_adv": False,
        "s2_goal": False,
        "s2_value": False,
        "s2_habit": False,
        "s2_ux": False,
        
        # Step3 (完了) 状態
        "step4": False,

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
#   Utilities: Back & Regenerate
# ============================================================

# 前の選択肢を遡って選択できる機能
def go_back():
    if state.s2_ux:
        state.s2_ux = False
        state.choice_ux = None
    elif state.s2_habit:
        state.s2_habit = False
        state.choice_habit = None
    elif state.s2_value:
        state.s2_value = False
        state.choice_value = None
    elif state.s2_goal:
        state.s2_goal = False
        state.choice_goal = None
    elif state.s2_adv:
        # Step 2 -> Step 1 end
        state.step2 = False
        state.s2_adv = False
        state.choice_adv = None

# 選択肢を再提示する機能
def regenerate_adv():
    with st.spinner("前衛的社会問題の候補を再生成中（ユーザー入力をより強く反映します）..."):
        hp_session.trigger_adv_candidates_generation()
        hp_session.wait_all() # wait for result
        state.adv_candidates = hp_session.get_future_adv_candidates()

# ============================================================
#   🟦 ステップ1：Q1〜Q4
# ============================================================

st.header("ステップ 1：あなたの経験についての4つの質問", divider="grey")

# ---------- Q1 ----------
st.subheader("Q1（Mt：日常の空間とユーザー体験）")
q1_label = "あなたがすきなことをしている情景を思い出して、どのような時に、どのような場所で何をしているかという体験を書き出してください。"
q1 = st.text_area(q1_label, key="input_q1", height=80)

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
    q2_label = "その一連の体験を成立させるために重要な製品やサービスを挙げてください。"
    q2 = st.text_area(q2_label, key="input_q2", height=60)

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
    q3_label = "あなたは、何のためにその製品やサービスを使用していますか？"
    q3 = st.text_area(q3_label, key="input_q3", height=60)

    if st.button("Q3 を送信", key="btn_q3"):
        if not q3.strip():
            st.warning("Q3に回答してください。")
        else:
            hp_session.handle_input3(q3)
            state.show_q4 = True
            st.success("Q3 を受け取りました。続いて Q4 へ。")

# ---------- Q4 ----------
if state.show_q4 and not state.step2:
    st.subheader("Q4（Mt：人々の価値観）")
    q4_label = "そのような体験を行うあなたはどんな自分でありたいですか？"
    q4 = st.text_area(q4_label, key="input_q4", height=60)

    if st.button("Q4 を送信して Step2 開始", key="btn_q4"):
        if not q4.strip():
            st.warning("Q4に回答してください。")
        else:
            with st.spinner("Mt・Mt-1・Mt+1 の初期情報を生成中（あなたの価値観を未来へ接続します）…"):
                hp_session.start_from_values_and_trigger_future(q4)
                # wait for future candidates immediately for UI
                hp_session.wait_all()
                state.adv_candidates = hp_session.get_future_adv_candidates()

            state.step2 = True
            state.s2_adv = True
            st.rerun()


# ============================================================
#   🟩 ステップ2：未来社会 5つの選択
# ============================================================

# (Mt+1) を削除
if state.step2:
    st.header("ステップ 2：未来社会を構成する5つの選択", divider="grey")

    # ① 前衛的社会問題
    if state.s2_adv and not state.s2_goal:
        st.subheader("① 前衛的社会問題")

        adv = state.adv_candidates or []
        if not adv:
            st.error("前衛的社会問題の候補生成に失敗しました。再生成を試してください。")
        else:
            idx_adv = st.radio(
                "あなたの価値観と体験から推測される、未来の「前衛的社会問題」です。最も共感するものを一つ選んでください。",
                list(range(len(adv))),
                format_func=lambda i: adv[i],
                key="radio_adv"
            )

            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("戻る", key="back_adv"):
                    go_back()
                    st.rerun()
            with col2:
                # 再生成ボタン
                if st.button("候補を再生成", key="regen_adv"):
                    regenerate_adv()
                    st.rerun()
            with col3:
                if st.button("① 確定して次へ", key="btn_adv", type="primary"):
                    state.choice_adv = idx_adv
                    hp_session.set_future_adv_choice(adv[idx_adv])

                    with st.spinner("『社会の目標』候補を生成中…"):
                        # Chain start
                        hp_session.generate_mtplus1_candidates_chain()
                        # 【重要修正】生成結果をStreamlitのstateに反映させる
                        state.mtplus1 = hp_session.mtplus1_candidates
                    
                    state.s2_goal = True
                    st.rerun()

    # ② 社会の目標
    if state.s2_goal and not state.s2_value:
        st.subheader("② 社会の目標")
        goals = state.mtplus1.get("goals", [])
        
        # 万が一空の場合のエラーハンドリング
        if not goals:
            st.error("候補が生成されていません。前のステップに戻ってやり直してください。")
        else:
            idx_goal = st.radio("選択肢から選んでください:", list(range(len(goals))), format_func=lambda i: goals[i], key="radio_goal")
            
            c1, c2 = st.columns([1, 3])
            if c1.button("戻る", key="back_goal"):
                go_back()
                st.rerun()
            if c2.button("② 確定して次へ", key="btn_goal", type="primary"):
                state.choice_goal = idx_goal
                state.s2_value = True
                st.rerun()

    # ③ 人々の価値観
    if state.s2_value and not state.s2_habit:
        st.subheader("③ 人々の価値観")
        values = state.mtplus1.get("values", [])
        
        idx_value = st.radio("選択肢から選んでください:", list(range(len(values))), format_func=lambda i: values[i], key="radio_value")

        c1, c2 = st.columns([1, 3])
        if c1.button("戻る", key="back_value"):
            go_back()
            st.rerun()
        if c2.button("③ 確定して次へ", key="btn_value", type="primary"):
            state.choice_value = idx_value
            state.s2_habit = True
            st.rerun()

    # ④ 慣習化
    if state.s2_habit and not state.s2_ux:
        st.subheader("④ 慣習化")
        habits = state.mtplus1.get("habits", [])
        
        idx_habit = st.radio("選択肢から選んでください:", list(range(len(habits))), format_func=lambda i: habits[i], key="radio_habit")

        c1, c2 = st.columns([1, 3])
        if c1.button("戻る", key="back_habit"):
            go_back()
            st.rerun()
        if c2.button("④ 確定して次へ", key="btn_habit", type="primary"):
            state.choice_habit = idx_habit
            state.s2_ux = True
            st.rerun()

    # ⑤ UX
    if state.s2_ux and not state.step4:
        st.subheader("⑤ 日常の空間とユーザー体験")
        ux_list = state.mtplus1.get("ux_future", [])
        
        idx_ux = st.radio("選択肢から選んでください:", list(range(len(ux_list))), format_func=lambda i: ux_list[i], key="radio_ux")

        c1, c2 = st.columns([1, 3])
        if c1.button("戻る", key="back_ux"):
            go_back()
            st.rerun()
        
        if c2.button("三世代HPモデルを完成させる", key="btn_finish", type="primary"):
            state.choice_ux = idx_ux

            with st.spinner("HPモデル（三世代）を最終構築中…"):
                hp_session.apply_mtplus1_choices(
                    state.choice_goal,
                    state.choice_value,
                    state.choice_habit,
                    state.choice_ux,
                )
                hp_session.wait_all()
                state.hp_json = hp_session.to_dict()

            state.step4 = True
            st.rerun()


# ============================================================
#   🟪 ステップ3：SF物語アウトライン生成
# ============================================================

if state.step4 and state.hp_json:
    st.header("ステップ 3：HPモデルの可視化 & 物語生成", divider="grey")
    
    st.info("完成したHPモデル（三世代）の構造図です。ノードにマウスを乗せると詳細が表示されます。")
    # visualization.py 側で全ノード描画に対応済み
    render_hp_visualization(state.hp_json)
    
    st.write("---") 

    st.subheader("SF物語ストーリー概要生成")

    if state.outline is None:
        if st.button("✨ ストーリー概要を生成", key="btn_generate_outline"):
            with st.spinner("GPT によるストーリー概要生成中…"):
                hp = state.hp_json
                state.outline = generate_outline(
                    ap_model_history=[
                        {"ap_model": hp.get("hp_mt_0", {})},
                        {"ap_model": hp.get("hp_mt_1", {})},
                        {"ap_model": hp.get("hp_mt_2", {})},
                    ],
                )
            st.success("ストーリー概要が生成されました。")
            st.rerun()

    if state.outline:
        st.subheader("現在のストーリー概要：")
        st.text_area(label="", value=state.outline, height=300, disabled=True)

        col1, col2 = st.columns(2)
        with col1:
            mod = st.text_area("修正提案：", height=100, key="outline_modify")
            if st.button("🔁 更新", key="btn_modify"):
                if mod.strip():
                    with st.spinner("ストーリー概要修正中…"):
                        new_outline = modify_outline(state.outline, mod)
                        state.outline = new_outline
                    st.success("ストーリー概要が更新されました。")
                    st.rerun()
                else:
                    st.warning("修正内容を入力してください。")

        with col2:
            if st.button("✔️ 確定", key="btn_confirm"):
                state.final_confirmed = True
                st.success("確定しました！下にダウンロードボタンが表示されます。")


# ============================================================
#   🟫 STEP4：ダウンロード
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
        "⬇️ ストーリー概要（outline.txt）",
        state.outline,
        "outline.txt",
        "text/plain",
        key="download_outline"
    )