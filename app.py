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
st.markdown('<div class="sub-title">Archaeological Prototyping（HPモデル）を用いて、あなたの経験から三世代の社会モデルとSF物語のアウトラインを共創します。</div>', unsafe_allow_html=True)

# ===== セッション状態の初期化 =====
if "hp_session" not in st.session_state:
    st.session_state.hp_session = HPGenerationSession()

if "adv_candidates" not in st.session_state:
    st.session_state.adv_candidates = None  # Mt+1 前衛的社会問題 候補

if "mtplus1_candidates" not in st.session_state:
    st.session_state.mtplus1_candidates = None  # 4つの5択候補

if "hp_json" not in st.session_state:
    st.session_state.hp_json = None

if "ap_model_history" not in st.session_state:
    st.session_state.ap_model_history = None

if "outline_text" not in st.session_state:
    st.session_state.outline_text = None

hp_session: HPGenerationSession = st.session_state.hp_session

# ===== レイアウト：左 = 入力 / 右 = 結果 =====
col_left, col_right = st.columns([1.3, 1.0])

# ---------------- 左側：入力とインタラクション ----------------
with col_left:
    st.header("ステップ 1：テーマと個人の経験を入力", divider="grey")

    with st.form("hp_input_form"):
        theme = st.text_input("SF物語のテーマ（例：AI教育、気候危機、メタバース社会 など）", value="")
        scene = st.text_area("物語の舞台設定（時間、場所、技術水準、社会状況など）", height=80)

        st.markdown("**Q1. 最近、「自分は他の人と違うかもしれない」と感じた行動はありますか？**（Mt：日常の空間とユーザー体験）")
        q1 = st.text_area("", key="q1", height=60)

        st.markdown("**Q2. その行動を実現するために、どのような製品・サービスを使っていますか？**（Mt：製品・サービス）")
        q2 = st.text_area("", key="q2", height=60)

        st.markdown("**Q3. なぜ、そのような製品・サービスを選んで使っているのだと思いますか？**（Mt：意味付け）")
        q3 = st.text_area("", key="q3", height=60)

        st.markdown("**Q4. その行動や選択を通じて、どのような自分でありたいと思っていますか？**（Mt：人々の価値観）")
        q4 = st.text_area("", key="q4", height=60)

        submitted = st.form_submit_button("▶ HPモデル生成（第1フェーズを開始）")

    if submitted:
        if not (q1 and q2 and q3 and q4):
            st.warning("4つの問いすべてに、簡単で構わないので入力してください。")
        else:
            with st.spinner("Tavily と GPT を用いて Mt / Mt-1 の構造および Mt+1 の候補を生成しています…"):
                # 1) 3つの入力
                hp_session.handle_input1(q1)
                hp_session.handle_input2(q2)
                hp_session.handle_input3(q3)
                # 2) Q4 に基づく Mt / Mt-1 のバックグラウンド連鎖を起動
                hp_session.start_from_values(q4)
                # 3) Mt+1 前衛的社会問題の候補（future_candidates_adv）を取得
                adv_candidates = hp_session.get_future_adv_candidates()

            st.session_state.adv_candidates = adv_candidates
            if adv_candidates:
                st.success("第1フェーズが完了しました。Mt+1 の「前衛的社会問題」の候補が生成されました。ステップ2で選択してください。")
            else:
                st.error("Mt+1 の「前衛的社会問題」の候補生成に失敗しました。少し時間をおいてから再度お試しください。")

    # ------ ステップ2：Mt+1 前衛的社会問題の選択 ------
    st.header("ステップ 2：Mt+1 の前衛的社会問題を選ぶ", divider="grey")

    adv_candidates = st.session_state.adv_candidates
    selected_adv_idx = None
    if adv_candidates:
        selected_adv_idx = st.radio(
            "以下の5つの候補から、未来社会（Mt+1）の中核となる「前衛的社会問題」を1つ選んでください：",
            options=list(range(len(adv_candidates))),
            format_func=lambda i: adv_candidates[i],
        )

        if st.button("▶ 前衛的社会問題を確定し、Mt+1 の他の候補を生成する", use_container_width=True):
            if selected_adv_idx is None:
                st.warning("候補を1つ選択してください。")
            else:
                hp_session.set_future_adv_choice(adv_candidates[selected_adv_idx])
                with st.spinner("前衛的社会問題に基づき、Mt+1 の目標・価値観・慣習・UXの候補を生成しています…"):
                    hp_session.generate_mtplus1_candidates()
                st.session_state.mtplus1_candidates = hp_session.mtplus1_candidates
                st.success("Mt+1 の4つの要素の候補が生成されました。ステップ3で5択を完了してください。")

    # ------ ステップ3：Mt+1 の4つの5択 ------ 
    st.header("ステップ 3：Mt+1 の5択を完成させる", divider="grey")

    mtplus1_candidates = st.session_state.mtplus1_candidates
    if mtplus1_candidates:
        goals_list = mtplus1_candidates["goals"] or []
        values_list = mtplus1_candidates["values"] or []
        habits_list = mtplus1_candidates["habits"] or []
        ux_list = mtplus1_candidates["ux_future"] or []

        if all([goals_list, values_list, habits_list, ux_list]):
            st.markdown("**(1) Mt+1：社会の目標**")
            idx_goals = st.radio(
                "未来社会が目指しているゴールとして、もっともしっくりくるものを選んでください：",
                options=list(range(len(goals_list))),
                format_func=lambda i: goals_list[i],
                key="idx_goals",
            )

            st.markdown("**(2) Mt+1：人々の価値観**")
            idx_values = st.radio(
                "未来の人々が共有している価値観として、もっともしっくりくるものを選んでください：",
                options=list(range(len(values_list))),
                format_func=lambda i: values_list[i],
                key="idx_values",
            )

            st.markdown("**(3) Mt+1：慣習化**")
            idx_habits = st.radio(
                "その価値観が日常生活にどのように「慣習」として根付いているか、もっとも近いものを選んでください：",
                options=list(range(len(habits_list))),
                format_func=lambda i: habits_list[i],
                key="idx_habits",
            )

            st.markdown("**(4) Mt+1：日常の空間とユーザー体験**")
            idx_ux = st.radio(
                "未来の典型的な日常空間・ユーザー体験として、イメージが湧くものを選んでください：",
                options=list(range(len(ux_list))),
                format_func=lambda i: ux_list[i],
                key="idx_ux",
            )

            if st.button("▶ 三世代のHPモデルを完成させる", type="primary", use_container_width=True):
                with st.spinner("Mt+1 の連鎖生成を行い、バックグラウンドで進行中の Mt / Mt-1 のスレッド完了を待機しています…"):
                    hp_session.apply_mtplus1_choices(idx_goals, idx_values, idx_habits, idx_ux)
                    hp_session.wait_all()
                    hp_json = hp_session.to_dict()
                st.session_state.hp_json = hp_json
                st.session_state.ap_model_history = [
                    {"ap_model": hp_json.get("hp_mt_0", {})},
                    {"ap_model": hp_json.get("hp_mt_1", {})},
                    {"ap_model": hp_json.get("hp_mt_2", {})},
                ]
                st.success("三世代のHPモデルが完成しました！右側のエリアでSF物語のアウトラインを生成できます。")
        else:
            st.info("ステップ2で前衛的社会問題を確定し、「Mt+1 の候補生成」ボタンを押してから再度お試しください。")

# ---------------- 右側：アウトライン生成 & ダウンロード ----------------
with col_right:
    st.header("ステップ 4：HPモデルからSF物語のアウトラインを生成", divider="grey")

    if st.session_state.hp_json and st.session_state.ap_model_history:
        # アウトライン生成ボタン
        if st.button("✨ SF物語のアウトラインを生成する", use_container_width=True):
            with st.spinner("GPT を用いて物語のアウトラインを生成しています…"):
                outline_text = generate_outline(
                    theme=theme or "（無題のテーマ）",
                    scene=scene or "（舞台設定が未記入）",
                    ap_model_history=st.session_state.ap_model_history,
                )
            st.session_state.outline_text = outline_text
            st.success("物語のアウトラインが生成されました。")

        outline_text = st.session_state.outline_text
        if outline_text:
            st.markdown("**現在の物語アウトライン：**")
            st.text_area("", value=outline_text, height=260, key="outline_display")

            # 修正要望
            st.markdown("**アウトラインを微調整したい場合は、下に修正要望を記入してください。**")
            modification = st.text_area("修正要望（任意）", height=90, key="modification")

            if st.button("🔁 修正要望に基づいてアウトラインを更新する", use_container_width=True):
                if not modification.strip():
                    st.warning("修正したいポイントを、ひとことでもよいので入力してください。")
                else:
                    with st.spinner("修正要望に基づいてアウトラインを再生成しています…"):
                        new_outline = modify_outline(outline_text, modification)
                    st.session_state.outline_text = new_outline
                    st.success("修正要望を反映したアウトラインに更新しました。")

            # ダウンロードボタン
            st.markdown("---")
            hp_json_str = json.dumps(st.session_state.hp_json, ensure_ascii=False, indent=2)
            st.download_button(
                "⬇️ HPモデルをダウンロード（hp_output.json）",
                data=hp_json_str,
                file_name="hp_output.json",
                mime="application/json",
                use_container_width=True,
            )

            st.download_button(
                "⬇️ 物語アウトラインをダウンロード（outline.txt）",
                data=st.session_state.outline_text,
                file_name="outline.txt",
                mime="text/plain",
                use_container_width=True,
            )
    else:
        st.info("左側のステップ1〜3で HPモデル（三世代）を生成してから、こちらでアウトライン生成を行ってください。")
