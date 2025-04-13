import json
import sys
import os
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

def main():
    # .envファイルから環境変数を読み込む
    load_dotenv(override=True)
    
    # コマンドライン引数を取得
    args = sys.argv[1:]  # 最初の引数(スクリプト名)を除く
    
    # 最初の引数をファイル名として使用
    filename = args[0] if args else 'wiki.json'

    # ファイルのパスを確認
    file_path = Path(filename)
    if not file_path.exists():
        print(f"エラー: ファイル '{filename}' が見つかりません。")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # OpenAI APIキーの設定
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("エラー: OPENAI_API_KEYが設定されていません。.envファイルを確認してください。")
        return
    
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not base_url:
        print("エラー: OPENAI_BASE_URLが設定されていません。OpenAIの公式apiに接続します。")
        base_url = "https://api.openai.com/v1"
    
    client = OpenAI(base_url=base_url, api_key=api_key)

    use_model = os.environ.get("OPENAI_USE_MODEL")
    if not use_model:
        print("エラー: OPENAI_USE_MODELが設定されていません。.envファイルを確認してください。")
        return
    
    # データからtextフィールドを抽出
    if "text" not in data[0]:
        print("エラー: 指定されたJSONファイルにtextフィールドがありません")
        return
    
    knowledge_text = data[0]["text"]
    
    # ユーザーに質問を入力してもらう
    user_query = f"""AIアシスタントに対してユーザーが依頼するであろうクエリをいくつか作成してください。
AIアシスタントは<knowledge>タグ内の文章を知識として備えており、ユーザーはAIアシスタントに対して質問や依頼を行います。

<knowledge>
{knowledge_text}
</knowledge>

# 作成してほしいクエリ
<knowledge>タグ内の知識について質問するクエリを5個ほど作成してください。このクエリには作品名を含めてください。
次に、<knowledge>タグ内の情報が答えとなるクエリを5個ほど作成してください。このクエリには作品名を含めません。
さらに、knowledge内の知識だけでは答えられないようなクエリも2個ほど混ぜてください。

これらクエリはひとつひとつを<query>タグで囲んでください。
<query>タグ内にはユーザーからのクエリのみを記載し、それ以外の内容を記載しないでください。

# 制約
- クエリには、「この作品」や「この人」といった主語をぼかす表現を使うことは禁止します。
"""
    
    # OpenAI APIを使用して回答を生成
    response = client.chat.completions.create(
        model=use_model,
        messages=[
            {"role": "user", "content": user_query}
        ]
    )
    
    # 応答を表示
    print("\n回答:")
    print(response.choices[0].message.content)

if __name__ == "__main__":
    main()
