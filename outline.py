from prompt import *
import json
# 读取 JSON 文件
with open("hp_output.json", "r", encoding="utf-8") as f:
    data = json.load(f)
# 将已读取的 data 映射为 generate_outline 所需的 ap_model_history（3 段）
ap_model_history = [
    {"ap_model": data.get("hp_mt_0", {})},  # Stage 1 (背景)
    {"ap_model": data.get("hp_mt_1", {})},  # Stage 2 (开始)
    {"ap_model": data.get("hp_mt_2", {})},  # Stage 3 (结尾)
]

# ========== Story Generation Functions ==========
def generate_outline(client, theme: str, scene: str, ap_model_history: list) -> str:
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
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}])
    return response.choices[0].message.content


def modify_part(outline):
    # ユーザーの修正意見を取得（日本語）
    modification_request = input("\nユーザーの修正内容は何ですか？ (修正意見を入力してください): ")
    
    # Promptを構築（日本語）
    prompt = f"""あなたはプロのSF作家です。
    
    【ユーザーの修正意見】に基づき、【元のストーリー概要】を調整してください。
    
    【ユーザーの修正意見】：
    {modification_request}
    
    【元のストーリー概要】：
    {outline}
    
    ユーザーの修正意見に基づき、ストーリー概要の関連部分を調整し、物語の一貫性を保ち、ユーザーの要求に合致させてください。修正後の完全なストーリー概要を出力してください。
    上記の情報を基に、指定された設定で展開される主要なプロット、キャラクター、中心的な対立を含む、革新的で魅力的なSF小説のスタイルに従った物語のあらすじを作成してください。
    """
    
    # デバッグ情報を表示（日本語）
    print("\n--- [デバッグ情報] GPT-4oにリクエストを送信中... ---")
    
    # APIを呼び出し
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}])
    return response.choices[0].message.content





#后面可放入app.py内
print("生成中...")
outline = generate_outline(client, " ", " ", ap_model_history)
print("生成されたストーリー概要:\n", outline)

while True:
    choice = input("\n--- 修正はありますか？ (y/n): ")
    modified_outline = modify_part(outline)
    # 修正結果を表示（日本語）
    print("\n修正後のストーリー概要:\n", modified_outline)
            
    # 5. ユーザーに継続可否を質問
    choice = input("\n--- 修正を続けますか？ (y/n): ")
        
    # 6. 終了条件をチェック
    if choice.lower().strip() != 'y':
        print("\n--- 修正が完了しました。ご利用ありがとうございました！ ---")
        break # while ループを抜ける
        
