import json
import sys
import os
import re #正規表現モジュールをインポート
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

def load_json_file(input_filename):
    with open(input_filename, 'r', encoding='utf-8') as f:
        try:
            # JSONファイルがオブジェクトのリストであることを期待
            data_list = json.load(f)
            if not isinstance(data_list, list) or not data_list:
                 print(f"エラー: '{input_filename}' は空か、JSONオブジェクトのリストではありません。リストの最初の要素のみ使用します。")
                 # もしリストでない単一オブジェクトならリストに入れる
                 if isinstance(data_list, dict):
                     data = data_list
                 else:
                     return # リストでも辞書でもなければ終了
            else:
                data = data_list
        except json.JSONDecodeError:
            print(f"エラー: ファイル '{input_filename}' は有効なJSONではありません。")
            return
        except Exception as e:
            print(f"エラー: ファイル '{input_filename}' の読み込み中にエラーが発生しました: {e}")
            return
        return data


def generate_queries(knowledge_text):
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    use_model = os.environ.get("OPENAI_USE_MODEL")

    client = OpenAI(base_url=base_url, api_key=api_key)

    user_query_prompt = f"""AIアシスタントに対してユーザーが依頼するであろうクエリをいくつか作成してください。
AIアシスタントは<knowledge>タグ内の文章を知識として備えており、ユーザーはAIアシスタントに対して質問や依頼を行います。

<knowledge>
{knowledge_text}
</knowledge>

# 作成してほしいクエリ
<knowledge>タグ内の知識について質問するクエリを5個ほど作成してください。このクエリには作品名を含めてください。（ただし作品名はかっこで囲ったりはしないこと）
次に、<knowledge>タグ内の情報が答えとなるクエリを5個ほど作成してください。このクエリには作品名を含めません。
さらに、knowledge内の知識だけでは答えられないようなクエリも2個ほど混ぜてください。

これらクエリはひとつひとつを<query>タグで囲んでください。
<query>タグ内にはユーザーからのクエリのみを記載し、それ以外の内容を記載しないでください。

# 制約
- クエリには、「この作品」や「この人」といった主語をぼかす表現を使うことは禁止します。
"""
    
    try:
        response = client.chat.completions.create(
            model=use_model,
            messages=[
                {"role": "user", "content": user_query_prompt}
            ]
        )
        generated_text = response.choices[0].message.content
    except Exception as e:
        print(f"エラー: OpenAI API呼び出し中にエラーが発生しました: {e}")
        return
    
    queries = re.findall(r'<query>(.*?)</query>', generated_text, re.DOTALL)

    return queries, user_query_prompt, generated_text
    

def main():
    # .envファイルから環境変数を読み込む
    load_dotenv(override=True)
    
    # コマンドライン引数を取得
    args = sys.argv[1:]  # 最初の引数(スクリプト名)を除く
    
    # 最初の引数をファイル名として使用
    input_filename = args[0] if args else 'wiki.json'
    # 2番目の引数を出力ファイル名として使用（なければデフォルト）
    output_filename = args[1] if len(args) > 1 else 'generated_queries.json'

    # 入力ファイルのパスを確認
    input_file_path = Path(input_filename)
    if not input_file_path.exists():
        print(f"エラー: ファイル '{input_filename}' が見つかりません。")
        return

    data = load_json_file(input_file_path)

    queries, user_query_prompt, generated_text = generate_queries(data[0]["text"])

    # 結果を格納するリスト
    results = []

    # 抽出したクエリごとにJSONオブジェクトを作成
    for query in queries:
        result_item = {
            "title": data[0].get("title"),
            "text": data[0].get("text"),
            "source": data[0].get("source"),
            "prompt": user_query_prompt,
            "generated_text": generated_text, # LLMが生成したテキスト全体
            "query": query.strip() # 前後の空白を削除
        }
        results.append(result_item)

    # 結果をJSONファイルに保存
    output_file_path = Path(output_filename)
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"生成されたクエリを '{output_filename}' に保存しました。")
    except Exception as e:
        print(f"エラー: ファイル '{output_filename}' への書き込み中にエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
