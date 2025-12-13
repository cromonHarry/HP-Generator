# chat_ui.py
import streamlit as st
from openai import OpenAI

def get_openai_client():
    return OpenAI(api_key=st.secrets["openai"]["api_key"])

def get_ai_response(user_input: str):
    client = get_openai_client()
    prompt = f"あなたは親切なアシスタントです。以下の質問に日本語で丁寧に答えてください:\n{user_input}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500
    )
    return response.choices[0].message.content

def render_chat_ui(container):
    with container:

        st.header("🤖 AIアシスタント")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # 用户输入
        user_input = st.text_input("メッセージを入力", key="chat_input")

        if st.button("送信", key="btn_send"):
            if user_input.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                with st.spinner("AIが考えています…"):
                    ai_reply = get_ai_response(user_input)
                st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
                #st.session_state.chat_input = ""  # 发送后清空输入框

        # 显示聊天记录气泡
        for msg in st.session_state.chat_history:
            color = "#DCF8C6" if msg["role"] == "user" else "#F1F0F0"
            float_dir = "right" if msg["role"] == "user" else "left"
            st.markdown(f"""
                <div style='background-color:{color}; padding:10px; border-radius:10px; margin:5px 0; max-width:70%; float:{float_dir}; clear:both; color:black;'>
                    {msg['content']}
                </div>
            """, unsafe_allow_html=True)
