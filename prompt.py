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
##対象
1. 前衛的社会問題: 技術や資源のパラダイムによって引き起こされる社会問題や日常生活が営まれる空間やそこでのユーザーの体験に対してアート(社会批評)を介して顕在化される社会問題。
2. 人々の価値観: 文化芸術振興を通して広められる前衛的社会問題や日常のコミュニケーションによって広められる制度で対応できない社会問題に共感する人々のありたい姿。この問題は誰もが認識しているのではなく、ある一部の先進的な/マイノリティの人々のみが認識する。具体的には、マクロの環境問題(気候・生態など)と人文環境問題(倫理・経済・衛生など)が含まれる。
3. 社会問題: 前衛的問題に取り組む先進的なコミュニティによって社会に認識される社会問題やメディアを介して暴露される制度で拘束された社会問題。社会において解決すべき対象として顕在化される。
4. 技術や資源: 日常生活のルーティンを円滑に機能させるために作られた制度のうち、標準化されて過去から制約を受ける技術や資源であり、社会問題を解決すべく組織化された組織(営利・非営利法人、法人格を持たない集団も含み、新規・既存を問わない)が持つ技術や資源。
5. 日常の空間とユーザー体験: 技術や資源を動員して開発された製品・サービスによって構成される物理的空間であり、その空間で製品・サービスに対してある価値観のもとでの意味づけを行い、それらを使用するユーザーの体験。価値観とユーザー体験の関係性は、例えば、「AI エンジニアになりたい」という価値観を持った人々が、PC に対して「プログラミングを学習するためのもの」という意味づけを行い、「プログラミング」という体験を行う、というようなものである。
6. 制度: ある価値観を持った人々が日常的に行う習慣をより円滑に行うために作られる制度や、日常の空間とユーザー体験を構成するビジネスを行う関係者(ビジネスエコシステム)がビジネスをより円滑に行うために作られる制度。具体的には、法律やガイドライン、業界標準、行政指導、モラルが挙げられる。

##矢
1. メディア : 現代の制度的欠陥を顕在化させるメディア。マスメディアやネットメディア等の主要なメディアに加え、情報発信を行う個人も含まれる。制度を社会問題に変換させる。(制度 -> 社会問題)
2. コミュニティ化: 前衛的な問題を認識する人々が集まってできるコミュニティ。公式か非公式かは問わない。前衛的社会問題を社会問題に変換させる。 (前衛的社会問題 -> 社会問題)
3. 文化芸術振興: アート(社会批評)が顕在化させた社会問題を作品として展示し、人々に伝える活動。前衛的社会問題を人々の価値観に変換させる。 (前衛的社会問題 -> 人々の価値観)
4. 標準化 : 制度の中でも、よりり広い関係者に影響を与えるために行われる制度の標準化。制度を新しい技術・資源に変換させる。 (制度 -> 技術・資源)
5. コミュニケーション: 社会問題をより多くの人々に伝えるためのコミュニケーション手段。例えば、近年は SNS を介して行われることが多い。社会問題を人々の価値観に変換させる。 (社会問題 -> 人々の価値観)
6. 組織化 : 社会問題を解決するために形成される組織。法人格の有無や新旧の組織かは問わず 、新しく生まれた社会問題に取り組む全ての組織。社会問題を新しい技術・資源に変換させる。 (社会問題 -> 技術・資源)
7. 意味付け : 人々が価値観に基づいて製品やサービスを使用する理由。人々の価値観を新しい日常の空間とユーザー体験に変換させる。 (人々の価値観 -> 日常の空間とユーザー体験)
8. 製品・サービス: 組織が保有する技術や資源を利用して創造する製品やサービス。技術・資源を日常の空間とユーザー体験に変換させる。 (技術・資源 -> 日常の空間とユーザー体験)
9. 習慣化 : 人々が価値観に基づいて行う習慣。人々の価値観を制度に変換させる。 (人々の価値観 -> 制度)
10. パラダイム : その時代の支配的な技術や資源として、次世代にも影響をもたらすもの。技術・資源を前衛的社会問題に変換させる。 (技術・資源 -> 前衛的社会問題)
11. ビジネスエコシステム : 日常の空間やユーザー体験を維持するために、構成する製品・サービスに関わる関係者が形成するネットワーク 。日常の空間とユーザー体験を制度に変換させる。 (日常の空間とユーザー体験 -> 制度)
12. アート(社会批評): 人々が気づかない問題を、主観的/内発的な視点で捉える人の信念。日常の空間とユーザー体験に違和感を持ち、問題を提示する役割を持つ。日常の空間とユーザー体験を前衛的社会問題に変換させる。 (日常の空間とユーザー体験 -> 前衛的社会問題)
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
