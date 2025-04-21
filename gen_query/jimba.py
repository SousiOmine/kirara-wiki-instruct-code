import json
import sys
import os
import re #正規表現モジュールをインポート
import uuid
import random
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datasets import load_dataset

# キャッシュディレクトリの設定
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

def load_json_file(input_filename):
    with open(input_filename, 'r', encoding='utf-8') as f:
        try:
            data_list = json.load(f)
            if not isinstance(data_list, list) or not data_list:
                 print(f"エラー: '{input_filename}' は空か、JSONオブジェクトのリストではありません。リストの最初の要素のみ使用します。")
                 if isinstance(data_list, dict):
                     data = data_list
                 else:
                     return
            else:
                data = data_list
        except json.JSONDecodeError:
            print(f"エラー: ファイル '{input_filename}' は有効なJSONではありません。")
            return
        except Exception as e:
            print(f"エラー: ファイル '{input_filename}' の読み込み中にエラーが発生しました: {e}")
            return
        return data

def generate_queries(knowledge_text, cache_id=None):
    # キャッシュチェック
    if cache_id:
        cache_file = CACHE_DIR / f"{cache_id}.json"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)

    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    use_model = os.environ.get("OPENAI_USE_MODEL")

    client = OpenAI(base_url=base_url, api_key=api_key)

    user_query_prompt = f"""AIアシスタントに対してユーザーが依頼するであろうクエリを10個ほど作成してください。
<knowledge>
{knowledge_text}
</knowledge>

# 作成してほしいクエリ
以下に例としてクエリを3つ提示するので、これを参考にしてください
<example_queries>
{random.sample(load_example_instruction_dataset(), 3)}
</example_queries>

これらクエリはひとつひとつを<query>タグで囲んでください。
<query>タグ内にはユーザーからのクエリのみを記載し、それ以外の内容を記載しないでください。

# 制約
- クエリには、「この作品」や「この人」といった主語をぼかす表現を使うことは禁止します。
- 作品名や人名、作中の固有名詞のいずれかは必ずクエリ内で用いてください。また、作品名や人名はかぎかっこで囲わずに記載してください。
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
    
    result = {
        "queries": queries, 
        "user_query_prompt": user_query_prompt, 
        "generated_text": generated_text
    }
    
    # キャッシュ保存
    if cache_id:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False)
    
    return result

def process_item(item, cache_id):
    return generate_queries(item["text"], cache_id)

def load_example_instruction_dataset(dataset_name="Kendamarron/jimba-instuction-1k-beta"):
    """Hugging Faceのデータセットからinstructionを読み込む"""
    try:
        dataset = load_dataset(dataset_name)
        instructions = [item["instruction"] for item in dataset["train"]]
        return instructions
    except Exception as e:
        print(f"エラー: データセットの読み込み中にエラーが発生しました: {e}")
        return []

def main():
    load_dotenv(override=True)
    args = sys.argv[1:]  
    
    # 新しいオプションを解析
    single_mode = False
    if '--single' in args:
        single_mode = True
        args.remove('--single')
    
    input_filename = args[0] if args else 'wiki.json'
    output_filename = args[1] if len(args) > 1 else 'generated_queries.json'
    text_and_prompt_filename = args[2] if len(args) > 2 else 'text_and_prompt.json'

    input_file_path = Path(input_filename)
    if not input_file_path.exists():
        print(f"エラー: ファイル '{input_filename}' が見つかりません。")
        return

    data = load_json_file(input_file_path)
    if not data:
        return
    
    # singleモードの場合、ランダムなアイテム1つを処理
    if single_mode:
        data = [random.choice(data)] if isinstance(data, list) else [data]
        print(f"単一knowledgeモードで実行します。ランダムに選択されたknowledgeを処理します。")
        print(f"選択されたknowledge: {data[0]['text'][:100]}...")

    # 並列処理
    start_time = time.time()
    processed_items = []
    skipped_items = 0

    max_workers = 5
    if(single_mode):
        max_workers = 1
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for item in data:
            cache_id = str(uuid.uuid5(uuid.NAMESPACE_URL, item["text"]))
            futures.append(executor.submit(process_item, item, cache_id))
        
        for i, future in enumerate(as_completed(futures)):
            try:
                result = future.result()
                if result:
                    # 元のアイテムのインデックスを保持
                    original_index = futures.index(future)
                    processed_items.append({
                        "result": result,
                        "original_index": original_index
                    })
                    print(f"処理済み: {original_index+1}/{len(data)}")
                else:
                    skipped_items += 1
            except Exception as e:
                print(f"エラー: アイテム処理中にエラーが発生しました: {e}")
    
    # 結果を結合
    all_queries = []
    text_and_prompt = []
    
    for item in processed_items:
        result = item["result"]
        original_index = item["original_index"]
        
        for query in result["queries"]:
            all_queries.append({
                "id": str(uuid.uuid4()),
                "text": data[original_index]["text"],
                "query": query
            })
        
        text_and_prompt.append({
            "text": data[original_index]["text"],
            "user_query_prompt": result["user_query_prompt"],
            "generated_text": result["generated_text"]
        })
    
    # 保存
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_queries, f, ensure_ascii=False, indent=2)
    with open(text_and_prompt_filename, 'w', encoding='utf-8') as f:
        json.dump(text_and_prompt, f, ensure_ascii=False, indent=2)
    
    print(f"\n完了! {len(all_queries)}個のクエリを生成しました (スキップ: {skipped_items})")
    print(f"所要時間: {time.time()-start_time:.2f}秒")
    print(f"生成されたクエリを '{output_filename}' に保存しました。")
    print(f"生成されたtext_and_promptを '{text_and_prompt_filename}' に保存しました。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nプログラムを終了します")
        sys.exit(0)
