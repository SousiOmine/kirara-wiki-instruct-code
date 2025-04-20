import json
import os

def main():
    articles = input_articles()
    
    # 既存のデータを読み込む（存在する場合）
    existing_data = []
    if os.path.exists('syudou.json'):
        with open('syudou.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    
    # 新しいデータを追加して保存
    combined_data = existing_data + articles
    with open('syudou.json', 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=4)

def input_articles():
    """
    ユーザーが手動で記事本文を入力する（複数行対応）
    """
    articles = []
    print("記事本文を入力してください ('q'で終了)")
    
    while True:
        print("新しい記事を開始します ('q'で終了)")
        lines = []
        
        while True:
            line = input("> ").strip()
            if line.lower() == 'q':
                break
            lines.append(line)
        
        if not lines:
            break
            
        text = '\n'.join(lines)
        articles.append({
            'title': text[:10],  # 最初の10文字をタイトルに
            'text': text,
            'source': ""
        })
        
        print(f"{len(articles)}件目の記事を追加しました。\n")
    
    return articles

if __name__ == "__main__":
    main()
