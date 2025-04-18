import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

CACHE_DIR = Path("cache")

def load_queries(input_filename):
    with open(input_filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def process_single_query(query_data, client, use_model):
    """単一クエリを処理"""
    query = query_data["query"]
    knowledge = query_data["text"]
    
    prompt = f"""以下の知識に基づいて質問に答えてください。

<knowledge>
{knowledge}
</knowledge>

質問: {query}
"""
    
    try:
        response = client.chat.completions.create(
            model=use_model,
            messages=[
                {"role": "system", "content": "あなたは知識に基づいて質問に答えるAIアシスタントです。"},
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
    use_model = os.environ.get("OPENAI_USE_MODEL", "gpt-3.5-turbo")

    client = OpenAI(base_url=base_url, api_key=api_key)
    
    # キャッシュディレクトリ作成
    CACHE_DIR.mkdir(exist_ok=True)
    
    results = []
    
    # スキップ済みクエリと未処理クエリを分離
    pending_queries = []
    for query_data in queries:
        cache_file = CACHE_DIR / f"{query_data['id']}.jsonl"
        
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                for line in f:
                    results.append(json.loads(line))
        else:
            pending_queries.append(query_data)
    
    # 並列処理 (5並列)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(process_single_query, query_data, client, use_model)
            for query_data in pending_queries
        ]
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                # 結果をキャッシュに保存
                cache_file = CACHE_DIR / f"{result['id']}.jsonl"
                with open(cache_file, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
                
                results.append(result)
    
    return results

def main():
    input_file = "../gen_query/generated_queries.json"
    output_file = "generated_answers.jsonl"
    
    queries = load_queries(input_file)
    answers = generate_answers(queries)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for answer in answers:
            f.write(json.dumps(answer, ensure_ascii=False) + '\n')
    
    print(f"生成された回答を '{output_file}' に保存しました。")

if __name__ == "__main__":
    main()
