# prompt.py
import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
from tavily import TavilyClient

client = OpenAI(api_key=st.secrets["openai"]["api_key"])
tavily_client = TavilyClient(api_key=st.secrets["tavily"]["api_key"])

HP_model = {
    1: "前衛的社会問題",
    2: "人々の価値観",
    3: "社会問題",
    4: "技術や資源",
    5: "日常の空間とユーザー体験",
    6: "制度",
    7: "メディア",
    8: "コミュニティ化",
    9: "文化芸術振興",
    10: "標準化",
    11: "コミュニケーション",
    12: "組織化",
    13: "意味付け",
    14: "製品・サービス",
    15: "習慣化",
    16: "パラダイム",
    17: "ビジネスエコシステム",
    18: "アート(社会批評)"
}

class Candidate(BaseModel):
    candidates: list[str]

#  System Prompt: 强调简洁性
SYSTEM_PROMPT = """君はサイエンスフィクションの専門家であり、「アーキオロジカル・プロトタイピング（HP）」モデルに基づいて社会を分析します。
君の任務は、ユーザーの具体的な「体験」と「価値観」を入力として受け取り、過去・現在・未来の3世代にわたる社会構造（18要素）を論理的かつ創造的に構築することです。

重要な指示:
1. 論理的接続: ステップ1でユーザーが入力した「体験(UX)」と「価値観」は、現在の社会(Mt)の核心です。未来(Mt+1)の予測や過去(Mt-1)の推定は、必ずこのユーザー入力と強い因果関係を持たせてください。
2. **簡潔性**: HPモデルの各要素（ノード）に入るテキストは、**原則50文字以内**の短いフレーズや単文にしてください。長々とした説明は避けてください。
3. 飛躍の回避: 脈絡のないSF的空想ではなく、入力された価値観が過激化・発展・あるいは反動として現れる未来を描いてください。

（以下、HPモデルの定義は省略しますが、各要素の役割に従ってください）
"""

def list_up_gpt(input_node: str, input_content: str, output_node: str, context: str = "") -> list[str]:
    context_str = f"なお、この社会の文脈・背景情報は以下の通りです：\n{context}\n" if context else ""
    
    prompt = f"""
HPモデルに基づき分析します。
【入力ノード】{input_node}
【内容】{input_content}
{context_str}
上記の入力内容（および文脈）から論理的に導き出される、【{output_node}】の未来の可能性を5つ挙げてください。

【制約】
- **各候補は50文字以内**で記述してください。
- ユーザーの入力した体験や価値観と断絶しないよう注意してください。

以下のJSON形式で出力してください：
{{ "candidates": ["内容1(50文字以内)", "内容2", "内容3", "内容4", "内容5"] }}
"""
    response = client.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=1.0,
        response_format=Candidate,
    )
    return response.choices[0].message.parsed.candidates

def single_gpt(input_node: str, input_content: str, output_node: str, context: str = "") -> str:
    context_str = f"文脈・背景情報：{context}\n" if context else ""
    prompt = f"""
HPモデルに基づき分析します。
【入力ノード】{input_node}
【内容】{input_content}
{context_str}
この内容を分析して、論理的に接続する【{output_node}】の内容を作成してください。

【制約】
- **50文字以内**で簡潔に記述してください。
- 余計な修飾語は省き、核心のみを出力してください。
- 出力は内容の文章のみにしてください。
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def generate_question_for_tavily(input_node: str, input_content: str, output_node: str, time: int) -> str:
    state = "過去" if time == 0 else "現在"
    prompt = f"""
{input_node}（{input_content}）という事象に基づき、HPモデルの要素「{output_node}」の{state}における状況を調査するための検索クエリを作成してください。
検索エンジンで有効な、具体的かつ自然な日本語の質問文を1つ出力してください。
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content + "\n**50文字以内**で簡潔に回答してください。"

def tavily_generate_answer(question: str) -> str:
    try:
        response = tavily_client.search(
            query=question,
            include_answer="advanced",
            search_depth="advanced",
            max_results=5,
        )
        # 検索結果も要約して短くする
        raw_answer = response.get("answer", "情報が見つかりませんでした。")
        # ここでGPTを使って要約させることも可能ですが、Tavilyのanswerは比較的まとまっているため、そのまま返すか、
        # 必要であればここで要約ロジックを入れることも可能です。今回は現状維持とします。
        return raw_answer
    except Exception as e:
        return f"検索エラー: {str(e)}"