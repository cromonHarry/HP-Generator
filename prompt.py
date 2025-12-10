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

#  プロンプトの改善：論理性と文脈の結合を強調
SYSTEM_PROMPT = """君はサイエンスフィクションの専門家であり、「アーキオロジカル・プロトタイピング（HP）」モデルに基づいて社会を分析します。
君の任務は、ユーザーの具体的な「体験」と「価値観」を入力として受け取り、過去・現在・未来の3世代にわたる社会構造（18要素）を論理的かつ創造的に構築することです。

重要な指示:
1. 論理的接続: ステップ1でユーザーが入力した「体験(UX)」と「価値観」は、現在の社会(Mt)の核心です。未来(Mt+1)の予測や過去(Mt-1)の推定は、必ずこのユーザー入力と強い因果関係を持たせてください。
2. 飛躍の回避: 脈絡のないSF的空想ではなく、入力された価値観が過激化・発展・あるいは反動として現れる未来を描いてください。

HPモデル定義:
（対象6項目・矢12項目は標準定義に従う）
1. 前衛的社会問題: 技術革新や社会変化によって新たに生まれる歪み。
2. 人々の価値観: 社会問題に対して人々が抱く理想や倫理観。
3. 社会問題: 多くの人が認識している解決すべき課題。
4. 技術や資源: 社会を動かす物理的・デジタルな基盤。
5. 日常の空間とユーザー体験(UX): 人々が製品・サービスを通じて得る具体的な体験。
6. 制度: 法律、慣習、ルール。
"""

def list_up_gpt(input_node: str, input_content: str, output_node: str, context: str = "") -> list[str]:
    #  文脈(context)を追加して、入力内容との乖離を防ぐ
    context_str = f"なお、この社会の文脈・背景情報は以下の通りです：\n{context}\n" if context else ""
    
    prompt = f"""
HPモデルに基づき分析します。
【入力ノード】{input_node}
【内容】{input_content}
{context_str}
上記の入力内容（および文脈）から論理的に導き出される、【{output_node}】の未来の可能性を5つ挙げてください。
ユーザーの入力した体験や価値観と断絶しないよう注意し、想像力を広げてください。

以下のJSON形式で出力してください：
{{ "candidates": ["内容1", "内容2", "内容3", "内容4", "内容5"] }}
"""
    response = client.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=1.0, # 少し創造性を担保
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
出力は内容の文章のみにしてください。
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
    return response.choices[0].message.content

def tavily_generate_answer(question: str) -> str:
    try:
        response = tavily_client.search(
            query=question,
            include_answer="advanced",
            search_depth="advanced",
            max_results=5,
        )
        return response.get("answer", "情報が見つかりませんでした。")
    except Exception as e:
        return f"検索エラー: {str(e)}"

# 旧的 user_choose_answer 在 Streamlit 里不会再用，保留兼容即可
def user_choose_answer(answer_list: list[str]) -> str:
    for i, a in enumerate(answer_list, start=1):
        print(f"{i}: {a}\n")
    return answer_list[int(input("どの回答を選択しますか？")) - 1]
