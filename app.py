import json
import streamlit as st
# 假设这些模块已存在且导入路径正确
from generate import HPGenerationSession
from outline import generate_outline, modify_outline
from prompt import list_up_gpt
from visualization import render_hp_visualization
from chat_ui import render_chat_ui # 聊天界面

# === 新增模块导入 ===
from agent_manager import AgentManager
from story_generator import StoryGenerator

# ===============================
# 0. セッション状態の初期化 (Page Configの前に判定が必要)
# ===============================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ログイン済みならサイドバーを「隠す(collapsed)」、未ログインなら「表示(expanded)」
# これにより、ログイン成功してリロードされた瞬間にサイドバーが閉じます
sb_state = "collapsed" if st.session_state.authenticated else "expanded"

# ===============================
# 1. ページ設定
# ===============================
st.set_page_config(
    page_title="HPモデル SFプロット生成ツール",
    page_icon="🛰️", 
    layout="wide",
    initial_sidebar_state=sb_state  # 👈 ここで動的に制御
)

# ===============================
# 2. 🔐 認証ロジック (极简版：登录后无痕迹)
# ===============================
def check_authentication():
    # --- A. 如果已经登录 ---
    if st.session_state.authenticated:
        # 啥也不显示，直接返回
        # 这样主程序就会接着往下运行，界面上不会有多余的按钮
        return

    # --- B. 如果未登录 (显示登录框) ---
    
    # 登录页样式
    st.markdown("""
    <style>
    .stApp { background-color: #0d0d1e; color: #fff; }
    div[data-testid="stForm"] { 
        background: rgba(20, 20, 40, 0.8); 
        padding: 40px; 
        border-radius: 15px; 
        border: 1px solid #6200ea;
        box-shadow: 0 0 20px rgba(98, 0, 234, 0.3);
    }
    h1 { text-align: center; color: #8cfffb; font-family: 'Space Mono', monospace; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1>🛰️ SYSTEM LOGIN</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #a7ffeb;'>HPモデル SFプロット生成ツールへようこそ</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            email = st.text_input("メールアドレス")
            password = st.text_input("パスワード", type="password")
            submitted = st.form_submit_button("🚀 ログイン開始", use_container_width=True)
            
            if submitted:
                try:
                    valid_users = st.secrets["passwords"]
                    if email in valid_users and valid_users[email] == password:
                        st.success("認証成功。")
                        st.session_state.authenticated = True
                        st.session_state.user_email = email
                        st.rerun() # 刷新页面，直接进入主程序
                    else:
                        st.error("⛔ メールアドレスまたはパスワードが間違っています。")
                except FileNotFoundError:
                    st.error("⚠️ エラー: secrets.toml が見つかりません。")
                except KeyError:
                    st.error("⚠️ エラー: secrets.toml に [passwords] がありません。")
    
    # 未登录时，停止后续代码运行
    st.stop()

# === 🚀 認証チェック実行 ===
check_authentication()

# ===============================
# 🎨 カスタムCSS (宇宙背景とアニメーション)
# ===============================
st.markdown("""
<style>
/* 1. 宇宙背景とダークテーマを適用 */
.stApp {
    background: 
        url('https://images.unsplash.com/photo-1502134249126-9f3755a50d78?fit=crop&w=1920&q=80') 
        center center / cover no-repeat fixed;
    background-color: #0d0d1e; /* 画像がない場合のフォールバック */
    color: #f0f2f6; /* 全体の文字色を明るく */
    text-shadow: 1px 1px 2px rgba(0,0,0,0.5); /* 文字を読みやすく */
}

/* 2. ヘッダーとタイトルを未来的に */
h1, h2, h3, .main-title {
    color: #8cfffb; /* アクセントカラー（明るいシアン） */
    font-family: 'Space Mono', monospace; /* 未来的なフォントを想定 */
    text-shadow: 0 0 5px rgba(140, 255, 251, 0.7);
    margin-top: 20px;
}
h2 {
    border-bottom: 2px solid rgba(140, 255, 251, 0.3);
    padding-bottom: 5px;
}

.main-title {
    font-size: 2.5em;
    font-weight: bold;
    color: #a7ffeb; /* メインタイトルはさらに明るく */
    text-align: center;
    padding: 10px 0;
}
.sub-title {
    color: #e0f7fa;
    text-align: center;
    margin-bottom: 30px;
}

/* 3. ボタンとインプットエリアのスタイル調整 (保留原 SF 样式) */
.stButton>button {
    background-color: #6200ea; /* SF的な紫 */
    color: white;
    border-radius: 8px;
    border: none;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(98, 0, 234, 0.4);
}
.stButton>button:hover {
    background-color: #3700b3;
    box-shadow: 0 6px 20px rgba(98, 0, 234, 0.6);
}
textarea, input[type="text"], [data-testid="stTextInput"], [data-testid="stTextarea"] {
    background-color: rgba(30, 30, 50, 0.7); /* 半透明の濃い背景 */
    color: #f0f2f6;
    border-radius: 5px;
    border: 1px solid #6200ea;
}

/* 4. アニメーションの定義 (保留原 SF 动画) */
@keyframes fadeInSlide {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
.fade-in {
    animation: fadeInSlide 1s ease-out forwards;
}
.fade-in-slow {
    animation: fadeInSlide 1.5s ease-out forwards;
}

/* 5. Streamlitのコンポーネント背景を透明化（背景画像が見えるように） */
.main, .block-container, .stAlert, .stRadio {
    background-color: rgba(0, 0, 0, 0.3) !important;
    border-radius: 10px;
    padding: 10px;
}
[data-testid="stVerticalBlock"] > div:nth-child(1) {
    background-color: transparent; /* 确保标题背景透明 */
}
</style>
""", unsafe_allow_html=True)


# ===============================
# 初始化 session_state
# ===============================
def init_state():
    defaults = {
        "hp_session": HPGenerationSession(),
        "adv_candidates": None,
        "mtplus1": {},
        "hp_json": None,
        "outline": None,
        "final_confirmed": False,
        "show_q2": False,
        "show_q3": False,
        "show_q4": False,
        "step2": False,
        "step4": False,
        "s2_adv": False,
        "s2_goal": False,
        "s2_value": False,
        "s2_habit": False,
        "s2_ux": False,
        "text_adv": None,
        "text_goal": None,
        "text_value": None,
        "text_habit": None,
        "text_ux": None,
        "show_chat": False, # 聊天界面切换
        "chat_history": [], # 聊天记录
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # === Multi-Agent Initializations ===
    if "agent_manager" not in st.session_state:
        st.session_state.agent_manager = AgentManager()
    
    if "story_generator" not in st.session_state:
        st.session_state.story_generator = StoryGenerator()

init_state()
state = st.session_state
hp_session: HPGenerationSession = state.hp_session

# ===============================
# Utilities
# ===============================
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

def get_context_for_agents():
    """获取当前已有的 HP 模型 JSON 字符串，供 Agent 使用"""
    # 组合 Mt-1, Mt 和目前已有的 Mt+1
    temp_json = hp_session.to_dict()
    return json.dumps(temp_json, ensure_ascii=False)

def get_topic_str():
    """生成用户输入的简要主题"""
    # 修正: state.hp_session.user_inputs を参照するように変更
    return f"現在のUX: {state.hp_session.user_inputs['q1_ux']} / 価値観: {state.hp_session.user_inputs['q4_value']}"

# ===============================
# 封装主界面 (Step 1)
# ===============================
def render_main_ui():
    st.header("ステップ 1：あなたの経験についての4つの質問", divider="grey")

    # Q1
    st.subheader("Q1")
    q1 = st.text_area("あなたがすきなことをしている情景を思い出して、どのような時に、どのような場所で何をしているかという体験を書き出してください。", key="input_q1", height=80)
    if st.button("Q1 を送信", key="btn_q1"):
        if not q1.strip():
            st.warning("Q1に回答してください。")
        else:
            hp_session.handle_input1(q1)
            state.show_q2 = True
            st.success("Q1 を受け取りました。")
            st.rerun() # 为了刷新右侧聊天状态

    if state.show_q2:
        st.subheader("Q2")
        q2 = st.text_area("その一連の体験を成立させるために重要な製品やサービスを挙げてください。", key="input_q2", height=68)
        if st.button("Q2 を送信", key="btn_q2"):
            if not q2.strip():
                st.warning("Q2に回答してください。")
            else:
                hp_session.handle_input2(q2)
                state.show_q3 = True
                st.success("Q2 を受け取りました。")
                st.rerun() # 为了刷新右侧聊天状态

    if state.show_q3:
        st.subheader("Q3")
        q3 = st.text_area("あなたは、何のためにその製品やサービスを使用していますか？", key="input_q3", height=68)
        if st.button("Q3 を送信", key="btn_q3"):
            if not q3.strip():
                st.warning("Q3に回答してください。")
            else:
                hp_session.handle_input3(q3)
                state.show_q4 = True
                st.success("Q3 を受け取りました。")
                st.rerun() # 为了刷新右侧聊天状态

    if state.show_q4 and not state.step2:
        st.subheader("Q4")
        q4 = st.text_area("そのような体験を行うあなたはどんな自分でありたいですか？", key="input_q4", height=68)
        if st.button("Q4 を送信して Step2 開始", key="btn_q4", type="primary"):
            if not q4.strip():
                st.warning("Q4に回答してください。")
            else:
                # 1. Start filling Mt/Mt-1 (Standard Logic)
                with st.spinner("Mt・Mt-1 の詳細情報を検索・生成中…"):
                    hp_session.start_from_values_and_trigger_future(q4)
                    hp_session.wait_all() # 确保过去和现在的节点填满
                
                # 2. Use Multi-Agent for the first future node (Adv Issue)
                st.info("🤖 3人の専門家エージェントを召喚し、未来の「前衛的社会問題」を議論中... (時間がかかります)")
                with st.spinner("Agents thinking (Iterative Generation)..."):
                    topic = get_topic_str()
                    context = get_context_for_agents()
                    
                    # Call Agent Manager
                    state.adv_candidates = state.agent_manager.run_multi_agent_generation(
                        element_type="前衛的社会問題",
                        element_desc="技術やパラダイムの変化、あるいは反動として生まれる未来の問題",
                        topic=topic,
                        full_context_str=context
                    )
                
                state.step2 = True
                state.s2_adv = True
                st.rerun()

# ============================================================
# 页面主分栏逻辑
# ============================================================

main_col, chat_col = st.columns([7, 3])

# --- 左栏：主应用界面 ---
with main_col:
    st.markdown('<div class="main-title fade-in">HPモデル × Multi-Agent SFプロット生成ツール</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title fade-in" style="animation-delay: 0.5s;">あなたの経験をもとに三世代HPモデルとSF物語ストーリー概要を共创します。</div>', unsafe_allow_html=True)

    render_main_ui()

    # ---------------------------------------------
    #   🟩 ステップ2：未来社会 5つの選択 (Multi-Agent)
    # ---------------------------------------------
    if state.step2:
        st.header("ステップ 2：未来社会を構成する5つの選択 (Multi-Agent Mode)", divider="grey")

        # --- ① 前衛的社会問題 ---
        if state.s2_adv and not state.s2_goal:
            st.subheader("① 前衛的社会問題")
            adv_list = state.adv_candidates or []
            
            if not adv_list:
                st.error("候補生成エラー：再読み込みしてください")
            else:
                sel_idx = st.radio("エージェントの提案から選ぶ:", range(len(adv_list)), format_func=lambda i: adv_list[i], key="r_adv")
                manual_adv = st.text_input("または、自分で入力する:", key="m_adv")
                
                c1, c2 = st.columns([1, 4])
                if c1.button("戻る", key="b_adv"):
                    go_back()
                    st.rerun()
                if c2.button("① 確定して次へ", key="n_adv", type="primary"):
                    final_text = manual_adv.strip() if manual_adv.strip() else adv_list[sel_idx]
                    state.text_adv = final_text
                    
                    # 1. Update HP Session State (uses old GPT-4o-mini logic for filling, but we ignore its return candidates)
                    with st.spinner("HPモデル更新中..."):
                         _ = hp_session.generate_goals_from_adv(final_text)
                    
                    # 2. Multi-Agent Generation for NEXT step
                    st.info("🤖 エージェントが次の「社会の目標」について議論中...")
                    with st.spinner("Agents thinking..."):
                        state.mtplus1["goals"] = state.agent_manager.run_multi_agent_generation(
                            element_type="社会の目標",
                            element_desc="前衛的社会問題を受けて、社会が目指す（あるいは恐れる）未来の目標",
                            topic=get_topic_str(),
                            full_context_str=get_context_for_agents()
                        )
                    
                    state.s2_goal = True
                    st.rerun()

        # --- ② 社会の目標 ---
        if state.s2_goal and not state.s2_value:
            st.subheader("② 社会の目標")
            st.info(f"前提（前衛的社会問題）: {state.text_adv}")
            goal_list = state.mtplus1.get("goals", [])
            
            if not goal_list:
                st.warning("候補が生成されませんでした。戻ってやり直してください。")
            else:
                sel_idx = st.radio("エージェントの提案から選ぶ:", range(len(goal_list)), format_func=lambda i: goal_list[i], key="r_goal")
                manual_goal = st.text_input("または、自分で入力する:", key="m_goal")
                
                c1, c2 = st.columns([1, 4])
                if c1.button("戻る", key="b_goal"):
                    go_back()
                    st.rerun()
                if c2.button("② 確定して次へ", key="n_goal", type="primary"):
                    final_text = manual_goal.strip() if manual_goal.strip() else goal_list[sel_idx]
                    state.text_goal = final_text
                    
                    with st.spinner("HPモデル更新中..."):
                         _ = hp_session.generate_values_from_goal(final_text)

                    st.info("🤖 エージェントが次の「人々の価値観」について議論中...")
                    with st.spinner("Agents thinking..."):
                        state.mtplus1["values"] = state.agent_manager.run_multi_agent_generation(
                            element_type="人々の価値観",
                            element_desc="その社会目標を実現するために必要な、人々の内面的な価値観",
                            topic=get_topic_str(),
                            full_context_str=get_context_for_agents()
                        )
                    
                    state.s2_value = True
                    st.rerun()

        # --- ③ 人々の価値観 ---
        if state.s2_value and not state.s2_habit:
            st.subheader("③ 人々の価値観")
            st.info(f"前提（社会の目標）: {state.text_goal}")
            val_list = state.mtplus1.get("values", [])
            
            sel_idx = st.radio("エージェントの提案から選ぶ:", range(len(val_list)), format_func=lambda i: val_list[i], key="r_val")
            manual_val = st.text_input("または、自分で入力する:", key="m_val")
            
            c1, c2 = st.columns([1, 4])
            if c1.button("戻る", key="b_val"):
                go_back()
                st.rerun()
            if c2.button("③ 確定して次へ", key="n_val", type="primary"):
                final_text = manual_val.strip() if manual_val.strip() else val_list[sel_idx]
                state.text_value = final_text

                with st.spinner("HPモデル更新中..."):
                     _ = hp_session.generate_habits_from_value(final_text)

                st.info("🤖 エージェントが次の「習慣化」について議論中...")
                with st.spinner("Agents thinking..."):
                    state.mtplus1["habits"] = state.agent_manager.run_multi_agent_generation(
                        element_type="習慣化",
                        element_desc="その価値観が普及した社会での日常的な習慣・行動様式",
                        topic=get_topic_str(),
                        full_context_str=get_context_for_agents()
                    )
                
                state.s2_habit = True
                st.rerun()

        # --- ④ 慣習化 ---
        if state.s2_habit and not state.s2_ux:
            st.subheader("④ 慣習化")
            st.info(f"前提（人々の価値観）: {state.text_value}")
            hab_list = state.mtplus1.get("habits", [])
            
            sel_idx = st.radio("エージェントの提案から選ぶ:", range(len(hab_list)), format_func=lambda i: hab_list[i], key="r_hab")
            manual_hab = st.text_input("または、自分で入力する:", key="m_hab")
            
            c1, c2 = st.columns([1, 4])
            if c1.button("戻る", key="b_hab"):
                go_back()
                st.rerun()
            if c2.button("④ 確定して次へ", key="n_hab", type="primary"):
                final_text = manual_hab.strip() if manual_hab.strip() else hab_list[sel_idx]
                state.text_habit = final_text
                
                with st.spinner("HPモデル更新中..."):
                     _ = hp_session.generate_ux_from_habit(final_text)

                st.info("🤖 エージェントが次の「UX空間」について議論中...")
                with st.spinner("Agents thinking..."):
                    state.mtplus1["ux_future"] = state.agent_manager.run_multi_agent_generation(
                        element_type="日常の空間とユーザー体験",
                        element_desc="その習慣が行われる物理的・デジタルな空間や具体的な体験",
                        topic=get_topic_str(),
                        full_context_str=get_context_for_agents()
                    )
                
                state.s2_ux = True
                st.rerun()

        # --- ⑤ UX ---
        if state.s2_ux and not state.step4:
            st.subheader("⑤ 日常の空間とユーザー体験")
            st.info(f"前提（慣習化）: {state.text_habit}")
            ux_list = state.mtplus1.get("ux_future", [])
            
            sel_idx = st.radio("エージェントの提案から選ぶ:", range(len(ux_list)), format_func=lambda i: ux_list[i], key="r_ux")
            manual_ux = st.text_input("または、自分で入力する:", key="m_ux")
            
            c1, c2 = st.columns([1, 4])
            if c1.button("戻る", key="b_ux"):
                go_back()
                st.rerun()
            if c2.button("三世代HPモデルを完成させる", key="n_ux", type="primary"):
                final_text = manual_ux.strip() if manual_ux.strip() else ux_list[sel_idx]
                state.text_ux = final_text
                
                with st.spinner("HPモデル（三世代）を最終構築中..."):
                    hp_session.finalize_mtplus1(final_text)
                    hp_session.wait_all()
                    state.hp_json = hp_session.to_dict()
                
                state.step4 = True
                st.rerun()

    # ---------------------------------------------
    #   🟪 ステップ3：SF物語アウトライン生成 (Multi-Agent Story Generator)
    # ---------------------------------------------
    if state.step4 and state.hp_json:
        st.header("ステップ 3：HPモデルの可視化 & 物語生成", divider="grey")
        
        st.info("完成したHPモデル（三世代）の構造図です。")
        render_hp_visualization(state.hp_json) 
        
        st.write("---") 

        st.subheader("SF物語ストーリー概要生成 (Multi-Agent Edition)")

        if state.outline is None:
            if st.button("✨ Agentチームにストーリー制作を依頼", key="btn_generate_outline", type="primary"):
                st.info("総監督、設定担当、プロット担当のエージェントたちが協力して物語を構築しています。これには数分かかる場合があります...")
                with st.spinner("Story Generating (Director -> Setting -> Outline)..."):
                    # Use the new Multi-Agent Story Generator
                    state.outline = state.story_generator.generate_story_outline(state.hp_json)
                st.success("ストーリー概要が生成されました。")
                st.rerun()

        if state.outline:
            st.subheader("現在のストーリー概要：")
            st.text_area(label="", value=state.outline, height=400, disabled=True)

            col1, col2 = st.columns(2)
            with col1:
                # 修改功能暂时保持原有的简单 GPT 逻辑，因为 Multi-Agent 主要用于生成
                mod = st.text_area("修正提案（簡易GPT編集）:", height=100, key="outline_modify")
                if st.button("🔁 更新", key="btn_modify"):
                    if mod.strip():
                        with st.spinner("ストーリー概要修正中…"):
                            # 调用原有的 modify_outline (outline.py)
                            new_outline = modify_outline(state.outline, mod)
                            state.outline = new_outline
                        st.success("ストーリー概要が更新されました。")
                        st.rerun()
                    else:
                        st.warning("修正内容を入力してください。")

            with col2:
                if st.button("✔️ 確定", key="btn_confirm", type="primary"):
                    state.final_confirmed = True
                    st.success("確定しました！下にダウンロードボタンが表示されます。")

    # ---------------------------------------------
    #   🟫 STEP4：ダウンロード
    # ---------------------------------------------
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

# --- 右栏：聊天界面 ---
with chat_col:
    st.markdown('<div style="height: 37px;"></div>', unsafe_allow_html=True)
    
    chat_placeholder = st.empty()

    if state.show_chat:
        with chat_placeholder.container():
            col_c1, col_c2 = st.columns([3, 1])
            with col_c2:
                if st.button("❌ 隠す", key="hide_chat_button"):
                    state.show_chat = False
                    st.rerun()
            
            # --- 自动判定当前阶段 ---
            current_phase = "normal"
            if not state.step2:
                if not state.show_q2:
                    current_phase = "q1"
                elif not state.show_q3:
                    current_phase = "q2"
                elif not state.show_q4:
                    current_phase = "q3"
                else:
                    current_phase = "q4"
            
            # 修正: state.hp_session.user_inputs を渡す
            render_chat_ui(st.container(), current_phase, state.hp_session.user_inputs) 
        
    else:
        with chat_placeholder.container():
            st.write("") 
            st.write("---")
            if st.button("🤖 AIアシスタントを開く", key="show_chat_btn"):
                state.show_chat = True
                st.rerun()

st.markdown("---")
if not state.show_chat:
    st.write("🤖 ヘルプが必要な場合は、右側の 'AIアシスタントを開く' ボタンをクリックしてチャットパネルを開いてください。")
else:
    st.write("💡 チャットパネルは開いています。")