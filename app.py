<<<<<<< Updated upstream

import streamlit as st
from workshop_flow import WorkshopFlow
from data_store import save_ap, save_text
from utils import ensure_str
from visualize_ap import draw_ap_model

st.set_page_config(page_title='HP Workshop — Final', layout='wide')

if 'flow' not in st.session_state:
    st.session_state['flow'] = WorkshopFlow()
if 'step_index' not in st.session_state:
    st.session_state['step_index'] = 0

flow: WorkshopFlow = st.session_state['flow']
idx = st.session_state['step_index']

st.title('HP ワークショップ — 固定流程（字段保留原样）')
st.write('步骤与 HP 字段名严格保留原样（含日语字段）。')

STEPS = [
    {'no': '1', 'actor': '参加者', 'content': '現代の自分自身の特徴的な行動を振り返る', 'hp': 'MtのUX空間'},
    {'no': '2', 'actor': '参加者', 'content': '現代でよく使う製品・サービスを列举', 'hp': 'Mtで使う製品・サービス'},
    {'no': '3', 'actor': '参加者', 'content': '日常で感じる不便や小さな問題点を挙げる', 'hp': 'Mtの不便・ペインポイント'},
    {'no': '4', 'actor': '参加者', 'content': '你对未来技术与生活の初步想像（简短）', 'hp': 'Mtの未来想像'},
    {'no': '5', 'actor': '参加者', 'content': '列出与你议题相关的主要角色/群体', 'hp': 'Mtの主要役割・群衆'},
    {'no': '6', 'actor': '参加者', 'content': '当前制度/机构如何影响上述问题', 'hp': 'Mtの制度・機関'},
    {'no': '7', 'actor': 'AI', 'content': '回顾相关历史背景与事件（Mt-1）', 'hp': 'Mt-1の歴史的出来事'},
    {'no': '8', 'actor': 'AI', 'content': '总结过去技术路径与失败案例（Mt-1）', 'hp': 'Mt-1の過去の技術と経路'},
    {'no': '9', 'actor': 'AI', 'content': '回顾过去的社会运动/文化潮流（Mt-1）', 'hp': 'Mt-1の社会運動・文化'},
    {'no': '10', 'actor': 'AI', 'content': '过去制度变迁的关键节点（Mt-1）', 'hp': 'Mt-1の制度変遷'},
    {'no': '11', 'actor': 'AI', 'content': '假设未来技术演进的可能路径（Mt+1）', 'hp': 'Mt+1の技術と資源'},
    {'no': '12', 'actor': 'AI', 'content': '描绘未来典型日常场景（Mt+1）', 'hp': 'Mt+1の生活空間'},
    {'no': '13', 'actor': 'AI', 'content': '预测未来的价值观与伦理争议（Mt+1）', 'hp': 'Mt+1の人々の価値観'},
    {'no': '14', 'actor': 'AI', 'content': '设想未来制度/治理模型（Mt+1）', 'hp': 'Mt+1の制度・ガバナンス'},
    {'no': '15', 'actor': 'AI', 'content': '识别潜在冲突与关键转折点（Mt+1）', 'hp': 'Mt+1の転換点・コンフリクト'},
    {'no': '16', 'actor': '参加者', 'content': '设定约束、评估指标与最终目标（用于评估）', 'hp': 'Mt+1の制約と評価指標'}
]

st.sidebar.title('步骤导航')
st.sidebar.write(f'当前步骤: {idx+1} / {len(STEPS)}')
for i, s in enumerate(STEPS):
    if st.sidebar.button(f"Step {i+1}: No.{s['no']}"):
        st.session_state['step_index'] = i
        st.rerun()

step = STEPS[idx]
st.header(f"Step {idx+1} — 作業No.{step['no']}  — 作業者: {step['actor']}")
st.subheader(step['content'])
st.caption(f"対応するHP フィールド: {step['hp']}")

def get_saved_value(flow, hp):
    for tf in ('mt', 'mt_minus1', 'mt_plus1'):
        v = getattr(flow.ap, tf).get(hp, None)
        if v:
            return v, tf
    return None, None

saved_val, saved_tf = get_saved_value(flow, step['hp'])
key_state = f"step_value_{idx}"

if step['actor'] == '参加者':
    existing = st.session_state.get(key_state, saved_val or '')
    text = st.text_area('参加者入力（请填写）', value=existing, height=220, key=f"input_{idx}")
    cols = st.columns([1,1,2])
    with cols[0]:
        if st.button('保存 (到 Mt)', key=f"save_{idx}"):
            flow.ap.set_element('mt', step['hp'], ensure_str(text))
            st.session_state[key_state] = text
            st.success('已保存到 Mt')
    with cols[1]:
        if st.button('AI 推薦（基于当前已填信息）', key=f"ai_suggest_{idx}"):
            prompt = f"作为 AI，基于当前 APModel 内容，为步骤 No.{step['no']} 提供 5 条可行建议。\\n\\n当前 AP: \\n" + str(flow.ap.to_json())
            try:
                out = flow.ai_infer_related(prompt, target_timeframe='mt', field_key=step['hp'] + '_ai_suggestions')
                st.text_area('AI 推荐结果', value=out, height=240)
            except Exception as e:
                st.error(f'AI 调用失败: {e}')
    with cols[2]:
        if saved_val:
            st.info(f'已有保存内容（{saved_tf}）:')
            st.text_area('已保存内容', value=saved_val, height=160)
elif step['actor'] == 'AI':
    st.write('本步骤由 AI 执行。点击下面按钮由 AI 生成并保存结果。')
    if st.button('AI: 生成并保存', key=f"ai_gen_{idx}"):
        prompt = f"请根据当前 APModel（下面）以及步骤说明，生成与此步骤（No.{step['no']}）相符的结构化段落或列表：\\n\\nAPModel:\\n" + str(flow.ap.to_json())
        try:
            out = flow.ai_infer_related(prompt, target_timeframe='mt', field_key=step['hp'])
            st.session_state[key_state] = out
            st.text_area('AI 结果', value=out, height=300)
            st.success('AI 结果已保存到 APModel.mt 的字段: ' + step['hp'])
        except Exception as e:
            st.error(f'AI 调用错误: {e}')
    if saved_val:
        st.info(f'已有保存内容（{saved_tf}）:')
        st.text_area('已保存内容', value=saved_val, height=200)

col1, col2, col3 = st.columns([1,1,6])
with col1:
    if st.button('前へ') and idx > 0:
        st.session_state['step_index'] = idx - 1
        st.rerun()
with col2:
    if st.button('次へ') and idx < len(STEPS)-1:
        st.session_state['step_index'] = idx + 1
        st.rerun()
with col3:
    st.write('')

st.markdown('---')
st.header('AP 模型可视化 & 导出')
if st.button('可视化当前 AP 模型'):
    try:
        fig = draw_ap_model(flow.ap)
        st.pyplot(fig)
    except Exception as e:
        st.error(f'可视化失败: {e}')

if st.button('导出 AP JSON') :
    path = save_ap(flow.ap)
    st.info(f'已导出: {path}')

if st.button('生成完整小说（分阶段生成）'):
    try:
        res = flow.generate_story_process()
        st.success('已生成：setting / expansion / story')
        st.text_area('设定摘要（setting）', value=res.get('setting',''), height=200)
        st.text_area('世界扩展（expansion）', value=res.get('expansion',''), height=200)
        st.text_area('短篇小说（story）', value=res.get('story',''), height=400)
        save_text(res.get('story',''), filename='sf_story.txt')
    except Exception as e:
        st.error(f'生成失败: {e}')
=======
import json
import streamlit as st
# 假设这些模块已存在且导入路径正确
from generate import HPGenerationSession
from outline import generate_outline, modify_outline
from prompt import list_up_gpt
from visualization import render_hp_visualization
from chat_ui import render_chat_ui # 聊天界面

# ===== 页面设置 =====
st.set_page_config(page_title="HPモデル SFプロット生成ツール",
                    page_icon="🛰️", layout="wide") # 使用 wide 布局

# ===============================
# 🎨 カスタムCSS (宇宙背景とアニメーション)
# ===============================
st.markdown("""
<style>
/* 1. 宇宙背景とダークテーマを適用 */
.stApp {
    /* **请替换成您的宇宙图片URL**。例如：'https://example.com/space.jpg' */
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
/* ❗ 移除所有针对右侧聊天栏的 margin/padding CSS 调整 */
/* 而是使用 HTML <div> 空间块来调整位置 */

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

# ===============================
# 封装主界面 (Step 1)
# ===============================
def render_main_ui():
    st.header("ステップ 1：あなたの経験についての4つの質問", divider="grey")

    # Q1
    st.subheader("Q1（Mt：日常の空間とユーザー体験）")
    q1 = st.text_area("あなたがすきなことをしている情景を思い出して、どのような時に、どのような場所で何をしているかという体験を書き出してください。", key="input_q1", height=80)
    if st.button("Q1 を送信", key="btn_q1"):
        if not q1.strip():
            st.warning("Q1に回答してください。")
        else:
            hp_session.handle_input1(q1)
            state.show_q2 = True
            st.success("Q1 を受け取りました。")

    if state.show_q2:
        st.subheader("Q2（Mt：製品・サービス）")
        # 已修改 height >= 68
        q2 = st.text_area("その一連の体験を成立させるために重要な製品やサービスを挙げてください。", key="input_q2", height=68)
        if st.button("Q2 を送信", key="btn_q2"):
            if not q2.strip():
                st.warning("Q2に回答してください。")
            else:
                hp_session.handle_input2(q2)
                state.show_q3 = True
                st.success("Q2 を受け取りました。")

    if state.show_q3:
        st.subheader("Q3（Mt：意味付け）")
        # 已修改 height >= 68
        q3 = st.text_area("あなたは、何のためにその製品やサービスを使用していますか？", key="input_q3", height=68)
        if st.button("Q3 を送信", key="btn_q3"):
            if not q3.strip():
                st.warning("Q3に回答してください。")
            else:
                hp_session.handle_input3(q3)
                state.show_q4 = True
                st.success("Q3 を受け取りました。")

    if state.show_q4 and not state.step2:
        st.subheader("Q4（Mt：人々の価値観）")
        # 已修改 height >= 68
        q4 = st.text_area("そのような体験を行うあなたはどんな自分でありたいですか？", key="input_q4", height=68)
        if st.button("Q4 を送信して Step2 開始", key="btn_q4", type="primary"):
            if not q4.strip():
                st.warning("Q4に回答してください。")
            else:
                with st.spinner("Mt・Mt-1・Mt+1 の初期情報を生成中…"):
                    hp_session.start_from_values_and_trigger_future(q4)
                    hp_session.wait_all()
                    state.adv_candidates = hp_session.get_future_adv_candidates()
                state.step2 = True
                state.s2_adv = True
                st.rerun()

# ============================================================
# 页面主分栏逻辑
# ============================================================

# 70% 留给主内容，30% 留给聊天框
main_col, chat_col = st.columns([7, 3])

# --- 左栏：主应用界面 (页头和 Step 1-4) ---
with main_col:
    # 重新显示页头 (保留动画)
    st.markdown('<div class="main-title fade-in">HPモデル × GPT × Tavily によるSFプロット生成ツール</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title fade-in" style="animation-delay: 0.5s;">あなたの経験をもとに三世代HPモデルとSF物語ストーリー概要を共创します。</div>', unsafe_allow_html=True)

    # 渲染 Step 1
    render_main_ui()

    # 渲染 Step 2 ~ Step 4 的内容

    # ---------------------------------------------
    #   🟩 ステップ2：未来社会 5つの選択 (逐次生成 & 手動入力)
    # ---------------------------------------------
    if state.step2:
        st.header("ステップ 2：未来社会を構成する5つの選択", divider="grey")

        # --- ① 前衛的社会問題 ---
        if state.s2_adv and not state.s2_goal:
            st.subheader("① 前衛的社会問題")
            adv_list = state.adv_candidates or []
            
            if not adv_list:
                st.error("候補生成エラー：再読み込みしてください")
            else:
                sel_idx = st.radio("選択肢から選ぶ:", range(len(adv_list)), format_func=lambda i: adv_list[i], key="r_adv")
                manual_adv = st.text_input("または、自分で入力する:", key="m_adv")
                
                c1, c2 = st.columns([1, 4])
                if c1.button("戻る", key="b_adv"):
                    go_back()
                    st.rerun()
                if c2.button("① 確定して次へ", key="n_adv", type="primary"):
                    final_text = manual_adv.strip() if manual_adv.strip() else adv_list[sel_idx]
                    state.text_adv = final_text
                    
                    
                    with st.spinner(f"「{final_text}」に基づく『社会の目標』候補を生成中..."):
                        state.mtplus1["goals"] = hp_session.generate_goals_from_adv(final_text)
                    
                    state.s2_goal = True
                    st.rerun()

        # --- ② 社会の目標 ---
        if state.s2_goal and not state.s2_value:
            st.subheader("② 社会の目標")
            st.info(f"前提（前衛的社会問題）: {state.text_adv}")
            goal_list = state.mtplus1.get("goals", [])
            
            if not goal_list:
                st.warning("候補が生成されませんでした。戻ってやり直してください。")
                if st.button("戻る", key="b_goal_err"):
                    go_back()
                    st.rerun()
            else:
                sel_idx = st.radio("選択肢から選ぶ:", range(len(goal_list)), format_func=lambda i: goal_list[i], key="r_goal")
                manual_goal = st.text_input("または、自分で入力する:", key="m_goal")
                
                c1, c2 = st.columns([1, 4])
                if c1.button("戻る", key="b_goal"):
                    go_back()
                    st.rerun()
                if c2.button("② 確定して次へ", key="n_goal", type="primary"):
                    final_text = manual_goal.strip() if manual_goal.strip() else goal_list[sel_idx]
                    state.text_goal = final_text
                    
                    with st.spinner(f"「{final_text}」に基づく『人々の価値観』候補を生成中..."):
                        state.mtplus1["values"] = hp_session.generate_values_from_goal(final_text)
                    
                    state.s2_value = True
                    st.rerun()

        # --- ③ 人々の価値観 ---
        if state.s2_value and not state.s2_habit:
            st.subheader("③ 人々の価値観")
            st.info(f"前提（社会の目標）: {state.text_goal}")
            val_list = state.mtplus1.get("values", [])
            
            sel_idx = st.radio("選択肢から選ぶ:", range(len(val_list)), format_func=lambda i: val_list[i], key="r_val")
            manual_val = st.text_input("または、自分で入力する:", key="m_val")
            
            c1, c2 = st.columns([1, 4])
            if c1.button("戻る", key="b_val"):
                go_back()
                st.rerun()
            if c2.button("③ 確定して次へ", key="n_val", type="primary"):
                final_text = manual_val.strip() if manual_val.strip() else val_list[sel_idx]
                state.text_value = final_text

                
                with st.spinner(f"「{final_text}」に基づく『慣習化』候補を生成中..."):
                    state.mtplus1["habits"] = hp_session.generate_habits_from_value(final_text)
                
                state.s2_habit = True # 修正：这里应设置 s2_habit 为 True
                st.rerun()

        # --- ④ 慣習化 ---
        if state.s2_habit and not state.s2_ux:
            st.subheader("④ 慣習化")
            st.info(f"前提（人々の価値観）: {state.text_value}")
            hab_list = state.mtplus1.get("habits", [])
            
            sel_idx = st.radio("選択肢から選ぶ:", range(len(hab_list)), format_func=lambda i: hab_list[i], key="r_hab")
            manual_hab = st.text_input("または、自分で入力する:", key="m_hab")
            
            c1, c2 = st.columns([1, 4])
            if c1.button("戻る", key="b_hab"):
                go_back()
                st.rerun()
            if c2.button("④ 確定して次へ", key="n_hab", type="primary"):
                final_text = manual_hab.strip() if manual_hab.strip() else hab_list[sel_idx]
                state.text_habit = final_text
                
                with st.spinner(f"「{final_text}」に基づく『UX空間』候補を生成中..."):
                    state.mtplus1["ux_future"] = hp_session.generate_ux_from_habit(final_text)
                
                state.s2_ux = True
                st.rerun()

        # --- ⑤ UX ---
        if state.s2_ux and not state.step4:
            st.subheader("⑤ 日常の空間とユーザー体験")
            st.info(f"前提（慣習化）: {state.text_habit}")
            ux_list = state.mtplus1.get("ux_future", [])
            
            sel_idx = st.radio("選択肢から選ぶ:", range(len(ux_list)), format_func=lambda i: ux_list[i], key="r_ux")
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
    #   🟪 ステップ3：SF物語アウトライン生成
    # ---------------------------------------------
    if state.step4 and state.hp_json:
        st.header("ステップ 3：HPモデルの可視化 & 物語生成", divider="grey")
        
        st.info("完成したHPモデル（三世代）の構造図です。")
        render_hp_visualization(state.hp_json) 
        
        st.write("---") 

        st.subheader("SF物語ストーリー概要生成")

        if state.outline is None:
            if st.button("✨ ストーリー概要を生成", key="btn_generate_outline", type="primary"):
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

# --- 右栏：聊天界面 (可隐藏/显示) ---
with chat_col:
    # ❗ 修正点: 在聊天区域开始前插入垂直空间 (15px)
    st.markdown('<div style="height: 37px;"></div>', unsafe_allow_html=True)
    
    # 聊天界面容器占位符
    chat_placeholder = st.empty()

    if state.show_chat:
        with chat_placeholder.container():
            # 顶部隐藏按钮
            # ❗ 修复 Key 冲突，并使用新的 Key
            col_c1, col_c2 = st.columns([3, 1])
            with col_c2:
                if st.button("❌ 隠す", key="hide_chat_button"): # 使用 unique key
                    state.show_chat = False
                    st.rerun()

            # 渲染聊天界面内容
            render_chat_ui(st.container()) 
        
    else:
        # 如果是隐藏状态，只显示一个开启按钮
        with chat_placeholder.container():
            st.write("") # 占位符
            st.write("---")
            if st.button("🤖 AIアシスタントを開く", key="show_chat_btn"):
                state.show_chat = True
                st.rerun()

# 最后的 next step 提示 (可选)
st.markdown("---")
if not state.show_chat:
    st.write("🤖 ヘルプが必要な場合は、右側の 'AIアシスタントを開く' ボタンをクリックしてチャットパネルを開いてください。")
else:
    st.write("💡 チャットパネルは開いています。いつでも質問したり、'❌ 隠す' ボタンをクリックして閉じることができます。")
>>>>>>> Stashed changes
