# outline.py
import json
from prompt import SYSTEM_PROMPT, client

def build_ap_model_history_from_dict(data: dict) -> list[dict]:
    """
    data 结构与 hp_output.json 一致时，把它转换成 outline 需要的 ap_model_history。
    """
    return [
        {"ap_model": data.get("hp_mt_0", {})},
        {"ap_model": data.get("hp_mt_1", {})},
        {"ap_model": data.get("hp_mt_2", {})},
    ]

def generate_outline(theme: str, scene: str, ap_model_history: list[dict]) -> str:
    prompt = f"""
あなたはプロのSF作家です。以下の情報に基づき、テーマ「{theme}」の短編SF小説のあらすじを作成してください。
## 物語の舞台設定:
{scene}
## 物語の序盤（Sカーブ ステージ2）:
{json.dumps(ap_model_history[1]['ap_model'], ensure_ascii=False, indent=2)}
## 物語の結末（Sカーブ ステージ3）:
{json.dumps(ap_model_history[2]['ap_model'], ensure_ascii=False, indent=2)}
## 物語の背景（Sカーブ ステージ1）:
{json.dumps(ap_model_history[0]['ap_model'], ensure_ascii=False, indent=2)}
上記の情報に基づき、指定された舞台設定で展開される主要なプロット、登場人物、中心的な対立を含む、革新的で魅力的なSF小説のスタイルに従った物語のあらすじを作成してください。
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content

def modify_outline(outline: str, modification_request: str) -> str:
    """
    根据用户修正意见调整故事大纲（无 input()，给 Streamlit 调用）。
    """
    prompt = f"""あなたはプロのSF作家です。

【ユーザーの修正意見】に基づき、【元のストーリー概要】を調整してください。

【ユーザーの修正意見】：
{modification_request}

【元のストーリー概要】：
{outline}

ユーザーの修正意見に基づき、ストーリー概要の関連部分を調整し、物語の一貫性を保ち、ユーザーの要求に合致させてください。修正後の完全なストーリー概要を出力してください。
上記の情報を基に、指定された設定で展開される主要なプロット、キャラクター、中心的な対立を含む、革新的で魅力的なSF小説のスタイルに従った物語のあらすじを作成してください。
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content
