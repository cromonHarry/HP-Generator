
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
