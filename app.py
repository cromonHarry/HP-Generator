# app.py
import json
import streamlit as st

from generate import HPGenerationSession
from outline import modify_outline
from visualization import render_hp_visualization
from story_generator import StoryGenerator # New Story Generator

# ===== ページ設定 =====
st.set_page_config(page_title="Multi-Agent HP Model & Story", page_icon="🧬", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 2.0rem; font-weight: 700; margin-bottom: 0.3rem; }
    .sub-title  { font-size: 0.9rem; color: #666; margin-bottom: 1.5rem; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">Multi-Agent HP Model & Story Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">マルチエージェント討論 (Step 2) と 監督-作家アーキテクチャ (Step 3) を搭載。</div>', unsafe_allow_html=True)

# ============================================================
#   🧠 セッション初期化
# ============================================================
def init_state():
    defaults = {
        "hp_session": HPGenerationSession(),
        "story_gen": StoryGenerator(), # Initialize Story Generator
        "adv_candidates": None,
        "mtplus1": {},
        "hp_json": None,
        "outline": None,
        "final_confirmed": False,

        "show_q2": False,
        "show_q3": False,
        "show_q4": False,

        "step2": False,
        "s2_adv": False,
        "s2_goal": False,
        "s2_value": False,
        "s2_habit": False,
        "s2_ux": False,
        
        "step4": False,
        
        "text_adv": None,
        "text_goal": None,
        "text_value": None,
        "text_habit": None,
        "text_ux": None,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
state = st.session_state
hp_session: HPGenerationSession = state.hp_session

# ============================================================
#   Utilities
# ============================================================

def go_back():
    if state.s2_ux:
        state.s2_ux = False
        state.text_ux = None
    elif state.s2_habit:
        state.s2_habit = False
        state.text_habit = None
    elif state.s2_value:
        state.s2_value = False
        state.text_value = None
    elif state.s2_goal:
        state.s2_goal = False
        state.text_goal = None
    elif state.s2_adv:
        state.step2 = False
        state.s2_adv = False
        state.text_adv = None

# ============================================================
#   🟦 ステップ1：Q1〜Q4 (No Change)
# ============================================================

st.header("ステップ 1：あなたの経験についての4つの質問", divider="grey")

col_q_L, col_q_R = st.columns([1, 1])

with col_q_L:
    st.subheader("Q1")
    q1 = st.text_area("どのような時に、どのような場所で何をしているかという体験", key="input_q1", height=80)
    if st.button("Q1 を送信", key="btn_q1"):
        if q1.strip():
            hp_session.handle_input1(q1)
            state.show_q2 = True

    if state.show_q2:
        st.subheader("Q2")
        q2 = st.text_area("重要な製品やサービス", key="input_q2", height=60)
        if st.button("Q2 を送信", key="btn_q2"):
            if q2.strip():
                hp_session.handle_input2(q2)
                state.show_q3 = True

with col_q_R:
    if state.show_q3:
        st.subheader("Q3")
        q3 = st.text_area("何のために使用していますか？", key="input_q3", height=60)
        if st.button("Q3 を送信", key="btn_q3"):
            if q3.strip():
                hp_session.handle_input3(q3)
                state.show_q4 = True

    if state.show_q4 and not state.step2:
        st.subheader("Q4")
        q4 = st.text_area("どんな自分でありたいですか？", key="input_q4", height=60)
        if st.button("Q4 を送信して Multi-Agent 起動", key="btn_q4", type="primary"):
            if q4.strip():
                with st.spinner("マルチエージェントチームを編成し、過去・現在の分析と未来予測の議論を開始します..."):
                    hp_session.start_from_values_and_trigger_future(q4)
                    hp_session.wait_all()
                    state.adv_candidates = hp_session.get_future_adv_candidates()
                state.step2 = True
                state.s2_adv = True
                st.rerun()

# ============================================================
#   🟩 ステップ2：未来社会 Multi-Agent 生成
# ============================================================

if state.step2:
    st.header("ステップ 2：Multi-Agent による未来構築", divider="grey")
    st.info("AIエージェントチーム（専門家3名）が議論し、最も創造的な候補を提案します。")

    # --- ① 前衛的社会問題 ---
    if state.s2_adv and not state.s2_goal:
        st.subheader("① 前衛的社会問題")
        adv_list = state.adv_candidates or []
        
        if not adv_list:
            st.error("生成エラー。もう一度試してください。")
        else:
            sel_idx = st.radio("エージェントの提案から選択:", range(len(adv_list)), format_func=lambda i: f"提案 {i+1}: {adv_list[i]}", key="r_adv")
            manual_adv = st.text_input("修正/手動入力:", key="m_adv")
            
            c1, c2 = st.columns([1, 4])
            if c1.button("戻る", key="b_adv"):
                go_back()
                st.rerun()
            if c2.button("① 確定して次へ", key="n_adv", type="primary"):
                final_text = manual_adv.strip() if manual_adv.strip() else adv_list[sel_idx]
                state.text_adv = final_text
                
                with st.spinner(f"「{final_text}」についてエージェントが議論中 (Goals)..."):
                    state.mtplus1["goals"] = hp_session.generate_goals_from_adv(final_text)
                state.s2_goal = True
                st.rerun()

    # --- ② 社会の目標 ---
    if state.s2_goal and not state.s2_value:
        st.subheader("② 社会の目標")
        goal_list = state.mtplus1.get("goals", [])
        
        sel_idx = st.radio("エージェントの提案から選択:", range(len(goal_list)), format_func=lambda i: f"提案 {i+1}: {goal_list[i]}", key="r_goal")
        manual_goal = st.text_input("修正/手動入力:", key="m_goal")
        
        c1, c2 = st.columns([1, 4])
        if c1.button("戻る", key="b_goal"):
            go_back()
            st.rerun()
        if c2.button("② 確定して次へ", key="n_goal", type="primary"):
            final_text = manual_goal.strip() if manual_goal.strip() else goal_list[sel_idx]
            state.text_goal = final_text
            
            with st.spinner(f"「{final_text}」についてエージェントが議論中 (Values)..."):
                state.mtplus1["values"] = hp_session.generate_values_from_goal(final_text)
            state.s2_value = True
            st.rerun()

    # --- ③ 人々の価値観 ---
    if state.s2_value and not state.s2_habit:
        st.subheader("③ 人々の価値観")
        val_list = state.mtplus1.get("values", [])
        
        sel_idx = st.radio("エージェントの提案から選択:", range(len(val_list)), format_func=lambda i: f"提案 {i+1}: {val_list[i]}", key="r_val")
        manual_val = st.text_input("修正/手動入力:", key="m_val")
        
        c1, c2 = st.columns([1, 4])
        if c1.button("戻る", key="b_val"):
            go_back()
            st.rerun()
        if c2.button("③ 確定して次へ", key="n_val", type="primary"):
            final_text = manual_val.strip() if manual_val.strip() else val_list[sel_idx]
            state.text_value = final_text
            
            with st.spinner(f"「{final_text}」についてエージェントが議論中 (Habits)..."):
                state.mtplus1["habits"] = hp_session.generate_habits_from_value(final_text)
            state.s2_habit = True
            st.rerun()

    # --- ④ 慣習化 ---
    if state.s2_habit and not state.s2_ux:
        st.subheader("④ 慣習化")
        hab_list = state.mtplus1.get("habits", [])
        
        sel_idx = st.radio("エージェントの提案から選択:", range(len(hab_list)), format_func=lambda i: f"提案 {i+1}: {hab_list[i]}", key="r_hab")
        manual_hab = st.text_input("修正/手動入力:", key="m_hab")
        
        c1, c2 = st.columns([1, 4])
        if c1.button("戻る", key="b_hab"):
            go_back()
            st.rerun()
        if c2.button("④ 確定して次へ", key="n_hab", type="primary"):
            final_text = manual_hab.strip() if manual_hab.strip() else hab_list[sel_idx]
            state.text_habit = final_text
            
            with st.spinner(f"「{final_text}」についてエージェントが議論中 (UX)..."):
                state.mtplus1["ux_future"] = hp_session.generate_ux_from_habit(final_text)
            state.s2_ux = True
            st.rerun()

    # --- ⑤ UX ---
    if state.s2_ux and not state.step4:
        st.subheader("⑤ 日常の空間とユーザー体験")
        ux_list = state.mtplus1.get("ux_future", [])
        
        sel_idx = st.radio("エージェントの提案から選択:", range(len(ux_list)), format_func=lambda i: f"提案 {i+1}: {ux_list[i]}", key="r_ux")
        manual_ux = st.text_input("修正/手動入力:", key="m_ux")
        
        c1, c2 = st.columns([1, 4])
        if c1.button("戻る", key="b_ux"):
            go_back()
            st.rerun()
        if c2.button("HPモデルを完成させる", key="n_ux", type="primary"):
            final_text = manual_ux.strip() if manual_ux.strip() else ux_list[sel_idx]
            state.text_ux = final_text
            
            with st.spinner("HPモデルの残りの要素を計算し、JSONを構築中..."):
                hp_session.finalize_mtplus1(final_text)
                hp_session.wait_all()
                state.hp_json = hp_session.to_dict()
            
            state.step4 = True
            st.rerun()

# ============================================================
#   🟪 ステップ3：Story Generator (Director-Agent)
# ============================================================

if state.step4 and state.hp_json:
    st.header("ステップ 3：HPモデルの可視化 & SF物語生成", divider="grey")
    
    # 可視化
    render_hp_visualization(state.hp_json)

    # 【新規】 修正ボタン
    if st.button("⬅️ Step 2 に戻ってHPモデルを修正", type="secondary"):
        # Step 3 フラグを落とし、HPモデルデータをクリア
        state.step4 = False
        state.hp_json = None
        # Step 2 の最終段階（UX選択）に戻る
        state.s2_ux = True
        st.rerun()

    st.write("---") 

    st.subheader("SF物語ストーリー概要 (Multi-Agent Director Mode)")
    st.markdown("""
    **アーキテクチャ:**
    1. **総監督 (Director)**: HPモデルから具体的な指示（ブリーフ）を作成します。
    2. **設定エージェント (Setting Agent)**: 世界観とキャラクターを構築します（監督が審査）。
    3. **プロットエージェント (Outline Agent)**: プロットを執筆します（監督が審査）。
    """)

    if state.outline is None:
        if st.button("✨ ストーリー概要を生成する", key="btn_generate_outline", type="primary"):
            with st.spinner("監督(Director)と作家(Agent)が協力してストーリーを構築中... (これには時間がかかります)"):
                # Multi-Agent Story Generation
                state.outline = state.story_gen.generate_story_outline(state.hp_json)
            st.success("ストーリー概要が生成されました！")
            st.rerun()

    if state.outline:
        st.text_area(label="生成されたアウトライン", value=state.outline, height=400, disabled=True)

        col1, col2 = st.columns(2)
        with col1:
            mod = st.text_area("修正提案（通常のGPT修正）:", height=100, key="outline_modify")
            if st.button("🔁 更新", key="btn_modify"):
                if mod.strip():
                    with st.spinner("ストーリー概要修正中…"):
                        new_outline = modify_outline(state.outline, mod)
                        state.outline = new_outline
                    st.success("ストーリー概要が更新されました。")
                    st.rerun()

        with col2:
            if st.button("✔️ 確定 & ダウンロードへ", key="btn_confirm"):
                state.final_confirmed = True
                st.success("確定しました！")

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