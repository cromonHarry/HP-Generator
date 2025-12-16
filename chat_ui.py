import streamlit as st
from openai import OpenAI
import os 

# --- API クライアントと応答ロジック (変更なし) ---

def get_openai_client():
    try:
        api_key = st.secrets["openai"]["api_key"]
    except KeyError:
        api_key = os.environ.get("OPENAI_API_KEY") 
    if not api_key:
        st.error("エラー: OpenAI APIキーが設定されていません。")
        st.stop()
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"OpenAIクライアントの初期化中にエラーが発生しました: {e}")
        st.stop()


def get_ai_response(chat_history: list) -> str:
    client = get_openai_client()
    system_prompt = "あなたは親切なアシスタントです。ユーザーは「アーキオロジカル・プロトタイピング（HP）」モデルについて相談します。簡潔な言葉でユーザーにアドバイスしてください。すべての質問に日本語で丁寧に答えてください。"
    messages_for_api = [{"role": "system", "content": system_prompt}]
    messages_for_api.extend(chat_history)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_for_api, 
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI応答の取得中にエラーが発生しました: {e}"


def render_chat_ui(container):
    """
    StreamlitのUIをレンダリングし、チャットロジックを処理します。
    """
    with container:

        st.header("🤖 AIアシスタント")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
            
        
        # ===================================================
        # ⚠️ 1. ユーザー入力 (最上部)
        # ===================================================
        user_input = st.text_input("メッセージを入力", key="chat_input")
        
        # ===================================================
        # ⚠️ 2. 送信ボタン (2番目)
        # ===================================================
        if st.button("送信", key="btn_send"):
            if user_input.strip():
                # 1. ユーザーの新しい発言を履歴に追加
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                with st.spinner("AIが考えています…"):
                    # 2. 履歴全体を渡して応答を取得
                    ai_reply = get_ai_response(st.session_state.chat_history)
                        
                # 3. AIの応答を履歴に追加
                st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
                
                # 履歴が更新された後、UIを再描画するために reruun
                st.rerun() 

        # ===================================================
        # ⚠️ 3. チャット履歴 (3番目)
        # ===================================================
        
        st.markdown("---") # 操作系と履歴の視覚的な区切り
            
        for msg in st.session_state.chat_history:
            color = "#DCF8C6" if msg["role"] == "user" else "#F1F0F0"
            float_dir = "right" if msg["role"] == "user" else "left"
            
            # Markdownを使用してチャットバブル風に表示
            st.markdown(f"""
                <div style='background-color:{color}; padding:10px; border-radius:10px; margin:5px 0; max-width:70%; float:{float_dir}; clear:both; color:black;'>
                    {msg['content']}
                </div>
            """, unsafe_allow_html=True)
            
        # 画面下部にスペーサー
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

        # ===================================================
        # ⚠️ 4. 清空ボタン (最下部)
        # ===================================================
        if st.button("🔄 清空記憶", key="btn_clear_bottom", help="会話履歴とAIの記憶をリセットします"):
            # 履歴をリセット
            st.session_state.chat_history = []
            # 刷新 UI
            st.rerun()


# --- アプリケーションのエントリポイント ---

if __name__ == '__main__':
    st.set_page_config(layout="centered", page_title="AIアシスタント")
    render_chat_ui(st.container())