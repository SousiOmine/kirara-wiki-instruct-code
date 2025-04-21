import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import random

CACHE_DIR = Path("cache")

def load_queries(input_filename):
    with open(input_filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def process_single_query(query_data, client, use_model):
    """単一クエリを処理"""
    query = query_data["query"]
    knowledge = query_data["text"]

    system_prompt = f"""あなたは親切なAIアシスタントです。一般常識のほかに、以下の知識を考慮して、質問に答えてください。

<knowledge>
{knowledge}
</knowledge>

# 注意点
- あなたはインターネットにアクセスできないため、最新の状況を取得することはできません。
- たまにあなたの知らないことを聞かれることがあります。知らない場合は知らないということを述べ、そのうえで回答を行ってください。
    """
    
    prompt = f"""{query}
"""
    
    try:
        response = client.chat.completions.create(
            model=use_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content
        
        return {
            "id": query_data["id"],
            "query": query,
            "answer": answer,
            "knowledge": knowledge
        }
        
    except Exception as e:
        print(f"エラー: クエリ '{query}' の処理中にエラーが発生しました: {e}")
        return None

def generate_answers(queries):
    load_dotenv(override=True)
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    use_model = os.environ.get("OPENAI_USE_MODEL", "gpt-4o-mini")

    client = OpenAI(base_url=base_url, api_key=api_key)
    
    # キャッシュディレクトリ作成
    CACHE_DIR.mkdir(exist_ok=True)
    
    results = []
    
    # 進捗表示用カウンタ
    progress_counter = 0
    total_queries = len(queries)
    
    # スキップ済みクエリと未処理クエリを分離
    pending_queries = []
    for query_data in queries:
        cache_file = CACHE_DIR / f"{query_data['id']}.jsonl"
        
        if cache_file.exists():
            print(f"キャッシュから読み込み中: {query_data['id']}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                for line in f:
                    results.append(json.loads(line))
        else:
            pending_queries.append(query_data)
    
    # 並列処理 (20並列)
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(process_single_query, query_data, client, use_model)
            for query_data in pending_queries
        ]
        
        for future in as_completed(futures):
            progress_counter += 1
            print(f"処理中: {progress_counter}/{total_queries} ({progress_counter/total_queries*100:.1f}%)")
            result = future.result()
            if result:
                # 結果をキャッシュに保存
                cache_file = CACHE_DIR / f"{result['id']}.jsonl"
                with open(cache_file, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
                
                results.append(result)
    
    return results

def main():
    import argparse
    import random
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, default="../gen_query/generated_queries.json", 
                       help='入力JSONファイルのパス')
    parser.add_argument('--test', action='store_true', help='テストモード: ランダムに10個のクエリだけ処理')
    args = parser.parse_args()
    
    output_file = "generated_answers.jsonl"
    
    queries = load_queries(args.input)
    
    if args.test:
        queries = random.sample(queries, min(10, len(queries)))
        print(f"テストモード: {len(queries)}個のクエリを処理します")
    
    answers = generate_answers(queries)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for answer in answers:
            f.write(json.dumps(answer, ensure_ascii=False) + '\n')
    
    print(f"生成された回答を '{output_file}' に保存しました。")

if __name__ == "__main__":
    main()
